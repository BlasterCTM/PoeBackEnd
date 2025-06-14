# Repositorio para operaciones sobre tarea

from datetime import date
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
    
    def crear_tarea(self, db: Session, id_supervisor: int, id_punto: int, id_reponedor: Optional[int] = None, current_user: Usuario = None) -> Tarea:
        """Crea una nueva tarea"""
        # Validar permisos
        if current_user and current_user.rol.nombre_rol.lower() not in ["administrador", "supervisor"]:
            raise Exception("No tienes permisos para crear tareas.")
        
        # Si el usuario es supervisor, solo puede crear tareas para sus reponedores
        if current_user and current_user.rol.nombre_rol.lower() == "supervisor" and id_reponedor:
            supervision = db.query(Supervision).filter(
                Supervision.reponedor_id == id_reponedor,
                Supervision.supervisor_id == current_user.id_usuario
            ).first()
            if not supervision:
                raise Exception("No tienes permisos para asignar tareas a este reponedor.")
        
        # Estado inicial: 1 = pendiente (según comentario en productos.py)
        estado_inicial = 1
        
        # Crear la tarea
        tarea = Tarea(
            fecha_creacion=date.today(),
            estado_id=estado_inicial,
            id_supervisor=id_supervisor,
            id_reponedor=id_reponedor,
            id_punto=id_punto
        )
        
        db.add(tarea)
        db.commit()
        db.refresh(tarea)
        return tarea
    
    def get_tareas_by_reponedor(self, db: Session, id_reponedor: int) -> List[Tarea]:
        """Obtiene todas las tareas asignadas a un reponedor"""
        return db.query(Tarea).filter(Tarea.id_reponedor == id_reponedor).all()
    
    def get_tareas_by_supervisor(self, db: Session, id_supervisor: int) -> List[Tarea]:
        """Obtiene todas las tareas creadas por un supervisor"""
        return db.query(Tarea).filter(Tarea.id_supervisor == id_supervisor).all()

# Instancia del repositorio para uso en endpoints
tarea_repository = TareaRepository()