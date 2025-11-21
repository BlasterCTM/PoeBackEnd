# 🧪 GUÍA DE PRUEBAS POSTMAN - PREDICCIONES ML

## 📋 Orden de Ejecución

Sigue este orden para probar correctamente:

---

## ✅ PASO 1: LOGIN (OBLIGATORIO PRIMERO)

### **Request:**
```
POST http://localhost:8000/usuarios/login
```

### **Headers:**
```
Content-Type: application/json
```

### **Body (raw JSON):**
```json
{
  "correo": "supervisor@empresa.com",
  "password": "tu_password_aqui"
}
```

### **Response Esperada (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzdXBlcnZpc29yQGVtcHJlc2EuY29tIiwiaWRfdXN1YXJpbyI6NSwiaWRfZW1wcmVzYSI6MSwicm9sIjoiU3VwZXJ2aXNvciIsImV4cCI6MTczMjM1MDAwMH0.abc123...",
  "refresh_token": "def456...",
  "token_type": "bearer",
  "usuario": {
    "id_usuario": 5,
    "nombre": "María Supervisor",
    "correo": "supervisor@empresa.com",
    "id_empresa": 1,
    "rol": {
      "id_rol": 3,
      "nombre": "Supervisor"
    }
  }
}
```

📝 **IMPORTANTE:** Copia el `access_token` para usarlo en las siguientes peticiones.

---

## ✅ PASO 2: GENERAR PREDICCIÓN (DICIEMBRE 2025)

### **Request:**
```
POST http://localhost:8000/api/v1/predicciones/generar
```

### **Headers:**
```
Content-Type: application/json
Authorization: Bearer TU_ACCESS_TOKEN_AQUI
```

### **Body (raw JSON):**
```json
{
  "mes": 12,
  "anio": 2025,
  "incluir_semanas": true,
  "notas": "Predicción para temporada navideña - prueba inicial"
}
```

### **Response Esperada (201 Created):**
```json
{
  "id_prediccion": 1,
  "id_empresa": 1,
  "mes": 12,
  "anio": 2025,
  "version_modelo": "1.0.0",
  "fecha_generacion": "2025-11-21T16:30:00.123456",
  "estado": "pendiente",
  "resumen": {
    "total_reposiciones": 1200,
    "total_unidades": 15000,
    "categorias_activas": [
      "Bebidas_Gaseosas",
      "Condimentos",
      "Congelados",
      "Enlatados",
      "Frutas_Verduras",
      "Lacteos",
      "Limpieza",
      "Panaderia"
    ],
    "promedio_diario": 484.0
  },
  "por_categoria": [
    {
      "categoria": "Bebidas_Gaseosas",
      "ubicacion_mueble": 112,
      "reposiciones": 150,
      "total_unidades": 1950,
      "dias_predichos": [1, 2, 3, 5, 6, 7, 8, 9, 10, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]
    },
    {
      "categoria": "Condimentos",
      "ubicacion_mueble": 110,
      "reposiciones": 140,
      "total_unidades": 1800,
      "dias_predichos": [1, 3, 4, 6, 7, 9, 10, 11, 12, 13, 14, 15, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]
    },
    {
      "categoria": "Congelados",
      "ubicacion_mueble": 115,
      "reposiciones": 145,
      "total_unidades": 1870,
      "dias_predichos": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]
    },
    {
      "categoria": "Enlatados",
      "ubicacion_mueble": 117,
      "reposiciones": 155,
      "total_unidades": 2000,
      "dias_predichos": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]
    },
    {
      "categoria": "Frutas_Verduras",
      "ubicacion_mueble": 108,
      "reposiciones": 160,
      "total_unidades": 2100,
      "dias_predichos": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]
    },
    {
      "categoria": "Lacteos",
      "ubicacion_mueble": 118,
      "reposiciones": 165,
      "total_unidades": 2150,
      "dias_predichos": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]
    },
    {
      "categoria": "Limpieza",
      "ubicacion_mueble": 111,
      "reposiciones": 142,
      "total_unidades": 1830,
      "dias_predichos": [1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]
    },
    {
      "categoria": "Panaderia",
      "ubicacion_mueble": 114,
      "reposiciones": 143,
      "total_unidades": 1840,
      "dias_predichos": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]
    }
  ],
  "por_semana": [
    {
      "semana": 1,
      "fecha_inicio": "12-01",
      "fecha_fin": "12-07",
      "total_unidades": 3500,
      "categorias": {
        "Bebidas_Gaseosas": 450,
        "Condimentos": 420,
        "Congelados": 430,
        "Enlatados": 460,
        "Frutas_Verduras": 480,
        "Lacteos": 490,
        "Limpieza": 410,
        "Panaderia": 420
      }
    },
    {
      "semana": 2,
      "fecha_inicio": "12-08",
      "fecha_fin": "12-14",
      "total_unidades": 3800,
      "categorias": {
        "Bebidas_Gaseosas": 480,
        "Condimentos": 450,
        "Congelados": 460,
        "Enlatados": 490,
        "Frutas_Verduras": 510,
        "Lacteos": 520,
        "Limpieza": 440,
        "Panaderia": 450
      }
    },
    {
      "semana": 3,
      "fecha_inicio": "12-15",
      "fecha_fin": "12-21",
      "total_unidades": 3900,
      "categorias": {
        "Bebidas_Gaseosas": 495,
        "Condimentos": 465,
        "Congelados": 475,
        "Enlatados": 505,
        "Frutas_Verduras": 525,
        "Lacteo": 535,
        "Limpieza": 455,
        "Panaderia": 465
      }
    },
    {
      "semana": 4,
      "fecha_inicio": "12-22",
      "fecha_fin": "12-28",
      "total_unidades": 4200,
      "categorias": {
        "Bebidas_Gaseosas": 530,
        "Condimentos": 500,
        "Congelados": 510,
        "Enlatados": 540,
        "Frutas_Verduras": 560,
        "Lacteos": 570,
        "Limpieza": 490,
        "Panaderia": 500
      }
    },
    {
      "semana": 5,
      "fecha_inicio": "12-29",
      "fecha_fin": "12-31",
      "total_unidades": 1800,
      "categorias": {
        "Bebidas_Gaseosas": 230,
        "Condimentos": 215,
        "Congelados": 220,
        "Enlatados": 235,
        "Frutas_Verduras": 245,
        "Lacteos": 250,
        "Limpieza": 210,
        "Panaderia": 215
      }
    }
  ],
  "features_utilizados": {
    "features": [
      "categoria_producto",
      "ubicacion_mueble",
      "hora",
      "dia_semana",
      "mes",
      "semana_mes",
      "dia_del_mes"
    ],
    "accuracy_clasificador": 0.6975,
    "r2_regresor": 0.7137,
    "n_filas_entrenamiento": 8000
  },
  "notas": "Predicción para temporada navideña - prueba inicial"
}
```

📝 **IMPORTANTE:** Guarda el `id_prediccion` (ejemplo: 1) para usarlo en los siguientes pasos.

---

## ✅ PASO 3: VER HISTORIAL

### **Request:**
```
GET http://localhost:8000/api/v1/predicciones/historial?skip=0&limit=10
```

### **Headers:**
```
Authorization: Bearer TU_ACCESS_TOKEN_AQUI
```

### **Response Esperada (200 OK):**
```json
{
  "total": 1,
  "predicciones": [
    {
      "id_prediccion": 1,
      "mes": 12,
      "anio": 2025,
      "fecha_generacion": "2025-11-21T16:30:00.123456",
      "estado": "pendiente",
      "total_unidades": 15000,
      "total_reposiciones": 1200,
      "version_modelo": "1.0.0"
    }
  ]
}
```

---

## ✅ PASO 4: VER DETALLE DE PREDICCIÓN

### **Request:**
```
GET http://localhost:8000/api/v1/predicciones/1
```
(Reemplaza `1` con el `id_prediccion` que obtuviste)

### **Headers:**
```
Authorization: Bearer TU_ACCESS_TOKEN_AQUI
```

### **Response Esperada (200 OK):**
Mismo JSON completo que en PASO 2 (generar predicción).

---

## ✅ PASO 5: ACTUALIZAR ESTADO A "APLICADO"

### **Request:**
```
PATCH http://localhost:8000/api/v1/predicciones/1/estado
```

### **Headers:**
```
Content-Type: application/json
Authorization: Bearer TU_ACCESS_TOKEN_AQUI
```

### **Body (raw JSON):**
```json
{
  "estado": "aplicado",
  "notas": "Predicción aplicada en sistema automático el 21/11/2025 a las 16:45"
}
```

### **Response Esperada (200 OK):**
```json
{
  "id_prediccion": 1,
  "id_empresa": 1,
  "mes": 12,
  "anio": 2025,
  "version_modelo": "1.0.0",
  "fecha_generacion": "2025-11-21T16:30:00.123456",
  "estado": "aplicado",
  "resumen": { ... },
  "por_categoria": [ ... ],
  "por_semana": [ ... ],
  "features_utilizados": { ... },
  "notas": "Predicción aplicada en sistema automático el 21/11/2025 a las 16:45"
}
```

---

## ✅ PASO 6: GENERAR OTRA PREDICCIÓN (ENERO 2026)

### **Request:**
```
POST http://localhost:8000/api/v1/predicciones/generar
```

### **Headers:**
```
Content-Type: application/json
Authorization: Bearer TU_ACCESS_TOKEN_AQUI
```

### **Body (raw JSON):**
```json
{
  "mes": 1,
  "anio": 2026,
  "incluir_semanas": true,
  "notas": "Predicción post-navidad - inicio de año"
}
```

### **Response Esperada (201 Created):**
Similar al PASO 2, pero con `id_prediccion: 2` y datos de Enero 2026.

---

## ✅ PASO 7: GENERAR PREDICCIÓN SIN SEMANAS

### **Request:**
```
POST http://localhost:8000/api/v1/predicciones/generar
```

### **Headers:**
```
Content-Type: application/json
Authorization: Bearer TU_ACCESS_TOKEN_AQUI
```

### **Body (raw JSON):**
```json
{
  "mes": 2,
  "anio": 2026,
  "incluir_semanas": false,
  "notas": "Predicción febrero sin desglose semanal"
}
```

### **Response Esperada (201 Created):**
```json
{
  "id_prediccion": 3,
  "mes": 2,
  "anio": 2026,
  "resumen": { ... },
  "por_categoria": [ ... ],
  "por_semana": null,
  ...
}
```

📝 **Nota:** `por_semana` será `null` porque `incluir_semanas: false`.

---

## ⚠️ TESTS DE VALIDACIÓN (ERRORES ESPERADOS)

### **TEST 1: Sin Token (401 Unauthorized)**

**Request:**
```
GET http://localhost:8000/api/v1/predicciones/historial
```

**Headers:**
```
(NINGUNO - Sin Authorization)
```

**Response Esperada (401 Unauthorized):**
```json
{
  "detail": "Not authenticated"
}
```

---

### **TEST 2: Mes Inválido (422 Validation Error)**

**Request:**
```
POST http://localhost:8000/api/v1/predicciones/generar
```

**Headers:**
```
Content-Type: application/json
Authorization: Bearer TU_ACCESS_TOKEN_AQUI
```

**Body (raw JSON):**
```json
{
  "mes": 13,
  "anio": 2025,
  "incluir_semanas": true
}
```

**Response Esperada (422 Unprocessable Entity):**
```json
{
  "detail": [
    {
      "type": "less_than_equal",
      "loc": ["body", "mes"],
      "msg": "Input should be less than or equal to 12",
      "input": 13,
      "ctx": {
        "le": 12
      }
    }
  ]
}
```

---

### **TEST 3: Predicción No Existe (404 Not Found)**

**Request:**
```
GET http://localhost:8000/api/v1/predicciones/99999
```

**Headers:**
```
Authorization: Bearer TU_ACCESS_TOKEN_AQUI
```

**Response Esperada (404 Not Found):**
```json
{
  "detail": "Predicción 99999 no encontrada"
}
```

---

### **TEST 4: Estado Inválido (422 Validation Error)**

**Request:**
```
PATCH http://localhost:8000/api/v1/predicciones/1/estado
```

**Headers:**
```
Content-Type: application/json
Authorization: Bearer TU_ACCESS_TOKEN_AQUI
```

**Body (raw JSON):**
```json
{
  "estado": "estado_invalido",
  "notas": "Test de validación"
}
```

**Response Esperada (422 Unprocessable Entity):**
```json
{
  "detail": [
    {
      "type": "enum",
      "loc": ["body", "estado"],
      "msg": "Input should be 'pendiente', 'aplicado' or 'rechazado'",
      "input": "estado_invalido",
      "ctx": {
        "expected": "'pendiente', 'aplicado' or 'rechazado'"
      }
    }
  ]
}
```

---

### **TEST 5: Usuario Reponedor No Puede Generar (403 Forbidden)**

**Login como Reponedor:**
```
POST http://localhost:8000/usuarios/login
```

**Body:**
```json
{
  "correo": "reponedor@empresa.com",
  "password": "tu_password"
}
```

**Intentar Generar Predicción:**
```
POST http://localhost:8000/api/v1/predicciones/generar
Authorization: Bearer TOKEN_DE_REPONEDOR
```

**Response Esperada (403 Forbidden):**
```json
{
  "detail": "Solo supervisores y administradores pueden generar predicciones"
}
```

---

## 📊 CHECKLIST DE PRUEBAS

- [ ] ✅ Login exitoso (200 OK)
- [ ] ✅ Generar predicción Diciembre 2025 (201 Created)
- [ ] ✅ Ver historial (200 OK, muestra 1 predicción)
- [ ] ✅ Ver detalle por ID (200 OK)
- [ ] ✅ Actualizar estado a "aplicado" (200 OK)
- [ ] ✅ Generar predicción Enero 2026 (201 Created)
- [ ] ✅ Generar predicción sin semanas (201 Created, por_semana = null)
- [ ] ✅ Ver historial (200 OK, muestra 3 predicciones)
- [ ] ❌ Request sin token (401 Unauthorized)
- [ ] ❌ Mes inválido (422 Validation Error)
- [ ] ❌ Predicción no existe (404 Not Found)
- [ ] ❌ Estado inválido (422 Validation Error)
- [ ] ❌ Reponedor no puede generar (403 Forbidden)

---

## 🔧 TIPS

1. **Reemplaza valores:**
   - `TU_ACCESS_TOKEN_AQUI` → Token del login
   - `supervisor@empresa.com` / `tu_password_aqui` → Tus credenciales reales

2. **URLs base:**
   - Local: `http://localhost:8000`
   - Producción: `https://tu-dominio.com`

3. **Importar a Postman:**
   Usa la colección JSON que te generé anteriormente: `postman/Predicciones_ML.postman_collection.json`

---

¡Listo para copiar y pegar en Postman! 🚀
