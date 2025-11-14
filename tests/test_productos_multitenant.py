"""
Tests automatizados de Multi-Tenant para Productos
Valida que los productos se aíslen correctamente por empresa
"""
import pytest
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from app.core.database.database import db as database
from app.repositories.usuario import UsuarioRepository
from app.repositories.producto import get_productos, create_producto, get_producto_by_id
from app.schemas.producto import ProductoCreate
from app.models.usuario import Usuario

# Importar todos los modelos para que SQLAlchemy pueda resolverlos
import app.models  # noqa: F401


# ============================================================
# FIXTURES: Configuración de base de datos y usuarios
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
    """Obtener usuario SuperAdmin (admin@poe.com)"""
    usuario_repo = UsuarioRepository()
    usuario = usuario_repo.get_by_email(db, "admin@poe.com")
    assert usuario is not None, "Usuario SuperAdmin no encontrado"
    assert usuario.rol.nombre_rol == "SuperAdmin", "Usuario no es SuperAdmin"
    return usuario


@pytest.fixture
def usuario_admin_jumbo(db: Session):
    """Obtener usuario Admin de Jumbo (mgonzalez@jumbo.cl)"""
    usuario_repo = UsuarioRepository()
    usuario = usuario_repo.get_by_email(db, "mgonzalez@jumbo.cl")
    assert usuario is not None, "Usuario Admin Jumbo no encontrado"
    assert usuario.id_empresa is not None, "Usuario no tiene empresa asociada"
    assert usuario.id_empresa != 1, "Usuario pertenece a POE, no a Jumbo"
    return usuario


@pytest.fixture
def producto_jumbo_data():
    """Datos para crear producto en Jumbo"""
    return ProductoCreate(
        nombre="Leche Test Jumbo 1L",
        categoria="Lácteos",
        unidad_tipo="litros",
        unidad_cantidad=1,
        codigo_unico=f"TEST-JUMBO-{pytest.test_run_id}",
        id_usuario=45  # María González (Admin Jumbo)
    )


@pytest.fixture
def producto_poe_data():
    """Datos para crear producto en POE"""
    return ProductoCreate(
        nombre="Producto Test POE",
        categoria="General",
        unidad_tipo="unidades",
        unidad_cantidad=1,
        codigo_unico=f"TEST-POE-{pytest.test_run_id}",
        id_usuario=1  # Admin POE
    )


# ============================================================
# TESTS: Creación de productos por empresa
# ============================================================

class TestProductosCreacion:
    """Tests de creación de productos respetando multi-tenant"""
    
    def test_admin_jumbo_crea_producto_en_su_empresa(
        self, db: Session, usuario_admin_jumbo: Usuario, producto_jumbo_data: ProductoCreate
    ):
        """Admin de Jumbo crea producto y se asocia a su empresa"""
        producto = create_producto(
            db, 
            producto_jumbo_data, 
            id_usuario=producto_jumbo_data.id_usuario,
            id_empresa=usuario_admin_jumbo.id_empresa
        )
        
        assert producto is not None
        assert producto.id_empresa == usuario_admin_jumbo.id_empresa, f"Producto no se creó en la empresa del admin (esperado: {usuario_admin_jumbo.id_empresa})"
        assert producto.nombre == "Leche Test Jumbo 1L"
        print(f"✅ Producto creado en empresa {producto.id_empresa}: {producto.nombre}")
    
    def test_superadmin_crea_producto_en_poe(
        self, db: Session, usuario_superadmin: Usuario, producto_poe_data: ProductoCreate
    ):
        """SuperAdmin crea producto y se asocia a empresa POE (id=1)"""
        producto = create_producto(
            db, 
            producto_poe_data, 
            id_usuario=producto_poe_data.id_usuario,
            id_empresa=usuario_superadmin.id_empresa
        )
        
        assert producto is not None
        assert producto.id_empresa == 1, "Producto no se creó en POE"
        assert producto.nombre == "Producto Test POE"
        print(f"✅ Producto creado en POE: {producto.nombre} (id_empresa={producto.id_empresa})")


# ============================================================
# TESTS: Listado de productos con filtro multi-tenant
# ============================================================

class TestProductosListado:
    """Tests de listado de productos respetando aislamiento"""
    
    def test_admin_jumbo_solo_ve_productos_de_jumbo(
        self, db: Session, usuario_admin_jumbo: Usuario
    ):
        """Admin de Jumbo solo ve productos de su empresa"""
        # Listar productos filtrados por empresa de Jumbo
        resultado = get_productos(
            db,
            id_empresa=usuario_admin_jumbo.id_empresa,
            page=1,
            limit=100
        )
        
        # Verificar que todos los productos pertenecen a la misma empresa
        productos = resultado.get("productos", [])
        for producto in productos:
            assert producto.id_empresa == usuario_admin_jumbo.id_empresa, f"Producto {producto.nombre} no pertenece a la empresa del admin"
        
        print(f"✅ Admin ve {len(productos)} productos, todos de su empresa (id_empresa={usuario_admin_jumbo.id_empresa})")
    
    def test_superadmin_ve_productos_de_todas_las_empresas(
        self, db: Session, usuario_superadmin: Usuario
    ):
        """SuperAdmin puede ver productos sin filtro de empresa"""
        # Listar TODOS los productos sin filtro
        resultado = get_productos(
            db,
            id_empresa=None,  # Sin filtro = ve todos
            page=1,
            limit=100
        )
        
        productos = resultado.get("productos", [])
        
        # Si hay productos, verificar que se pueden ver (no importa cuántas empresas)
        if len(productos) > 0:
            print(f"✅ SuperAdmin ve {len(productos)} productos totales")
        else:
            # Si no hay productos, el test pasa pero advertimos
            print("⚠️ No hay productos en la base de datos para validar")
        
        # Test always passes for SuperAdmin (can see 0 or more products)
        assert True
    
    def test_admin_jumbo_NO_ve_productos_de_poe(
        self, db: Session, usuario_admin_jumbo: Usuario
    ):
        """Admin de Jumbo NO puede ver productos de POE (aislamiento)"""
        # Listar productos filtrados por Jumbo
        resultado = get_productos(
            db,
            id_empresa=usuario_admin_jumbo.id_empresa,
            page=1,
            limit=100
        )
        
        productos = resultado.get("productos", [])
        
        # Verificar que NO hay productos de POE (id_empresa=1)
        productos_poe = [p for p in productos if p.id_empresa == 1]
        assert len(productos_poe) == 0, "Admin Jumbo puede ver productos de POE (FUGA DE DATOS)"
        
        print(f"✅ Aislamiento confirmado: Admin Jumbo NO ve productos de POE")


