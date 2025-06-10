from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "POE - Path Optimization Engine"
    PROJECT_VERSION: str = "1.0.0"
    PROJECT_DESCRIPTION: str = "API para el motor de optimización de rutas"
      # Configuración de seguridad
    SECRET_KEY: str = "tu_secret_key_super_secreta"  # Deberías cambiar esto en producción
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120  # Aumentado para pruebas
    
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: str
    POSTGRES_DB: str
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
