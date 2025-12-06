from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from fastapi import Depends
from app.core.database.database import get_db
from app.models.tarea import Tarea
from app.models.estado_tarea import EstadoTarea
from app.models.usuario import Usuario
from app.models.punto_reposicion import PuntoReposicion
from app.models.detalle_tarea import DetalleTarea
from app.schemas.punto_reposicion import PuntoReposicionCreate
from app.api.dependencies.auth import get_current_user
from app.api.dependencies.plan_limites import validar_limite_plan
from app.utils.tenant import is_super_admin
from app.core.security.auth import get_current_user

router = APIRouter()

@router.get("/puntos/{id_punto}/disponibilidad")
def verificar_disponibilidad_punto(id_punto: int, db: Session = Depends(get_db)):
    estados_bloqueo = ["pendiente", "en progreso"]
    # Buscar si hay algún detalle de tarea activo para ese punto
    resultado = db.query(DetalleTarea, Tarea, EstadoTarea, Usuario).\
        join(Tarea, DetalleTarea.id_tarea == Tarea.id_tarea).\
        join(EstadoTarea, Tarea.estado_id == EstadoTarea.estado_id).\
        join(Usuario, Tarea.id_reponedor == Usuario.id_usuario).\
        filter(
            DetalleTarea.id_punto == id_punto,
            EstadoTarea.nombre_estado.in_(estados_bloqueo)
        ).first()
    if resultado:
        detalle, tarea, estado, reponedor = resultado
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
def crear_punto_reposicion(
    punto: PuntoReposicionCreate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Validar límites del plan antes de crear punto
    if not is_super_admin(current_user):
        validar_limite_plan("puntos", current_user.id_empresa, db)
    
    # Verifica si ya existe un punto igual en el mismo mueble, nivel y estantería EN LA MISMA EMPRESA
    existente = db.query(PuntoReposicion).filter_by(
        id_mueble=punto.id_mueble,
        nivel=punto.nivel,
        estanteria=punto.estanteria,
        id_empresa=current_user.id_empresa
    ).first()
    if existente:
        raise HTTPException(status_code=409, detail="Ya existe un punto de reposición con esos datos.")
    nuevo_punto = PuntoReposicion(
        id_mueble=punto.id_mueble,
        nivel=punto.nivel,
        estanteria=punto.estanteria,
        id_producto=punto.id_producto,
        id_usuario=punto.id_usuario,
        id_empresa=current_user.id_empresa
    )
    db.add(nuevo_punto)
    db.commit()
    db.refresh(nuevo_punto)
    return {
        "id_punto": nuevo_punto.id_punto,
        "mensaje": "Punto de reposición creado exitosamente."
    }
