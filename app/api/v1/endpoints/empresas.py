from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database.database import get_db
from app.schemas.empresa import (
    EmpresaCreate, 
    EmpresaResponse, 
    EmpresaUpdate,
    EmpresaRegistroRequest,
    EmpresaRegistroResponse
)
from app.repositories.empresa import EmpresaRepository
from app.repositories.usuario import UsuarioRepository
from app.api.dependencies.auth import get_current_user
from app.models.usuario import Usuario, RolEnum
from app.utils.tenant import (
    validate_tenant_access, 
    get_tenant_filter,
    is_super_admin
)

router = APIRouter()

@router.post("/registro", response_model=EmpresaRegistroResponse, status_code=status.HTTP_201_CREATED)
def registrar_empresa(
    registro: EmpresaRegistroRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Registrar nueva empresa con su usuario administrador (Solo SuperAdmin o Administrador).
    
    Este endpoint crea:
    1. Una nueva empresa en el sistema
    2. Un usuario administrador asociado a esa empresa
    
    **Requiere autenticación como SuperAdmin o Administrador.**
    """
    # Validar que sea SuperAdmin o Administrador
    if current_user.rol.nombre_rol not in [RolEnum.SUPERADMIN.value, RolEnum.ADMINISTRADOR.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo SuperAdmin o Administradores pueden registrar nuevas empresas"
        )
    
    # Validar que no exista el RUT
    if EmpresaRepository.existe_rut(db, registro.empresa.rut_empresa):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe una empresa con el RUT {registro.empresa.rut_empresa}"
        )
    
    # Validar que no exista el correo del admin
    usuario_repo = UsuarioRepository()
    if usuario_repo.get_by_email(db, registro.admin_correo):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un usuario con el correo {registro.admin_correo}"
        )
    
    try:
        # Crear la empresa
        nueva_empresa = EmpresaRepository.create_empresa(db, registro.empresa)
        
        # Obtener el rol de Administrador
        rol_admin = usuario_repo.get_rol_by_nombre(db, "Administrador")
        
        if not rol_admin:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error: Rol 'Administrador' no encontrado en el sistema"
            )
        
        # Crear el usuario administrador de la empresa
        nuevo_admin = usuario_repo.create_usuario(
            db=db,
            nombre=registro.admin_nombre,
            correo=registro.admin_correo,
            contraseña=registro.admin_contraseña,
            rol_id=rol_admin.id_rol,
            id_empresa=nueva_empresa.id_empresa
        )
        
        # TODO: Enviar email con credenciales al nuevo administrador
        
        return EmpresaRegistroResponse(
            mensaje="Empresa registrada exitosamente",
            empresa={
                "id_empresa": nueva_empresa.id_empresa,
                "nombre_empresa": nueva_empresa.nombre_empresa,
                "rut_empresa": nueva_empresa.rut_empresa,
                "ciudad": nueva_empresa.ciudad,
                "region": nueva_empresa.region,
                "estado": nueva_empresa.estado
            },
            administrador={
                "id_usuario": nuevo_admin.id_usuario,
                "nombre": nuevo_admin.nombre,
                "correo": nuevo_admin.correo,
                "rol": nuevo_admin.rol.nombre_rol
            }
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al registrar empresa: {str(e)}"
        )

@router.get("/", response_model=List[EmpresaResponse])
def listar_empresas(
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(100, ge=1, le=500, description="Número máximo de registros"),
    estado: Optional[str] = Query(None, pattern="^(activo|inactivo)$", description="Filtrar por estado"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Listar empresas.
    
    - SuperAdmin: Ve todas las empresas
    - Administrador: Solo ve su propia empresa
    - Otros roles: Solo ven su propia empresa
    
    Permite paginación y filtrado por estado.
    """
    # SuperAdmin puede ver todas las empresas
    if is_super_admin(current_user):
        empresas = EmpresaRepository.get_all(db, skip=skip, limit=limit, estado=estado)
    else:
        # Usuarios normales solo ven su empresa
        empresa = EmpresaRepository.get_by_id(db, current_user.id_empresa)
        if not empresa:
            return []
        
        # Aplicar filtro de estado si existe
        if estado and empresa.estado != estado:
            return []
        
        empresas = [empresa]
    
    return empresas

@router.get("/mi-empresa", response_model=EmpresaResponse)
def obtener_mi_empresa(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtener información de la empresa del usuario autenticado.
    
    - SuperAdmin: Puede ver todas las empresas usando GET /empresas/
    - Otros usuarios: Ven solo su propia empresa
    """
    # Si es SuperAdmin, sugerir usar el endpoint correcto
    if is_super_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Como SuperAdmin, use GET /empresas/ para ver todas las empresas o GET /empresas/{id} para una específica"
        )
    
    empresa = EmpresaRepository.get_by_id(db, current_user.id_empresa)
    
    if not empresa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa no encontrada"
        )
    
    return empresa

@router.get("/{id_empresa}", response_model=EmpresaResponse)
def obtener_empresa(
    id_empresa: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtener información de una empresa específica.
    
    - SuperAdmin: Puede ver cualquier empresa
    - Otros roles: Solo pueden ver su propia empresa
    """
    empresa = EmpresaRepository.get_by_id(db, id_empresa)
    
    if not empresa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa no encontrada"
        )
    
    # Validar acceso multi-tenant
    validate_tenant_access(current_user, id_empresa, "ver esta empresa")
    
    return empresa

@router.patch("/{id_empresa}", response_model=EmpresaResponse)
def actualizar_empresa(
    id_empresa: int,
    empresa_data: EmpresaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Actualizar información de una empresa.
    
    - SuperAdmin: Puede modificar cualquier empresa
    - Administrador: Solo puede modificar su propia empresa
    """
    # Validar acceso multi-tenant
    validate_tenant_access(current_user, id_empresa, "modificar esta empresa")
    
    # Verificar que sea administrador (o SuperAdmin)
    if not is_super_admin(current_user) and current_user.rol.nombre_rol != RolEnum.ADMINISTRADOR.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden modificar datos de empresas"
        )
    
    try:
        empresa = EmpresaRepository.update_empresa(db, id_empresa, empresa_data)
        
        if not empresa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Empresa no encontrada"
            )
        
        return empresa
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/{id_empresa}", status_code=status.HTTP_200_OK)
def desactivar_empresa(
    id_empresa: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Desactivar una empresa (soft delete).
    
    - SuperAdmin: Puede desactivar cualquier empresa
    - Administrador: Puede desactivar solo su propia empresa
    """
    # Validar acceso multi-tenant
    validate_tenant_access(current_user, id_empresa, "desactivar esta empresa")
    
    # Solo administradores pueden desactivar empresas
    if not is_super_admin(current_user) and current_user.rol.nombre_rol != RolEnum.ADMINISTRADOR.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden desactivar empresas"
        )
    
    success = EmpresaRepository.delete_empresa(db, id_empresa)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa no encontrada"
        )
    
    return {
        "mensaje": "Empresa desactivada exitosamente",
        "id_empresa": id_empresa
    }

@router.get("/estadisticas/resumen", status_code=status.HTTP_200_OK)
def obtener_estadisticas_empresas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtener estadísticas generales de empresas (Solo Administradores).
    
    Retorna contadores de empresas activas e inactivas.
    """
    if current_user.rol.nombre_rol != RolEnum.ADMINISTRADOR.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para ver estadísticas"
        )
    
    total_activas = EmpresaRepository.contar_empresas(db, estado="activo")
    total_inactivas = EmpresaRepository.contar_empresas(db, estado="inactivo")
    total = total_activas + total_inactivas
    
    return {
        "total_empresas": total,
        "empresas_activas": total_activas,
        "empresas_inactivas": total_inactivas
    }
