from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from app.schemas.producto import ProductoCreate, ProductoOut, ProductoUpdate
from app.repositories.producto import (
    create_producto,
    get_productos,
    update_producto,
    get_producto_by_id,
    producto_vinculado_a_tareas_activas,
    buscar_productos,  # <-- importar la nueva función
)
from app.core.database.database import get_db
from app.api.dependencies.auth import get_current_user
from app.models.usuario import Usuario, RolEnum
from app.models.usuario import Usuario as UsuarioModel
from fastapi import Response
import uuid
from app.repositories.punto_reposicion import (
    obtener_punto_por_producto,
    desasignar_punto_por_producto,
    asignar_o_reasignar_producto_a_punto, obtener_ubicacion_producto
)
from app.models.punto_reposicion import PuntoReposicion
from app.models.objeto_mapa import ObjetoMapa
from app.models.mueble_reposicion import MuebleReposicion
from app.models.ubicacion_fisica import UbicacionFisica
from app.schemas.mapa import PuntoReposicionOut, ProductoAsociado
from app.utils.tenant import validate_tenant_access, is_super_admin

router = APIRouter()

# Estados activos: debes ajustar estos IDs según tu tabla estado_tarea
ESTADOS_ACTIVOS = [1, 2]  # Ejemplo: 1=pendiente, 2=en_progreso


