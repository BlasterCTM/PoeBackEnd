from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
  PROJECT_NAME: str = "POE - Path Optimization Engine"
  PROJECT_VERSION: str = "1.0.0"
  PROJECT_DESCRIPTION: str = "API para el motor de optimización de rutas"

  # Configuración de seguridad
  SECRET_KEY: str = "tu_secret_key_super_secreta"  # Deberías cambiar esto en producción
  REFRESH_SECRET_KEY: str = "tu_refresh_secret_key_super_secreta"  # Clave diferente para refresh tokens
  ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # 1 hora para access token
  REFRESH_TOKEN_EXPIRE_DAYS: int = 60  # 60 días para refresh token

  # Configuración de límites de tareas
  MAX_TAREAS_PENDIENTES_POR_REPONEDOR: int = 5  # Máximo de tareas pendientes por reponedor

  # Selección de origen de base de datos
  DATABASE_TARGET: str = "local"  # Opciones: "local", "azure"

  # Conexión a base de datos Postgres (local por defecto)
  DATABASE_URL: Optional[str] = None
  POSTGRES_USER: Optional[str] = None
  POSTGRES_PASSWORD: Optional[str] = None
  POSTGRES_HOST: Optional[str] = None
  POSTGRES_PORT: Optional[str] = None
  POSTGRES_DB: Optional[str] = None

  # Conexión alternativa a Postgres (por ejemplo Azure)
  AZURE_DATABASE_URL: Optional[str] = None
  AZURE_POSTGRES_USER: Optional[str] = None
  AZURE_POSTGRES_PASSWORD: Optional[str] = None
  AZURE_POSTGRES_HOST: Optional[str] = None
  AZURE_POSTGRES_PORT: Optional[str] = None
  AZURE_POSTGRES_DB: Optional[str] = None

  def __init__(self, **data):
    super().__init__(**data)
    target = (self.DATABASE_TARGET or "local").strip().lower()

    if target == "azure":
      if self.AZURE_DATABASE_URL:
        self.DATABASE_URL = self.AZURE_DATABASE_URL
      elif all([
        self.AZURE_POSTGRES_USER,
        self.AZURE_POSTGRES_PASSWORD,
        self.AZURE_POSTGRES_HOST,
        self.AZURE_POSTGRES_PORT,
        self.AZURE_POSTGRES_DB,
      ]):
        self.DATABASE_URL = (
          f"postgresql+psycopg://{self.AZURE_POSTGRES_USER}:{self.AZURE_POSTGRES_PASSWORD}"
          f"@{self.AZURE_POSTGRES_HOST}:{self.AZURE_POSTGRES_PORT}/{self.AZURE_POSTGRES_DB}?sslmode=require"
        )
      elif not self.DATABASE_URL:
        raise ValueError(
          "DATABASE_TARGET=azure pero no se proporcionó AZURE_DATABASE_URL ni variables AZURE_POSTGRES_."
        )
    else:
      if not self.DATABASE_URL:
        if all([
          self.POSTGRES_USER,
          self.POSTGRES_PASSWORD,
          self.POSTGRES_HOST,
          self.POSTGRES_PORT,
          self.POSTGRES_DB,
        ]):
          self.DATABASE_URL = (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
          )
        else:
          raise ValueError(
            "DATABASE_URL no está configurada y faltan variables POSTGRES_ para construirla."
          )

  class Config:
    env_file = ".env"
    case_sensitive = True


settings = Settings()
