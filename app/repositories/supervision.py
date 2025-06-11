from sqlalchemy.orm import Session
from app.models.supervision import Supervision
from app.models.usuario import Usuario, RolEnum, Rol
from app.repositories.base import BaseRepository
from typing import List, Optional
from sqlalchemy import and_, not_, exists

class SupervisionRepository(BaseRepository[Supervision]):
    def __init__(self):
        super().__init__(Supervision)
    
    def get_reponedores_by_supervisor(self, db: Session, supervisor_id: int) -> List[Usuario]:
        """Obtiene todos los reponedores asignados a un supervisor"""
        return db.query(Usuario).join(
            Supervision, Supervision.reponedor_id == Usuario.id_usuario
        ).filter(
            and_(
                Supervision.supervisor_id == supervisor_id,
                Usuario.estado == "activo"  # Solo reponedores activos
            )
        ).all()

    def get_reponedores_disponibles(self, db: Session) -> List[Usuario]:
        """Obtiene todos los reponedores que no están asignados a ningún supervisor"""
        subquery = db.query(Supervision.reponedor_id)
        return db.query(Usuario).join(
            Rol, Usuario.rol_id == Rol.id_rol
        ).filter(
            and_(
                Rol.nombre_rol == RolEnum.REPONEDOR.value,
                Usuario.estado == "activo",
                not_(exists().where(Supervision.reponedor_id == Usuario.id_usuario))
            )
        ).all()

    def get_supervisor_of_reponedor(self, db: Session, reponedor_id: int) -> Optional[Usuario]:
        """Obtiene el supervisor asignado a un reponedor"""
        return db.query(Usuario).join(
            Supervision, Supervision.supervisor_id == Usuario.id_usuario
        ).filter(
            Supervision.reponedor_id == reponedor_id
        ).first()

    def asignar_reponedor(self, db: Session, supervisor_id: int, reponedor_id: int) -> Supervision:
        """Asigna un reponedor a un supervisor"""
        # Verificar si ya existe la asignación
        supervision_existente = db.query(Supervision).filter(
            and_(
                Supervision.supervisor_id == supervisor_id,
                Supervision.reponedor_id == reponedor_id
            )
        ).first()
        
        if supervision_existente:
            return supervision_existente
            
        supervision = Supervision(
            supervisor_id=supervisor_id,
            reponedor_id=reponedor_id
        )
        db.add(supervision)
        db.commit()
        db.refresh(supervision)
        return supervision

    def desasignar_reponedor(self, db: Session, supervisor_id: int, reponedor_id: int) -> None:
        """Desasigna un reponedor de un supervisor"""
        db.query(Supervision).filter(
            and_(
                Supervision.supervisor_id == supervisor_id,
                Supervision.reponedor_id == reponedor_id
            )
        ).delete()
        db.commit()
