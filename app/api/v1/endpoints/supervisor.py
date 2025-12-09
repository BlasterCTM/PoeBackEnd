from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated, List
from app.api.dependencies.database import get_database
from app.schemas.usuario import (
    ReponedorCreate, UsuarioResponse, ReponedorListado, 
    ReponedoresResponse, ReponedoresDisponiblesResponse
)
from app.repositories.usuario import UsuarioRepository
from app.repositories.supervision import SupervisionRepository
from app.core.security.auth import get_current_user
from app.models.usuario import RolEnum, Usuario
from app.api.dependencies.plan_limites import validar_limite_plan
from app.utils.tenant import is_super_admin

router = APIRouter(
    prefix="/supervisor",
    tags=["supervisor"]
)

@router.post(
    "/reponedores",
    response_model=UsuarioResponse,
    status_code=status.HTTP_201_CREATED,
    description="Registrar un nuevo reponedor (requiere ser supervisor)"
)
async def registrar_reponedor(
    reponedor: ReponedorCreate,
    db: Annotated[Session, Depends(get_database)],
    current_user: Annotated[Usuario, Depends(get_current_user)]
):
    # Verificar que el usuario sea supervisor
    usuario_repo = UsuarioRepository()
    rol_supervisor = usuario_repo.get_rol_by_nombre(db, RolEnum.SUPERVISOR.value)
    
    if current_user.rol_id != rol_supervisor.id_rol:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Solo los supervisores pueden registrar reponedores"
        )
    
    # Verificar si el correo ya existe EN LA EMPRESA
    if usuario_repo.get_by_email(db, reponedor.correo, current_user.id_empresa):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El correo electrónico ya está registrado en esta empresa"
        )
    
    # Obtener el rol de reponedor
    rol_reponedor = usuario_repo.get_rol_by_nombre(db, RolEnum.REPONEDOR.value)
    if not rol_reponedor:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener el rol de reponedor"
        )
    
    # Validar límites del plan antes de crear reponedor
    if not is_super_admin(current_user):
        validar_limite_plan("reponedores", current_user.id_empresa, db)
    
    try:
        # Crear el reponedor con rol predefinido Y LA EMPRESA DEL SUPERVISOR
        nuevo_reponedor = usuario_repo.create_usuario(
            db=db,
            nombre=reponedor.nombre,
            correo=reponedor.correo,
            contraseña=reponedor.contraseña,
            rol_id=rol_reponedor.id_rol,
            id_empresa=current_user.id_empresa
        )
        
        # Asignar automáticamente el reponedor al supervisor actual
        supervision_repo = SupervisionRepository()
        supervision_repo.asignar_reponedor(
            db, 
            supervisor_id=current_user.id_usuario, 
            reponedor_id=nuevo_reponedor.id_usuario,
            id_empresa=current_user.id_empresa
        )
        
        return UsuarioResponse(
            mensaje="Reponedor registrado y asignado exitosamente",
            usuario=nuevo_reponedor
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear el reponedor: {str(e)}"
        )

@router.get(
    "/reponedores",
    response_model=ReponedoresResponse,
    status_code=status.HTTP_200_OK,
    description="Obtener la lista de reponedores asignados al supervisor"
)
async def listar_reponedores(
    db: Annotated[Session, Depends(get_database)],
    current_user: Annotated[Usuario, Depends(get_current_user)]
):
    # Verificar que el usuario sea supervisor
    usuario_repo = UsuarioRepository()
    rol_supervisor = usuario_repo.get_rol_by_nombre(db, RolEnum.SUPERVISOR.value)
    
    if current_user.rol_id != rol_supervisor.id_rol:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Solo los supervisores pueden ver sus reponedores asignados"
        )
    
    try:
        supervision_repo = SupervisionRepository()
        reponedores = supervision_repo.get_reponedores_by_supervisor(
            db, 
            current_user.id_usuario,
            current_user.id_empresa
        )
        
        if not reponedores:
            return ReponedoresResponse(
                total=0,
                reponedores=[],
                mensaje="No tienes reponedores asignados"
            )
        
        # Transformar los reponedores a su formato de salida
        reponedores_response = [
            ReponedorListado(
                id=reponedor.id_usuario,
                nombre=reponedor.nombre,
                correo=reponedor.correo,
                estado=reponedor.estado
            ) for reponedor in reponedores
        ]
        
        return ReponedoresResponse(
            total=len(reponedores_response),
            reponedores=reponedores_response,
            mensaje="Reponedores listados exitosamente"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al listar reponedores: {str(e)}"
        )

