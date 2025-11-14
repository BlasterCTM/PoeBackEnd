"""
Script para generar hash de contraseña compatible con el sistema POE
"""
from passlib.context import CryptContext

# Usar el mismo contexto de password que usa la aplicación
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Generar hash para "admin123"
password = "admin123"
hashed = pwd_context.hash(password)

print("=" * 60)
print("HASH GENERADO PARA LA CONTRASEÑA")
print("=" * 60)
print(f"Contraseña: {password}")
print(f"Hash: {hashed}")
print("=" * 60)
print("\nCopia este hash y úsalo en el script SQL insert_superadmin.sql")
print("=" * 60)
