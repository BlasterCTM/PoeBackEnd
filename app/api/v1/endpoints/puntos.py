from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from fastapi import Depends
from app.core.database.database import get_db
from app.models.tarea import Tarea
from app.models.estado_tarea import EstadoTarea
from app.models.usuario import Usuario

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
