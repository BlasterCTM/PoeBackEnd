from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated, Union, Optional
from app.api.dependencies.database import get_database
from app.schemas.usuario import (
    UsuarioCreate, UsuarioResponse, Token, LoginSchema, 
    LoginResponse, ListaUsuariosResponse, UsuarioOutListado, 
    UsuarioUpdate, UsuarioEstadoUpdate, UsuarioPerfilOut
)
from app.repositories.usuario import UsuarioRepository
from app.core.security.auth import create_access_token, get_current_admin_user, get_current_user
from app.core.security.password import verify_password
from datetime import timedelta
from app.core.config.settings import settings
from app.models.usuario import Usuario, RolEnum

router = APIRouter(
    prefix="/usuarios",
    tags=["usuarios"]
)

@router.post(
    "/",
    response_model=UsuarioResponse,
    status_code=status.HTTP_201_CREATED,
    description="Crear un nuevo usuario (requiere ser administrador)"
)
async def crear_usuario(
    usuario: UsuarioCreate,
    db: Annotated[Session, Depends(get_database)],
    _: Annotated[dict, Depends(get_current_admin_user)]
):
    # Inicializar el repositorio
    usuario_repo = UsuarioRepository()
    
    try:
        print(f"Intentando crear usuario: {usuario.nombre} con rol {usuario.rol.value}")
        
        # Verificar si el correo ya existe
        if usuario_repo.get_by_email(db, usuario.correo):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El correo electrónico ya está registrado"
            )
        
        # Obtener el ID del rol correspondiente
        rol = usuario_repo.get_rol_by_nombre(db, usuario.rol.value)
        print(f"Rol encontrado: {rol.id_rol if rol else 'No encontrado'}")
        
        if not rol:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El rol {usuario.rol.value} no existe"
            )
        
        # Crear el usuario
        nuevo_usuario = usuario_repo.create_usuario(
            db=db,
            nombre=usuario.nombre,
            correo=usuario.correo,
            contraseña=usuario.contraseña,
            rol_id=rol.id_rol
        )
        print(f"Usuario creado exitosamente con ID: {nuevo_usuario.id_usuario}")
        
        return UsuarioResponse(
            mensaje="Usuario creado exitosamente",
            usuario=nuevo_usuario
        )
    except HTTPException as e:
        print(f"Error HTTP: {e.detail}")
        raise e
    except Exception as e:
        print(f"Error al crear usuario: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear el usuario: {str(e)}"
        )

@router.post("/token", response_model=LoginResponse)
async def login_for_access_token(
    login_data: LoginSchema,
    db: Session = Depends(get_database)
):
    try:
        # Buscar usuario por correo
        usuario_repo = UsuarioRepository()
        usuario = usuario_repo.get_by_email(db, login_data.correo)
        
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error_type": "not_found",
                    "message": "El correo electrónico no está registrado",
                    "detail": "No se encontró una cuenta con este correo electrónico"
                }
            )
        
        # Verificar si el usuario está activo
        if usuario.estado != "activo":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error_type": "inactive",
                    "message": "La cuenta no está activa",
                    "detail": "Esta cuenta ha sido desactivada. Contacte al administrador."
                }
            )
        
        # Verificar contraseña
        if not verify_password(login_data.contraseña, usuario.contraseña):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error_type": "invalid_password",
                    "message": "La contraseña es incorrecta",
                    "detail": "La contraseña proporcionada no es válida"
                }
            )
        
        # Obtener el rol del usuario
        rol = usuario_repo.get_rol_by_id(db, usuario.rol_id)
        if not rol:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al obtener el rol del usuario"
            )
        
        # Crear token de acceso
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "sub": usuario.correo,
                "rol": rol.nombre_rol
            }, 
            expires_delta=access_token_expires
        )
        
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user_info={
                "id": str(usuario.id_usuario),
                "nombre": usuario.nombre,
                "correo": usuario.correo,
                "rol": rol.nombre_rol,
                "estado": usuario.estado
            }
        )
            
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error en login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_type": "server_error",
                "message": "Error interno del servidor",
                "detail": str(e)
            }
        )

