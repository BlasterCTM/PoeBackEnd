from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Annotated, Optional

from app.api.dependencies.database import get_database
from app.api.dependencies.auth import get_current_user
from app.models.usuario import Usuario, RolEnum
from app.schemas.prediccion import (
    PrediccionRequest,
    PrediccionResponse,
    PrediccionHistorialResponse,
    ActualizarEstadoRequest,
    EstadoPrediccion
)
from app.services.prediccion_service import prediction_service


router = APIRouter(
    prefix="/predicciones",
    tags=["predicciones"]
)


@router.post(
    "/generar",
    response_model=PrediccionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generar predicción de reposiciones para un mes",
    description="""
    Genera una predicción ML de reposiciones para un mes específico.
    
    - **Requiere**: Rol Supervisor o Admin
    - **Usa**: Modelo RandomForest entrenado con datos históricos
    - **Devuelve**: Predicciones agregadas por categoría y semana
    
    Si ya existe una predicción para el período solicitado, se devuelve la existente.
    """
)
async def generar_prediccion(
    request: PrediccionRequest,
    db: Annotated[Session, Depends(get_database)],
    current_user: Annotated[Usuario, Depends(get_current_user)]
):
    """
    Endpoint para generar predicción de reposiciones.
    
    Args:
        request: Parámetros de la predicción (mes, año, opciones)
        db: Sesión de base de datos
        current_user: Usuario autenticado
        
    Returns:
        PrediccionResponse con resultados completos
        
    Raises:
        HTTPException 403: Si el usuario no tiene permisos
        HTTPException 500: Si ocurre error en el pipeline ML
    """
    # Validar permisos (solo Supervisor y Admin)
    if current_user.rol.nombre_rol not in [RolEnum.ADMINISTRADOR.value, RolEnum.SUPERVISOR.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo supervisores y administradores pueden generar predicciones"
        )
    
    try:
        prediccion = prediction_service.generar_prediccion_mes(
            db=db,
            id_empresa=current_user.id_empresa,
            id_usuario=current_user.id_usuario,
            request=request
        )
        return prediccion
    
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Modelo ML no disponible: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generando predicción: {str(e)}"
        )


@router.get(
    "/historial",
    response_model=PrediccionHistorialResponse,
    summary="Obtener historial de predicciones",
    description="""
    Devuelve el historial de todas las predicciones generadas por la empresa.
    
    - **Requiere**: Autenticación (cualquier rol)
    - **Soporta**: Paginación
    """
)
async def obtener_historial(
    db: Annotated[Session, Depends(get_database)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
    skip: int = Query(0, ge=0, description="Offset para paginación"),
    limit: int = Query(20, ge=1, le=100, description="Límite de resultados")
):
    """
    Endpoint para obtener historial de predicciones.
    
    Args:
        db: Sesión de base de datos
        current_user: Usuario autenticado
        skip: Offset para paginación
        limit: Límite de resultados
        
    Returns:
        PrediccionHistorialResponse con lista paginada
    """
    historial = prediction_service.obtener_historial(
        db=db,
        id_empresa=current_user.id_empresa,
        skip=skip,
        limit=limit
    )
    return historial


@router.get(
    "/{id_prediccion}",
    response_model=PrediccionResponse,
    summary="Obtener detalle de una predicción",
    description="""
    Devuelve los detalles completos de una predicción específica.
    
    - **Requiere**: Autenticación
    - **Validación**: Multi-tenant (solo predicciones de su empresa)
    """
)
async def obtener_prediccion(
    id_prediccion: int,
    db: Annotated[Session, Depends(get_database)],
    current_user: Annotated[Usuario, Depends(get_current_user)]
):
    """
    Endpoint para obtener detalle de predicción.
    
    Args:
        id_prediccion: ID de la predicción
        db: Sesión de base de datos
        current_user: Usuario autenticado
        
    Returns:
        PrediccionResponse con detalles completos
        
    Raises:
        HTTPException 404: Si la predicción no existe o no pertenece a la empresa
    """
    prediccion = prediction_service.obtener_prediccion(
        db=db,
        id_prediccion=id_prediccion,
        id_empresa=current_user.id_empresa
    )
    
    if not prediccion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Predicción {id_prediccion} no encontrada"
        )
    
    return prediccion


@router.patch(
    "/{id_prediccion}/estado",
    response_model=PrediccionResponse,
    summary="Actualizar estado de predicción",
    description="""
    Actualiza el estado de una predicción (pendiente → aplicado/rechazado).
    
    - **Requiere**: Rol Supervisor o Admin
    - **Estados**: pendiente, aplicado, rechazado
    """
)
async def actualizar_estado_prediccion(
    id_prediccion: int,
    request: ActualizarEstadoRequest,
    db: Annotated[Session, Depends(get_database)],
    current_user: Annotated[Usuario, Depends(get_current_user)]
):
    """
    Endpoint para actualizar estado de predicción.
    
    Args:
        id_prediccion: ID de la predicción
        request: Nuevo estado y notas
        db: Sesión de base de datos
        current_user: Usuario autenticado
        
    Returns:
        PrediccionResponse actualizada
        
    Raises:
        HTTPException 403: Si el usuario no tiene permisos
        HTTPException 404: Si la predicción no existe
    """
    # Validar permisos
    if current_user.rol.nombre_rol not in [RolEnum.ADMINISTRADOR.value, RolEnum.SUPERVISOR.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo supervisores y administradores pueden actualizar predicciones"
        )
    
    prediccion = prediction_service.actualizar_estado_prediccion(
        db=db,
        id_prediccion=id_prediccion,
        id_empresa=current_user.id_empresa,
        estado=request.estado,
        notas=request.notas
    )
    
    if not prediccion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Predicción {id_prediccion} no encontrada"
        )
    
    return prediccion
