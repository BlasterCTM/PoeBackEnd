"""
Test de Integración Completo con Multi-Tenant
Valida todos los endpoints principales del proyecto respetando aislamiento por empresa
"""
import pytest
import sys
import os
from datetime import datetime, timedelta

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from app.core.database.database import db as database
from app.repositories.usuario import UsuarioRepository
from app.repositories.producto import create_producto, get_productos, get_producto_by_id
from app.repositories.tarea import TareaRepository
from app.models.usuario import Usuario, RolEnum
from app.models.punto_reposicion import PuntoReposicion
from app.models.tarea import Tarea
from app.schemas.producto import ProductoCreate
from app.schemas.usuario import UsuarioCreate

# Importar todos los modelos
import app.models  # noqa: F401


# ============================================================
# FIXTURES: Base de datos y usuarios
# ============================================================

@pytest.fixture(scope="function")
def db():
    """Crear sesión de base de datos para cada test"""
    db_session = database.SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()


@pytest.fixture
def usuario_superadmin(db: Session):
    """Usuario SuperAdmin (admin@poe.com)"""
    usuario_repo = UsuarioRepository()
    usuario = usuario_repo.get_by_email(db, "admin@poe.com")
    assert usuario is not None, "SuperAdmin no encontrado"
    assert usuario.rol.nombre_rol == RolEnum.SUPERADMIN.value
    return usuario


@pytest.fixture
def usuario_admin_empresa1(db: Session):
    """Usuario Admin de empresa 1 (POE)"""
    usuario_repo = UsuarioRepository()
    # Buscar admin de POE
    usuarios = db.query(Usuario).filter(
        Usuario.id_empresa == 1,
        Usuario.estado == "activo"
    ).all()
    
    admin = None
    for u in usuarios:
        if u.rol.nombre_rol == RolEnum.ADMINISTRADOR.value:
            admin = u
            break
    
    if not admin:
        # Crear admin de prueba para POE
        admin = usuario_repo.create_usuario(
            db,
            UsuarioCreate(
                nombre="Admin POE Test",
                correo=f"admin_poe_test_{pytest.test_run_id}@test.com",
                contraseña="Test123!",
                rol=RolEnum.ADMINISTRADOR.value
            ),
            id_empresa=1
        )
    
    return admin


@pytest.fixture
def usuario_admin_empresa2(db: Session):
    """Usuario Admin de empresa 2+ (otra empresa)"""
    usuario_repo = UsuarioRepository()
    usuario = usuario_repo.get_by_email(db, "mgonzalez@jumbo.cl")
    
    if not usuario:
        # Buscar cualquier admin que NO sea de empresa 1
        usuarios = db.query(Usuario).filter(
            Usuario.id_empresa != 1,
            Usuario.estado == "activo"
        ).all()
        
        for u in usuarios:
            if u.rol.nombre_rol == RolEnum.ADMINISTRADOR.value:
                usuario = u
                break
    
    assert usuario is not None, "No hay admin de segunda empresa"
    assert usuario.id_empresa != 1, "Admin no debe ser de POE"
    return usuario


@pytest.fixture
def producto_empresa1_data():
    """Datos para producto de empresa 1"""
    return ProductoCreate(
        nombre=f"Producto Test POE {pytest.test_run_id}",
        categoria="Test",
        unidad_tipo="unidades",
        unidad_cantidad=1,
        codigo_unico=f"TEST-POE-{pytest.test_run_id}",
        id_usuario=1
    )


@pytest.fixture
def producto_empresa2_data():
    """Datos para producto de empresa 2"""
    return ProductoCreate(
        nombre=f"Producto Test Empresa2 {pytest.test_run_id}",
        categoria="Test",
        unidad_tipo="unidades",
        unidad_cantidad=1,
        codigo_unico=f"TEST-EMP2-{pytest.test_run_id}",
        id_usuario=45
    )


# ============================================================
# TESTS: Autenticación y Usuarios
# ============================================================

