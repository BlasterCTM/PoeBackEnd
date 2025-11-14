# Inventario Completo de Endpoints - POE API

## Total: ~77 Endpoints

### 1. USUARIOS (9 endpoints) - Prefix: `/usuarios`
| Método | Endpoint | Multi-tenant | Role Required | Descripción |
|--------|----------|--------------|---------------|-------------|
| POST | `/usuarios/` | ✅ | Administrador+ | Crear usuario |
| POST | `/usuarios/token` | ❌ | Public | Login |
| POST | `/usuarios/refresh` | ❌ | Authenticated | Refresh token |
| GET | `/usuarios/` | ✅ | Administrador+ | Listar usuarios |
| DELETE | `/usuarios/{id}` | ✅ | Administrador+ | Eliminar usuario |
| PUT | `/usuarios/{id}` | ✅ | Administrador+ | Actualizar usuario |
| PATCH | `/usuarios/{id}/estado` | ✅ | Administrador+ | Cambiar estado |
| GET | `/usuarios/perfil` | ❌ | Authenticated | Obtener perfil |
| GET | `/usuarios/reponedores/disponibles` | ✅ | Supervisor+ | Listar reponedores |

### 2. SUPERVISOR (8 endpoints) - Prefix: `/supervisor`
| Método | Endpoint | Multi-tenant | Role Required | Descripción |
|--------|----------|--------------|---------------|-------------|
| POST | `/supervisor/reponedores` | ✅ | Supervisor | Registrar reponedor |
| GET | `/supervisor/reponedores` | ✅ | Supervisor | Listar reponedores |
| GET | `/supervisor/reponedores/{id}` | ✅ | Supervisor | Obtener reponedor |
| POST | `/supervisor/reponedores/{id}/supervisa` | ✅ | Supervisor | Asignar supervisión |
| DELETE | `/supervisor/reponedores/{id}/supervisa` | ✅ | Supervisor | Quitar supervisión |
| GET | `/supervisor/reponedores/supervisados` | ✅ | Supervisor | Mis supervisados |
| GET | `/supervisor/{id}/estadisticas` | ✅ | Supervisor | Estadísticas supervisor |
| PUT | `/supervisor/reponedores/{id}` | ✅ | Supervisor | Actualizar reponedor |

### 3. PRODUCTOS (9 endpoints) - Prefix: `/productos`
| Método | Endpoint | Multi-tenant | Role Required | Descripción |
|--------|----------|--------------|---------------|-------------|
| POST | `/productos` | ✅ | Administrador+ | Crear producto |
| GET | `/productos` | ✅ | Authenticated | Listar productos |
| GET | `/productos/buscar` | ✅ | Authenticated | Buscar productos |
| GET | `/productos/{id_producto}` | ✅ | Authenticated | Obtener producto |
| PUT | `/productos/{id_producto}` | ✅ | Administrador+ | Actualizar producto |
| DELETE | `/productos/{id_producto}` | ✅ | Administrador+ | Eliminar producto |
| DELETE | `/productos/{id_producto}/desasignar-punto` | ✅ | Administrador+ | Desasignar de punto |
| PUT | `/productos/{id_producto}/asignar-punto` | ✅ | Administrador+ | Asignar a punto |
| GET | `/productos/{id_producto}/ubicacion` | ✅ | Authenticated | Obtener ubicación |

