from sqlalchemy.orm import Session
from app.models.usuario import Usuario, Rol
from app.repositories.base import BaseRepository
from app.core.security.password import get_password_hash

class UsuarioRepository(BaseRepository[Usuario]):
    def __init__(self):
        super().__init__(Usuario)
    
    def get_by_email(self, db: Session, email: str) -> Usuario:
        return db.query(Usuario).filter(Usuario.correo == email).first()
    
    def create_usuario(self, db: Session, nombre: str, correo: str, contraseña: str, rol_id: int, estado: str = "activo") -> Usuario:
        hashed_password = get_password_hash(contraseña)
        db_usuario = Usuario(
            nombre=nombre,
            correo=correo,
            contraseña=hashed_password,
            rol_id=rol_id,
            estado=estado
        )
        db.add(db_usuario)
        db.commit()
        db.refresh(db_usuario)
        return db_usuario

    def get_rol_by_nombre(self, db: Session, nombre_rol: str) -> Rol:
        return db.query(Rol).filter(Rol.nombre_rol == nombre_rol).first()

    def get_rol_by_id(self, db: Session, rol_id: int) -> Rol:
        return db.query(Rol).filter(Rol.id_rol == rol_id).first()