@router.post("/productos", response_model=ProductoOut, status_code=201)
def crear_producto(
    producto: ProductoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    if current_user.rol.nombre_rol != RolEnum.ADMINISTRADOR.value:
        raise HTTPException(status_code=403, detail="No tienes permisos para crear productos")
    # Generar código único si no se proporciona
    codigo_unico = producto.codigo_unico or str(uuid.uuid4())[:8].upper()
    try:
        db_producto = create_producto(
            db, 
            producto, 
            id_usuario=producto.id_usuario, 
            id_empresa=current_user.id_empresa,
            codigo_unico=codigo_unico
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return db_producto


@router.get("/productos")
def listar_productos(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=100),
    orden: str = Query("nombre", pattern="^(nombre|fecha)$"),
    estado: str = Query(None, pattern="^(activo|inactivo)?$")
):
    if not current_user:
        raise HTTPException(status_code=401, detail="No autenticado")
    # Filtrar por id_usuario solo si es supervisor Y por empresa
    if current_user.rol.nombre_rol == RolEnum.SUPERVISOR.value:
        data = get_productos(
            db, 
            id_empresa=current_user.id_empresa,
            page=page, 
            limit=limit, 
            orden=orden, 
            estado=estado, 
            id_usuario=current_user.id_usuario
        )
    else:
        data = get_productos(
            db, 
            id_empresa=current_user.id_empresa,
            page=page, 
            limit=limit, 
            orden=orden, 
            estado=estado
        )
    
    # Enriquecer los productos con el nombre del supervisor
    productos_enriquecidos = []
    for producto in data["productos"]:
        # Obtener el supervisor del producto
        supervisor = db.query(UsuarioModel).filter(UsuarioModel.id_usuario == producto.id_usuario).first()
        
        producto_dict = {
            "id_producto": producto.id_producto,
            "nombre": producto.nombre,
            "categoria": producto.categoria,
            "unidad_tipo": producto.unidad_tipo,
            "unidad_cantidad": producto.unidad_cantidad,
            "codigo_unico": producto.codigo_unico,
            "estado": producto.estado,
            "id_usuario": producto.id_usuario,
            "nombre_supervisor": supervisor.nombre if supervisor else None
        }
        productos_enriquecidos.append(producto_dict)
    
    return {
        "total": data["total"],
        "page": data["page"],
        "limit": data["limit"],
        "productos": productos_enriquecidos
    }


@router.get("/productos/buscar")
def buscar_productos_endpoint(
    nombre: str = Query(None, description="Nombre parcial o completo del producto"),
    categoria: str = Query(None, description="Categoría exacta del producto"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if not current_user or current_user.rol.nombre_rol not in [RolEnum.ADMINISTRADOR.value, RolEnum.SUPERVISOR.value]:
        raise HTTPException(status_code=403, detail="Solo administradores o supervisores pueden buscar productos.")
    # Filtrar por id_usuario solo si es supervisor
    id_usuario = current_user.id_usuario if current_user.rol.nombre_rol == RolEnum.SUPERVISOR.value else None
    resultados = buscar_productos(
        db, 
        id_empresa=current_user.id_empresa,
        nombre=nombre, 
        categoria=categoria, 
        id_usuario=id_usuario
    )
    if not resultados:
        return {"total": 0, "mensaje": "Sin resultados para los filtros aplicados."}
    
    # Enriquecer los resultados con el nombre del supervisor
    resultados_enriquecidos = []
    for p in resultados:
        supervisor = db.query(UsuarioModel).filter(UsuarioModel.id_usuario == p.id_usuario).first()
        resultado_dict = {
            "id": p.id_producto,
            "nombre": p.nombre,
            "categoria": p.categoria,
            "unidad_tipo": p.unidad_tipo,
            "unidad_cantidad": p.unidad_cantidad,
            "id_usuario": p.id_usuario,
            "nombre_supervisor": supervisor.nombre if supervisor else None
        }
        resultados_enriquecidos.append(resultado_dict)
    
    return {
        "total": len(resultados_enriquecidos),
        "resultados": resultados_enriquecidos
    }


@router.get("/productos/{id_producto}")
def obtener_producto_con_ubicacion(
    id_producto: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    db_producto = get_producto_by_id(db, id_producto, current_user.id_empresa)
    if not db_producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    # Obtener información del supervisor
    supervisor = db.query(UsuarioModel).filter(UsuarioModel.id_usuario == db_producto.id_usuario).first()
    
    punto = obtener_punto_por_producto(db, id_producto)
    punto_out = None
    if punto:
        punto_out = PuntoReposicionOut(
            id_punto=punto.id_punto,
            id_mueble=punto.id_mueble,
            nivel=punto.nivel,
            estanteria=punto.estanteria,
            producto=ProductoAsociado(
                nombre=db_producto.nombre,
                categoria=db_producto.categoria,
                unidad_tipo=db_producto.unidad_tipo,
                unidad_cantidad=db_producto.unidad_cantidad
            )
        )
    
    # Crear objeto producto enriquecido con información del supervisor
    producto_enriquecido = {
        "id_producto": db_producto.id_producto,
        "nombre": db_producto.nombre,
        "categoria": db_producto.categoria,
        "unidad_tipo": db_producto.unidad_tipo,
        "unidad_cantidad": db_producto.unidad_cantidad,
        "codigo_unico": db_producto.codigo_unico,
        "estado": db_producto.estado,
        "id_usuario": db_producto.id_usuario,
        "nombre_supervisor": supervisor.nombre if supervisor else None
    }
    
    return {
        "producto": producto_enriquecido,
        "ubicacion": punto_out
    }


@router.put("/productos/{id_producto}", response_model=ProductoOut)
def actualizar_producto(
    id_producto: int,
    producto_update: ProductoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    # Verificar permisos: administrador o supervisor propietario del producto
    if current_user.rol.nombre_rol not in [RolEnum.ADMINISTRADOR.value, RolEnum.SUPERVISOR.value]:
        raise HTTPException(status_code=403, detail="No tienes permisos para editar productos")
    
    db_producto = get_producto_by_id(db, id_producto, current_user.id_empresa)
    if not db_producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    # Si es supervisor, verificar que el producto le pertenece
    if current_user.rol.nombre_rol == RolEnum.SUPERVISOR.value:
        if db_producto.id_usuario != current_user.id_usuario:
            raise HTTPException(
                status_code=403, 
                detail="Solo puedes editar productos que te pertenecen"
            )
        # Los supervisores no pueden cambiar el id_usuario (supervisor asignado)
        if producto_update.id_usuario is not None and producto_update.id_usuario != current_user.id_usuario:
            raise HTTPException(
                status_code=403,
                detail="Los supervisores no pueden reasignar productos a otros supervisores"
            )
    
    # Si es administrador y se quiere cambiar id_usuario, validar que existe
    if producto_update.id_usuario is not None:
        nuevo_supervisor = db.query(UsuarioModel).filter(UsuarioModel.id_usuario == producto_update.id_usuario).first()
        if not nuevo_supervisor:
            raise HTTPException(
                status_code=404,
                detail="El supervisor especificado no existe"
            )
        # Verificar que el nuevo usuario sea supervisor
        if nuevo_supervisor.rol.nombre_rol != RolEnum.SUPERVISOR.value:
            raise HTTPException(
                status_code=400,
                detail="Solo se puede asignar productos a usuarios con rol de supervisor"
            )
    
    cambios = {}
    if producto_update.nombre is not None:
        cambios["nombre"] = producto_update.nombre
    if producto_update.categoria is not None:
        cambios["categoria"] = producto_update.categoria
    if producto_update.codigo_unico is not None:
        cambios["codigo_unico"] = producto_update.codigo_unico
    if producto_update.id_usuario is not None:
        cambios["id_usuario"] = producto_update.id_usuario
    if producto_update.unidad_tipo is not None:
        cambios["unidad_tipo"] = producto_update.unidad_tipo
    if producto_update.unidad_cantidad is not None:
        cambios["unidad_cantidad"] = producto_update.unidad_cantidad
    
    if not cambios:
        raise HTTPException(status_code=422, detail="No se proporcionaron campos válidos para actualizar")
    
    try:
        db_producto = update_producto(db, db_producto, **cambios)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return db_producto


@router.delete("/productos/{id_producto}", status_code=200)
def eliminar_producto(
    id_producto: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.rol.nombre_rol != RolEnum.ADMINISTRADOR.value:
        raise HTTPException(status_code=403, detail="Solo administradores pueden eliminar productos.")
    db_producto = get_producto_by_id(db, id_producto, current_user.id_empresa)
    if not db_producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    if producto_vinculado_a_tareas_activas(db, id_producto, ESTADOS_ACTIVOS):
        raise HTTPException(
            status_code=409,
            detail="Este producto no puede ser eliminado porque está vinculado a tareas activas de reposición."
        )
    db_producto.estado = "inactivo"
    db.commit()
    return {"detail": "Producto eliminado correctamente (soft delete)."}


@router.delete("/productos/{id_producto}/desasignar-punto")
def desasignar_punto_de_producto(
    id_producto: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.rol.nombre_rol not in [RolEnum.ADMINISTRADOR.value, RolEnum.SUPERVISOR.value]:
        raise HTTPException(status_code=403, detail="Solo administradores o supervisores pueden desasignar productos de puntos.")
    try:
        punto = desasignar_punto_por_producto(db, id_producto)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {
        "mensaje": "Producto desasignado del punto correctamente",
        "punto": {
            "id_punto": punto.id_punto,
            "id_mueble": punto.id_mueble,
            "nivel": punto.nivel,
            "estanteria": punto.estanteria,
            "producto": None
        }
    }


@router.put("/productos/{id_producto}/asignar-punto")
def asignar_punto_a_producto(
    id_producto: int,
    body: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.rol.nombre_rol.lower() not in ["administrador", "supervisor"]:
        raise HTTPException(status_code=403, detail="Solo administradores o supervisores pueden asociar productos a puntos.")
    id_punto = body.get("id_punto")
    if not id_punto:
        raise HTTPException(status_code=422, detail="El campo id_punto es obligatorio.")
    producto = get_producto_by_id(db, id_producto, current_user.id_empresa)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado.")
    try:
        punto = asignar_o_reasignar_producto_a_punto(db, id_producto, id_punto)
    except Exception as e:
        raise HTTPException(status_code=409, detail=str(e))
    # Obtener info de ubicación
    mueble = db.query(MuebleReposicion).filter(MuebleReposicion.id_mueble == punto.id_mueble).first()
    objeto = db.query(ObjetoMapa).filter(ObjetoMapa.id_objeto == mueble.id_objeto).first() if mueble else None
    ubicacion = db.query(UbicacionFisica).filter(UbicacionFisica.id_objeto == objeto.id_objeto).first() if objeto else None
    return {
        "mensaje": f"Producto '{producto.nombre}' asociado correctamente al punto {id_punto}.",
        "ubicacion": {
            "pasillo": objeto.nombre if objeto else None,
            "estanteria": punto.estanteria,
            "nivel": punto.nivel
        }
    }


@router.get("/productos/{id_producto}/ubicacion")
def obtener_ubicacion_de_producto(
    id_producto: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    producto = get_producto_by_id(db, id_producto, current_user.id_empresa)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado.")
    punto = obtener_ubicacion_producto(db, id_producto)
    if not punto:
        return {
            "producto": producto.nombre,
            "asignado": False,
            "mensaje": "Este producto aún no tiene una ubicación asignada."
        }
    mueble = db.query(MuebleReposicion).filter(MuebleReposicion.id_mueble == punto.id_mueble).first()
    objeto = db.query(ObjetoMapa).filter(ObjetoMapa.id_objeto == mueble.id_objeto).first() if mueble else None
    return {
        "producto": producto.nombre,
        "asignado": True,
        "ubicacion": {
            "id_punto": punto.id_punto,
            "pasillo": objeto.nombre if objeto else None,
            "estanteria": punto.estanteria,
            "nivel": punto.nivel
        }
    }


from fastapi import Security
from fastapi.security import OAuth2PasswordBearer
