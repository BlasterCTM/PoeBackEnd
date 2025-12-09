"""
Script de inicialización de base de datos para Azure.
Ejecuta automáticamente al iniciar el contenedor por primera vez.
"""
import sys
import os
from sqlalchemy import text
from app.core.database.database import SessionLocal, engine, Base
from app.models.usuario import Rol, Usuario, RolEnum
from app.models.estado_tarea import EstadoTarea
from app.core.security.password import get_password_hash
from sqlalchemy.exc import IntegrityError

def check_database_initialized():
    """Verifica si la base de datos ya fue inicializada"""
    try:
        db = SessionLocal()
        # Verificar si existen roles
        roles = db.query(Rol).count()
        db.close()
        return roles > 0
    except Exception as e:
        print(f"[WARNING] Base de datos no inicializada: {e}")
        return False

def create_tables():
    """Crear todas las tablas"""
    print("[INFO] Creando tablas...")
    Base.metadata.create_all(bind=engine)
    print("[SUCCESS] Tablas creadas")

def create_poe_empresa():
    """Crear empresa POE Sistema para el equipo de desarrollo"""
    db = SessionLocal()
    try:
        print("[INFO] Verificando empresa POE Sistema...")
        
        # Importar modelo Empresa
        from app.models.empresa import Empresa
        
        # Verificar si ya existe
        existing = db.query(Empresa).filter(Empresa.id_empresa == 0).first()
        if existing:
            print(f"  [SKIP] Empresa POE Sistema ya existe")
            return
        
        # Crear empresa POE con id_empresa = 0
        empresa_poe = Empresa(
            id_empresa=0,
            nombre_empresa="POE Sistema",
            rut_empresa="00000000-0",
            direccion="Sistema Interno",
            ciudad="Santiago",
            region="Metropolitana",
            telefono="+56900000000",
            email="dev@poe.com",
            estado="activo"
        )
        
        db.add(empresa_poe)
        db.commit()
        print(f"  [SUCCESS] Empresa POE Sistema creada (id_empresa=0)")
        
    except IntegrityError as e:
        print(f"  [SKIP] Empresa POE Sistema ya existe o error de integridad")
        db.rollback()
    except Exception as e:
        print(f"[ERROR] Error creando empresa POE: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def create_roles():
    """Crear roles del sistema"""
    db = SessionLocal()
    try:
        print("[INFO] Creando roles...")
        
        # Orden correcto según la base de datos
        roles_data = [
            {"id_rol": 1, "nombre_rol": RolEnum.ADMINISTRADOR.value},
            {"id_rol": 2, "nombre_rol": RolEnum.SUPERVISOR.value},
            {"id_rol": 3, "nombre_rol": RolEnum.REPONEDOR.value},
            {"id_rol": 4, "nombre_rol": RolEnum.SUPERADMIN.value},
        ]
        
        for role_data in roles_data:
            existing = db.query(Rol).filter(Rol.nombre_rol == role_data["nombre_rol"]).first()
            if not existing:
                rol = Rol(**role_data)
                db.add(rol)
                print(f"  [SUCCESS] Rol '{role_data['nombre_rol']}' creado")
            else:
                print(f"  [SKIP] Rol '{role_data['nombre_rol']}' ya existe")
        
        db.commit()
        print("[SUCCESS] Roles creados correctamente")
        
    except Exception as e:
        print(f"[ERROR] Error creando roles: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def create_estados_tarea():
    """Crear estados de tarea"""
    db = SessionLocal()
    try:
        print("[INFO] Creando estados de tarea...")
        
        estados_data = [
            {"estado_id": 1, "nombre_estado": "pendiente"},
            {"estado_id": 2, "nombre_estado": "en_progreso"},
            {"estado_id": 3, "nombre_estado": "completada"},
            {"estado_id": 4, "nombre_estado": "cancelada"},
            {"estado_id": 5, "nombre_estado": "sin asignar"},
        ]
        
        for estado_data in estados_data:
            existing = db.query(EstadoTarea).filter(
                EstadoTarea.nombre_estado == estado_data["nombre_estado"]
            ).first()
            
            if not existing:
                estado = EstadoTarea(**estado_data)
                db.add(estado)
                print(f"  [SUCCESS] Estado '{estado_data['nombre_estado']}' creado")
            else:
                print(f"  [SKIP] Estado '{estado_data['nombre_estado']}' ya existe")
        
        db.commit()
        print("[SUCCESS] Estados de tarea creados correctamente")
        
    except Exception as e:
        print(f"[ERROR] Error creando estados: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def create_superadmin():
    """Crear usuario SuperAdmin por defecto"""
    db = SessionLocal()
    try:
        print("[INFO] Creando SuperAdmin...")
        
        # Obtener rol SuperAdmin
        rol_superadmin = db.query(Rol).filter(
            Rol.nombre_rol == RolEnum.SUPERADMIN.value
        ).first()
        
        if not rol_superadmin:
            print("[ERROR] Rol SuperAdmin no encontrado. Crear roles primero.")
            return
        
        # Verificar si ya existe un SuperAdmin
        existing_superadmin = db.query(Usuario).filter(
            Usuario.rol_id == rol_superadmin.id_rol
        ).first()
        
        if existing_superadmin:
            print(f"  [SKIP] SuperAdmin ya existe: {existing_superadmin.correo}")
            return
        
        # Credenciales desde variables de entorno o defaults
        superadmin_email = os.getenv("SUPERADMIN_EMAIL", "superadmin@poe.com")
        superadmin_password = os.getenv("SUPERADMIN_PASSWORD", "Admin123!@#")
        superadmin_name = os.getenv("SUPERADMIN_NAME", "Super Administrador")
        
        # Crear SuperAdmin asignado a empresa POE (id_empresa=0)
        superadmin = Usuario(
            nombre=superadmin_name,
            correo=superadmin_email,
            contraseña=get_password_hash(superadmin_password),
            rol_id=rol_superadmin.id_rol,
            estado="activo",
            id_empresa=0  # Empresa POE Sistema (equipo de desarrollo)
        )
        
        db.add(superadmin)
        db.commit()
        db.refresh(superadmin)
        
        print(f"[SUCCESS] SuperAdmin creado exitosamente:")
        print(f"   Email: {superadmin_email}")
        print(f"   Password: {superadmin_password}")
        print(f"   [WARNING] CAMBIAR LA CONTRASEÑA INMEDIATAMENTE EN PRODUCCION")
        
    except Exception as e:
        print(f"[ERROR] Error creando SuperAdmin: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def init_database():
    """Inicializar base de datos completa"""
    print("\n" + "="*60)
    print("INICIALIZACION DE BASE DE DATOS POE")
    print("="*60 + "\n")
    
    try:
        # Verificar si ya está inicializada
        if check_database_initialized():
            print("[SUCCESS] Base de datos ya esta inicializada. Omitiendo inicializacion.")
            return
        
        # 1. Crear tablas
        create_tables()
        
        # 2. Crear empresa POE Sistema (id_empresa=0)
        create_poe_empresa()
        
        # 3. Crear roles
        create_roles()
        
        # 4. Crear estados de tarea
        create_estados_tarea()
        
        # 5. Crear SuperAdmin
        create_superadmin()
        
        print("\n" + "="*60)
        print("INICIALIZACION COMPLETADA EXITOSAMENTE")
        print("="*60 + "\n")
        
    except Exception as e:
        print("\n" + "="*60)
        print(f"ERROR EN INICIALIZACION: {e}")
        print("="*60 + "\n")
        sys.exit(1)

if __name__ == "__main__":
    init_database()