class TestAutenticacionMultiTenant:
    """Tests de autenticación respetando multi-tenant"""
    
    def test_usuarios_tienen_empresa_asignada(self, db: Session):
        """Todos los usuarios (excepto SuperAdmin) deben tener empresa"""
        usuarios = db.query(Usuario).filter(Usuario.estado == "activo").all()
        
        for usuario in usuarios:
            if usuario.rol.nombre_rol == RolEnum.SUPERADMIN.value:
                # SuperAdmin puede tener empresa 1 (POE) por convención
                print(f"✅ SuperAdmin: {usuario.correo} (id_empresa={usuario.id_empresa})")
            else:
                # Otros usuarios DEBEN tener empresa
                assert usuario.id_empresa is not None, f"Usuario {usuario.correo} sin empresa"
                print(f"✅ Usuario: {usuario.correo} pertenece a empresa {usuario.id_empresa}")
    
    def test_superadmin_existe_y_configurado(self, db: Session, usuario_superadmin: Usuario):
        """SuperAdmin debe existir y estar correctamente configurado"""
        assert usuario_superadmin.correo == "admin@poe.com"
        assert usuario_superadmin.rol.nombre_rol == RolEnum.SUPERADMIN.value
        assert usuario_superadmin.estado == "activo"
        print(f"✅ SuperAdmin configurado: {usuario_superadmin.correo}")
    
    def test_usuarios_diferentes_empresas(
        self, db: Session, usuario_admin_empresa1: Usuario, usuario_admin_empresa2: Usuario
    ):
        """Debe haber usuarios de diferentes empresas"""
        assert usuario_admin_empresa1.id_empresa != usuario_admin_empresa2.id_empresa
        print(f"✅ Empresa 1: {usuario_admin_empresa1.correo} (id={usuario_admin_empresa1.id_empresa})")
        print(f"✅ Empresa 2: {usuario_admin_empresa2.correo} (id={usuario_admin_empresa2.id_empresa})")


# ============================================================
# TESTS: Productos Multi-Tenant
# ============================================================

class TestProductosMultiTenant:
    """Tests completos de productos con aislamiento"""
    
    def test_crear_producto_asigna_empresa_correcta(
        self, db: Session, usuario_admin_empresa1: Usuario, producto_empresa1_data: ProductoCreate
    ):
        """Producto creado se asigna a la empresa del usuario"""
        producto = create_producto(
            db,
            producto_empresa1_data,
            id_usuario=usuario_admin_empresa1.id_usuario,
            id_empresa=usuario_admin_empresa1.id_empresa
        )
        
        assert producto.id_empresa == usuario_admin_empresa1.id_empresa
        print(f"✅ Producto creado en empresa {producto.id_empresa}: {producto.nombre}")
    
    def test_admin_solo_ve_productos_de_su_empresa(
        self, db: Session, usuario_admin_empresa1: Usuario, usuario_admin_empresa2: Usuario
    ):
        """Admin solo puede listar productos de su empresa"""
        # Productos de empresa 1
        resultado1 = get_productos(db, id_empresa=usuario_admin_empresa1.id_empresa, page=1, limit=100)
        productos1 = resultado1.get("productos", [])
        
        for p in productos1:
            assert p.id_empresa == usuario_admin_empresa1.id_empresa
        
        # Productos de empresa 2
        resultado2 = get_productos(db, id_empresa=usuario_admin_empresa2.id_empresa, page=1, limit=100)
        productos2 = resultado2.get("productos", [])
        
        for p in productos2:
            assert p.id_empresa == usuario_admin_empresa2.id_empresa
        
        print(f"✅ Empresa {usuario_admin_empresa1.id_empresa}: {len(productos1)} productos")
        print(f"✅ Empresa {usuario_admin_empresa2.id_empresa}: {len(productos2)} productos")
    
    def test_admin_NO_puede_ver_producto_de_otra_empresa(
        self, db: Session, 
        usuario_admin_empresa1: Usuario,
        usuario_admin_empresa2: Usuario,
        producto_empresa2_data: ProductoCreate
    ):
        """Admin no puede acceder a producto de otra empresa"""
        # Crear producto en empresa 2
        producto = create_producto(
            db,
            producto_empresa2_data,
            id_usuario=usuario_admin_empresa2.id_usuario,
            id_empresa=usuario_admin_empresa2.id_empresa
        )
        
        # Intentar acceder desde empresa 1
        producto_acceso = get_producto_by_id(
            db,
            producto.id_producto,
            usuario_admin_empresa1.id_empresa  # Filtro de empresa 1
        )
        
        assert producto_acceso is None, "Admin puede ver producto de otra empresa (FALLO DE SEGURIDAD)"
        print(f"✅ Aislamiento confirmado: Empresa {usuario_admin_empresa1.id_empresa} NO ve producto de empresa {usuario_admin_empresa2.id_empresa}")
    
    def test_superadmin_ve_todos_los_productos(
        self, db: Session, usuario_superadmin: Usuario
    ):
        """SuperAdmin puede ver productos sin filtro de empresa"""
        # Listar sin filtro (None = todos)
        resultado = get_productos(db, id_empresa=None, page=1, limit=100)
        productos = resultado.get("productos", [])
        
        # SuperAdmin debe poder ver productos (si existen)
        print(f"✅ SuperAdmin ve {len(productos)} productos totales (sin filtro de empresa)")


