from sqlalchemy.orm import Session
from app.core.database.database import db
from app.models.usuario import Rol, Usuario, RolEnum
from app.core.security.password import get_password_hash

def init_roles_and_admin():
    db_session = db.SessionLocal()
    try:
        print("=== Iniciando inicialización de la base de datos ===")
        print("1. Iniciando creación de roles...")
        # Crear roles si no existen
        roles = {
            RolEnum.ADMINISTRADOR.value: "Administrador del sistema",
            RolEnum.SUPERVISOR.value: "Supervisor de reposición",
            RolEnum.REPONEDOR.value: "Reponedor de productos"
        }
        
        for nombre_rol, descripcion in roles.items():
            existing_rol = db_session.query(Rol).filter(Rol.nombre_rol == nombre_rol).first()
            if not existing_rol:
                print(f"Creando rol: {nombre_rol}")
                rol = Rol(nombre_rol=nombre_rol, descripcion=descripcion)
                db_session.add(rol)
                db_session.commit()
            else:
                print(f"El rol {nombre_rol} ya existe con ID: {existing_rol.id_rol}")
        
        print("2. Roles creados/verificados exitosamente")
        
        # Crear usuario administrador si no existe
        admin_email = "admin@poe.com"
        print(f"3. Verificando existencia del administrador ({admin_email})...")
        existing_admin = db_session.query(Usuario).filter(Usuario.correo == admin_email).first()
        
        if not existing_admin:
            print("4. Administrador no encontrado, procediendo a crear uno nuevo...")
            rol_admin = db_session.query(Rol).filter(Rol.nombre_rol == RolEnum.ADMINISTRADOR.value).first()
            
            if rol_admin:
                print(f"5. Rol administrador encontrado con ID: {rol_admin.id_rol}")
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
                print("6. Usuario administrador creado exitosamente")
                print(f"   - ID: {admin.id_usuario}")
                print(f"   - Correo: {admin.correo}")
                print(f"   - Estado: {admin.estado}")
            else:
                print("Error: No se encontró el rol de administrador en la base de datos")
        else:
            print(f"4. El usuario administrador ya existe:")
            print(f"   - ID: {existing_admin.id_usuario}")
            print(f"   - Correo: {existing_admin.correo}")
            print(f"   - Estado: {existing_admin.estado}")
        
        print("=== Inicialización completada ===")
        
    except Exception as e:
        print(f"Error al inicializar la base de datos: {e}")
        db_session.rollback()
        raise
    finally:
        db_session.close()

if __name__ == "__main__":
    init_roles_and_admin()