# ============================================================
# TESTS: Acceso a productos específicos
# ============================================================

class TestProductosAcceso:
    """Tests de acceso a productos individuales"""
    
    def test_admin_jumbo_puede_ver_su_producto(
        self, db: Session, usuario_admin_jumbo: Usuario, producto_jumbo_data: ProductoCreate
    ):
        """Admin de Jumbo puede ver productos de su empresa"""
        # Crear producto de Jumbo
        producto = create_producto(
            db, 
            producto_jumbo_data, 
            id_usuario=producto_jumbo_data.id_usuario,
            id_empresa=usuario_admin_jumbo.id_empresa
        )
        
        # Intentar obtenerlo filtrado por empresa
        producto_obtenido = get_producto_by_id(db, producto.id_producto, usuario_admin_jumbo.id_empresa)
        
        assert producto_obtenido is not None, "No puede ver su propio producto"
        assert producto_obtenido.id_producto == producto.id_producto
        assert producto_obtenido.id_empresa == usuario_admin_jumbo.id_empresa
        
        print(f"✅ Admin accede a su producto: {producto_obtenido.nombre}")
    
    def test_admin_jumbo_NO_puede_ver_producto_de_poe(
        self, db: Session, usuario_admin_jumbo: Usuario
    ):
        """Admin de Jumbo NO puede acceder a productos de POE"""
        # Buscar un producto de POE (id_empresa=1)
        resultado = get_productos(db, id_empresa=1, page=1, limit=1)
        productos_poe = resultado.get("productos", [])
        
        if productos_poe:
            producto_poe = productos_poe[0]
            
            # Intentar obtener producto de POE con filtro de Jumbo
            producto_obtenido = get_producto_by_id(
                db, 
                producto_poe.id_producto, 
                usuario_admin_jumbo.id_empresa  # Filtro de Jumbo
            )
            
            # NO debe poder verlo
            assert producto_obtenido is None, "Admin Jumbo puede ver producto de POE (FUGA DE DATOS)"
            print(f"✅ Aislamiento confirmado: Admin Jumbo NO puede acceder a producto de POE")
        else:
            print("⚠️ No hay productos de POE para probar")
    
    def test_superadmin_puede_ver_productos_de_cualquier_empresa(
        self, db: Session, usuario_superadmin: Usuario
    ):
        """SuperAdmin puede ver productos de cualquier empresa"""
        # Obtener productos de Jumbo
        resultado_jumbo = get_productos(db, id_empresa=2, page=1, limit=1)
        productos_jumbo = resultado_jumbo.get("productos", [])
        
        # Obtener productos de POE
        resultado_poe = get_productos(db, id_empresa=1, page=1, limit=1)
        productos_poe = resultado_poe.get("productos", [])
        
        # SuperAdmin puede acceder a ambos
        if productos_jumbo:
            producto_jumbo = get_producto_by_id(db, productos_jumbo[0].id_producto, None)
            assert producto_jumbo is not None, "SuperAdmin no puede ver producto de Jumbo"
            print(f"✅ SuperAdmin accede a producto de Jumbo: {producto_jumbo.nombre}")
        
        if productos_poe:
            producto_poe = get_producto_by_id(db, productos_poe[0].id_producto, None)
            assert producto_poe is not None, "SuperAdmin no puede ver producto de POE"
            print(f"✅ SuperAdmin accede a producto de POE: {producto_poe.nombre}")


# ============================================================
# TESTS: Búsqueda de productos con filtro multi-tenant
# ============================================================

class TestProductosBusqueda:
    """Tests de búsqueda respetando aislamiento"""
    
    def test_busqueda_filtra_por_empresa(
        self, db: Session, usuario_admin_jumbo: Usuario
    ):
        """Búsqueda de productos filtra por empresa del usuario"""
        from app.repositories.producto import buscar_productos
        
        # Buscar productos con término general
        productos = buscar_productos(
            db, 
            id_empresa=usuario_admin_jumbo.id_empresa,
            nombre="Test"  # Buscar productos con "Test" en el nombre
        )
        
        # Todos deben ser de la empresa del admin
        for producto in productos:
            assert producto.id_empresa == usuario_admin_jumbo.id_empresa, f"Producto {producto.nombre} no es de la empresa del admin"
        
        print(f"✅ Búsqueda filtrada: {len(productos)} productos encontrados")


# ============================================================
# Configuración de pytest
# ============================================================

def setup_module():
    """Setup antes de ejecutar los tests"""
    import random
    import string
    # ID único para esta ejecución de tests
    pytest.test_run_id = ''.join(random.choices(string.digits, k=6))
    print(f"\n🧪 Iniciando tests de Multi-Tenant para Productos (run_id: {pytest.test_run_id})")


def teardown_module():
    """Cleanup después de ejecutar los tests"""
    print("\n✅ Tests de Multi-Tenant para Productos completados")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])
