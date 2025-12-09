from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.plan_empresa import PlanEmpresa
from app.repositories.base import BaseRepository


class PlanEmpresaRepository(BaseRepository[PlanEmpresa]):
    """Repository para gestión de planes de empresa"""
    
    def __init__(self):
        super().__init__(PlanEmpresa)
    
    def get_by_id(self, db: Session, id_plan: int) -> Optional[PlanEmpresa]:
        """Obtiene plan por ID"""
        return db.query(PlanEmpresa).filter(PlanEmpresa.id_plan == id_plan).first()
    
    def get_by_empresa(self, db: Session, id_empresa: int) -> Optional[PlanEmpresa]:
        """Obtiene plan de una empresa específica"""
        return db.query(PlanEmpresa).filter(PlanEmpresa.id_empresa == id_empresa).first()
    
    def get_all(self, db: Session, skip: int = 0, limit: int = 100, activo: Optional[bool] = None) -> List[PlanEmpresa]:
        """Obtiene todos los planes con filtros opcionales"""
        query = db.query(PlanEmpresa)
        
        if activo is not None:
            query = query.filter(PlanEmpresa.activo == activo)
        
        return query.offset(skip).limit(limit).all()
    
    def create(self, db: Session, plan_data: dict) -> PlanEmpresa:
        """Crea un nuevo plan para una empresa"""
        plan = PlanEmpresa(**plan_data)
        db.add(plan)
        db.commit()
        db.refresh(plan)
        return plan
    
    def update(self, db: Session, id_plan: int, update_data: dict) -> Optional[PlanEmpresa]:
        """Actualiza un plan"""
        plan = self.get_by_id(db, id_plan)
        if not plan:
            return None
        
        for key, value in update_data.items():
            if value is not None:
                setattr(plan, key, value)
        
        db.commit()
        db.refresh(plan)
        return plan
    
    def activar_desactivar(self, db: Session, id_plan: int, activo: bool) -> Optional[PlanEmpresa]:
        """Activa o desactiva un plan"""
        plan = self.get_by_id(db, id_plan)
        if not plan:
            return None
        
        plan.activo = activo
        db.commit()
        db.refresh(plan)
        return plan
    
    def validar_limite(self, db: Session, id_empresa: int, recurso: str, cantidad_actual: int) -> dict:
        """
        Valida si la cantidad actual de un recurso excede el límite del plan
        
        Args:
            id_empresa: ID de la empresa
            recurso: Tipo de recurso ('locales', 'supervisores', 'reponedores', 'productos', 'puntos')
            cantidad_actual: Cantidad actual del recurso
        
        Returns:
            dict con validación
        """
        plan = self.get_by_empresa(db, id_empresa)
        if not plan:
            return {
                "valido": False,
                "mensaje": "Empresa sin plan activo"
            }
        
        if not plan.activo:
            return {
                "valido": False,
                "mensaje": "Plan inactivo"
            }
        
        # Mapeo de recursos a campos del plan
        campo_map = {
            "supervisores": "cantidad_supervisores",
            "reponedores": "cantidad_reponedores",
            "productos": "cantidad_productos",
            "puntos": "cantidad_puntos"
        }
        
        campo = campo_map.get(recurso)
        if not campo:
            return {
                "valido": False,
                "mensaje": f"Recurso '{recurso}' no reconocido"
            }
        
        limite = getattr(plan, campo)
        if limite is None:
            # Si el límite es None, no hay restricción
            return {
                "valido": True,
                "mensaje": "Sin límite para este recurso"
            }
        
        # Excedido solo si la cantidad actual es MAYOR (no igual) al límite
        # Esto permite usar hasta el límite (ej: si límite=1, se puede tener 1 usuario)
        excedido = cantidad_actual > limite
        disponible = max(0, limite - cantidad_actual)
        porcentaje_uso = (cantidad_actual / limite * 100) if limite > 0 else 0
        
        return {
            "valido": not excedido,
            "recurso": recurso,
            "cantidad_actual": cantidad_actual,
            "limite_plan": limite,
            "disponible": disponible,
            "porcentaje_uso": round(porcentaje_uso, 2),
            "excedido": excedido,
            "mensaje": f"Límite excedido: {cantidad_actual}/{limite}" if excedido else "Dentro del límite"
        }
    
    def tiene_feature(self, db: Session, id_empresa: int, feature: str) -> bool:
        """
        Verifica si una empresa tiene un feature habilitado
        
        Args:
            id_empresa: ID de la empresa
            feature: Nombre del feature
        
        Returns:
            bool
        """
        plan = self.get_by_empresa(db, id_empresa)
        if not plan or not plan.activo:
            return False
        
        features = plan.features or {}
        return features.get(feature, False)
    
    def get_uso_recursos(self, db: Session, id_empresa: int) -> dict:
        """
        Obtiene el uso actual de recursos de una empresa
        
        Args:
            id_empresa: ID de la empresa
        
        Returns:
            dict con uso de recursos
        """
        from app.models.usuario import Usuario, Rol, RolEnum
        from app.models.producto import Producto
        from app.models.punto_reposicion import PuntoReposicion
        
        # Contar usuarios por rol usando IDs específicos
        # IMPORTANTE: Solo se cuentan Supervisores y Reponedores
        # Se EXCLUYEN del conteo: Administrador (id=1) y SuperAdmin (id=4)
        # IDs de roles: 1=Administrador, 2=Supervisor, 3=Reponedor, 4=SuperAdmin
        from sqlalchemy import func
        
        # Contar Supervisores (rol_id = 2)
        supervisores = db.query(func.count(Usuario.id_usuario)).filter(
            and_(
                Usuario.id_empresa == id_empresa,
                Usuario.rol_id == 2  # Supervisor
            )
        ).scalar() or 0
        
        # Contar Reponedores (rol_id = 3)
        reponedores = db.query(func.count(Usuario.id_usuario)).filter(
            and_(
                Usuario.id_empresa == id_empresa,
                Usuario.rol_id == 3  # Reponedor
            )
        ).scalar() or 0
        
        # Contar solo productos activos (no eliminados lógicamente)
        productos = db.query(func.count(Producto.id_producto)).filter(
            and_(
                Producto.id_empresa == id_empresa,
                Producto.estado == "activo"
            )
        ).scalar() or 0
        
        puntos = db.query(func.count(PuntoReposicion.id_punto)).filter(
            PuntoReposicion.id_empresa == id_empresa
        ).scalar() or 0
        
        return {
            "uso_supervisores": supervisores,
            "uso_reponedores": reponedores,
            "uso_productos": productos,
            "uso_puntos": puntos
        }
