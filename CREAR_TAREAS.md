# Funcionalidad para Crear Tareas

Este documento explica cómo utilizar la nueva funcionalidad para crear tareas en el sistema POE (Path Optimization Engine).

## Estructura de una Tarea

Una tarea en el sistema POE tiene los siguientes componentes:

- **Tarea**: Contiene la información básica como fecha de creación, estado, supervisor, reponedor y punto de reposición.
- **Detalle de Tarea**: Contiene los productos asociados a la tarea, cada uno con su cantidad.

## Endpoints Disponibles

### 1. Crear una Tarea

```
POST /tareas
```

**Permisos**: Solo administradores y supervisores pueden crear tareas.

**Payload para Supervisores**:
```json
{
  "id_punto": 1,           // ID del punto de reposición (obligatorio)
  "id_reponedor": 3       // ID del reponedor (opcional)
}
```

**Payload para Administradores**:
```json
{
  "id_supervisor": 2,     // ID del supervisor (obligatorio para administradores)
  "id_punto": 1,          // ID del punto de reposición (obligatorio)
  "id_reponedor": 3       // ID del reponedor (opcional)
}
```

**Respuesta**:
```json
{
  "id_tarea": 1,
  "fecha_creacion": "2023-11-15",
  "estado_id": 1,
  "id_supervisor": 2,
  "id_punto": 1,
  "id_reponedor": 3
}
```

### 2. Agregar Productos a una Tarea

```
POST /tareas/{id_tarea}/detalle
```

**Payload**:
```json
{
  "id_producto": 5,       // ID del producto a agregar
  "cantidad": 10          // Cantidad del producto
}
```

**Respuesta**:
```json
{
  "mensaje": "Producto agregado correctamente a la tarea.",
  "detalle_tarea": {
    "id_producto": 5,
    "nombre_producto": "Nombre del Producto",
    "cantidad": 10
  }
}
```

### 3. Obtener Detalle de una Tarea

```
GET /tareas/{id_tarea}/detalle
```

**Respuesta**:
```json
[
  {
    "id_producto": 5,
    "nombre_producto": "Nombre del Producto 1",
    "cantidad": 10
  },
  {
    "id_producto": 8,
    "nombre_producto": "Nombre del Producto 2",
    "cantidad": 5
  }
]
```

### 4. Eliminar un Producto de una Tarea

```
DELETE /tareas/{id_tarea}/detalle/{id_producto}
```

**Respuesta**:
```json
{
  "mensaje": "Producto eliminado del detalle de la tarea."
}
```

## Ejemplo de Uso

Se ha incluido un script de ejemplo `ejemplo_crear_tarea.py` que muestra cómo utilizar estos endpoints desde Python. Para ejecutarlo:

1. Asegúrate de que el backend esté en ejecución
2. Ajusta los IDs en el script para que coincidan con datos existentes en tu base de datos
3. Ejecuta el script: `python ejemplo_crear_tarea.py`

## Notas Importantes

- Los productos que quieras agregar a una tarea deben existir previamente en el catálogo
- La tarea debe existir antes de poder agregar productos a ella
- Los estados de tarea son: 1 = pendiente, 2 = en_progreso (estos valores pueden variar según la configuración)
- Solo los administradores y supervisores pueden crear tareas
- Los supervisores solo pueden crear tareas para reponedores que estén bajo su supervisión