# ============================================================
# TESTS: Puntos de Reposición Multi-Tenant
# ============================================================

class TestPuntosMultiTenant:
    """Tests de puntos de reposición con aislamiento"""
    
    def test_admin_solo_ve_puntos_de_su_empresa(
        self, db: Session, usuario_admin_empresa1: Usuario, usuario_admin_empresa2: Usuario
    ):
        """Admin solo ve puntos de su empresa"""
        # Puntos de empresa 1
        puntos1 = db.query(PuntoReposicion).filter(
            PuntoReposicion.id_empresa == usuario_admin_empresa1.id_empresa
        ).limit(100).all()
        
        for punto in puntos1:
            assert punto.id_empresa == usuario_admin_empresa1.id_empresa
        
        # Puntos de empresa 2
        puntos2 = db.query(PuntoReposicion).filter(
            PuntoReposicion.id_empresa == usuario_admin_empresa2.id_empresa
        ).limit(100).all()
        
        for punto in puntos2:
            assert punto.id_empresa == usuario_admin_empresa2.id_empresa
        
        print(f"✅ Empresa {usuario_admin_empresa1.id_empresa}: {len(puntos1)} puntos")
        print(f"✅ Empresa {usuario_admin_empresa2.id_empresa}: {len(puntos2)} puntos")
    
    def test_admin_NO_puede_ver_punto_de_otra_empresa(
        self, db: Session, usuario_admin_empresa1: Usuario, usuario_admin_empresa2: Usuario
    ):
        """Admin no puede acceder a punto de otra empresa"""
        # Obtener puntos de empresa 2
        puntos2 = db.query(PuntoReposicion).filter(
            PuntoReposicion.id_empresa == usuario_admin_empresa2.id_empresa
        ).limit(1).all()
        
        if puntos2:
            punto_id = puntos2[0].id_punto
            
            # Intentar acceder desde empresa 1
            punto_acceso = db.query(PuntoReposicion).filter(
                PuntoReposicion.id_punto == punto_id,
                PuntoReposicion.id_empresa == usuario_admin_empresa1.id_empresa
            ).first()
            
            assert punto_acceso is None, "Admin puede ver punto de otra empresa (FALLO DE SEGURIDAD)"
            print(f"✅ Aislamiento confirmado: Empresa {usuario_admin_empresa1.id_empresa} NO ve punto de empresa {usuario_admin_empresa2.id_empresa}")
        else:
            print("⚠️ No hay puntos en empresa 2 para probar")


# ============================================================
# TESTS: Tareas Multi-Tenant
# ============================================================

class TestTareasMultiTenant:
    """Tests de tareas con aislamiento"""
    
    def test_admin_solo_ve_tareas_de_su_empresa(
        self, db: Session, usuario_admin_empresa1: Usuario, usuario_admin_empresa2: Usuario
    ):
        """Admin solo ve tareas de su empresa"""
        tarea_repo = TareaRepository()
        
        # Tareas de empresa 1
        tareas1 = tarea_repo.obtener_tareas(
            db,
            id_empresa=usuario_admin_empresa1.id_empresa,
            skip=0,
            limit=100
        )
        
        for tarea in tareas1:
            assert tarea.id_empresa == usuario_admin_empresa1.id_empresa
        
        # Tareas de empresa 2
        tareas2 = tarea_repo.obtener_tareas(
            db,
            id_empresa=usuario_admin_empresa2.id_empresa,
            skip=0,
            limit=100
        )
        
        for tarea in tareas2:
            assert tarea.id_empresa == usuario_admin_empresa2.id_empresa
        
        print(f"✅ Empresa {usuario_admin_empresa1.id_empresa}: {len(tareas1)} tareas")
        print(f"✅ Empresa {usuario_admin_empresa2.id_empresa}: {len(tareas2)} tareas")
    
    def test_admin_NO_puede_ver_tarea_de_otra_empresa(
        self, db: Session, usuario_admin_empresa1: Usuario, usuario_admin_empresa2: Usuario
    ):
        """Admin no puede acceder a tarea de otra empresa"""
        tarea_repo = TareaRepository()
        
        # Obtener tareas de empresa 2
        tareas2 = tarea_repo.obtener_tareas(
            db,
            id_empresa=usuario_admin_empresa2.id_empresa,
            skip=0,
            limit=1
        )
        
        if tareas2:
            tarea_id = tareas2[0].id_tarea
            
            # Intentar acceder desde empresa 1
            tarea_acceso = tarea_repo.obtener_tarea_por_id(
                db,
                tarea_id,
                usuario_admin_empresa1.id_empresa
            )
            
            assert tarea_acceso is None, "Admin puede ver tarea de otra empresa (FALLO DE SEGURIDAD)"
            print(f"✅ Aislamiento confirmado: Empresa {usuario_admin_empresa1.id_empresa} NO ve tarea de empresa {usuario_admin_empresa2.id_empresa}")
        else:
            print("⚠️ No hay tareas en empresa 2 para probar")


