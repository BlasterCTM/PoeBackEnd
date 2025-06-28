from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from app.models.ruta_optimizada import RutaOptimizada
from app.models.detalle_ruta import DetalleRuta
from app.models.paso_ruta import PasoRuta
from app.models.metrica_optimizacion import MetricaOptimizacion
from app.schemas.ruta_detallada import (
    RutaOptimizadaCreate, 
    DetalleRutaCreate, 
    PasoRutaCreate,
    MetricaOptimizacionCreate
)

class RutaDetalladaRepository:
    
    @staticmethod
    def crear_ruta_completa(
        db: Session,
        ruta_data: RutaOptimizadaCreate,
        detalles_data: List[DetalleRutaCreate],
        pasos_data: List[List[PasoRutaCreate]]  # Lista de listas: pasos para cada detalle
    ) -> RutaOptimizada:
        """
        Crea una ruta completa con todos sus detalles y pasos
        """
        # Crear la ruta principal
        ruta = RutaOptimizada(**ruta_data.dict())
        db.add(ruta)
        db.flush()  # Para obtener el ID de la ruta
        
        # Crear los detalles de la ruta
        for i, detalle_data in enumerate(detalles_data):
            detalle = DetalleRuta(
                id_ruta=ruta.id_ruta,
                **detalle_data.dict(exclude={'id_ruta'})
            )
            db.add(detalle)
            db.flush()  # Para obtener el ID del detalle
            
            # Crear los pasos para este detalle
            if i < len(pasos_data):
                for paso_data in pasos_data[i]:
                    paso = PasoRuta(
                        id_detalle_ruta=detalle.id_detalle_ruta,
                        **paso_data.dict(exclude={'id_detalle_ruta'})
                    )
                    db.add(paso)
        
        db.commit()
        db.refresh(ruta)
        return ruta
    
    @staticmethod
    def obtener_ruta_por_id(db: Session, id_ruta: int) -> Optional[RutaOptimizada]:
        """
        Obtiene una ruta con todos sus detalles y pasos
        """
        return db.query(RutaOptimizada).filter(RutaOptimizada.id_ruta == id_ruta).first()
    
    @staticmethod
    def obtener_rutas_por_tarea(db: Session, id_tarea: int) -> List[RutaOptimizada]:
        """
        Obtiene todas las rutas de una tarea específica
        """
        return db.query(RutaOptimizada).filter(RutaOptimizada.id_tarea == id_tarea).all()
    
    @staticmethod
    def obtener_rutas_por_reponedor(db: Session, id_reponedor: int) -> List[RutaOptimizada]:
        """
        Obtiene todas las rutas de un reponedor específico
        """
        return db.query(RutaOptimizada).filter(RutaOptimizada.id_reponedor == id_reponedor).all()
    
    @staticmethod
    def agregar_metrica(db: Session, metrica_data: MetricaOptimizacionCreate) -> MetricaOptimizacion:
        """
        Agrega métricas de optimización a una ruta
        """
        metrica = MetricaOptimizacion(**metrica_data.dict())
        db.add(metrica)
        db.commit()
        db.refresh(metrica)
        return metrica
    
    @staticmethod
    def obtener_pasos_detalle(db: Session, id_detalle_ruta: int) -> List[PasoRuta]:
        """
        Obtiene todos los pasos de un detalle de ruta específico
        """
        return db.query(PasoRuta).filter(
            PasoRuta.id_detalle_ruta == id_detalle_ruta
        ).order_by(PasoRuta.secuencia).all()
    
    @staticmethod
    def eliminar_ruta(db: Session, id_ruta: int) -> bool:
        """
        Elimina una ruta y todos sus detalles y pasos (por CASCADE)
        """
        ruta = db.query(RutaOptimizada).filter(RutaOptimizada.id_ruta == id_ruta).first()
        if ruta:
            db.delete(ruta)
            db.commit()
            return True
        return False
