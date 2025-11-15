# ============================================
# FLUJO DE DATOS: PROCESO DE SUSCRIPCIÓN B2B
# ============================================

## 📋 DESCRIPCIÓN GENERAL
Sistema de suscripción mensual para empresas (supermercados) que contratan el servicio POE.
Cada empresa tiene un plan personalizado con límites de uso y facturación automática mensual.

## 🔄 FLUJO COMPLETO DEL PROCESO

### ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
### FASE 1: PROSPECCIÓN Y COTIZACIÓN
### ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌─────────────────────────────────────────────────────────────┐
│ 1. CLIENTE POTENCIAL SOLICITA COTIZACIÓN                    │
│    (Formulario web "Cotiza Acá")                            │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ POST /cotizaciones                                          │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│ Payload:                                                     │
│ {                                                           │
│   "nombre_contacto": "Juan Pérez",                         │
│   "empresa": "Supermercado Central",                       │
│   "email": "juan@supercentral.cl",                         │
│   "telefono": "+56912345678",                              │
│   "cargo": "Gerente de Operaciones",                       │
│   "cantidad_locales": 5,                                   │
│   "ciudades": "Santiago, Valparaíso, Concepción",          │
│   "cantidad_supervisores": 10,                             │
│   "cantidad_reponedores": 50,                              │
│   "cantidad_productos": 5000,                              │
│   "integraciones_requeridas": "ERP SAP, sistema de stock", │
│   "comentarios": "Necesitamos implementar en 3 meses"      │
│ }                                                           │
│                                                             │
│ Estado inicial: "pendiente"                                │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. EQUIPO POE REVISA COTIZACIÓN                            │
│    (SuperAdmin/Comercial)                                   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ GET /cotizaciones?estado=pendiente                          │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│ Listar todas las cotizaciones pendientes                   │
│                                                             │
│ GET /cotizaciones/{id_cotizacion}                          │
│ Ver detalle de una cotización específica                   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. CALCULAR PRECIO Y ELABORAR PROPUESTA                    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ PUT /cotizaciones/{id_cotizacion}                          │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│ {                                                           │
│   "precio_sugerido": 1500000,  // CLP mensual             │
│   "features_sugeridos": {                                  │
│     "dashboard": true,                                     │
│     "optimizacion_rutas": true,                            │
│     "reportes_pdf": true,                                  │
│     "app_movil": true,                                     │
│     "multilocal": true                                     │
│   },                                                        │
│   "notas_internas": "Cliente premium, priorizar"           │
│ }                                                           │
│                                                             │
│ PATCH /cotizaciones/{id}/estado                            │
│ { "nuevo_estado": "en_revision" }                          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. NEGOCIACIÓN CON CLIENTE                                 │
│    (Pueden haber múltiples iteraciones)                     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ PUT /cotizaciones/{id_cotizacion}                          │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│ {                                                           │
│   "precio_final": 1350000,  // Después de negociación     │
│   "fecha_validez": "2025-12-31"                            │
│ }                                                           │
│                                                             │
│ Estado: "en_revision" → "cotizada" → "negociacion"        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. CLIENTE ACEPTA O RECHAZA                                │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ PATCH /cotizaciones/{id}/estado                            │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│ { "nuevo_estado": "aprobada" }  ✅                         │
│     o                                                       │
│ { "nuevo_estado": "rechazada" } ❌                         │
└─────────────────────────────────────────────────────────────┘


### ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
### FASE 2: CONVERSIÓN A CLIENTE (ONBOARDING)
### ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌─────────────────────────────────────────────────────────────┐
│ 6. CONVERTIR COTIZACIÓN APROBADA EN EMPRESA + PLAN         │
│    (Solo si estado = "aprobada")                            │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ POST /cotizaciones/{id}/convertir                          │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│ ACCIÓN AUTOMÁTICA:                                          │
│                                                             │
│ 1. Crear Empresa:                                          │
│    - nombre_empresa: "Supermercado Central"                │
│    - rut_empresa: "76.123.456-7"                           │
│    - direccion, ciudad, region, telefono, email            │
│    - estado: "activo"                                      │
│                                                             │
│ 2. Crear PlanEmpresa:                                      │
│    - id_empresa: (nuevo ID generado)                       │
│    - cantidad_locales: 5                                   │
│    - cantidad_supervisores: 10                             │
│    - cantidad_reponedores: 50                              │
│    - cantidad_productos: 5000                              │
│    - precio_mensual: 1350000                               │
│    - features: {...}                                       │
│    - fecha_inicio: HOY                                     │
│    - fecha_vencimiento: NULL (sin límite)                  │
│    - activo: true                                          │
│                                                             │
│ 3. Crear Usuario Admin inicial:                           │
│    - nombre: "Juan Pérez"                                  │
│    - correo: "juan@supercentral.cl"                        │
│    - rol: "ADMIN"                                          │
│    - contraseña temporal (enviar por email)                │
│                                                             │
│ 4. Actualizar Cotización:                                  │
│    - estado: "convertida"                                  │
│    - id_empresa_creada: (ID nueva empresa)                 │
│    - id_plan_creado: (ID nuevo plan)                       │
│    - fecha_conversion: AHORA                               │
│                                                             │
│ Response:                                                   │
│ {                                                           │
│   "empresa": {...},                                        │
│   "plan": {...},                                           │
│   "usuario_admin": {...},                                  │
│   "mensaje": "Cliente creado exitosamente"                 │
│ }                                                           │
└─────────────────────────────────────────────────────────────┘


### ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
### FASE 3: GESTIÓN MENSUAL (OPERACIÓN)
### ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌─────────────────────────────────────────────────────────────┐
│ 7. FACTURACIÓN MENSUAL AUTOMÁTICA                          │
│    (Ejecutar 1ro de cada mes - Cron Job)                   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ POST /facturas/generar-mensual                             │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│ Genera facturas para todas las empresas activas            │
│                                                             │
│ O bien:                                                     │
│                                                             │
│ POST /facturas                                             │
│ {                                                           │
│   "id_empresa": 1,                                         │
│   "id_plan": 1,                                            │
│   "periodo_facturado": "Noviembre 2025",                   │
│   "fecha_vencimiento": "2025-12-10",                       │
│   // Cálculo automático:                                   │
│   "subtotal": 1134454,  // precio_mensual / 1.19          │
│   "iva": 215546,        // subtotal * 0.19                 │
│   "total": 1350000,     // precio_mensual del plan         │
│   "descripcion": "Suscripción POE - Nov 2025"              │
│ }                                                           │
│                                                             │
│ Estado inicial: "pendiente"                                │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 8. CONSULTAR FACTURAS PENDIENTES                           │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ GET /facturas?id_empresa=1&estado=pendiente                │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│ Ver facturas pendientes de pago                            │
│                                                             │
│ GET /facturas/{id_factura}                                 │
│ Ver detalle de factura específica                          │
│                                                             │
│ GET /facturas/{id_factura}/pdf                             │
│ Descargar factura en PDF                                   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 9. REGISTRAR PAGO DE FACTURA                               │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ PATCH /facturas/{id_factura}/pagar                         │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│ {                                                           │
│   "metodo_pago": "transferencia",                          │
│   "referencia_pago": "TRF-123456",                         │
│   "fecha_pago": "2025-11-08"                               │
│ }                                                           │
│                                                             │
│ ACCIÓN:                                                     │
│ - estado: "pendiente" → "pagada"                           │
│ - fecha_pago: AHORA                                        │
└─────────────────────────────────────────────────────────────┘


### ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
### FASE 4: GESTIÓN DE PLAN Y LÍMITES
### ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌─────────────────────────────────────────────────────────────┐
│ 10. VALIDAR LÍMITES DE USO (Constante)                     │
│     Cada vez que se crea un recurso                         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ GET /planes/empresa/{id_empresa}/validar-limites            │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│ Response:                                                   │
│ {                                                           │
│   "plan": {                                                │
│     "cantidad_locales": 5,                                 │
│     "cantidad_supervisores": 10,                           │
│     "cantidad_reponedores": 50,                            │
│     "cantidad_productos": 5000                             │
│   },                                                        │
│   "uso_actual": {                                          │
│     "locales": 3,                                          │
│     "supervisores": 8,                                     │
│     "reponedores": 45,                                     │
│     "productos": 4200                                      │
│   },                                                        │
│   "validaciones": [                                        │
│     {                                                      │
│       "recurso": "supervisores",                           │
│       "disponible": 2,                                     │
│       "excedido": false                                    │
│     },                                                      │
│     ...                                                     │
│   ]                                                         │
│ }                                                           │
│                                                             │
│ LÓGICA EN BACKEND:                                          │
│ - Antes de crear Usuario con rol=SUPERVISOR:              │
│   if (count_supervisores >= plan.cantidad_supervisores) { │
│     throw "Límite de supervisores alcanzado"              │
│   }                                                         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 11. UPGRADE/DOWNGRADE DE PLAN                              │
│     Cliente necesita más recursos                          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ PUT /planes/{id_plan}                                      │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│ {                                                           │
│   "cantidad_supervisores": 15,  // Era 10, ahora 15       │
│   "precio_mensual": 1550000,     // Nuevo precio           │
│   "notas": "Upgrade por expansión"                         │
│ }                                                           │
│                                                             │
│ ACCIÓN:                                                     │
│ - Actualizar plan                                          │
│ - Siguiente factura reflejará nuevo precio                │
└─────────────────────────────────────────────────────────────┘


### ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
### FASE 5: SOPORTE Y SEGUIMIENTO
### ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌─────────────────────────────────────────────────────────────┐
│ 12. REGISTRAR ACTIVIDADES CON CLIENTE                      │
│     (Soporte, capacitaciones, incidencias)                  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ POST /actividades                                          │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│ {                                                           │
│   "id_empresa": 1,                                         │
│   "tipo": "capacitacion",                                  │
│   "titulo": "Capacitación uso dashboard",                  │
│   "descripcion": "Entrenar a supervisores en reportes",    │
│   "id_usuario_responsable": 5,  // Account Manager POE    │
│   "fecha_programada": "2025-11-20T10:00:00Z"               │
│ }                                                           │
│                                                             │
│ Tipos: capacitacion, soporte, incidencia, reunion,        │
│        upgrade, otro                                        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ GET /actividades?id_empresa=1                              │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│ Ver historial de todas las interacciones con el cliente   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ PATCH /actividades/{id}/completar                          │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│ { "notas": "Capacitación exitosa, 8 supervisores" }        │
│                                                             │
│ estado: "pendiente" → "completada"                         │
└─────────────────────────────────────────────────────────────┘


### ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
### MÓDULO BACKOFFICE: SUPERVISIÓN SUPERADMIN
### ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌─────────────────────────────────────────────────────────────┐
│ 13. DASHBOARD EJECUTIVO (SuperAdmin POE)                   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ GET /backoffice/dashboard/metricas                         │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│ Response:                                                   │
│ {                                                           │
│   "empresas": {                                            │
│     "total": 50,                                           │
│     "activas": 45,                                         │
│     "inactivas": 3,                                        │
│     "prueba": 2                                            │
│   },                                                        │
│   "usuarios": {                                            │
│     "total": 1250,                                         │
│     "activos": 1180,                                       │
│     "por_rol": {                                           │
│       "ADMIN": 50,                                         │
│       "SUPERVISOR": 250,                                   │
│       "REPONEDOR": 950                                     │
│     }                                                       │
│   },                                                        │
│   "suscripciones": {                                       │
│     "planes_activos": 45,                                  │
│     "planes_vencidos": 5                                   │
│   },                                                        │
│   "facturacion": {                                         │
│     "total_mes_actual": 67500000,  // CLP                 │
│     "facturas_pagadas": 40,                                │
│     "facturas_pendientes": 5,                              │
│     "facturas_vencidas": 2                                 │
│   },                                                        │
│   "cotizaciones": {                                        │
│     "pendientes": 15,                                      │
│     "aprobadas": 8,                                        │
│     "rechazadas": 3                                        │
│   },                                                        │
│   "actividades": {                                         │
│     "pendientes": 25,                                      │
│     "completadas_mes": 40                                  │
│   }                                                         │
│ }                                                           │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 14. GESTIÓN DE EMPRESAS (SuperAdmin)                       │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ GET /backoffice/empresas                                   │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│ Lista todas las empresas con:                              │
│ - Datos básicos (nombre, RUT, ubicación)                   │
│ - Estado suscripción                                       │
│ - Consumo vs límites                                       │
│ - Última factura                                           │
│                                                             │
│ SIN DATOS SENSIBLES:                                       │
│ ❌ Empleados (nombres, RUT, salarios)                      │
│ ❌ Productos (SKU, stock)                                  │
│ ❌ Logística (rutas, tareas)                               │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ GET /backoffice/empresas/{id}/resumen                      │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│ Resumen completo de una empresa:                           │
│ - Plan actual                                              │
│ - Consumo de recursos                                      │
│ - Usuarios por rol (solo conteos)                         │
│ - Historial de facturas                                   │
│ - Actividades recientes                                   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ GET /backoffice/empresas/{id}/consumo                      │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│ Response:                                                   │
│ {                                                           │
│   "recursos": [                                            │
│     {                                                      │
│       "nombre": "Supervisores",                            │
│       "uso": 8,                                            │
│       "limite": 10,                                        │
│       "porcentaje": 80,                                    │
│       "disponible": 2,                                     │
│       "estado": "normal"  // normal, proximo, excedido    │
│     },                                                      │
│     ...                                                     │
│   ]                                                         │
│ }                                                           │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 15. SUSPENDER/REACTIVAR EMPRESA (Por falta de pago)        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ POST /backoffice/empresas/{id}/suspender                   │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│ {                                                           │
│   "motivo": "Factura vencida hace 30 días"                │
│ }                                                           │
│                                                             │
│ ACCIÓN:                                                     │
│ - empresa.estado = "inactivo"                              │
│ - plan.activo = false                                      │
│ - REGISTRA EN AUDITORÍA:                                   │
│   * Usuario que suspendió                                  │
│   * Timestamp                                              │
│   * Motivo                                                 │
│   * Datos anteriores vs nuevos                            │
│                                                             │
│ POST /backoffice/empresas/{id}/reactivar                   │
│ { "motivo": "Pago recibido" }                              │
│                                                             │
│ ACCIÓN:                                                     │
│ - empresa.estado = "activo"                                │
│ - plan.activo = true                                       │
│ - REGISTRA EN AUDITORÍA                                    │
└─────────────────────────────────────────────────────────────┘


### ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
### AUDITORÍA Y TRAZABILIDAD
### ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌─────────────────────────────────────────────────────────────┐
│ 16. CONSULTAR LOGS DE AUDITORÍA                            │
│     Todas las acciones de SuperAdmin quedan registradas    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ GET /backoffice/auditoria/logs                             │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│ Query params:                                              │
│ - usuario_id: Filtrar por usuario                         │
│ - accion: CREATE, UPDATE, DELETE, SUSPEND, REACTIVATE     │
│ - entidad: Empresa, PlanEmpresa, Usuario, etc.            │
│ - fecha_desde / fecha_hasta                                │
│ - page, limit (paginación)                                 │
│                                                             │
│ Response:                                                   │
│ {                                                           │
│   "logs": [                                                │
│     {                                                      │
│       "id_log": 123,                                       │
│       "usuario": "admin@poe.cl",                           │
│       "accion": "SUSPEND",                                 │
│       "entidad": "Empresa",                                │
│       "id_entidad": 5,                                     │
│       "datos_anteriores": {"estado": "activo"},            │
│       "datos_nuevos": {"estado": "inactivo"},              │
│       "ip_origen": "192.168.1.100",                        │
│       "fecha": "2025-11-15T14:30:00Z"                      │
│     }                                                       │
│   ],                                                        │
│   "total": 1250,                                           │
│   "pagina": 1                                              │
│ }                                                           │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ GET /backoffice/auditoria/estadisticas                     │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│ Response:                                                   │
│ {                                                           │
│   "total_logs": 5430,                                      │
│   "por_accion": {                                          │
│     "CREATE": 2100,                                        │
│     "UPDATE": 2800,                                        │
│     "DELETE": 350,                                         │
│     "SUSPEND": 120,                                        │
│     "REACTIVATE": 60                                       │
│   },                                                        │
│   "usuarios_mas_activos": [                                │
│     {"usuario": "admin1@poe.cl", "acciones": 450},         │
│     ...                                                     │
│   ],                                                        │
│   "entidades_mas_modificadas": [                           │
│     {"entidad": "PlanEmpresa", "modificaciones": 320},     │
│     ...                                                     │
│   ]                                                         │
│ }                                                           │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ GET /backoffice/auditoria/entidad/{entidad}/{id}           │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│ Ejemplo: GET /backoffice/auditoria/entidad/Empresa/5       │
│                                                             │
│ Historial COMPLETO de cambios en una entidad específica:  │
│ - Quién la creó                                            │
│ - Todas las modificaciones                                 │
│ - Quién/cuándo/qué cambió                                  │
│ - Datos antes y después                                    │
└─────────────────────────────────────────────────────────────┘