### 4. TAREAS (22 endpoints) - Prefix: `/tareas`
| Método | Endpoint | Multi-tenant | Role Required | Descripción |
|--------|----------|--------------|---------------|-------------|
| POST | `/tareas` | ✅ | Supervisor+ | Crear tarea |
| GET | `/tareas/disponibles` | ✅ | Reponedor | Tareas disponibles |
| GET | `/tareas/asignadas` | ✅ | Reponedor | Tareas asignadas |
| GET | `/tareas/no-asignadas` | ✅ | Supervisor+ | Tareas sin asignar |
| GET | `/tareas/supervisor` | ✅ | Supervisor | Tareas del supervisor |
| GET | `/tareas/reponedor` | ✅ | Reponedor | Tareas del reponedor |
| GET | `/tareas/{id_tarea}` | ✅ | Authenticated | Obtener tarea |
| GET | `/tareas/{id_tarea}/detalle` | ✅ | Authenticated | Detalle de tarea |
| GET | `/tareas/{id_tarea}/ruta-optimizada` | ✅ | Authenticated | Ruta optimizada |
| PUT | `/tareas/{id_tarea}/cambiar-estado` | ✅ | Supervisor+ | Cambiar estado |
| PUT | `/tareas/{id_tarea}/asignar-reponedor` | ✅ | Supervisor+ | Asignar reponedor |
| PUT | `/tareas/{id_tarea}/iniciar` | ✅ | Reponedor | Iniciar tarea |
| PUT | `/tareas/{id_tarea}/reiniciar` | ✅ | Supervisor+ | Reiniciar tarea |
| PUT | `/tareas/{id_tarea}/completar` | ✅ | Reponedor | Completar tarea |
| PUT | `/tareas/{id_tarea}/cancelar` | ✅ | Supervisor+ | Cancelar tarea |
| PUT | `/tareas/{id_tarea}/detalle/reemplazar` | ✅ | Supervisor+ | Reemplazar detalle |
| PUT | `/tareas/{id_tarea}/detalle/{id_punto}` | ✅ | Supervisor+ | Actualizar detalle |
| POST | `/tareas/{id_tarea}/detalle` | ✅ | Supervisor+ | Agregar detalle |
| DELETE | `/tareas/{id_tarea}/detalle/{id_producto}` | ✅ | Supervisor+ | Eliminar detalle |
| PUT | `/detalles-tarea/{id_detalle}/completar` | ✅ | Reponedor | Completar detalle |
| PUT | `/detalle-tarea/{id_detalle}/cambiar-estado` | ✅ | Supervisor+ | Cambiar estado detalle |

### 5. EMPRESAS (7 endpoints) - Prefix: `/empresas`
| Método | Endpoint | Multi-tenant | Role Required | Descripción |
|--------|----------|--------------|---------------|-------------|
| POST | `/empresas/registro` | ❌ | SuperAdmin | Registrar empresa |
| GET | `/empresas/` | ⚠️ | Administrador+ | Listar empresas (SuperAdmin: todas, Admin: su empresa) |
| GET | `/empresas/mi-empresa` | ✅ | Authenticated | Obtener mi empresa |
| GET | `/empresas/{id_empresa}` | ⚠️ | Administrador+ | Obtener empresa |
| PATCH | `/empresas/{id_empresa}` | ⚠️ | Administrador+ | Actualizar empresa |
| DELETE | `/empresas/{id_empresa}` | ❌ | SuperAdmin | Eliminar empresa |
| GET | `/empresas/estadisticas/resumen` | ⚠️ | Administrador+ | Estadísticas empresa |

### 6. REPORTE (8 endpoints) - Prefix: `/reportes`
| Método | Endpoint | Multi-tenant | Role Required | Descripción |
|--------|----------|--------------|---------------|-------------|
| GET | `/reportes/reponedores` | ✅ | Supervisor+ | Listar reponedores |
| GET | `/reportes/reponedor/{id_reponedor}` | ✅ | Supervisor+ | Reporte de reponedor |
| GET | `/reportes/reponedor/{id_reponedor}/descargar` | ✅ | Supervisor+ | Descargar PDF |
| GET | `/reportes/supervisor/{id_supervisor}/reponedores` | ✅ | Supervisor+ | Reponedores del supervisor |
| GET | `/reportes/estadisticas/general` | ✅ | Administrador+ | Estadísticas generales |
| POST | `/reportes/productos-repuestos` | ✅ | Supervisor+ | Reporte productos repuestos |
| POST | `/reportes/productos-repuestos/descargar` | ✅ | Supervisor+ | Descargar Excel |
| GET | `/reportes/productos-repuestos/preview` | ✅ | Supervisor+ | Preview reporte |

### 7. ESTADISTICAS (9 endpoints) - Prefix: `/admin/estadisticas`
| Método | Endpoint | Multi-tenant | Role Required | Descripción |
|--------|----------|--------------|---------------|-------------|
| GET | `/admin/estadisticas/puntos-mas-usados` | ✅ | Administrador+ | Puntos más usados |
| GET | `/admin/estadisticas/productos-disponibles` | ✅ | Administrador+ | Productos disponibles |
| GET | `/admin/estadisticas/reponedores-disponibles` | ✅ | Administrador+ | Reponedores disponibles |
| GET | `/admin/estadisticas/punto-detalle/{id_punto}` | ✅ | Administrador+ | Detalle de punto |
| GET | `/admin/estadisticas/resumen-general` | ✅ | Administrador+ | Resumen general |
| GET | `/admin/estadisticas/supervisor/metricas` | ✅ | Supervisor | Métricas de supervisor |
| GET | `/admin/estadisticas/supervisor/{id_supervisor}/metricas` | ✅ | Administrador+ | Métricas de supervisor específico |
| GET | `/admin/estadisticas/supervisor/reponedores-rendimiento` | ✅ | Supervisor | Rendimiento reponedores |
| GET | `/admin/estadisticas/supervisor/productos-estadisticas` | ✅ | Supervisor | Estadísticas productos |