@router.get(
    "/reponedores/disponibles",
    response_model=ReponedoresDisponiblesResponse,
    status_code=status.HTTP_200_OK,
    description="Obtener la lista de reponedores disponibles para asignar"
)
async def listar_reponedores_disponibles(
    db: Annotated[Session, Depends(get_database)],
    current_user: Annotated[Usuario, Depends(get_current_user)]
):
    # Verificar que el usuario sea supervisor
    usuario_repo = UsuarioRepository()
    rol_supervisor = usuario_repo.get_rol_by_nombre(db, RolEnum.SUPERVISOR.value)
    
    if current_user.rol_id != rol_supervisor.id_rol:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Solo los supervisores pueden ver reponedores disponibles"
        )
    
    try:
        supervision_repo = SupervisionRepository()
        reponedores = supervision_repo.get_reponedores_disponibles(db, current_user.id_empresa)
        
        if not reponedores:
            return ReponedoresDisponiblesResponse(
                total=0,
                reponedores=[],
                mensaje="No hay reponedores disponibles para asignar"
            )
        
        # Transformar los reponedores a su formato de salida
        reponedores_response = [
            ReponedorListado(
                id=reponedor.id_usuario,
                nombre=reponedor.nombre,
                correo=reponedor.correo,
                estado=reponedor.estado
            ) for reponedor in reponedores
        ]
        
        return ReponedoresDisponiblesResponse(
            total=len(reponedores_response),
            reponedores=reponedores_response,
            mensaje="Reponedores disponibles listados exitosamente"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al listar reponedores disponibles: {str(e)}"
        )

@router.post(
    "/reponedores/{reponedor_id}/asignar",
    response_model=UsuarioResponse,
    status_code=status.HTTP_200_OK,
    description="Asignar un reponedor al supervisor"
)
async def asignar_reponedor(
    reponedor_id: int,
    db: Annotated[Session, Depends(get_database)],
    current_user: Annotated[Usuario, Depends(get_current_user)]
):
    # Verificar que el usuario sea supervisor
    usuario_repo = UsuarioRepository()
    rol_supervisor = usuario_repo.get_rol_by_nombre(db, RolEnum.SUPERVISOR.value)
    
    if current_user.rol_id != rol_supervisor.id_rol:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Solo los supervisores pueden asignar reponedores"
        )
    
    try:
        # Verificar que el reponedor exista y esté disponible
        supervision_repo = SupervisionRepository()
        reponedor = usuario_repo.get_usuario_by_id(db, reponedor_id)
        
        if not reponedor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reponedor no encontrado"
            )
            
        # Verificar que sea un reponedor
        rol_reponedor = usuario_repo.get_rol_by_nombre(db, RolEnum.REPONEDOR.value)
        if reponedor.rol_id != rol_reponedor.id_rol:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El usuario seleccionado no es un reponedor"
            )
            
        # Verificar que no esté asignado a otro supervisor
        if supervision_repo.get_supervisor_of_reponedor(db, reponedor_id, current_user.id_empresa):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este reponedor ya está asignado a otro supervisor"
            )
        
        # Asignar el reponedor
        supervision_repo.asignar_reponedor(
            db=db,
            supervisor_id=current_user.id_usuario,
            reponedor_id=reponedor_id,
            id_empresa=current_user.id_empresa
        )
        
        return UsuarioResponse(
            mensaje="Reponedor asignado exitosamente",
            usuario=reponedor
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al asignar reponedor: {str(e)}"
        )

@router.delete(
    "/reponedores/{reponedor_id}/desasignar",
    response_model=UsuarioResponse,
    status_code=status.HTTP_200_OK,
    description="Desasignar un reponedor del supervisor"
)
async def desasignar_reponedor(
    reponedor_id: int,
    db: Annotated[Session, Depends(get_database)],
    current_user: Annotated[Usuario, Depends(get_current_user)]
):
    # Verificar que el usuario sea supervisor
    usuario_repo = UsuarioRepository()
    rol_supervisor = usuario_repo.get_rol_by_nombre(db, RolEnum.SUPERVISOR.value)
    
    if current_user.rol_id != rol_supervisor.id_rol:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Solo los supervisores pueden desasignar reponedores"
        )
    
    try:
        supervision_repo = SupervisionRepository()
        reponedor = usuario_repo.get_usuario_by_id(db, reponedor_id)
        
        if not reponedor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reponedor no encontrado"
            )
        
        # Verificar que el reponedor esté asignado a este supervisor
        supervisor = supervision_repo.get_supervisor_of_reponedor(db, reponedor_id, current_user.id_empresa)
        if not supervisor or supervisor.id_usuario != current_user.id_usuario:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este reponedor no está asignado a tu supervisión"
            )
        
        # Desasignar el reponedor
        supervision_repo.desasignar_reponedor(
            db, 
            current_user.id_usuario, 
            reponedor_id,
            current_user.id_empresa
        )
        
        return UsuarioResponse(
            mensaje="Reponedor desasignado exitosamente",
            usuario=reponedor
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al desasignar reponedor: {str(e)}"
        )