## ═══════════════════════════════════════════════════════════
## 📊 RESUMEN DE ENDPOINTS POR MÓDULO
## ═══════════════════════════════════════════════════════════

### 🔹 COTIZACIONES (9 endpoints)
POST   /cotizaciones                          - Crear cotización
GET    /cotizaciones                          - Listar con filtros
GET    /cotizaciones/{id}                     - Ver detalle
PUT    /cotizaciones/{id}                     - Actualizar
DELETE /cotizaciones/{id}                     - Eliminar
PATCH  /cotizaciones/{id}/estado              - Cambiar estado
POST   /cotizaciones/{id}/convertir           - Convertir a cliente ⭐
GET    /cotizaciones/estadisticas             - Estadísticas
GET    /cotizaciones/dashboard                - Dashboard comercial

### 🔹 PLANES (10 endpoints)
POST   /planes                                - Crear plan
GET    /planes/empresa/{id_empresa}           - Plan de empresa
GET    /planes/{id}                           - Ver plan
PUT    /planes/{id}                           - Modificar plan
DELETE /planes/{id}                           - Eliminar plan
GET    /planes/empresa/{id}/validar-limites   - Validar límites ⭐
GET    /planes/validar-recurso                - Validar recurso específico
GET    /planes/vencidos                       - Planes vencidos
GET    /planes/estadisticas                   - Estadísticas
PUT    /planes/{id}/renovar                   - Renovar plan

### 🔹 FACTURAS (10 endpoints)
POST   /facturas                              - Crear factura manual
POST   /facturas/generar-mensual              - Generar automático ⭐
GET    /facturas                              - Listar con filtros
GET    /facturas/{id}                         - Ver detalle
PUT    /facturas/{id}                         - Actualizar
DELETE /facturas/{id}                         - Anular
PATCH  /facturas/{id}/pagar                   - Registrar pago ⭐
GET    /facturas/{id}/pdf                     - Descargar PDF
GET    /facturas/vencidas                     - Facturas vencidas
GET    /facturas/estadisticas                 - Estadísticas

### 🔹 ACTIVIDADES (10 endpoints)
POST   /actividades                           - Crear actividad
GET    /actividades                           - Listar con filtros
GET    /actividades/{id}                      - Ver detalle
PUT    /actividades/{id}                      - Actualizar
DELETE /actividades/{id}                      - Eliminar
PATCH  /actividades/{id}/completar            - Marcar completada ⭐
PATCH  /actividades/{id}/cancelar             - Cancelar
POST   /actividades/{id}/archivo              - Subir archivo
GET    /actividades/estadisticas              - Estadísticas
GET    /actividades/calendario                - Vista calendario