@router.get(
    "/",
    response_model=ListaUsuariosResponse,
    status_code=status.HTTP_200_OK,
    description="Listar todos los usuarios (requiere ser administrador)"
)
async def listar_usuarios(
    nombre: Optional[str] = None,
    rol: Optional[str] = None,
    db: Session = Depends(get_database),
    current_user: Usuario = Depends(get_current_admin_user)
):
    try:
        # Verificar que el rol sea válido si se proporciona
        if rol and rol not in [r.value for r in RolEnum]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Rol inválido. Roles permitidos: {', '.join([r.value for r in RolEnum])}"
            )
        
        # Obtener usuarios
        usuario_repo = UsuarioRepository()
        usuarios = usuario_repo.listar_usuarios(db, nombre, rol)
        
        if not usuarios:
            return ListaUsuariosResponse(
                total=0,
                usuarios=[],
                mensaje="No se encontraron usuarios con los filtros especificados."
            )
        
        # Transformar los usuarios a su formato de salida
        usuarios_response = []
        for usuario in usuarios:
            rol = usuario_repo.get_rol_by_id(db, usuario.rol_id)
            usuarios_response.append(
                UsuarioOutListado(
                    id_usuario=usuario.id_usuario,
                    nombre=usuario.nombre,
                    correo=usuario.correo,
                    rol=rol.nombre_rol if rol else "Sin rol",
                    estado=usuario.estado
                )
            )
        
        return ListaUsuariosResponse(
            total=len(usuarios_response),
            usuarios=usuarios_response,
            mensaje="Usuarios listados exitosamente"
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error al listar usuarios: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al listar usuarios"
        )

@router.put(
    "/{usuario_id}",
    response_model=UsuarioResponse,
    status_code=status.HTTP_200_OK,
    description="Actualizar datos de un usuario (requiere ser administrador)"
)
async def actualizar_usuario(
    usuario_id: int,
    usuario_update: UsuarioUpdate,
    db: Session = Depends(get_database),
    current_user: Usuario = Depends(get_current_admin_user)
):
    try:
        # Obtener el usuario a actualizar
        usuario_repo = UsuarioRepository()
        usuario = usuario_repo.get_usuario_by_id(db, usuario_id)
        
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No se encontró el usuario con ID: {usuario_id}"
            )

        # Preparar los datos para la actualización
        update_data = {}
        
        if usuario_update.nombre is not None:
            update_data["nombre"] = usuario_update.nombre
            
        if usuario_update.correo is not None:
            update_data["correo"] = usuario_update.correo
            
        if usuario_update.rol is not None:
            # Obtener el ID del nuevo rol
            nuevo_rol = usuario_repo.get_rol_by_nombre(db, usuario_update.rol.value)
            if not nuevo_rol:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El rol {usuario_update.rol.value} no existe"
                )
            update_data["rol_id"] = nuevo_rol.id_rol

        try:
            # Actualizar el usuario
            usuario_actualizado = usuario_repo.update_usuario(
                db=db,
                usuario=usuario,
                **update_data
            )
            
            return UsuarioResponse(
                mensaje="Usuario actualizado exitosamente",
                usuario=usuario_actualizado
            )
            
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )
            
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error al actualizar usuario: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al actualizar usuario"
        )

@router.patch(
    "/{usuario_id}/estado",
    response_model=UsuarioResponse,
    status_code=status.HTTP_200_OK,
    description="Activar o desactivar un usuario (requiere ser administrador)"
)
async def actualizar_estado_usuario(
    usuario_id: int,
    estado_update: UsuarioEstadoUpdate,
    db: Session = Depends(get_database),
    current_user: Usuario = Depends(get_current_admin_user)
):
    try:
        # Obtener el usuario a actualizar
        usuario_repo = UsuarioRepository()
        usuario = usuario_repo.get_usuario_by_id(db, usuario_id)
        
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No se encontró el usuario con ID: {usuario_id}"
            )

        # No permitir que un administrador se desactive a sí mismo
        if usuario.id_usuario == current_user.id_usuario:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No puedes cambiar tu propio estado"
            )

        # Verificar si el estado es diferente al actual
        if usuario.estado == estado_update.estado:
            return UsuarioResponse(
                mensaje=f"El usuario ya se encuentra {estado_update.estado}",
                usuario=usuario
            )

        try:
            # Actualizar el estado
            usuario_actualizado = usuario_repo.update_estado(
                db=db,
                usuario=usuario,
                estado=estado_update.estado
            )
            
            mensaje = "Usuario activado correctamente" if estado_update.estado == "activo" else "Usuario desactivado correctamente"
            
            return UsuarioResponse(
                mensaje=mensaje,
                usuario=usuario_actualizado
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al actualizar el estado del usuario: {str(e)}"
            )
            
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error al actualizar estado de usuario: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al actualizar estado del usuario"
        )

@router.get(
    "/me",
    response_model=UsuarioPerfilOut,
    status_code=status.HTTP_200_OK,
    description="Obtener el perfil del usuario autenticado"
)
async def obtener_perfil(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    try:
        usuario_repo = UsuarioRepository()
        rol = usuario_repo.get_rol_by_id(db, current_user.rol_id)
        
        if not rol:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al obtener el rol del usuario"
            )
        
        return UsuarioPerfilOut(
            nombre=current_user.nombre,
            correo=current_user.correo,
            rol=rol.nombre_rol,
            estado=current_user.estado
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error al obtener perfil: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener el perfil"
        )
