
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, KFold
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix, mean_squared_error, r2_score
import matplotlib.pyplot as plt
from datetime import datetime
from calendar import monthrange
import joblib

# --- 1. Cargar y preparar datos en memoria ---
from preprocesamiento_datos import preprocesar_df
from analisis_exploratorio_eda import preparar_df_enriquecido
df_enriquecido = preparar_df_enriquecido(graficar=False)
df, le = preprocesar_df(df_enriquecido)
cat_col = 'categoria_producto'
cat_names = le.classes_
cat_ids = sorted(df[cat_col].unique())
cat_map = {num: nombre for num, nombre in zip(range(len(cat_names)), cat_names)}

# --- 2. Entrenamiento modelos en memoria ---
# Clasificación
X_cls = df.drop(['etiqueta_reposicion', 'cantidad_repuesta', 'timestamp_reposicion'], axis=1)
y_cls = df['etiqueta_reposicion']
X_train_cls, X_test_cls, y_train_cls, y_test_cls = train_test_split(X_cls, y_cls, test_size=0.2, random_state=42)
clf = RandomForestClassifier(random_state=42)
clf.fit(X_train_cls, y_train_cls)

# Regresión (solo donde hay reposición)
df_reg = df[df['etiqueta_reposicion'] == 1]
X_reg = df_reg.drop(['etiqueta_reposicion', 'cantidad_repuesta', 'timestamp_reposicion'], axis=1)
y_reg = df_reg['cantidad_repuesta']
# Aumento de datos: añadir ruido gaussiano
X_aug = pd.concat([X_reg, X_reg + np.random.normal(0, 0.05, X_reg.shape)])
y_aug = pd.concat([y_reg, y_reg])
# División en entrenamiento y prueba
from sklearn.model_selection import train_test_split
X_train_reg, X_test_reg, y_train_reg, y_test_reg = train_test_split(X_aug, y_aug, test_size=0.2, random_state=42)
reg = RandomForestRegressor(n_estimators=100, random_state=42)
reg.fit(X_train_reg, y_train_reg)
# --- 3. Simulación de predicción integrada para el próximo mes ---
hoy = datetime.now()
proximo_mes = hoy.month + 1 if hoy.month < 12 else 1
anio = hoy.year if hoy.month < 12 else hoy.year + 1
num_dias = monthrange(anio, proximo_mes)[1]
semanas = [(i*7+1, min((i+1)*7, num_dias)) for i in range((num_dias+6)//7)]
print('\n--- Predicción del modelo para el próximo mes (por semana) ---')
for i, (dia_ini, dia_fin) in enumerate(semanas, 1):
    sim_data = []
    for dia in range(dia_ini, dia_fin+1):
        for cat in cat_ids:
            sim_data.append({
                'categoria_producto': cat,
                'ubicacion_mueble': 0,
                'hora': 12,
                'mes': proximo_mes,
                'semana_mes': (dia - 1) // 7 + 1,
                'dia_semana': (datetime(anio, proximo_mes, dia)).weekday(),
                'dia_del_mes': dia
            })
    sim_df = pd.DataFrame(sim_data)
    num_cols = ['ubicacion_mueble', 'hora', 'mes', 'semana_mes', 'dia_del_mes']
    sim_df[num_cols] = (sim_df[num_cols] - X_cls[num_cols].mean()) / X_cls[num_cols].std()
    le_dia = LabelEncoder()
    sim_df['dia_semana'] = le_dia.fit_transform(sim_df['dia_semana'])
    sim_df = sim_df[X_cls.columns]
    sim_pred_cls = clf.predict(sim_df)
    sim_df['reposicion_predicha'] = sim_pred_cls
    sim_df_reg = sim_df[sim_df['reposicion_predicha'] == 1].copy()
    if not sim_df_reg.empty:
        cantidad_pred = reg.predict(sim_df_reg[X_reg.columns])
        cantidad_pred = [max(0, round(x)) for x in cantidad_pred]
        sim_df_reg['cantidad_predicha'] = cantidad_pred
    resumen = sim_df_reg.groupby('categoria_producto').agg(
        reposiciones=('cantidad_predicha', 'count'),
        total_unidades=('cantidad_predicha', 'sum')
    )
    print(f'\nSemana {i} ({dia_ini}-{dia_fin}):')
    # Mostrar las categorías en el orden original del LabelEncoder
    for cat_num, cat_name in cat_map.items():
        if cat_num in resumen.index:
            row = resumen.loc[cat_num]
            # Usar LabelEncoder para obtener el nombre textual
            nombre_textual = le.inverse_transform([cat_num])[0]
            print(f"  {nombre_textual}: {row['reposiciones']} reposiciones, {row['total_unidades']} unidades a reponer")
    print(f"  TOTAL SEMANAL: {resumen['total_unidades'].sum()} unidades a reponer")
import joblib
modelos = {'clasificador': clf, 'regresor': reg}
joblib.dump(modelos, 'modelos_rf.joblib')
print('\nModelos guardados en conjunto en modelos_rf.joblib para uso futuro.')
## --- 4. Guardar modelos y exportar predicciones eliminado ---
## El flujo permanece completamente en memoria. Si se requiere exportar, descomentar y adaptar según necesidad.
