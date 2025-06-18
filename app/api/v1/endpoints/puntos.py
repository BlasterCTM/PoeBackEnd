from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from fastapi import Depends
from app.core.database.database import get_db
from app.models.tarea import Tarea
from app.models.estado_tarea import EstadoTarea
from app.models.usuario import Usuario
from app.models.punto_reposicion import PuntoReposicion
from app.schemas.punto_reposicion import PuntoReposicionCreate

router = APIRouter()

@router.get("/puntos/{id_punto}/disponibilidad")
def verificar_disponibilidad_punto(id_punto: int, db: Session = Depends(get_db)):
    estados_bloqueo = ["pendiente", "en progreso"]
    # Join explícito para obtener estado y reponedor
    resultado = db.query(Tarea, EstadoTarea, Usuario).\
        join(EstadoTarea, Tarea.estado_id == EstadoTarea.estado_id).\
        join(Usuario, Tarea.id_reponedor == Usuario.id_usuario).\
        filter(
            Tarea.id_punto == id_punto,
            EstadoTarea.nombre_estado.in_(estados_bloqueo)
        ).first()
    if resultado:
        tarea, estado, reponedor = resultado
        return {
            "disponible": False,
            "mensaje": "El punto ya está ocupado por una tarea activa.",
            "tarea_conflictiva": {
                "id_tarea": tarea.id_tarea,
                "estado": estado.nombre_estado,
                "reponedor": reponedor.nombre
            }
        }
    return {
        "disponible": True,
        "mensaje": "El punto está disponible para asignación."
    }

@router.post("/puntos", status_code=201)
def crear_punto_reposicion(punto: PuntoReposicionCreate, db: Session = Depends(get_db)):
    # Verifica si ya existe un punto igual en el mismo mueble, nivel y estantería
    existente = db.query(PuntoReposicion).filter_by(
        id_mueble=punto.id_mueble,
        nivel=punto.nivel,
        estanteria=punto.estanteria
    ).first()
    if existente:
        raise HTTPException(status_code=409, detail="Ya existe un punto de reposición con esos datos.")
    nuevo_punto = PuntoReposicion(**punto.dict())
    db.add(nuevo_punto)
    db.commit()
    db.refresh(nuevo_punto)
    return {
        "id_punto": nuevo_punto.id_punto,
        "mensaje": "Punto de reposición creado exitosamente."
    }