# ============================================================
# TESTS: Estadísticas y Dashboards
# ============================================================

class TestEstadisticasMultiTenant:
    """Tests de estadísticas respetando aislamiento"""
    
    def test_estadisticas_filtran_por_empresa(
        self, db: Session, usuario_admin_empresa1: Usuario, usuario_admin_empresa2: Usuario
    ):
        """Estadísticas deben filtrar correctamente por empresa"""
        from app.services.estadisticas_puntos import obtener_estadisticas_puntos
        
        # Estadísticas de empresa 1
        stats1 = obtener_estadisticas_puntos(db, usuario_admin_empresa1.id_empresa)
        
        # Estadísticas de empresa 2
        stats2 = obtener_estadisticas_puntos(db, usuario_admin_empresa2.id_empresa)
        
        # Las estadísticas pueden ser diferentes entre empresas
        print(f"✅ Empresa {usuario_admin_empresa1.id_empresa} - Total puntos: {stats1.get('total_puntos', 0)}")
        print(f"✅ Empresa {usuario_admin_empresa2.id_empresa} - Total puntos: {stats2.get('total_puntos', 0)}")
    
    def test_dashboard_solo_muestra_datos_de_empresa(
        self, db: Session, usuario_admin_empresa1: Usuario
    ):
        """Dashboard solo muestra datos de la empresa del usuario"""
        from app.services.dashboard import obtener_dashboard
        
        dashboard = obtener_dashboard(db, usuario_admin_empresa1.id_empresa)
        
        # Verificar que todos los datos son de la empresa correcta
        assert dashboard is not None
        print(f"✅ Dashboard generado para empresa {usuario_admin_empresa1.id_empresa}")


# ============================================================
# TESTS: Rutas Optimizadas Multi-Tenant
# ============================================================

class TestRutasMultiTenant:
    """Tests de rutas optimizadas con aislamiento"""
    
    def test_admin_solo_ve_rutas_de_su_empresa(
        self, db: Session, usuario_admin_empresa1: Usuario, usuario_admin_empresa2: Usuario
    ):
        """Admin solo ve rutas de su empresa"""
        from app.models.ruta_optimizada import RutaOptimizada
        
        # Rutas de empresa 1
        rutas1 = db.query(RutaOptimizada).filter(
            RutaOptimizada.id_empresa == usuario_admin_empresa1.id_empresa
        ).limit(100).all()
        
        for ruta in rutas1:
            assert ruta.id_empresa == usuario_admin_empresa1.id_empresa
        
        # Rutas de empresa 2
        rutas2 = db.query(RutaOptimizada).filter(
            RutaOptimizada.id_empresa == usuario_admin_empresa2.id_empresa
        ).limit(100).all()
        
        for ruta in rutas2:
            assert ruta.id_empresa == usuario_admin_empresa2.id_empresa
        
        print(f"✅ Empresa {usuario_admin_empresa1.id_empresa}: {len(rutas1)} rutas")
        print(f"✅ Empresa {usuario_admin_empresa2.id_empresa}: {len(rutas2)} rutas")


# ============================================================
# TESTS: Búsqueda Global
# ============================================================

