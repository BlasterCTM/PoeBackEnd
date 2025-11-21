from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from app.repositories.base import BaseRepository
from app.models.prediccion_reposicion import PrediccionReposicion


class PrediccionRepository(BaseRepository[PrediccionReposicion]):
    """
    Repositorio para operaciones CRUD de predicciones de reposición.
    Extiende BaseRepository con queries específicas multi-tenant.
    """
    
    def __init__(self):
        super().__init__(PrediccionReposicion)
    
    def get_by_id(self, db: Session, id_prediccion: int, id_empresa: int) -> Optional[PrediccionReposicion]:
        """
        Obtiene una predicción específica asegurando multi-tenancy.
        
        Args:
            db: Sesión de base de datos
            id_prediccion: ID de la predicción
            id_empresa: ID de la empresa (tenant)
            
        Returns:
            Predicción o None si no existe/no pertenece a la empresa
        """
        return db.query(PrediccionReposicion).filter(
            and_(
                PrediccionReposicion.id_prediccion == id_prediccion,
                PrediccionReposicion.id_empresa == id_empresa
            )
        ).first()
    
    def get_historial_empresa(
        self, 
        db: Session, 
        id_empresa: int,
        skip: int = 0,
        limit: int = 20
    ) -> List[PrediccionReposicion]:
        """
        Obtiene historial de predicciones de una empresa, ordenadas por fecha descendente.
        
        Args:
            db: Sesión de base de datos
            id_empresa: ID de la empresa
            skip: Offset para paginación
            limit: Límite de resultados
            
        Returns:
            Lista de predicciones
        """
        return db.query(PrediccionReposicion).filter(
            PrediccionReposicion.id_empresa == id_empresa
        ).order_by(
            desc(PrediccionReposicion.fecha_generacion)
        ).offset(skip).limit(limit).all()
    
    def count_by_empresa(self, db: Session, id_empresa: int) -> int:
        """
        Cuenta total de predicciones de una empresa.
        
        Args:
            db: Sesión de base de datos
            id_empresa: ID de la empresa
            
        Returns:
            Cantidad de predicciones
        """
        return db.query(PrediccionReposicion).filter(
            PrediccionReposicion.id_empresa == id_empresa
        ).count()
    
    def get_by_periodo(
        self, 
        db: Session, 
        id_empresa: int,
        mes: int,
        anio: int,
        semana_mes: Optional[int] = None
    ) -> Optional[PrediccionReposicion]:
        """
        Busca predicción existente para un período específico.
        
        Args:
            db: Sesión de base de datos
            id_empresa: ID de la empresa
            mes: Mes (1-12)
            anio: Año
            semana_mes: Semana del mes (opcional, 1-5)
            
        Returns:
            Predicción existente o None
        """
        query = db.query(PrediccionReposicion).filter(
            and_(
                PrediccionReposicion.id_empresa == id_empresa,
                PrediccionReposicion.mes == mes,
                PrediccionReposicion.anio == anio
            )
        )
        
        if semana_mes is not None:
            query = query.filter(PrediccionReposicion.semana_mes == semana_mes)
        
        return query.first()
    
    def get_predicciones_pendientes(
        self, 
        db: Session, 
        id_empresa: int
    ) -> List[PrediccionReposicion]:
        """
        Obtiene predicciones con estado 'pendiente' de una empresa.
        
        Args:
            db: Sesión de base de datos
            id_empresa: ID de la empresa
            
        Returns:
            Lista de predicciones pendientes
        """
        return db.query(PrediccionReposicion).filter(
            and_(
                PrediccionReposicion.id_empresa == id_empresa,
                PrediccionReposicion.estado == "pendiente"
            )
        ).order_by(
            PrediccionReposicion.anio.asc(),
            PrediccionReposicion.mes.asc()
        ).all()
    
    def crear_prediccion(
        self,
        db: Session,
        id_empresa: int,
        mes: int,
        anio: int,
        resultados: dict,
        version_modelo: str,
        generado_por: int,
        features_utilizados: Optional[dict] = None,
        semana_mes: Optional[int] = None,
        notas: Optional[str] = None
    ) -> PrediccionReposicion:
        """
        Crea una nueva predicción en la base de datos.
        
        Args:
            db: Sesión de base de datos
            id_empresa: ID de la empresa
            mes: Mes (1-12)
            anio: Año
            resultados: JSON con resultados de predicción
            version_modelo: Versión del modelo ML usado
            generado_por: ID del usuario que generó la predicción
            features_utilizados: JSON con metadata de features
            semana_mes: Semana del mes (opcional)
            notas: Notas adicionales
            
        Returns:
            Predicción creada
        """
        prediccion = PrediccionReposicion(
            id_empresa=id_empresa,
            mes=mes,
            anio=anio,
            semana_mes=semana_mes,
            version_modelo=version_modelo,
            generado_por=generado_por,
            resultados_prediccion=resultados,
            features_utilizados=features_utilizados,
            estado="pendiente",
            notas=notas
        )
        
        db.add(prediccion)
        db.commit()
        db.refresh(prediccion)
        
        return prediccion
    
    def actualizar_estado(
        self,
        db: Session,
        id_prediccion: int,
        id_empresa: int,
        estado: str,
        notas: Optional[str] = None
    ) -> Optional[PrediccionReposicion]:
        """
        Actualiza el estado de una predicción.
        
        Args:
            db: Sesión de base de datos
            id_prediccion: ID de la predicción
            id_empresa: ID de la empresa (validación multi-tenant)
            estado: Nuevo estado ('pendiente', 'aplicado', 'rechazado')
            notas: Notas adicionales (opcional)
            
        Returns:
            Predicción actualizada o None si no existe
        """
        prediccion = self.get_by_id(db, id_prediccion, id_empresa)
        
        if not prediccion:
            return None
        
        prediccion.estado = estado
        if notas:
            prediccion.notas = notas
        
        db.commit()
        db.refresh(prediccion)
        
        return prediccion


# Instancia singleton
prediccion_repository = PrediccionRepository()
