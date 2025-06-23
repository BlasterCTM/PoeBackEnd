# File: app/schemas/rutas.py
from pydantic import BaseModel

class Punto(BaseModel):
    x: int
    y: int

class RutaOptimaRequest(BaseModel):
    mapa_id: int
    inicio: Punto
    fin: Punto

class RutaOptimaResponse(BaseModel):
    ruta: list[Punto]
