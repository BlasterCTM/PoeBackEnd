"""Cliente auxiliar para Azure Key Vault.

Proporciona helpers asíncronos sencillos para leer secretos desde Azure Key Vault
usando `DefaultAzureCredential`. Funciona localmente con `az login` y en Azure
con identidades administradas (asignada al sistema o asignada al usuario).

Variables de entorno soportadas:
- `AZURE_KEY_VAULT_NAME` (ej. my-keyvault) O
- `AZURE_KEY_VAULT_URL`  (ej. https://my-keyvault.vault.azure.net/)

Uso:
    await init_key_vault(["DB_PASSWORD", "API_KEY"])
    val = await get_secret("DB_PASSWORD")
"""
from __future__ import annotations

import os
import json
from typing import Optional, Dict, List

try:
    from azure.identity.aio import DefaultAzureCredential
    from azure.keyvault.secrets.aio import SecretClient
except Exception:  # pragma: no cover - paquetes faltantes
    DefaultAzureCredential = None
    SecretClient = None

_cache: Dict[str, str] = {}
_client: Optional[SecretClient] = None


def _vault_url_from_env() -> Optional[str]:
    name = os.getenv("AZURE_KEY_VAULT_NAME")
    url = os.getenv("AZURE_KEY_VAULT_URL")
    if url:
        return url
    if name:
        return f"https://{name}.vault.azure.net/"
    return None


async def init_key_vault(secret_names: Optional[List[str]] = None) -> None:
    """Inicializa el SecretClient y opcionalmente precarga una lista de secretos.

    Esta función es segura de llamar cuando los paquetes de Azure no están
    instalados; en ese caso no realizará ninguna acción (no-op).
    """
    global _client
    if DefaultAzureCredential is None or SecretClient is None:
        return

    vault_url = _vault_url_from_env()
    if not vault_url:
        return

    cred = DefaultAzureCredential()
    _client = SecretClient(vault_url=vault_url, credential=cred)

    if secret_names:
        for name in secret_names:
            try:
                val = await _client.get_secret(name)
                _cache[name] = val.value
            except Exception:
                # ignorar fallos al leer secretos opcionales durante el inicio
                continue


async def get_secret(name: str, fallback_env: Optional[str] = None) -> Optional[str]:
    """Obtiene el valor de un secreto por su nombre.

    Orden de resolución:
    1. valor en caché del cliente de Key Vault (si ya fue obtenido)
    2. lectura desde Key Vault (si el cliente está disponible)
    3. fallback a la variable de entorno llamada `fallback_env` o `name`
    """
    # cached
    if name in _cache:
        return _cache[name]

    # try Key Vault
    if _client is not None:
        try:
            secret = await _client.get_secret(name)
            _cache[name] = secret.value
            return secret.value
        except Exception:
            pass

    # fallback to env var
    if fallback_env and fallback_env in os.environ:
        return os.environ.get(fallback_env)
    return os.environ.get(name)


def get_secret_sync(name: str, fallback_env: Optional[str] = None) -> Optional[str]:
    """Helper síncrono que lee solo de la caché o de las variables de entorno.

    Usar esto desde código síncrono donde el cliente asíncrono no está disponible.
    No intentará llamadas de red a Key Vault.
    """
    if name in _cache:
        return _cache[name]
    if fallback_env and fallback_env in os.environ:
        return os.environ.get(fallback_env)
    return os.environ.get(name)


async def close_client() -> None:
    """Cierra el SecretClient y las credenciales subyacentes si existen."""
    global _client
    if _client is not None:
        try:
            await _client.close()
        except Exception:
            pass
        _client = None
