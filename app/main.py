# app/main.py

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.config.settings import settings
from app.core.database.database import init_db
from app.api.dependencies.database import get_database
from app.api.v1.endpoints import usuarios, supervisor, productos, mapa, tareas, puntos
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.security.auth import get_current_user as get_current_user_core
from app.core.database.database import get_db
from fastapi.security import OAuth2PasswordBearer
from app.core.database.init_data import init_estados_tarea

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
origins = [
    "http://localhost:3000",  # Para React
    "http://localhost:4200",  # Para Angular
    "http://127.0.0.1:5500",  # Para VS Code Live Server
    "http://localhost:5173",  # Para Vite
    "http://127.0.0.1:5173"   # Para Vite
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Incluir los routers
app.include_router(usuarios.router)
app.include_router(supervisor.router)
app.include_router(productos.router)
app.include_router(mapa.router)
app.include_router(tareas.router)
app.include_router(puntos.router)

# Inicializar la base de datos al arrancar la aplicación
@app.on_event("startup")
async def startup_event():
    init_db()
    init_estados_tarea()

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

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/usuarios/token")

async def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    user = await get_current_user_core(token=token, db=db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")
    return user
