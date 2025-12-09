# Repositorio para operaciones sobre tarea

from app.utils.timezone import now_utc
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.tarea import Tarea
from app.models.usuario import Usuario, RolEnum
from app.models.supervision import Supervision
from app.repositories.base import BaseRepository
from sqlalchemy.exc import NoResultFound

class TareaRepository(BaseRepository[Tarea]):
    def __init__(self):
        super().__init__(Tarea)
    
    def crear_tarea(self, db: Session, id_supervisor: int, id_punto: int, id_empresa: int, id_reponedor: Optional[int] = None, current_user: Usuario = None) -> Tarea:
        """Crea una nueva tarea"""
        # Validar permisos
        if current_user and current_user.rol.nombre_rol.lower() not in ["administrador", "supervisor"]:
            raise Exception("No tienes permisos para crear tareas.")
        
        # Si el usuario es supervisor, solo puede crear tareas para sus reponedores
        if current_user and current_user.rol.nombre_rol.lower() == "supervisor" and id_reponedor:
            supervision = db.query(Supervision).filter(
                Supervision.reponedor_id == id_reponedor,
                Supervision.supervisor_id == current_user.id_usuario,
                Supervision.id_empresa == id_empresa
            ).first()
            if not supervision:
                raise Exception("No tienes permisos para asignar tareas a este reponedor.")
        
        # Estado inicial: 1 = pendiente (según comentario en productos.py)
        estado_inicial = 1
        
        # Crear la tarea
        tarea = Tarea(
            # Keep DB column as Date for now but derive the date from UTC
            fecha_creacion=now_utc().date(),
            estado_id=estado_inicial,
            id_supervisor=id_supervisor,
            id_reponedor=id_reponedor,
            id_punto=id_punto,
            id_empresa=id_empresa
        )
        
        db.add(tarea)
        db.commit()
        db.refresh(tarea)
        return tarea
    
    def get_tareas_by_reponedor(self, db: Session, id_reponedor: int, id_empresa: int) -> List[Tarea]:
        """Obtiene todas las tareas asignadas a un reponedor"""
        return db.query(Tarea).filter(
            Tarea.id_reponedor == id_reponedor,
            Tarea.id_empresa == id_empresa
        ).all()
    
    def get_tareas_by_supervisor(self, db: Session, id_supervisor: int, id_empresa: int) -> List[Tarea]:
        """Obtiene todas las tareas creadas por un supervisor"""
        return db.query(Tarea).filter(
            Tarea.id_supervisor == id_supervisor,
            Tarea.id_empresa == id_empresa
        ).all()
    
    def get_tarea_by_id(self, db: Session, id_tarea: int, id_empresa: int) -> Optional[Tarea]:
        """Obtiene una tarea por ID validando que pertenezca a la empresa"""
        return db.query(Tarea).filter(
            Tarea.id_tarea == id_tarea,
            Tarea.id_empresa == id_empresa
        ).first()

# Instancia del repositorio para uso en endpoints
tarea_repository = TareaRepository()
