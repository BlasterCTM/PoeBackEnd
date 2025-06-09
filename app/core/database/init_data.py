from sqlalchemy.orm import Session
from app.core.database.database import db
from app.models.usuario import Rol, Usuario, RolEnum
from app.core.security.password import get_password_hash

def init_roles_and_admin():
    db_session = db.SessionLocal()
    try:
        # Crear roles si no existen
        roles = {
            RolEnum.ADMINISTRADOR.value: "Administrador del sistema",
            RolEnum.SUPERVISOR.value: "Supervisor de reposición",
            RolEnum.REPONEDOR.value: "Reponedor de productos"
        }
        
        for nombre_rol, descripcion in roles.items():
            if not db_session.query(Rol).filter(Rol.nombre_rol == nombre_rol).first():
                rol = Rol(nombre_rol=nombre_rol)
                db_session.add(rol)
        
        db_session.commit()
        
        # Crear usuario administrador si no existe
        admin_email = "admin@poe.com"
        if not db_session.query(Usuario).filter(Usuario.correo == admin_email).first():
            # Obtener el rol de administrador
            rol_admin = db_session.query(Rol).filter(Rol.nombre_rol == RolEnum.ADMINISTRADOR.value).first()
            
            # Crear el usuario administrador
            admin = Usuario(
                nombre="Administrador",
                correo=admin_email,
                contraseña=get_password_hash("admin123"),
                rol_id=rol_admin.id_rol,
                estado="activo"
            )
            db_session.add(admin)
            db_session.commit()
            print("Usuario administrador creado exitosamente")
        
    except Exception as e:
        print(f"Error al inicializar la base de datos: {e}")
        db_session.rollback()
    finally:
        db_session.close()

if __name__ == "__main__":
    init_roles_and_admin()
