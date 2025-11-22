"""
Repository para gestión de Logs de Auditoría
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from datetime import datetime, timedelta
from app.models.log_auditoria import LogAuditoria
from app.schemas.log_auditoria import LogAuditoriaCreate, LogAuditoriaFiltros


class LogAuditoriaRepository:
    """Repository para gestión de logs de auditoría"""
    
    def registrar_accion(
        self,
        db: Session,
        log_data: LogAuditoriaCreate
    ) -> LogAuditoria:
        """
        Registra una acción en el log de auditoría
        
        Args:
            db: Sesión de base de datos
            log_data: Datos del log a registrar
            
        Returns:
            LogAuditoria creado
        """
        log = LogAuditoria(**log_data.model_dump())
        db.add(log)
        db.commit()
        db.refresh(log)
        return log
    
    def obtener_logs(
        self,
        db: Session,
        filtros: LogAuditoriaFiltros
    ) -> tuple[List[LogAuditoria], int]:
        """
        Obtiene logs con filtros
        
        Returns:
            Tupla (logs, total)
        """
        query = db.query(LogAuditoria)
        
        # Aplicar filtros
        if filtros.id_usuario:
            query = query.filter(LogAuditoria.id_usuario == filtros.id_usuario)
        
        if filtros.accion:
            query = query.filter(LogAuditoria.accion == filtros.accion)
        
        if filtros.entidad:
            query = query.filter(LogAuditoria.entidad == filtros.entidad)
        
        if filtros.id_entidad:
            query = query.filter(LogAuditoria.id_entidad == filtros.id_entidad)
        
        if filtros.fecha_desde:
            query = query.filter(LogAuditoria.fecha >= filtros.fecha_desde)
        
        if filtros.fecha_hasta:
            query = query.filter(LogAuditoria.fecha <= filtros.fecha_hasta)
        
        # Contar total
        total = query.count()
        
        # Ordenar por fecha descendente y paginar
        logs = query.order_by(desc(LogAuditoria.fecha)).offset(filtros.skip).limit(filtros.limit).all()
        
        return logs, total
    
    def obtener_log_por_id(self, db: Session, id_log: int) -> Optional[LogAuditoria]:
        """Obtiene un log por ID"""
        return db.query(LogAuditoria).filter(LogAuditoria.id_log == id_log).first()
    
    def obtener_logs_por_entidad(
        self,
        db: Session,
        entidad: str,
        id_entidad: int,
        limit: int = 50
    ) -> List[LogAuditoria]:
        """
        Obtiene todos los logs relacionados a una entidad específica
        
        Útil para ver el historial completo de cambios de un registro
        """
        return db.query(LogAuditoria).filter(
            LogAuditoria.entidad == entidad,
            LogAuditoria.id_entidad == id_entidad
        ).order_by(desc(LogAuditoria.fecha)).limit(limit).all()
    
    def obtener_estadisticas(self, db: Session) -> Dict[str, Any]:
        """
        Obtiene estadísticas de auditoría
        
        Returns:
            Dict con estadísticas agregadas
        """
        ahora = datetime.utcnow()
        hace_24h = ahora - timedelta(hours=24)
        hace_7d = ahora - timedelta(days=7)
        
        # Total de logs
        total_logs = db.query(func.count(LogAuditoria.id_log)).scalar()
        
        # Acciones por tipo
        acciones = db.query(
            LogAuditoria.accion,
            func.count(LogAuditoria.id_log).label('count')
        ).group_by(LogAuditoria.accion).order_by(desc('count')).limit(10).all()
        
        acciones_por_tipo = {accion: count for accion, count in acciones}
        
        # Usuarios más activos
        usuarios_activos = db.query(
            LogAuditoria.id_usuario,
            LogAuditoria.nombre_usuario,
            func.count(LogAuditoria.id_log).label('acciones')
        ).group_by(
            LogAuditoria.id_usuario,
            LogAuditoria.nombre_usuario
        ).order_by(desc('acciones')).limit(10).all()
        
        usuarios_mas_activos = [
            {
                "id_usuario": id_usuario,
                "nombre": nombre,
                "total_acciones": acciones
            }
            for id_usuario, nombre, acciones in usuarios_activos
        ]
        
        # Entidades más modificadas
        entidades = db.query(
            LogAuditoria.entidad,
            func.count(LogAuditoria.id_log).label('modificaciones')
        ).group_by(LogAuditoria.entidad).order_by(desc('modificaciones')).limit(10).all()
        
        entidades_mas_modificadas = [
            {
                "entidad": entidad,
                "total_modificaciones": mods
            }
            for entidad, mods in entidades
        ]
        
        # Logs últimas 24 horas
        logs_24h = db.query(func.count(LogAuditoria.id_log)).filter(
            LogAuditoria.fecha >= hace_24h
        ).scalar()
        
        # Logs última semana
        logs_7d = db.query(func.count(LogAuditoria.id_log)).filter(
            LogAuditoria.fecha >= hace_7d
        ).scalar()
        
        return {
            "total_logs": total_logs,
            "acciones_por_tipo": acciones_por_tipo,
            "usuarios_mas_activos": usuarios_mas_activos,
            "entidades_mas_modificadas": entidades_mas_modificadas,
            "logs_ultimas_24h": logs_24h,
            "logs_ultima_semana": logs_7d
        }
    
    def eliminar_logs_antiguos(self, db: Session, dias: int = 365) -> int:
        """
        Elimina logs más antiguos que X días (para limpieza periódica)
        
        Args:
            db: Sesión de base de datos
            dias: Días de retención (default 1 año)
            
        Returns:
            Cantidad de logs eliminados
        """
        fecha_limite = datetime.utcnow() - timedelta(days=dias)
        
        resultado = db.query(LogAuditoria).filter(
            LogAuditoria.fecha < fecha_limite
        ).delete()
        
        db.commit()
        return resultado
    
    def listar_con_filtros(
        self,
        db: Session,
        filtros: LogAuditoriaFiltros,
        skip: int = 0,
        limit: int = 50
    ) -> List[LogAuditoria]:
        """
        Lista logs aplicando filtros con paginación
        
        Args:
            db: Sesión de base de datos
            filtros: Filtros a aplicar
            skip: Registros a saltar
            limit: Límite de registros
            
        Returns:
            Lista de logs
        """
        query = db.query(LogAuditoria)
        
        # Aplicar filtros
        if filtros.id_usuario:
            query = query.filter(LogAuditoria.id_usuario == filtros.id_usuario)
        
        if filtros.accion:
            query = query.filter(LogAuditoria.accion == filtros.accion)
        
        if filtros.entidad:
            query = query.filter(LogAuditoria.entidad == filtros.entidad)
        
        if filtros.id_entidad:
            query = query.filter(LogAuditoria.id_entidad == filtros.id_entidad)
        
        if filtros.fecha_desde:
            # Convertir date a datetime
            fecha_desde_dt = datetime.combine(filtros.fecha_desde, datetime.min.time())
            query = query.filter(LogAuditoria.fecha >= fecha_desde_dt)
        
        if filtros.fecha_hasta:
            # Convertir date a datetime y agregar 1 día para incluir todo el día
            fecha_hasta_dt = datetime.combine(filtros.fecha_hasta, datetime.max.time())
            query = query.filter(LogAuditoria.fecha <= fecha_hasta_dt)
        
        # Ordenar y paginar
        logs = query.order_by(desc(LogAuditoria.fecha)).offset(skip).limit(limit).all()
        
        return logs
    
    def listar_acciones_unicas(self, db: Session) -> List[str]:
        """
        Lista todas las acciones únicas registradas
        
        Útil para autocompletar filtros en UI
        """
        result = db.query(LogAuditoria.accion).distinct().order_by(LogAuditoria.accion).all()
        return [row[0] for row in result]
    
    def listar_entidades_unicas(self, db: Session) -> List[str]:
        """
        Lista todas las entidades únicas registradas
        
        Útil para autocompletar filtros en UI
        """
        result = db.query(LogAuditoria.entidad).distinct().order_by(LogAuditoria.entidad).all()
        return [row[0] for row in result]