### 8. DASHBOARD (1 endpoint) - Prefix: `/dashboard`
| Método | Endpoint | Multi-tenant | Role Required | Descripción |
|--------|----------|--------------|---------------|-------------|
| GET | `/dashboard/resumen` | ✅ | Administrador+ | Resumen dashboard |

### 9. RESUMEN SEMANAL (3 endpoints) - Prefix: `/reponedor`
| Método | Endpoint | Multi-tenant | Role Required | Descripción |
|--------|----------|--------------|---------------|-------------|
| GET | `/reponedor/resumen-semanal` | ✅ | Reponedor | Resumen semanal |
| GET | `/reponedor/semanas-disponibles` | ✅ | Reponedor | Semanas disponibles |
| GET | `/reponedor/resumen-semanal/estadisticas` | ✅ | Reponedor | Estadísticas semanales |

### 10. MAPA (13 endpoints) - Prefix: `/mapa` o `/puntos` o `/mapas`
| Método | Endpoint | Multi-tenant | Role Required | Descripción |
|--------|----------|--------------|---------------|-------------|
| GET | `/mapa/reposicion` | ✅ | Authenticated | Visualizar mapa |
| GET | `/mapa/vista-grafica` | ✅ | Authenticated | Vista gráfica |
| GET | `/mapa/supervisor` | ✅ | Supervisor | Vista supervisor |
| GET | `/mapa/supervisor/vista` | ✅ | Supervisor | Mapeo supervisor |
| GET | `/mapa/reponedor/vista` | ✅ | Reponedor | Mapeo reponedor |
| GET | `/mapa/activo` | ✅ | Authenticated | Obtener mapa activo |
| PUT | `/mapa/{id_mapa}/activar` | ✅ | Administrador+ | Activar mapa |
| POST | `/mapas` | ✅ | Administrador+ | Crear mapa |
| POST | `/puntos/asignar` | ✅ | Administrador+ | Asignar punto |
| DELETE | `/puntos/desasignar` | ✅ | Administrador+ | Desasignar punto |
| PUT | `/puntos/{id_punto}/asignar-producto` | ✅ | Administrador+ | Asignar producto |
| DELETE | `/puntos/{id_punto}/desasignar-producto` | ✅ | Administrador+ | Desasignar producto |

### 11. PUNTOS (2 endpoints) - Prefix: `/puntos`
| Método | Endpoint | Multi-tenant | Role Required | Descripción |
|--------|----------|--------------|---------------|-------------|
| GET | `/puntos/{id_punto}/disponibilidad` | ✅ | Authenticated | Verificar disponibilidad |
| POST | `/puntos` | ✅ | Administrador+ | Crear punto |

### 12. MUEBLES (2 endpoints) - Prefix: `/muebles`
| Método | Endpoint | Multi-tenant | Role Required | Descripción |
|--------|----------|--------------|---------------|-------------|
| GET | `/muebles/reposicion` | ✅ | Authenticated | Listar muebles |
| POST | `/muebles/reposicion` | ✅ | Administrador+ | Crear mueble |

### 13. RUTA (1 endpoint) - Prefix: `/ruta`
| Método | Endpoint | Multi-tenant | Role Required | Descripción |
|--------|----------|--------------|---------------|-------------|
| POST | `/ruta/optima` | ❌ | Authenticated | Calcular ruta óptima |

## Leyenda
- ✅ **Multi-tenant:** Endpoint filtra por `id_empresa`
- ❌ **No Multi-tenant:** Endpoint NO filtra por empresa (público o utilitario)
- ⚠️ **Condicional:** SuperAdmin ve todo, Administrador solo su empresa

## Roles
- **SuperAdmin**: Acceso global a todas las empresas
- **Administrador**: Acceso a su empresa
- **Supervisor**: Gestión de reponedores y tareas
- **Reponedor**: Ejecución de tareas

## Notas de Testing
1. **Autenticación**: Todos excepto `/usuarios/token` requieren token JWT
2. **Multi-tenant**: La mayoría de endpoints deben filtrar por `id_empresa`
3. **Roles**: Validar 403 para roles insuficientes
4. **Datos**: Cada test debe crear sus propios datos de prueba
