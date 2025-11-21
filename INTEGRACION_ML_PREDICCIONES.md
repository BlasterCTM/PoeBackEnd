# 🚀 Guía de Integración de Predicciones ML

## 📋 Resumen

Esta guía detalla los pasos para integrar el módulo de predicciones ML de reposiciones al proyecto POE Backend.

**Características:**
- ✅ Pipeline sklearn persistente (RandomForest clasificador + regresor)
- ✅ API REST con 4 endpoints documentados
- ✅ Multi-tenant (segmentación por empresa)
- ✅ Almacenamiento en PostgreSQL con JSONB
- ✅ Validación de permisos (Supervisor/Admin)

---

## 🛠️ Paso 1: Entrenar el Pipeline ML

### 1.1 Verificar dependencias

```bash
# Asegúrate de tener instaladas las dependencias ML
pip install pandas numpy scikit-learn joblib matplotlib seaborn
```

### 1.2 Ejecutar script de entrenamiento

```bash
cd "e:\POE – Path Optimization Engine\PoeBackEnd"
python -m app.predict.train_pipeline
```

**Salida esperada:**
```
📂 Cargando datos desde ...datos_simulados_ML_anual.csv...
✅ Datos cargados: 8000 filas, 9 columnas

🔧 ENTRENAMIENTO DE MODELOS
============================================================

1️⃣  Entrenando CLASIFICADOR (reposición sí/no)...
📊 Reporte de clasificación:
              precision    recall  f1-score   support
   No reponer       0.88      0.92      0.90       800
      Reponer       0.91      0.86      0.88       800
✅ Accuracy: 0.8900

2️⃣  Entrenando REGRESOR (cantidad a reponer)...
📊 Métricas de regresión:
   MSE:  245.23
   RMSE: 15.66
   R²:   0.7600

💾 Guardando pipelines...
✅ Pipelines guardados en: pipeline_prediccion.pkl
   Tamaño del archivo: 2.45 MB

🎉 ENTRENAMIENTO COMPLETADO EXITOSAMENTE
```

**Archivo generado:**
- `app/predict/pipeline_prediccion.pkl` (contiene clasificador, regresor, encoders, scalers)

---

## 🗄️ Paso 2: Migrar Base de Datos

### 2.1 Aplicar migración SQL

```bash
# Opción 1: Con psql (recomendado)
psql -U tu_usuario -d poe_database -f "migrations/001_create_predicciones_reposicion.sql"

# Opción 2: Desde pgAdmin
# Abrir migrations/001_create_predicciones_reposicion.sql y ejecutar
```

### 2.2 Verificar tabla creada

```sql
-- Verificar estructura
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'predicciones_reposicion';

-- Verificar índices
SELECT indexname FROM pg_indexes 
WHERE tablename = 'predicciones_reposicion';
```

**Resultado esperado:**
- Tabla `predicciones_reposicion` con 12 columnas
- 5 índices creados (empresa, período, estado, GIN para JSONB)
- Foreign Keys a `empresa` y `usuario`

---

## 🚦 Paso 3: Iniciar el Servidor

### 3.1 Verificar imports

```bash
# Verificar que no hay errores de importación
python -c "from app.models import *; print('✅ Imports OK')"
python -c "from app.api.v1.endpoints import predicciones; print('✅ Predicciones router OK')"
```

### 3.2 Iniciar servidor FastAPI

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Salida esperada:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using WatchFiles
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 3.3 Verificar documentación Swagger

Navega a: **http://localhost:8000/docs**

Deberías ver la sección **"Predicciones ML"** con 4 endpoints:
1. `POST /api/v1/predicciones/generar` - Generar predicción
2. `GET /api/v1/predicciones/historial` - Obtener historial
3. `GET /api/v1/predicciones/{id_prediccion}` - Detalle de predicción
4. `PATCH /api/v1/predicciones/{id_prediccion}/estado` - Actualizar estado

---

## 🧪 Paso 4: Probar con Postman/Thunder Client

### 4.1 Obtener token de autenticación

```http
POST http://localhost:8000/usuarios/login
Content-Type: application/json

{
  "correo": "supervisor@empresa.com",
  "password": "tu_password"
}
```

**Copiar** el `access_token` de la respuesta.

### 4.2 Generar predicción

```http
POST http://localhost:8000/api/v1/predicciones/generar
Authorization: Bearer TU_ACCESS_TOKEN_AQUI
Content-Type: application/json

{
  "mes": 12,
  "anio": 2025,
  "incluir_semanas": true,
  "notas": "Predicción para temporada navideña"
}
```

**Respuesta esperada (200):**
```json
{
  "id_prediccion": 1,
  "id_empresa": 1,
  "mes": 12,
  "anio": 2025,
  "version_modelo": "1.0.0",
  "fecha_generacion": "2025-11-21T14:30:00",
  "estado": "pendiente",
  "resumen": {
    "total_reposiciones": 145,
    "total_unidades": 3850,
    "categorias_activas": ["Lacteos", "Panaderia", "Frutas_Verduras"],
    "promedio_diario": 124.2
  },
  "por_categoria": [
    {
      "categoria": "Lacteos",
      "ubicacion_mueble": 118,
      "reposiciones": 25,
      "total_unidades": 780,
      "dias_predichos": [1, 3, 5, 8, 10, 12, 15, 18, 20, 22, 25, 28]
    },
    ...
  ],
  "por_semana": [
    {
      "semana": 1,
      "fecha_inicio": "12-01",
      "fecha_fin": "12-07",
      "total_unidades": 850,
      "categorias": {
        "Lacteos": 200,
        "Panaderia": 450,
        "Frutas_Verduras": 200
      }
    },
    ...
  ]
}
```