@router.get(
    "/productos",
    status_code=status.HTTP_200_OK,
    description="Obtener todos los productos asociados al supervisor"
)
async def listar_productos_supervisor(
    db: Annotated[Session, Depends(get_database)],
    current_user: Annotated[Usuario, Depends(get_current_user)]
):
    """
    Endpoint para que el supervisor visualice todos los productos que tiene asociados.
    Incluye información del supervisor: ID, nombre, correo y rol.
    """
    # Verificar que el usuario sea supervisor
    usuario_repo = UsuarioRepository()
    rol_supervisor = usuario_repo.get_rol_by_nombre(db, RolEnum.SUPERVISOR.value)
    
    if current_user.rol_id != rol_supervisor.id_rol:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Solo los supervisores pueden acceder a este recurso"
        )
    
    try:
        from app.models.producto import Producto
        
        # Información del supervisor
        supervisor_info = {
            "id": current_user.id_usuario,
            "nombre": current_user.nombre,
            "correo": current_user.correo,
            "rol": RolEnum.SUPERVISOR.value
        }
        
        # Obtener productos asociados al supervisor
        productos_asociados = db.query(Producto).filter(
            Producto.id_usuario == current_user.id_usuario
        ).all()
        
        # Formatear productos
        productos_info = []
        for producto in productos_asociados:
            productos_info.append({
                "id_producto": producto.id_producto,
                "nombre": producto.nombre,
                "categoria": producto.categoria,
                "unidad_tipo": producto.unidad_tipo,
                "unidad_cantidad": producto.unidad_cantidad
            })
        
        return {
            "supervisor": supervisor_info,
            "total_productos": len(productos_info),
            "productos": productos_info
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener los productos del supervisor: {str(e)}"
        )

@router.get(
    "/productos/{id_producto}",
    status_code=status.HTTP_200_OK,
    description="Obtener un producto específico del supervisor"
)
async def obtener_producto_supervisor(
    id_producto: int,
    db: Annotated[Session, Depends(get_database)],
    current_user: Annotated[Usuario, Depends(get_current_user)]
):
    """
    Obtener detalles de un producto específico asociado al supervisor.
    """
    # Verificar que el usuario sea supervisor
    usuario_repo = UsuarioRepository()
    rol_supervisor = usuario_repo.get_rol_by_nombre(db, RolEnum.SUPERVISOR.value)
    
    if current_user.rol_id != rol_supervisor.id_rol:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Solo los supervisores pueden acceder a este recurso"
        )
    
    try:
        from app.models.producto import Producto
        
        # Obtener el producto verificando que pertenezca al supervisor
        producto = db.query(Producto).filter(
            Producto.id_producto == id_producto,
            Producto.id_usuario == current_user.id_usuario
        ).first()
        
        if not producto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Producto no encontrado o no tienes permisos para verlo"
            )
        
        return {
            "id_producto": producto.id_producto,
            "nombre": producto.nombre,
            "categoria": producto.categoria,
            "unidad_tipo": producto.unidad_tipo,
            "unidad_cantidad": producto.unidad_cantidad,
            "supervisor": {
                "id": current_user.id_usuario,
                "nombre": current_user.nombre,
                "correo": current_user.correo,
                "rol": RolEnum.SUPERVISOR.value
            }
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener el producto: {str(e)}"
        )

@router.put(
    "/productos/{id_producto}",
    status_code=status.HTTP_200_OK,
    description="Editar un producto del supervisor"
)
async def editar_producto_supervisor(
    id_producto: int,
    producto_data: dict,
    db: Annotated[Session, Depends(get_database)],
    current_user: Annotated[Usuario, Depends(get_current_user)]
):
    """
    Endpoint para que el supervisor pueda editar los productos que tiene asociados.
    """
    # Verificar que el usuario sea supervisor
    usuario_repo = UsuarioRepository()
    rol_supervisor = usuario_repo.get_rol_by_nombre(db, RolEnum.SUPERVISOR.value)
    
    if current_user.rol_id != rol_supervisor.id_rol:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Solo los supervisores pueden editar productos"
        )
    
    try:
        from app.models.producto import Producto
        
        # Verificar que el producto existe y pertenece al supervisor
        producto = db.query(Producto).filter(
            Producto.id_producto == id_producto,
            Producto.id_usuario == current_user.id_usuario
        ).first()
        
        if not producto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Producto no encontrado o no tienes permisos para editarlo"
            )
        
        # Validar y actualizar campos
        if "nombre" in producto_data and producto_data["nombre"]:
            producto.nombre = producto_data["nombre"]
        
        if "categoria" in producto_data and producto_data["categoria"]:
            producto.categoria = producto_data["categoria"]
        
        if "unidad_tipo" in producto_data and producto_data["unidad_tipo"]:
            producto.unidad_tipo = producto_data["unidad_tipo"]
        
        if "unidad_cantidad" in producto_data and producto_data["unidad_cantidad"] is not None:
            if producto_data["unidad_cantidad"] <= 0:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="La cantidad de unidad debe ser mayor a 0"
                )
            producto.unidad_cantidad = producto_data["unidad_cantidad"]
        
        # Guardar cambios
        db.commit()
        db.refresh(producto)
        
        return {
            "mensaje": "Producto actualizado exitosamente",
            "producto": {
                "id_producto": producto.id_producto,
                "nombre": producto.nombre,
                "categoria": producto.categoria,
                "unidad_tipo": producto.unidad_tipo,
                "unidad_cantidad": producto.unidad_cantidad
            },
            "supervisor": {
                "id": current_user.id_usuario,
                "nombre": current_user.nombre,
                "correo": current_user.correo,
                "rol": RolEnum.SUPERVISOR.value
            }
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar el producto: {str(e)}"
        )
