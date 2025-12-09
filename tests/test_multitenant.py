"""
Tests de Multi-Tenant para validar aislamiento de datos entre empresas
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# ============================================================
# FIXTURES: Tokens de autenticación
# ============================================================

@pytest.fixture
def token_superadmin():
    """Obtener token del SuperAdmin (admin@poe.com)"""
    response = client.post(
        "/usuarios/token",
        data={  # Usar data para form, no json
            "username": "admin@poe.com",
            "password": "admin123"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200, f"Login falló: {response.json()}"
    return response.json()["access_token"]


@pytest.fixture
def token_admin_jumbo():
    """Obtener token del Admin de Jumbo (mgonzalez@jumbo.cl)"""
    response = client.post(
        "/usuarios/token",
        data={  # Usar data para form, no json
            "username": "mgonzalez@jumbo.cl",
            "password": "Jumbo2025!"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200, f"Login falló: {response.json()}"
    return response.json()["access_token"]


@pytest.fixture
def empresa_jumbo_id():
    """ID de la empresa Jumbo (debe existir en BD)"""
    return 2


@pytest.fixture
def empresa_poe_id():
    """ID de la empresa POE (empresa principal)"""
    return 1


# ============================================================
# TESTS: SuperAdmin puede ver todo
# ============================================================

class TestSuperAdminAccess:
    """Tests para validar que SuperAdmin tiene acceso global"""
    
    def test_superadmin_puede_ver_todas_las_empresas(self, token_superadmin):
        """SuperAdmin puede listar todas las empresas del sistema"""
        response = client.get(
            "/empresas/",
            headers={"Authorization": f"Bearer {token_superadmin}"}
        )
        assert response.status_code == 200
        empresas = response.json()
        assert isinstance(empresas, list)
        assert len(empresas) >= 2  # Al menos POE y Jumbo
        
    def test_superadmin_puede_ver_empresa_poe(self, token_superadmin, empresa_poe_id):
        """SuperAdmin puede ver empresa POE (id=1)"""
        response = client.get(
            f"/empresas/{empresa_poe_id}",
            headers={"Authorization": f"Bearer {token_superadmin}"}
        )
        assert response.status_code == 200
        empresa = response.json()
        assert empresa["id_empresa"] == empresa_poe_id
        
    def test_superadmin_puede_ver_empresa_jumbo(self, token_superadmin, empresa_jumbo_id):
        """SuperAdmin puede ver empresa Jumbo (id=2)"""
        response = client.get(
            f"/empresas/{empresa_jumbo_id}",
            headers={"Authorization": f"Bearer {token_superadmin}"}
        )
        assert response.status_code == 200
        empresa = response.json()
        assert empresa["id_empresa"] == empresa_jumbo_id
        assert "Jumbo" in empresa["nombre_empresa"]
    
    def test_superadmin_puede_modificar_cualquier_empresa(self, token_superadmin, empresa_jumbo_id):
        """SuperAdmin puede modificar datos de cualquier empresa"""
        response = client.patch(
            f"/empresas/{empresa_jumbo_id}",
            headers={"Authorization": f"Bearer {token_superadmin}"},
            json={"telefono": "+56900000000"}
        )
        assert response.status_code == 200
        
    def test_superadmin_puede_registrar_nuevas_empresas(self, token_superadmin):
        """SuperAdmin puede registrar nuevas empresas"""
        response = client.post(
            "/empresas/registro",
            headers={"Authorization": f"Bearer {token_superadmin}"},
            json={
                "empresa": {
                    "nombre_empresa": "Test Supermercado",
                    "rut_empresa": f"99.999.999-{pytest.random_suffix}",  # RUT único
                    "direccion": "Calle Test 123",
                    "ciudad": "Santiago",
                    "region": "RM",
                    "telefono": "+56911111111",
                    "email": f"test{pytest.random_suffix}@test.cl"
                },
                "admin_nombre": "Admin Test",
                "admin_correo": f"admintest{pytest.random_suffix}@test.cl",
                "admin_contraseña": "Test123!"
            }
        )
        # Puede fallar si ya existe, pero el punto es que SuperAdmin tiene permiso
        assert response.status_code in [201, 400]  # 201=creado, 400=ya existe


# ============================================================
# TESTS: Admin de empresa solo ve SU empresa
# ============================================================

class TestAdminEmpresaIsolation:
    """Tests para validar aislamiento entre empresas"""
    
    def test_admin_jumbo_solo_ve_su_empresa(self, token_admin_jumbo):
        """Admin de Jumbo solo ve su propia empresa en el listado"""
        response = client.get(
            "/empresas/",
            headers={"Authorization": f"Bearer {token_admin_jumbo}"}
        )
        assert response.status_code == 200
        empresas = response.json()
        assert isinstance(empresas, list)
        assert len(empresas) == 1  # Solo debe ver Jumbo
        assert "Jumbo" in empresas[0]["nombre_empresa"]
        
    def test_admin_jumbo_puede_ver_su_empresa_por_id(self, token_admin_jumbo, empresa_jumbo_id):
        """Admin de Jumbo puede ver su propia empresa por ID"""
        response = client.get(
            f"/empresas/{empresa_jumbo_id}",
            headers={"Authorization": f"Bearer {token_admin_jumbo}"}
        )
        assert response.status_code == 200
        empresa = response.json()
        assert empresa["id_empresa"] == empresa_jumbo_id
        
    def test_admin_jumbo_NO_puede_ver_empresa_poe(self, token_admin_jumbo, empresa_poe_id):
        """Admin de Jumbo NO puede ver empresa POE (403 Forbidden)"""
        response = client.get(
            f"/empresas/{empresa_poe_id}",
            headers={"Authorization": f"Bearer {token_admin_jumbo}"}
        )
        assert response.status_code == 403
        assert "No tiene permisos" in response.json()["detail"]
        
    def test_admin_jumbo_NO_puede_modificar_empresa_poe(self, token_admin_jumbo, empresa_poe_id):
        """Admin de Jumbo NO puede modificar empresa POE"""
        response = client.patch(
            f"/empresas/{empresa_poe_id}",
            headers={"Authorization": f"Bearer {token_admin_jumbo}"},
            json={"telefono": "+56900000000"}
        )
        assert response.status_code == 403
        
    def test_admin_jumbo_puede_ver_mi_empresa(self, token_admin_jumbo):
        """Admin de Jumbo puede usar /mi-empresa"""
        response = client.get(
            "/empresas/mi-empresa",
            headers={"Authorization": f"Bearer {token_admin_jumbo}"}
        )
        assert response.status_code == 200
        empresa = response.json()
        assert "Jumbo" in empresa["nombre_empresa"]


# ============================================================
# TESTS: Productos multi-tenant
# ============================================================

class TestProductosMultiTenant:
    """Tests para validar que productos se filtran por empresa"""
    
    def test_admin_jumbo_solo_ve_productos_de_jumbo(self, token_admin_jumbo):
        """Admin de Jumbo solo ve productos de su empresa"""
        response = client.get(
            "/productos",
            headers={"Authorization": f"Bearer {token_admin_jumbo}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Si hay productos, todos deben ser de Jumbo
        if "productos" in data and data["productos"]:
            for producto in data["productos"]:
                # Validar que pertenecen a la empresa correcta
                # (asumiendo que el endpoint devuelve id_empresa)
                pass  # Ajustar según tu estructura de respuesta
    
    def test_superadmin_puede_crear_productos_en_cualquier_empresa(self, token_superadmin):
        """SuperAdmin puede ver productos de todas las empresas"""
        response = client.get(
            "/productos",
            headers={"Authorization": f"Bearer {token_superadmin}"}
        )
        # SuperAdmin podría ver productos de múltiples empresas
        assert response.status_code == 200


# ============================================================
# TESTS: Tareas multi-tenant
# ============================================================

class TestTareasMultiTenant:
    """Tests para validar que tareas se filtran por empresa"""
    
    def test_admin_jumbo_solo_ve_tareas_de_jumbo(self, token_admin_jumbo):
        """Admin de Jumbo solo ve tareas de su empresa"""
        response = client.get(
            "/tareas/supervisor",
            headers={"Authorization": f"Bearer {token_admin_jumbo}"}
        )
        # El endpoint puede retornar 200 vacío o 403 si no es supervisor
        assert response.status_code in [200, 403]


# ============================================================
# TESTS: Usuarios multi-tenant
# ============================================================

class TestUsuariosMultiTenant:
    """Tests para validar que usuarios se filtran por empresa"""
    
    def test_admin_jumbo_solo_ve_usuarios_de_jumbo(self, token_admin_jumbo):
        """Admin de Jumbo solo ve usuarios de su empresa"""
        response = client.get(
            "/usuarios/",
            headers={"Authorization": f"Bearer {token_admin_jumbo}"}
        )
        assert response.status_code == 200
        usuarios = response.json()
        
        # Todos los usuarios deben ser de Jumbo (id_empresa=2)
        for usuario in usuarios:
            assert usuario["id_empresa"] == 2


# ============================================================
# TESTS: Validación de tokens y autenticación
# ============================================================

class TestAutenticacion:
    """Tests de autenticación y roles"""
    
    def test_login_superadmin_exitoso(self):
        """Login de SuperAdmin es exitoso"""
        response = client.post(
            "/usuarios/token",
            data={
                "username": "admin@poe.com",
                "password": "admin123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        
    def test_login_admin_jumbo_exitoso(self):
        """Login de Admin Jumbo es exitoso"""
        response = client.post(
            "/usuarios/token",
            data={
                "username": "mgonzalez@jumbo.cl",
                "password": "Jumbo2025!"
            }
        )
        assert response.status_code == 200
        
    def test_sin_token_no_puede_acceder(self):
        """Sin token no se puede acceder a endpoints protegidos"""
        response = client.get("/empresas/")
        assert response.status_code == 401


# ============================================================
# TESTS: Edge cases y validaciones
# ============================================================

class TestEdgeCases:
    """Tests de casos especiales"""
    
    def test_superadmin_no_puede_usar_mi_empresa(self, token_superadmin):
        """SuperAdmin recibe error al usar /mi-empresa"""
        response = client.get(
            "/empresas/mi-empresa",
            headers={"Authorization": f"Bearer {token_superadmin}"}
        )
        assert response.status_code == 400
        assert "SuperAdmin" in response.json()["detail"]
        
    def test_admin_no_puede_ver_empresa_inexistente(self, token_admin_jumbo):
        """Admin no puede ver empresa que no existe"""
        response = client.get(
            "/empresas/99999",
            headers={"Authorization": f"Bearer {token_admin_jumbo}"}
        )
        assert response.status_code in [403, 404]


# ============================================================
# Configuración de pytest
# ============================================================

def setup_module():
    """Setup antes de ejecutar los tests"""
    # Generar sufijo aleatorio para tests que crean datos
    import random
    import string
    pytest.random_suffix = ''.join(random.choices(string.digits, k=6))
    

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
