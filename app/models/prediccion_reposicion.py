from sqlalchemy import Column, Integer, String, DateTime, ARRAY, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database.database import Base


class PrediccionReposicion(Base):
    """
    Modelo para almacenar predicciones de reposición generadas por el modelo ML.
    
    Cada registro representa una predicción mensual para una empresa específica,
    con detalles de qué categorías/ubicaciones deben reponerse y en qué cantidades.
    """
    __tablename__ = "predicciones_reposicion"
    
    # ============================================
    # IDENTIFICACIÓN
    # ============================================
    id_prediccion = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_empresa = Column(Integer, ForeignKey("empresa.id_empresa", ondelete="CASCADE"), nullable=False, index=True)
    
    # ============================================
    # PERÍODO DE PREDICCIÓN
    # ============================================
    mes = Column(Integer, nullable=False)  # 1-12
    anio = Column(Integer, nullable=False)  # 2024, 2025, etc.
    semana_mes = Column(Integer)  # 1-5 (opcional, si se predice por semana)
    
    # ============================================
    # METADATA DEL MODELO
    # ============================================
    version_modelo = Column(String(20), default="1.0.0")  # Versión del pipeline usado
    fecha_generacion = Column(DateTime, default=datetime.utcnow, nullable=False)
    generado_por = Column(Integer, ForeignKey("usuario.id_usuario"))  # Supervisor/Admin que solicitó
    
    # ============================================
    # RESULTADOS DE LA PREDICCIÓN
    # ============================================
    # Estructura JSON con predicciones detalladas
    # Ejemplo:
    # {
    #   "resumen": {
    #     "total_reposiciones": 145,
    #     "total_unidades": 3850,
    #     "categorias_activas": ["Lacteos", "Panaderia", "Frutas_Verduras"]
    #   },
    #   "por_categoria": [
    #     {
    #       "categoria": "Lacteos",
    #       "ubicacion_mueble": 118,
    #       "reposiciones": 25,
    #       "total_unidades": 780,
    #       "dias_predichos": [1, 3, 5, 8, 10, ...]
    #     },
    #     ...
    #   ],
    #   "por_semana": [
    #     {
    #       "semana": 1,
    #       "fecha_inicio": "2025-12-01",
    #       "fecha_fin": "2025-12-07",
    #       "total_unidades": 850,
    #       "categorias": {...}
    #     },
    #     ...
    #   ]
    # }
    resultados_prediccion = Column(JSON, nullable=False)
    
    # ============================================
    # FEATURES USADOS EN LA PREDICCIÓN
    # ============================================
    # Almacena los features utilizados para auditoría/debugging
    # Ejemplo:
    # {
    #   "features": ["categoria_producto", "ubicacion_mueble", "hora", "dia_semana", "mes"],
    #   "n_registros_simulados": 2000,
    #   "accuracy_clasificador": 0.89,
    #   "r2_regresor": 0.76
    # }
    features_utilizados = Column(JSON)
    
    # ============================================
    # ESTADO Y NOTAS
    # ============================================
    estado = Column(String(20), default="pendiente")  # pendiente, aplicado, rechazado
    notas = Column(Text)  # Comentarios del supervisor
    
    # ============================================
    # AUDITORÍA
    # ============================================
    fecha_actualizacion = Column(DateTime, onupdate=datetime.utcnow)
    
    # ============================================
    # RELACIONES
    # ============================================
    empresa = relationship("Empresa", foreign_keys=[id_empresa])
    usuario = relationship("Usuario", foreign_keys=[generado_por])
    
    # ============================================
    # CONSTRAINTS
    # ============================================
    __table_args__ = (
        # Asegurar que mes esté en rango válido
        # CheckConstraint('mes BETWEEN 1 AND 12', name='prediccion_mes_check'),
        # Evitar duplicados de predicción para mismo mes/año/empresa/semana
        # UniqueConstraint('id_empresa', 'mes', 'anio', 'semana_mes', name='uq_prediccion_empresa_periodo'),
    )
    
    def __repr__(self):
        return f"<PrediccionReposicion(id={self.id_prediccion}, empresa={self.id_empresa}, periodo={self.mes}/{self.anio})>"
