from app.core.database.database import Database
from app.models.usuario import Rol, Usuario

def recreate_database():
    database = Database()
    print("Recreando la base de datos...")
    database.Base.metadata.drop_all(bind=database.engine)
    database.Base.metadata.create_all(bind=database.engine)
    print("Base de datos recreada exitosamente")

if __name__ == "__main__":
    recreate_database()
