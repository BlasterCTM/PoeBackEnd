from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.core.database.database import get_db
from app.schemas.cotizacion import (
    CotizacionCreate,
    CotizacionUpdate,
    CotizacionResponse,
    CotizacionListItem,
    CotizacionConvertir,
    CotizacionConvertidaResponse,
    CotizacionStats,
    EstadoCotizacion
)
from app.repositories.cotizacion import CotizacionRepository
from app.repositories.plan_empresa import PlanEmpresaRepository
from app.repositories.empresa import EmpresaRepository
from app.repositories.usuario import UsuarioRepository
from app.api.dependencies.auth import get_current_user
from app.models.usuario import Usuario
from app.utils.tenant import require_super_admin
from app.services.calculadora_precios import CalculadoraPreciosService

router = APIRouter()


# ============================================
# ENDPOINTS PÚBLICOS (Sin autenticación)
# ============================================

@router.post("/solicitar", response_model=CotizacionResponse, status_code=status.HTTP_201_CREATED)
def solicitar_cotizacion(
    cotizacion: CotizacionCreate,
    db: Session = Depends(get_db)
):
    """
    **ENDPOINT PÚBLICO** - Formulario "Cotiza Acá"
    
    Permite que cualquier persona solicite una cotización sin autenticación.
    Este es el formulario web público donde los potenciales clientes ingresan sus datos.
    """
    cotizacion_repo = CotizacionRepository()
    
    # Calcular precio sugerido automáticamente
    calculadora = CalculadoraPreciosService()
    cotizacion_calculada = calculadora.generar_cotizacion_completa(
        cantidad_supervisores=cotizacion.cantidad_supervisores,
        cantidad_reponedores=cotizacion.cantidad_reponedores,
        cantidad_productos=cotizacion.cantidad_productos,
        integraciones=cotizacion.integraciones_requeridas.split(",") if cotizacion.integraciones_requeridas else None,
        tiempo_servicio="mensual"  # Por defecto mensual
    )
    
    # Preparar datos
    cotizacion_data = cotizacion.model_dump()
    cotizacion_data["precio_sugerido"] = cotizacion_calculada["precio_sugerido"]
    cotizacion_data["features_sugeridos"] = cotizacion_calculada["features_sugeridos"]
    cotizacion_data["estado"] = "pendiente"
    
    # Calcular fecha de validez (30 días)
    cotizacion_data["fecha_validez"] = (datetime.utcnow() + timedelta(days=30)).date()
    
    # Crear cotización
    nueva_cotizacion = cotizacion_repo.create(db, cotizacion_data)
    
    # TODO: Enviar notificación por email al equipo POE
    # TODO: Enviar email de confirmación al solicitante
    
    return nueva_cotizacion


# ============================================
# ENDPOINTS PRIVADOS (SuperAdmin)
# ============================================

