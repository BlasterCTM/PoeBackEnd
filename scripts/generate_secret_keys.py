#!/usr/bin/env python3
"""
Script para generar claves secretas seguras para producción
"""
import secrets

def generate_secret_key(length=64):
    """Genera una clave secreta segura"""
    return secrets.token_urlsafe(length)

if __name__ == "__main__":
    print("\n" + "="*70)
    print("CLAVES SECRETAS PARA AZURE APP SERVICE")
    print("="*70)
    print("\nCopia estas claves a las variables de entorno de Azure:\n")
    
    secret_key = generate_secret_key()
    refresh_key = generate_secret_key()
    
    print(f"SECRET_KEY={secret_key}")
    print(f"\nREFRESH_SECRET_KEY={refresh_key}")
    
    print("\n" + "="*70)
    print("⚠️  IMPORTANTE: Guarda estas claves de forma segura")
    print("⚠️  NO las compartas ni las incluyas en el repositorio")
    print("="*70 + "\n")
