# app/main.py

from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.config.settings import settings
from app.core.database.database import init_db
from app.api.dependencies.database import get_database

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Inicializar la base de datos al arrancar la aplicación
@app.on_event("startup")
async def startup_event():
    init_db()

@app.get("/")
async def root():
    return {
        "mensaje": "Bienvenido a POE - Path Optimization Engine",
        "documentacion": "/docs",
        "estado": "/health"
    }

# Ejemplo de endpoint usando la base de datos
@app.get("/health")
def health_check(db: Session = Depends(get_database)):
    try:
        # Intenta hacer una consulta simple para verificar la conexión
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": str(e)}