### 🔹 BACKOFFICE (9 endpoints) 🆕
GET    /backoffice/dashboard/metricas         - Dashboard SuperAdmin ⭐
GET    /backoffice/empresas                   - Listar empresas seguro
GET    /backoffice/empresas/{id}/resumen      - Resumen empresa ⭐
GET    /backoffice/empresas/{id}/consumo      - Consumo vs límites ⭐
POST   /backoffice/empresas/{id}/suspender    - Suspender empresa ⭐
POST   /backoffice/empresas/{id}/reactivar    - Reactivar empresa ⭐
GET    /backoffice/auditoria/logs             - Logs de auditoría ⭐
GET    /backoffice/auditoria/estadisticas     - Estadísticas auditoría
GET    /backoffice/auditoria/entidad/{e}/{id} - Historial entidad ⭐


## ═══════════════════════════════════════════════════════════
## 🎯 CASOS DE USO PRINCIPALES
## ═══════════════════════════════════════════════════════════

### CASO 1: NUEVO CLIENTE (ONBOARDING COMPLETO)
1. POST /cotizaciones                    → Cliente solicita
2. GET /cotizaciones?estado=pendiente    → POE revisa
3. PUT /cotizaciones/{id}                → POE cotiza
4. PATCH /cotizaciones/{id}/estado       → Cliente aprueba
5. POST /cotizaciones/{id}/convertir     → ⭐ Crear empresa + plan
6. POST /facturas/generar-mensual        → Primera factura
7. POST /actividades                     → Programar onboarding

### CASO 2: FACTURACIÓN MENSUAL
1. POST /facturas/generar-mensual        → Cron 1ro del mes
2. GET /facturas?estado=pendiente        → Cliente ve facturas
3. PATCH /facturas/{id}/pagar            → Cliente paga
   (Si no paga en 30 días...)
4. POST /backoffice/empresas/{id}/suspender → SuperAdmin suspende

### CASO 3: UPGRADE DE PLAN
1. GET /planes/empresa/{id}/validar-limites  → Cliente en 90% límite
2. POST /actividades                         → Agendar reunión upgrade
3. PUT /planes/{id}                          → Actualizar plan
4. POST /facturas                            → Factura prorrateo (opcional)

### CASO 4: AUDITORÍA DE CAMBIOS
1. POST /backoffice/empresas/{id}/suspender  → Acción crítica
2. (Automático) → Se registra en log_auditoria
3. GET /backoffice/auditoria/logs            → SuperAdmin revisa
4. GET /backoffice/auditoria/entidad/Empresa/5 → Historial completo


## ═══════════════════════════════════════════════════════════
## 🔐 SEGURIDAD Y VALIDACIONES
## ═══════════════════════════════════════════════════════════

### VALIDACIÓN DE LÍMITES (Automática)
Antes de crear cualquier recurso:

```python
# Ejemplo: Crear nuevo supervisor
def crear_usuario(id_empresa, rol, ...):
    if rol == "SUPERVISOR":
        plan = get_plan_empresa(id_empresa)
        count = count_usuarios(id_empresa, rol="SUPERVISOR")
        
        if count >= plan.cantidad_supervisores:
            raise HTTPException(
                status_code=403,
                detail="Límite de supervisores alcanzado. Upgrade plan."
            )
    
    # Crear usuario...
```

### AUDITORÍA AUTOMÁTICA (Decorator)
Todas las acciones de SuperAdmin se registran automáticamente:

```python
@auditar(entidad="Empresa", accion="SUSPEND")
def suspender_empresa(id_empresa, motivo, current_user):
    # El decorator captura automáticamente:
    # - current_user
    # - datos_anteriores (estado antes)
    # - datos_nuevos (estado después)
    # - IP, timestamp, etc.
```


## ═══════════════════════════════════════════════════════════
## 📈 MÉTRICAS Y KPIs
## ═══════════════════════════════════════════════════════════

El dashboard backoffice permite monitorear:

✅ **Ingresos**: Total MRR (Monthly Recurring Revenue)
✅ **Churn**: Empresas que cancelan / Total empresas
✅ **Conversión**: Cotizaciones aprobadas / Total cotizaciones
✅ **Mora**: Facturas vencidas / Total facturas
✅ **Consumo**: Empresas cerca del límite (oportunidad upsell)
✅ **Actividad**: Soporte vs capacitaciones vs incidencias