@router.get("/", response_model=List[CotizacionListItem])
def listar_cotizaciones(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    estado: Optional[EstadoCotizacion] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    **SUPERADMIN** - Lista todas las cotizaciones
    
    Permite filtrar por estado y paginar resultados.
    """
    require_super_admin(current_user)
    
    cotizacion_repo = CotizacionRepository()
    cotizaciones = cotizacion_repo.get_all(
        db, 
        skip=skip, 
        limit=limit,
        estado=estado.value if estado else None
    )
    
    return cotizaciones


@router.get("/pendientes", response_model=List[CotizacionListItem])
def listar_cotizaciones_pendientes(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    **SUPERADMIN** - Lista cotizaciones pendientes de revisión
    
    Muestra cotizaciones en estado 'pendiente' o 'en_revision'.
    """
    require_super_admin(current_user)
    
    cotizacion_repo = CotizacionRepository()
    return cotizacion_repo.get_pendientes(db)


@router.get("/estadisticas", response_model=CotizacionStats)
def obtener_estadisticas_cotizaciones(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    **SUPERADMIN** - Estadísticas de cotizaciones
    
    Retorna estadísticas generales: total, por estado, montos, tasa de conversión.
    """
    require_super_admin(current_user)
    
    cotizacion_repo = CotizacionRepository()
    return cotizacion_repo.get_stats(db)


@router.get("/{id_cotizacion}", response_model=CotizacionResponse)
def obtener_cotizacion(
    id_cotizacion: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    **SUPERADMIN** - Obtiene una cotización por ID
    """
    require_super_admin(current_user)
    
    cotizacion_repo = CotizacionRepository()
    cotizacion = cotizacion_repo.get_by_id(db, id_cotizacion)
    
    if not cotizacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cotización {id_cotizacion} no encontrada"
        )
    
    return cotizacion


@router.patch("/{id_cotizacion}", response_model=CotizacionResponse)
def actualizar_cotizacion(
    id_cotizacion: int,
    cotizacion_update: CotizacionUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    **SUPERADMIN** - Actualiza una cotización
    
    Permite actualizar precio, features, estado, notas internas, etc.
    """
    require_super_admin(current_user)
    
    cotizacion_repo = CotizacionRepository()
    
    # Verificar que existe
    cotizacion = cotizacion_repo.get_by_id(db, id_cotizacion)
    if not cotizacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cotización {id_cotizacion} no encontrada"
        )
    
    # Actualizar
    update_data = cotizacion_update.model_dump(exclude_unset=True)
    update_data["atendido_por"] = current_user.id_usuario
    
    cotizacion_actualizada = cotizacion_repo.update(db, id_cotizacion, update_data)
    
    return cotizacion_actualizada


@router.post("/{id_cotizacion}/cambiar-estado")
def cambiar_estado_cotizacion(
    id_cotizacion: int,
    nuevo_estado: EstadoCotizacion,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    **SUPERADMIN** - Cambia el estado de una cotizacion
    
    Estados: pendiente → en_revision → cotizada → negociacion → aprobada → rechazada
    """
    require_super_admin(current_user)
    
    cotizacion_repo = CotizacionRepository()
    
    cotizacion = cotizacion_repo.cambiar_estado(
        db, 
        id_cotizacion, 
        nuevo_estado.value,
        current_user.id_usuario
    )
    
    if not cotizacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cotización {id_cotizacion} no encontrada"
        )
    
    # TODO: Enviar notificación al solicitante según el nuevo estado
    
    return {
        "mensaje": f"Estado cambiado a '{nuevo_estado.value}'",
        "id_cotizacion": id_cotizacion,
        "nuevo_estado": nuevo_estado.value
    }


@router.post("/{id_cotizacion}/convertir", response_model=CotizacionConvertidaResponse)
def convertir_cotizacion_en_cliente(
    id_cotizacion: int,
    conversion_data: CotizacionConvertir,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    **SUPERADMIN** - Convierte una cotización en empresa + plan + usuario admin
    
    Este es el paso final del flujo:
    1. Crea la empresa
    2. Crea el plan personalizado
    3. Crea el usuario administrador
    4. Marca la cotización como convertida
    """
    require_super_admin(current_user)
    
    cotizacion_repo = CotizacionRepository()
    empresa_repo = EmpresaRepository()
    plan_repo = PlanEmpresaRepository()
    usuario_repo = UsuarioRepository()
    
    # Validar que la cotización existe y está aprobada
    cotizacion = cotizacion_repo.get_by_id(db, id_cotizacion)
    if not cotizacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cotización {id_cotizacion} no encontrada"
        )
    
    if cotizacion.estado not in ["aprobada", "cotizada"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La cotización debe estar en estado 'aprobada' o 'cotizada' para convertirse. Estado actual: '{cotizacion.estado}'"
        )
    
    # Validar que no exista el RUT
    if empresa_repo.existe_rut(db, conversion_data.rut_empresa):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe una empresa con el RUT {conversion_data.rut_empresa}"
        )
    
    # Validar que no exista el email del admin
    if usuario_repo.get_by_email(db, conversion_data.admin_correo):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un usuario con el correo {conversion_data.admin_correo}"
        )
    
    try:
        # 1. Crear empresa
        from app.schemas.empresa import EmpresaCreate
        
        empresa_data = EmpresaCreate(
            nombre_empresa=conversion_data.nombre_empresa,
            rut_empresa=conversion_data.rut_empresa,
            direccion=conversion_data.direccion,
            ciudad=conversion_data.ciudad,
            region=conversion_data.region
        )
        nueva_empresa = empresa_repo.create_empresa(db, empresa_data)
        
        # 2. Crear plan personalizado
        plan_data = {
            "id_empresa": nueva_empresa.id_empresa,
            "cantidad_supervisores": conversion_data.cantidad_supervisores,
            "cantidad_reponedores": conversion_data.cantidad_reponedores,
            "cantidad_productos": conversion_data.cantidad_productos,
            "cantidad_puntos": conversion_data.cantidad_puntos,
            "precio_mensual": conversion_data.precio_mensual,
            "features": conversion_data.features,
            "fecha_inicio": conversion_data.fecha_inicio or datetime.utcnow().date(),
            "fecha_vencimiento": conversion_data.fecha_vencimiento,
            "activo": True,
            "creado_por": current_user.id_usuario
        }
        nuevo_plan = plan_repo.create(db, plan_data)
        
        # 3. Crear usuario administrador
        rol_admin = usuario_repo.get_rol_by_nombre(db, "Administrador")
        if not rol_admin:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error: Rol 'Administrador' no encontrado"
            )
        
        nuevo_admin = usuario_repo.create_usuario(
            db=db,
            nombre=conversion_data.admin_nombre,
            correo=conversion_data.admin_correo,
            contraseña=conversion_data.admin_contraseña,
            rol_id=rol_admin.id_rol,
            id_empresa=nueva_empresa.id_empresa
        )
        
        # 4. Marcar cotización como convertida
        cotizacion_repo.marcar_convertida(
            db,
            id_cotizacion,
            nueva_empresa.id_empresa,
            nuevo_plan.id_plan
        )
        
        # TODO: Enviar email al nuevo admin con credenciales
        # TODO: Enviar email de bienvenida
        
        return CotizacionConvertidaResponse(
            mensaje="Cotización convertida exitosamente en cliente",
            id_cotizacion=id_cotizacion,
            id_empresa=nueva_empresa.id_empresa,
            id_plan=nuevo_plan.id_plan,
            id_usuario_admin=nuevo_admin.id_usuario,
            empresa={
                "id_empresa": nueva_empresa.id_empresa,
                "nombre_empresa": nueva_empresa.nombre_empresa,
                "rut_empresa": nueva_empresa.rut_empresa
            },
            plan={
                "id_plan": nuevo_plan.id_plan,
                "precio_mensual": nuevo_plan.precio_mensual
            },
            admin={
                "id_usuario": nuevo_admin.id_usuario,
                "nombre": nuevo_admin.nombre,
                "correo": nuevo_admin.correo
            }
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al convertir cotización: {str(e)}"
        )
