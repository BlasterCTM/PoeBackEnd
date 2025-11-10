from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.empresa import Empresa
from app.schemas.empresa import EmpresaCreate, EmpresaUpdate
from typing import Optional, List

class EmpresaRepository:
    """Repository para operaciones CRUD de empresas"""
    
    @staticmethod
    def create_empresa(db: Session, empresa_data: EmpresaCreate) -> Empresa:
        """
        Crear una nueva empresa
        
        Args:
            db: Sesión de base de datos
            empresa_data: Datos de la empresa a crear
            
        Returns:
            Empresa creada
            
        Raises:
            ValueError: Si el RUT ya existe
        """
        # Verificar que no exista el RUT
        if EmpresaRepository.get_by_rut(db, empresa_data.rut_empresa):
            raise ValueError(f"Ya existe una empresa con el RUT {empresa_data.rut_empresa}")
        
        nueva_empresa = Empresa(
            nombre_empresa=empresa_data.nombre_empresa,
            rut_empresa=empresa_data.rut_empresa,
            direccion=empresa_data.direccion,
            ciudad=empresa_data.ciudad,
            region=empresa_data.region,
            telefono=empresa_data.telefono,
            email=empresa_data.email,
            estado='activo'
        )
        
        try:
            db.add(nueva_empresa)
            db.commit()
            db.refresh(nueva_empresa)
            return nueva_empresa
        except IntegrityError as e:
            db.rollback()
            raise ValueError(f"Error al crear empresa: {str(e)}")
    
    @staticmethod
    def get_by_id(db: Session, id_empresa: int) -> Optional[Empresa]:
        """Obtener empresa por ID"""
        return db.query(Empresa).filter(Empresa.id_empresa == id_empresa).first()
    
    @staticmethod
    def get_by_rut(db: Session, rut_empresa: str) -> Optional[Empresa]:
        """Obtener empresa por RUT"""
        return db.query(Empresa).filter(Empresa.rut_empresa == rut_empresa).first()
    
    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[Empresa]:
        """Obtener empresa por email"""
        return db.query(Empresa).filter(Empresa.email == email).first()
    
    @staticmethod
    def get_all(
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        estado: Optional[str] = None
    ) -> List[Empresa]:
        """
        Listar todas las empresas con paginación
        
        Args:
            db: Sesión de base de datos
            skip: Número de registros a saltar
            limit: Número máximo de registros a retornar
            estado: Filtrar por estado (activo/inactivo)
        """
        query = db.query(Empresa)
        
        if estado:
            query = query.filter(Empresa.estado == estado)
        
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def update_empresa(
        db: Session, 
        id_empresa: int, 
        empresa_data: EmpresaUpdate
    ) -> Optional[Empresa]:
        """
        Actualizar datos de una empresa
        
        Args:
            db: Sesión de base de datos
            id_empresa: ID de la empresa a actualizar
            empresa_data: Nuevos datos de la empresa
            
        Returns:
            Empresa actualizada o None si no existe
        """
        empresa = EmpresaRepository.get_by_id(db, id_empresa)
        
        if not empresa:
            return None
        
        # Actualizar solo los campos proporcionados
        update_data = empresa_data.model_dump(exclude_unset=True)
        
        for campo, valor in update_data.items():
            setattr(empresa, campo, valor)
        
        try:
            db.commit()
            db.refresh(empresa)
            return empresa
        except IntegrityError as e:
            db.rollback()
            raise ValueError(f"Error al actualizar empresa: {str(e)}")
    
    @staticmethod
    def delete_empresa(db: Session, id_empresa: int) -> bool:
        """
        Desactivar una empresa (soft delete)
        
        Args:
            db: Sesión de base de datos
            id_empresa: ID de la empresa a desactivar
            
        Returns:
            True si se desactivó, False si no existe
        """
        empresa = EmpresaRepository.get_by_id(db, id_empresa)
        
        if not empresa:
            return False
        
        empresa.estado = 'inactivo'
        db.commit()
        return True
    
    @staticmethod
    def existe_rut(db: Session, rut_empresa: str) -> bool:
        """Verificar si existe una empresa con ese RUT"""
        return db.query(Empresa).filter(Empresa.rut_empresa == rut_empresa).first() is not None
    
    @staticmethod
    def contar_empresas(db: Session, estado: Optional[str] = None) -> int:
        """Contar total de empresas"""
        query = db.query(Empresa)
        
        if estado:
            query = query.filter(Empresa.estado == estado)
        
        return query.count()
