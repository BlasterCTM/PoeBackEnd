"""
Script de entrenamiento del Pipeline completo para predicción de reposiciones.

Este script:
1. Carga y preprocesa los datos
2. Crea un Pipeline sklearn con ColumnTransformer
3. Entrena clasificador (reposición sí/no) y regresor (cantidad)
4. Persiste TODO (encoders, scalers, modelos) en un solo archivo .pkl

Ejecutar: python -m app.predict.train_pipeline
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import StandardScaler, LabelEncoder, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, mean_squared_error, r2_score
import joblib
from pathlib import Path
from datetime import datetime

# Rutas
BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "datos_simulados_ML_anual.csv"
PIPELINE_PATH = BASE_DIR / "pipeline_prediccion.pkl"


def preparar_datos_enriquecidos(csv_path: Path) -> pd.DataFrame:
    """
    Carga CSV y agrega features temporales.
    
    Args:
        csv_path: Ruta al CSV con datos
        
    Returns:
        DataFrame enriquecido con features temporales
    """
    print(f"\n📂 Cargando datos desde {csv_path}...")
    df = pd.read_csv(csv_path)
    
    # Convertir timestamp
    df['timestamp_reposicion'] = pd.to_datetime(df['timestamp_reposicion'])
    
    # Extraer features temporales
    df['hora'] = df['timestamp_reposicion'].dt.hour
    df['dia_semana'] = df['timestamp_reposicion'].dt.dayofweek  # 0=Monday, 6=Sunday
    df['mes'] = df['timestamp_reposicion'].dt.month
    df['dia_del_mes'] = df['timestamp_reposicion'].dt.day
    df['semana_mes'] = (df['dia_del_mes'] - 1) // 7 + 1
    
    print(f"✅ Datos cargados: {len(df)} filas, {len(df.columns)} columnas")
    print(f"   Categorías únicas: {df['categoria_producto'].nunique()}")
    print(f"   Rango temporal: {df['timestamp_reposicion'].min()} a {df['timestamp_reposicion'].max()}")
    
    return df


def crear_pipeline_clasificador() -> Pipeline:
    """
    Crea Pipeline para clasificación (reposición sí/no).
    
    Pipeline stages:
    1. ColumnTransformer: maneja categorías y variables numéricas
    2. RandomForestClassifier
    
    Returns:
        Pipeline configurado
    """
    # Definir columnas
    categorical_features = ['categoria_producto', 'dia_semana']
    numeric_features = ['ubicacion_mueble', 'hora', 'mes', 'semana_mes', 'dia_del_mes']
    
    # ColumnTransformer
    preprocessor = ColumnTransformer(
        transformers=[
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_features),
            ('num', StandardScaler(), numeric_features)
        ],
        remainder='drop'
    )
    
    # Pipeline completo
    pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('classifier', RandomForestClassifier(
            n_estimators=150,
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        ))
    ])
    
    return pipeline


def crear_pipeline_regresor() -> Pipeline:
    """
    Crea Pipeline para regresión (cantidad a reponer).
    
    Returns:
        Pipeline configurado
    """
    # Definir columnas
    categorical_features = ['categoria_producto', 'dia_semana']
    numeric_features = ['ubicacion_mueble', 'hora', 'mes', 'semana_mes', 'dia_del_mes']
    
    # ColumnTransformer
    preprocessor = ColumnTransformer(
        transformers=[
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_features),
            ('num', StandardScaler(), numeric_features)
        ],
        remainder='drop'
    )
    
    # Pipeline completo
    pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('regressor', RandomForestRegressor(
            n_estimators=150,
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        ))
    ])
    
    return pipeline


def entrenar_modelos(df: pd.DataFrame):
    """
    Entrena clasificador y regresor, los guarda en un archivo .pkl
    
    Args:
        df: DataFrame con datos de entrenamiento
    """
    print("\n🔧 ENTRENAMIENTO DE MODELOS")
    print("=" * 60)
    
    # Features y target
    feature_cols = ['categoria_producto', 'ubicacion_mueble', 'hora', 'dia_semana', 
                    'mes', 'semana_mes', 'dia_del_mes']
    
    # ========================================
    # 1. CLASIFICADOR (reposición sí/no)
    # ========================================
    print("\n1️⃣  Entrenando CLASIFICADOR (reposición sí/no)...")
    
    X_cls = df[feature_cols].copy()
    y_cls = df['etiqueta_reposicion']
    
    X_train_cls, X_test_cls, y_train_cls, y_test_cls = train_test_split(
        X_cls, y_cls, test_size=0.2, random_state=42, stratify=y_cls
    )
    
    pipeline_cls = crear_pipeline_clasificador()
    pipeline_cls.fit(X_train_cls, y_train_cls)
    
    # Evaluación
    y_pred_cls = pipeline_cls.predict(X_test_cls)
    print("\n📊 Reporte de clasificación:")
    print(classification_report(y_test_cls, y_pred_cls, target_names=['No reponer', 'Reponer']))
    
    accuracy = (y_pred_cls == y_test_cls).mean()
    print(f"✅ Accuracy: {accuracy:.4f}")
    
    # ========================================
    # 2. REGRESOR (cantidad a reponer)
    # ========================================
    print("\n2️⃣  Entrenando REGRESOR (cantidad a reponer)...")
    
    # Solo entrenar con casos donde hubo reposición
    df_reg = df[df['etiqueta_reposicion'] == 1].copy()
    print(f"   Datos para regresión: {len(df_reg)} filas (solo reposiciones positivas)")
    
    X_reg = df_reg[feature_cols].copy()
    y_reg = df_reg['cantidad_repuesta']
    
    # Data augmentation con ruido gaussiano
    print("   Aplicando data augmentation (ruido gaussiano)...")
    X_aug = pd.concat([X_reg, X_reg.copy()], ignore_index=True)
    y_aug = pd.concat([y_reg, y_reg.copy()], ignore_index=True)
    
    # Agregar ruido solo a columnas numéricas de la segunda mitad
    numeric_cols = ['ubicacion_mueble', 'hora', 'dia_semana', 'mes', 'semana_mes', 'dia_del_mes']
    noise_df = pd.DataFrame(
        np.random.normal(0, 0.05, (len(X_reg), len(numeric_cols))),
        columns=numeric_cols
    )
    
    # Aplicar ruido solo a segunda mitad y solo columnas numéricas
    for col in numeric_cols:
        X_aug.loc[len(X_reg):, col] = X_aug.loc[len(X_reg):, col].astype(float) + noise_df[col].values
    
    X_train_reg, X_test_reg, y_train_reg, y_test_reg = train_test_split(
        X_aug, y_aug, test_size=0.2, random_state=42
    )
    
    pipeline_reg = crear_pipeline_regresor()
    pipeline_reg.fit(X_train_reg, y_train_reg)
    
    # Evaluación
    y_pred_reg = pipeline_reg.predict(X_test_reg)
    mse = mean_squared_error(y_test_reg, y_pred_reg)
    r2 = r2_score(y_test_reg, y_pred_reg)
    
    print(f"\n📊 Métricas de regresión:")
    print(f"   MSE:  {mse:.2f}")
    print(f"   RMSE: {np.sqrt(mse):.2f}")
    print(f"   R²:   {r2:.4f}")
    
    # ========================================
    # 3. GUARDAR PIPELINES
    # ========================================
    print("\n💾 Guardando pipelines...")
    
    # Guardar metadatos útiles
    metadatos = {
        'fecha_entrenamiento': datetime.now().isoformat(),
        'n_filas_entrenamiento': len(df),
        'n_filas_clasificador': len(X_train_cls),
        'n_filas_regresor': len(X_train_reg),
        'accuracy_clasificador': float(accuracy),
        'r2_regresor': float(r2),
        'categorias_producto': sorted(df['categoria_producto'].unique()),
        'feature_cols': feature_cols,
        'version': '1.0.0'
    }
    
    # Empaquetar todo
    package = {
        'pipeline_clasificador': pipeline_cls,
        'pipeline_regresor': pipeline_reg,
        'metadatos': metadatos
    }
    
    joblib.dump(package, PIPELINE_PATH)
    print(f"✅ Pipelines guardados en: {PIPELINE_PATH}")
    print(f"   Tamaño del archivo: {PIPELINE_PATH.stat().st_size / 1024 / 1024:.2f} MB")
    
    # ========================================
    # 4. VERIFICACIÓN
    # ========================================
    print("\n🔍 Verificando carga del pipeline...")
    package_loaded = joblib.load(PIPELINE_PATH)
    
    # Test rápido
    sample = X_test_cls.iloc[:5].copy()
    pred_cls = package_loaded['pipeline_clasificador'].predict(sample)
    print(f"✅ Pipeline cargado correctamente. Test predicción: {pred_cls}")
    
    print("\n" + "=" * 60)
    print("🎉 ENTRENAMIENTO COMPLETADO EXITOSAMENTE")
    print("=" * 60)
    print(f"\n📦 Archivo generado: {PIPELINE_PATH.name}")
    print(f"📊 Accuracy Clasificador: {accuracy:.4f}")
    print(f"📊 R² Regresor: {r2:.4f}")
    print(f"🗂️  Categorías soportadas: {len(metadatos['categorias_producto'])}")
    print(f"✨ Versión: {metadatos['version']}")
    print("\nAhora puedes usar este pipeline en FastAPI con PredictionService.")


if __name__ == "__main__":
    # Ejecutar pipeline de entrenamiento
    df = preparar_datos_enriquecidos(CSV_PATH)
    entrenar_modelos(df)
