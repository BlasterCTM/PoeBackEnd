import requests
import json
from typing import Dict, Optional

class TestSupervisor:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.admin_token = None
        self.supervisor_token = None
        self.reponedor_id = None
    
    def login_admin(self) -> Optional[str]:
        """Login como administrador para crear supervisor"""
        login_data = {
            "correo": "admin@poe.com",
            "contraseña": "admin123"
        }
        
        response = requests.post(
            f"{self.base_url}/usuarios/token",
            json=login_data
        )
        
        if response.status_code == 200:
            self.admin_token = response.json()["access_token"]
            print("✅ Login administrador exitoso")
            return self.admin_token
        else:
            print(f"❌ Error en login administrador: {response.json()}")
            return None

    def crear_supervisor(self) -> Optional[Dict]:
        """Crear un supervisor de prueba"""
        if not self.admin_token:
            print("❌ Se requiere token de administrador")
            return None
            
        supervisor_data = {
            "nombre": "Supervisor Test",
            "correo": "supervisor.test@poe.com",
            "contraseña": "supervisor123",
            "rol": "Supervisor"
        }
        
        headers = {
            "Authorization": f"Bearer {self.admin_token}"
        }
        
        response = requests.post(
            f"{self.base_url}/usuarios/",
            json=supervisor_data,
            headers=headers
        )
        
        if response.status_code == 201:
            print("✅ Supervisor creado exitosamente")
            return response.json()
        else:
            print(f"❌ Error al crear supervisor: {response.json()}")
            return None

    def login_supervisor(self) -> Optional[str]:
        """Login como supervisor"""
        login_data = {
            "correo": "supervisor.test@poe.com",
            "contraseña": "supervisor123"
        }
        
        response = requests.post(
            f"{self.base_url}/usuarios/token",
            json=login_data
        )
        
        if response.status_code == 200:
            self.supervisor_token = response.json()["access_token"]
            print("✅ Login supervisor exitoso")
            return self.supervisor_token
        else:
            print(f"❌ Error en login supervisor: {response.json()}")
            return None

    def crear_reponedor(self) -> Optional[Dict]:
        """Crear un reponedor de prueba"""
        if not self.supervisor_token:
            print("❌ Se requiere token de supervisor")
            return None
            
        reponedor_data = {
            "nombre": "Reponedor Test",
            "correo": "reponedor.test@poe.com",
            "contraseña": "reponedor123",
            "estado": "activo"
        }
        
        headers = {
            "Authorization": f"Bearer {self.supervisor_token}"
        }
        
        response = requests.post(
            f"{self.base_url}/supervisor/reponedores",
            json=reponedor_data,
            headers=headers
        )
        
        if response.status_code == 201:
            print("✅ Reponedor creado exitosamente")
            self.reponedor_id = response.json()["usuario"]["id_usuario"]
            return response.json()
        else:
            print(f"❌ Error al crear reponedor: {response.json()}")
            return None

    def listar_reponedores_disponibles(self) -> Optional[Dict]:
        """Listar reponedores disponibles para asignar"""
        if not self.supervisor_token:
            print("❌ Se requiere token de supervisor")
            return None
            
        headers = {
            "Authorization": f"Bearer {self.supervisor_token}"
        }
        
        response = requests.get(
            f"{self.base_url}/supervisor/reponedores/disponibles",
            headers=headers
        )
        
        if response.status_code == 200:
            print("✅ Lista de reponedores disponibles obtenida")
            return response.json()
        else:
            print(f"❌ Error al listar reponedores disponibles: {response.json()}")
            return None

    def asignar_reponedor(self, reponedor_id: int) -> Optional[Dict]:
        """Asignar un reponedor al supervisor"""
        if not self.supervisor_token:
            print("❌ Se requiere token de supervisor")
            return None
            
        headers = {
            "Authorization": f"Bearer {self.supervisor_token}"
        }
        
        response = requests.post(
            f"{self.base_url}/supervisor/reponedores/{reponedor_id}/asignar",
            headers=headers
        )
        
        if response.status_code == 200:
            print("✅ Reponedor asignado exitosamente")
            return response.json()
        else:
            print(f"❌ Error al asignar reponedor: {response.json()}")
            return None

    def listar_reponedores_asignados(self) -> Optional[Dict]:
        """Listar reponedores asignados al supervisor"""
        if not self.supervisor_token:
            print("❌ Se requiere token de supervisor")
            return None
            
        headers = {
            "Authorization": f"Bearer {self.supervisor_token}"
        }
        
        response = requests.get(
            f"{self.base_url}/supervisor/reponedores",
            headers=headers
        )
        
        if response.status_code == 200:
            print("✅ Lista de reponedores asignados obtenida")
            return response.json()
        else:
            print(f"❌ Error al listar reponedores asignados: {response.json()}")
            return None

    def desasignar_reponedor(self, reponedor_id: int) -> Optional[Dict]:
        """Desasignar un reponedor del supervisor"""
        if not self.supervisor_token:
            print("❌ Se requiere token de supervisor")
            return None
            
        headers = {
            "Authorization": f"Bearer {self.supervisor_token}"
        }
        
        response = requests.delete(
            f"{self.base_url}/supervisor/reponedores/{reponedor_id}/desasignar",
            headers=headers
        )
        
        if response.status_code == 200:
            print("✅ Reponedor desasignado exitosamente")
            return response.json()
        else:
            print(f"❌ Error al desasignar reponedor: {response.json()}")
            return None

def run_tests():
    print("\n=== Iniciando pruebas de gestión de reponedores ===\n")
    
    test = TestSupervisor()
    
    # 1. Login como administrador
    if not test.login_admin():
        return
    
    # 2. Crear supervisor de prueba
    if not test.crear_supervisor():
        return
    
    # 3. Login como supervisor
    if not test.login_supervisor():
        return
    
    # 4. Crear reponedor
    reponedor = test.crear_reponedor()
    if not reponedor:
        return
    
    print("\n--- Reponedor creado:", json.dumps(reponedor, indent=2))
    
    # 5. Listar reponedores disponibles
    disponibles = test.listar_reponedores_disponibles()
    if not disponibles:
        return
    
    print("\n--- Reponedores disponibles:", json.dumps(disponibles, indent=2))
    
    # 6. Asignar reponedor
    if test.reponedor_id:
        asignacion = test.asignar_reponedor(test.reponedor_id)
        if not asignacion:
            return
        
        print("\n--- Asignación:", json.dumps(asignacion, indent=2))
    
    # 7. Listar reponedores asignados
    asignados = test.listar_reponedores_asignados()
    if not asignados:
        return
    
    print("\n--- Reponedores asignados:", json.dumps(asignados, indent=2))
    
    # 8. Desasignar reponedor
    if test.reponedor_id:
        desasignacion = test.desasignar_reponedor(test.reponedor_id)
        if not desasignacion:
            return
        
        print("\n--- Desasignación:", json.dumps(desasignacion, indent=2))
    
    print("\n=== Pruebas completadas exitosamente ===\n")

if __name__ == "__main__":
    run_tests()