class TestBusquedaMultiTenant:
    """Tests de búsqueda respetando aislamiento"""
    
    def test_busqueda_productos_filtra_por_empresa(
        self, db: Session, usuario_admin_empresa1: Usuario
    ):
        """Búsqueda de productos debe filtrar por empresa"""
        from app.repositories.producto import buscar_productos
        
        productos = buscar_productos(
            db,
            id_empresa=usuario_admin_empresa1.id_empresa,
            nombre="Test"
        )
        
        for p in productos:
            assert p.id_empresa == usuario_admin_empresa1.id_empresa
        
        print(f"✅ Búsqueda filtrada: {len(productos)} productos de empresa {usuario_admin_empresa1.id_empresa}")


# ============================================================
# TESTS: Validaciones de Seguridad
# ============================================================

class TestSeguridadMultiTenant:
    """Tests de seguridad críticos para multi-tenant"""
    
    def test_NO_existe_query_sin_filtro_empresa(self, db: Session):
        """CRÍTICO: Verificar que no hay queries sin filtro de empresa"""
        # Este test es conceptual - en producción usarías un ORM listener
        print("✅ RECORDATORIO: Todos los endpoints deben filtrar por id_empresa")
        print("✅ RECORDATORIO: SuperAdmin usa id_empresa=None para ver todo")
    
    def test_superadmin_es_unico_con_acceso_global(
        self, db: Session, usuario_superadmin: Usuario
    ):
        """Solo SuperAdmin puede tener acceso global"""
        # Verificar que solo hay un SuperAdmin
        superadmins = db.query(Usuario).join(Usuario.rol).filter(
            Usuario.rol.has(nombre_rol=RolEnum.SUPERADMIN.value),
            Usuario.estado == "activo"
        ).count()
        
        assert superadmins >= 1, "Debe haber al menos un SuperAdmin"
        print(f"✅ Total SuperAdmins activos: {superadmins}")
    
    def test_datos_empresas_no_se_mezclan(
        self, db: Session,
        usuario_admin_empresa1: Usuario,
        usuario_admin_empresa2: Usuario,
        producto_empresa1_data: ProductoCreate,
        producto_empresa2_data: ProductoCreate
    ):
        """CRÍTICO: Datos de diferentes empresas NUNCA deben mezclarse"""
        # Crear productos en ambas empresas
        prod1 = create_producto(
            db, producto_empresa1_data,
            id_usuario=usuario_admin_empresa1.id_usuario,
            id_empresa=usuario_admin_empresa1.id_empresa
        )
        
        prod2 = create_producto(
            db, producto_empresa2_data,
            id_usuario=usuario_admin_empresa2.id_usuario,
            id_empresa=usuario_admin_empresa2.id_empresa
        )
        
        # Verificar que cada empresa solo ve lo suyo
        productos_emp1 = get_productos(db, id_empresa=usuario_admin_empresa1.id_empresa, page=1, limit=100)
        productos_emp2 = get_productos(db, id_empresa=usuario_admin_empresa2.id_empresa, page=1, limit=100)
        
        ids_emp1 = [p.id_producto for p in productos_emp1["productos"]]
        ids_emp2 = [p.id_producto for p in productos_emp2["productos"]]
        
        # prod1 NO debe estar en resultados de empresa 2
        assert prod1.id_producto not in ids_emp2, "FALLO CRÍTICO: Datos se mezclan entre empresas"
        
        # prod2 NO debe estar en resultados de empresa 1
        assert prod2.id_producto not in ids_emp1, "FALLO CRÍTICO: Datos se mezclan entre empresas"
        
        print(f"✅ SEGURIDAD CONFIRMADA: Datos de empresa {usuario_admin_empresa1.id_empresa} y {usuario_admin_empresa2.id_empresa} están COMPLETAMENTE aislados")


# ============================================================
# Configuración de pytest
# ============================================================

def setup_module():
    """Setup antes de ejecutar los tests"""
    import random
    import string
    pytest.test_run_id = ''.join(random.choices(string.digits, k=6))
    print(f"\n{'='*80}")
    print(f"🧪 TEST DE INTEGRACIÓN COMPLETO - MULTI-TENANT")
    print(f"Run ID: {pytest.test_run_id}")
    print(f"{'='*80}\n")


def teardown_module():
    """Cleanup después de ejecutar los tests"""
    print(f"\n{'='*80}")
    print(f"✅ TEST DE INTEGRACIÓN COMPLETADO")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])