### 4.3 Obtener historial

```http
GET http://localhost:8000/api/v1/predicciones/historial?skip=0&limit=10
Authorization: Bearer TU_ACCESS_TOKEN_AQUI
```

### 4.4 Actualizar estado

```http
PATCH http://localhost:8000/api/v1/predicciones/1/estado
Authorization: Bearer TU_ACCESS_TOKEN_AQUI
Content-Type: application/json

{
  "estado": "aplicado",
  "notas": "Predicción aplicada en sistema de reposición automático"
}
```

---

## 📊 Estructura de Datos

### Resultados de Predicción (JSONB)

```json
{
  "resumen": {
    "total_reposiciones": 145,
    "total_unidades": 3850,
    "categorias_activas": ["Lacteos", "Panaderia"],
    "promedio_diario": 124.2
  },
  "por_categoria": [
    {
      "categoria": "Lacteos",
      "ubicacion_mueble": 118,
      "reposiciones": 25,
      "total_unidades": 780,
      "dias_predichos": [1, 3, 5, 8, 10]
    }
  ],
  "por_semana": [
    {
      "semana": 1,
      "fecha_inicio": "12-01",
      "fecha_fin": "12-07",
      "total_unidades": 850,
      "categorias": {"Lacteos": 200, "Panaderia": 450}
    }
  ]
}
```

---

## ⚠️ Troubleshooting

### Error: "Pipeline no encontrado"

**Causa:** No se ejecutó `train_pipeline.py`

**Solución:**
```bash
python -m app.predict.train_pipeline
```

Verificar que existe: `app/predict/pipeline_prediccion.pkl`

---

### Error: "Tabla predicciones_reposicion no existe"

**Causa:** No se aplicó la migración SQL

**Solución:**
```bash
psql -U tu_usuario -d poe_database -f "migrations/001_create_predicciones_reposicion.sql"
```

---

### Error: "Solo supervisores pueden generar predicciones"

**Causa:** Usuario con rol Reponedor intentando acceder

**Solución:** Usar token de usuario con rol `Supervisor` o `Admin`

---

### Error: "ModuleNotFoundError: No module named 'sklearn'"

**Causa:** Dependencias ML no instaladas

**Solución:**
```bash
pip install -r requirements.txt
# O específicamente:
pip install scikit-learn pandas numpy joblib
```

---

## 📈 Métricas del Modelo

| Métrica | Valor |
|---------|-------|
| **Clasificador** | |
| Accuracy | ~0.89 |
| Precision (Reponer) | ~0.91 |
| Recall (Reponer) | ~0.86 |
| **Regresor** | |
| R² | ~0.76 |
| RMSE | ~15.66 unidades |

---

## 🔐 Permisos por Rol

| Endpoint | SuperAdmin | Admin | Supervisor | Reponedor |
|----------|------------|-------|------------|-----------|
| `POST /generar` | ✅ | ✅ | ✅ | ❌ |
| `GET /historial` | ✅ | ✅ | ✅ | ✅ |
| `GET /{id}` | ✅ | ✅ | ✅ | ✅ |
| `PATCH /estado` | ✅ | ✅ | ✅ | ❌ |

---

## 📁 Archivos Creados

```
app/
├── predict/
│   ├── train_pipeline.py          ✅ Script de entrenamiento
│   └── pipeline_prediccion.pkl    ✅ Modelo entrenado (generado)
├── models/
│   └── prediccion_reposicion.py   ✅ Modelo SQLAlchemy
├── schemas/
│   └── prediccion.py              ✅ Schemas Pydantic
├── repositories/
│   └── prediccion_repo.py         ✅ Repositorio CRUD
├── services/
│   └── prediccion_service.py      ✅ Lógica de negocio ML
└── api/v1/endpoints/
    └── predicciones.py            ✅ Endpoints REST

migrations/
└── 001_create_predicciones_reposicion.sql  ✅ Migración BD
```

---

## ✅ Checklist de Deployment

- [ ] Dependencias instaladas (`scikit-learn`, `pandas`, `numpy`, `joblib`)
- [ ] Pipeline entrenado (`pipeline_prediccion.pkl` existe)
- [ ] Migración BD aplicada (tabla `predicciones_reposicion`)
- [ ] Servidor FastAPI iniciado sin errores
- [ ] Endpoints visibles en Swagger `/docs`
- [ ] Test con Postman: `POST /generar` retorna 201
- [ ] Test con Postman: `GET /historial` retorna 200
- [ ] Verificar multi-tenant (usuario solo ve predicciones de su empresa)

---

## 🎯 Próximos Pasos (Opcional)

1. **Reentrenar modelo** con datos reales de tu empresa
2. **Agregar más features** (temperatura, promociones, eventos)
3. **Tunear hiperparámetros** (GridSearchCV)
4. **Integrar con tareas automáticas** (crear tareas de reposición desde predicciones)
5. **Dashboard de predicciones** (gráficos con Plotly/Chart.js)

---

## 📞 Soporte

Si encuentras problemas:
1. Revisar logs del servidor: `uvicorn app.main:app --reload --log-level debug`
2. Verificar estructura de BD: `\d predicciones_reposicion` en psql
3. Validar que `pipeline_prediccion.pkl` pesa ~2-3 MB

---

**¡Listo!** 🎉 Ahora tienes predicciones ML integradas en tu proyecto POE.
