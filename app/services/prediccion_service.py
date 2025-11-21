"""
Servicio de predicción de reposiciones usando Machine Learning.

Este servicio:
1. Carga el pipeline entrenado (clasificador + regresor)
2. Genera predicciones para períodos futuros
3. Almacena resultados en la base de datos
4. Proporciona análisis agregados por categoría y semana
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime, date
from calendar import monthrange
from pathlib import Path
import joblib
from sqlalchemy.orm import Session

from app.repositories.prediccion_repo import prediccion_repository
from app.models.prediccion_reposicion import PrediccionReposicion
from app.schemas.prediccion import (
    PrediccionRequest,
    PrediccionResponse,
    PrediccionHistorialItem,
    PrediccionHistorialResponse,
    ResumenPrediccion,
    CategoriaPrediction,
    SemanaPrediction,
    EstadoPrediccion
)


class PredictionService:
    """Servicio para generar y gestionar predicciones ML de reposiciones"""
    
    def __init__(self):
        """Inicializa el servicio y carga el pipeline ML"""
        self.pipeline_path = Path(__file__).resolve().parent.parent / "predict" / "pipeline_prediccion.pkl"
        self.pipeline_loaded = False
        self.pipeline_clasificador = None
        self.pipeline_regresor = None
        self.metadatos = None
        
    def _cargar_pipeline(self):
        """Carga el pipeline desde disco (lazy loading)"""
        if self.pipeline_loaded:
            return
        
        if not self.pipeline_path.exists():
            raise FileNotFoundError(
                f"Pipeline no encontrado en {self.pipeline_path}. "
                "Ejecuta: python -m app.predict.train_pipeline"
            )
        
        try:
            package = joblib.load(self.pipeline_path)
            self.pipeline_clasificador = package['pipeline_clasificador']
            self.pipeline_regresor = package['pipeline_regresor']
            self.metadatos = package['metadatos']
            self.pipeline_loaded = True
            print(f"✅ Pipeline cargado: versión {self.metadatos['version']}")
        except Exception as e:
            raise RuntimeError(f"Error cargando pipeline: {str(e)}")
    
    def generar_prediccion_mes(
        self,
        db: Session,
        id_empresa: int,
        id_usuario: int,
        request: PrediccionRequest
    ) -> PrediccionResponse:
        """
        Genera predicción de reposiciones para un mes específico.
        
        Args:
            db: Sesión de base de datos
            id_empresa: ID de la empresa (multi-tenant)
            id_usuario: ID del usuario que solicita predicción
            request: Parámetros de la predicción
            
        Returns:
            PrediccionResponse con resultados completos
        """
        # Cargar pipeline si no está cargado
        self._cargar_pipeline()
        
        # Verificar si ya existe predicción para este período
        prediccion_existente = prediccion_repository.get_by_periodo(
            db, id_empresa, request.mes, request.anio
        )
        
        if prediccion_existente:
            # Devolver predicción existente
            return self._convertir_a_response(prediccion_existente)
        
        # Generar datos simulados para el mes
        df_simulado = self._generar_datos_mes(request.mes, request.anio)
        
        # Ejecutar predicciones
        resultados_prediccion = self._ejecutar_prediccion(
            df_simulado, 
            incluir_semanas=request.incluir_semanas
        )
        
        # Persistir en BD
        prediccion_db = prediccion_repository.crear_prediccion(
            db=db,
            id_empresa=id_empresa,
            mes=request.mes,
            anio=request.anio,
            resultados=resultados_prediccion,
            version_modelo=self.metadatos['version'],
            generado_por=id_usuario,
            features_utilizados={
                "features": self.metadatos['feature_cols'],
                "accuracy_clasificador": self.metadatos['accuracy_clasificador'],
                "r2_regresor": self.metadatos['r2_regresor'],
                "n_filas_entrenamiento": self.metadatos['n_filas_entrenamiento']
            },
            notas=request.notas
        )
        
        # Convertir a response
        return self._convertir_a_response(prediccion_db)
    
    def _generar_datos_mes(self, mes: int, anio: int) -> pd.DataFrame:
        """
        Genera DataFrame con todas las combinaciones de categorías/días para predicción.
        
        Args:
            mes: Mes (1-12)
            anio: Año
            
        Returns:
            DataFrame con features para predicción
        """
        num_dias = monthrange(anio, mes)[1]
        categorias = self.metadatos['categorias_producto']
        
        # Ubicaciones de muebles (basado en datos de entrenamiento)
        ubicaciones = list(range(100, 125))  # Ejemplo: muebles 100-124
        
        data = []
        for dia in range(1, num_dias + 1):
            fecha = datetime(anio, mes, dia)
            dia_semana = fecha.weekday()  # 0=Monday, 6=Sunday
            semana_mes = (dia - 1) // 7 + 1
            
            for categoria in categorias:
                # Generar predicción para hora promedio (12pm)
                for ubicacion in [np.random.choice(ubicaciones)]:  # Una ubicación por categoría/día
                    data.append({
                        'categoria_producto': categoria,
                        'ubicacion_mueble': ubicacion,
                        'hora': 12,
                        'dia_semana': dia_semana,
                        'mes': mes,
                        'semana_mes': semana_mes,
                        'dia_del_mes': dia
                    })
        
        return pd.DataFrame(data)
    
    def _ejecutar_prediccion(
        self, 
        df: pd.DataFrame,
        incluir_semanas: bool = True
    ) -> Dict[str, Any]:
        """
        Ejecuta predicción con clasificador y regresor.
        
        Args:
            df: DataFrame con features
            incluir_semanas: Si se deben generar predicciones por semana
            
        Returns:
            Diccionario con resultados estructurados
        """
        # 1. Clasificación (¿habrá reposición?)
        prediccion_cls = self.pipeline_clasificador.predict(df)
        df['reposicion_predicha'] = prediccion_cls
        
        # 2. Regresión (cantidad) solo donde se predijo reposición
        df_con_reposicion = df[df['reposicion_predicha'] == 1].copy()
        
        if len(df_con_reposicion) > 0:
            cantidad_pred = self.pipeline_regresor.predict(df_con_reposicion)
            # Redondear y asegurar valores positivos
            cantidad_pred = [max(0, round(x)) for x in cantidad_pred]
            df_con_reposicion['cantidad_predicha'] = cantidad_pred
        else:
            df_con_reposicion['cantidad_predicha'] = []
        
        # 3. Agregar por categoría
        por_categoria = []
        if len(df_con_reposicion) > 0:
            agrupado = df_con_reposicion.groupby('categoria_producto').agg(
                reposiciones=('cantidad_predicha', 'count'),
                total_unidades=('cantidad_predicha', 'sum'),
                ubicacion_promedio=('ubicacion_mueble', 'mean'),
                dias_predichos=('dia_del_mes', lambda x: sorted(x.unique()))
            ).reset_index()
            
            for _, row in agrupado.iterrows():
                por_categoria.append({
                    "categoria": row['categoria_producto'],
                    "ubicacion_mueble": int(round(row['ubicacion_promedio'])),
                    "reposiciones": int(row['reposiciones']),
                    "total_unidades": int(row['total_unidades']),
                    "dias_predichos": [int(d) for d in row['dias_predichos']]
                })
        
        # 4. Agregar por semana (opcional)
        por_semana = []
        if incluir_semanas and len(df_con_reposicion) > 0:
            agrupado_semana = df_con_reposicion.groupby('semana_mes').agg(
                total_unidades=('cantidad_predicha', 'sum'),
                categorias=('categoria_producto', list)
            ).reset_index()
            
            for _, row in agrupado_semana.iterrows():
                semana = int(row['semana_mes'])
                # Calcular rango de días de la semana
                dia_inicio = (semana - 1) * 7 + 1
                dia_fin = min(semana * 7, df['dia_del_mes'].max())
                
                # Agregar unidades por categoría en esta semana
                df_semana = df_con_reposicion[df_con_reposicion['semana_mes'] == semana]
                cat_dict = df_semana.groupby('categoria_producto')['cantidad_predicha'].sum().to_dict()
                cat_dict = {k: int(v) for k, v in cat_dict.items()}
                
                por_semana.append({
                    "semana": semana,
                    "fecha_inicio": f"{df['mes'].iloc[0]:02d}-{dia_inicio:02d}",
                    "fecha_fin": f"{df['mes'].iloc[0]:02d}-{dia_fin:02d}",
                    "total_unidades": int(row['total_unidades']),
                    "categorias": cat_dict
                })
        
        # 5. Resumen ejecutivo
        total_reposiciones = int(len(df_con_reposicion)) if len(df_con_reposicion) > 0 else 0
        total_unidades = int(df_con_reposicion['cantidad_predicha'].sum()) if len(df_con_reposicion) > 0 else 0
        categorias_activas = sorted(df_con_reposicion['categoria_producto'].unique()) if len(df_con_reposicion) > 0 else []
        promedio_diario = total_unidades / df['dia_del_mes'].nunique() if len(df) > 0 else 0
        
        resumen = {
            "total_reposiciones": total_reposiciones,
            "total_unidades": total_unidades,
            "categorias_activas": categorias_activas,
            "promedio_diario": round(promedio_diario, 2)
        }
        
        # 6. Estructura final
        return {
            "resumen": resumen,
            "por_categoria": por_categoria,
            "por_semana": por_semana if incluir_semanas else None
        }
    
    def _convertir_a_response(self, prediccion_db: PrediccionReposicion) -> PrediccionResponse:
        """
        Convierte modelo de BD a schema de response.
        
        Args:
            prediccion_db: Objeto de BD
            
        Returns:
            PrediccionResponse
        """
        resultados = prediccion_db.resultados_prediccion
        
        return PrediccionResponse(
            id_prediccion=prediccion_db.id_prediccion,
            id_empresa=prediccion_db.id_empresa,
            mes=prediccion_db.mes,
            anio=prediccion_db.anio,
            version_modelo=prediccion_db.version_modelo,
            fecha_generacion=prediccion_db.fecha_generacion,
            estado=EstadoPrediccion(prediccion_db.estado),
            resumen=ResumenPrediccion(**resultados['resumen']),
            por_categoria=[CategoriaPrediction(**cat) for cat in resultados['por_categoria']],
            por_semana=[SemanaPrediction(**sem) for sem in resultados['por_semana']] if resultados.get('por_semana') else None,
            features_utilizados=prediccion_db.features_utilizados,
            notas=prediccion_db.notas
        )
    
    def obtener_historial(
        self,
        db: Session,
        id_empresa: int,
        skip: int = 0,
        limit: int = 20
    ) -> PrediccionHistorialResponse:
        """
        Obtiene historial de predicciones de una empresa.
        
        Args:
            db: Sesión de base de datos
            id_empresa: ID de la empresa
            skip: Offset para paginación
            limit: Límite de resultados
            
        Returns:
            PrediccionHistorialResponse con lista de predicciones
        """
        predicciones = prediccion_repository.get_historial_empresa(db, id_empresa, skip, limit)
        total = prediccion_repository.count_by_empresa(db, id_empresa)
        
        items = []
        for p in predicciones:
            resumen = p.resultados_prediccion.get('resumen', {})
            items.append(PrediccionHistorialItem(
                id_prediccion=p.id_prediccion,
                mes=p.mes,
                anio=p.anio,
                fecha_generacion=p.fecha_generacion,
                estado=EstadoPrediccion(p.estado),
                total_unidades=resumen.get('total_unidades', 0),
                total_reposiciones=resumen.get('total_reposiciones', 0),
                version_modelo=p.version_modelo
            ))
        
        return PrediccionHistorialResponse(total=total, predicciones=items)
    
    def obtener_prediccion(
        self,
        db: Session,
        id_prediccion: int,
        id_empresa: int
    ) -> Optional[PrediccionResponse]:
        """
        Obtiene una predicción específica.
        
        Args:
            db: Sesión de base de datos
            id_prediccion: ID de la predicción
            id_empresa: ID de la empresa (multi-tenant)
            
        Returns:
            PrediccionResponse o None si no existe
        """
        prediccion = prediccion_repository.get_by_id(db, id_prediccion, id_empresa)
        if not prediccion:
            return None
        return self._convertir_a_response(prediccion)
    
    def actualizar_estado_prediccion(
        self,
        db: Session,
        id_prediccion: int,
        id_empresa: int,
        estado: EstadoPrediccion,
        notas: Optional[str] = None
    ) -> Optional[PrediccionResponse]:
        """
        Actualiza el estado de una predicción.
        
        Args:
            db: Sesión de base de datos
            id_prediccion: ID de la predicción
            id_empresa: ID de la empresa (multi-tenant)
            estado: Nuevo estado
            notas: Notas adicionales
            
        Returns:
            PrediccionResponse actualizada o None
        """
        prediccion = prediccion_repository.actualizar_estado(
            db, id_prediccion, id_empresa, estado.value, notas
        )
        
        if not prediccion:
            return None
        return self._convertir_a_response(prediccion)


# Instancia singleton
prediction_service = PredictionService()
