from pydantic import BaseModel, Field
from typing import Optional

class MuebleCompletoCreate(BaseModel):
    nombre: str = Field(..., min_length=1, description="Nombre visible en el mapa")
    filas: int = Field(..., gt=0, description="Cantidad de niveles verticales")
    columnas: int = Field(..., gt=0, description="Cantidad de divisiones horizontales")
    direccion: Optional[str] = Field("T", description="Dirección de acceso: N, S, E, O, T")
