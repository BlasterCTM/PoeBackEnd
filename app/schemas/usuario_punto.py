from pydantic import BaseModel

class AsignarPuntoRequest(BaseModel):
    id_usuario: int
    id_punto: int
