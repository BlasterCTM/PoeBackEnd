from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func
from app.models.factura import Factura
from app.repositories.base import BaseRepository
from datetime import datetime, timedelta


class FacturaRepository(BaseRepository[Factura]):
    """Repository para gestión de facturas"""
    
    def __init__(self):
        super().__init__(Factura)
    
    def get_by_id(self, db: Session, id_factura: int) -> Optional[Factura]:
        """Obtiene factura por ID"""
        return db.query(Factura).filter(Factura.id_factura == id_factura).first()
    
    def get_by_numero(self, db: Session, numero_factura: str) -> Optional[Factura]:
        """Obtiene factura por número"""
        return db.query(Factura).filter(Factura.numero_factura == numero_factura).first()
    
    def get_by_empresa(
        self, 
        db: Session, 
        id_empresa: int, 
        skip: int = 0, 
        limit: int = 100,
        estado: Optional[str] = None
    ) -> List[Factura]:
        """Obtiene facturas de una empresa"""
        query = db.query(Factura).filter(Factura.id_empresa == id_empresa)
        
        if estado:
            query = query.filter(Factura.estado == estado)
        
        return query.order_by(Factura.fecha_emision.desc()).offset(skip).limit(limit).all()
    
    def get_all(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        estado: Optional[str] = None
    ) -> List[Factura]:
        """Obtiene todas las facturas con filtros opcionales"""
        query = db.query(Factura).options(joinedload(Factura.empresa))
        
        if estado:
            query = query.filter(Factura.estado == estado)
        
        return query.order_by(Factura.fecha_emision.desc()).offset(skip).limit(limit).all()
    
    def get_pendientes(self, db: Session) -> List[Factura]:
        """Obtiene facturas pendientes de pago"""
        return db.query(Factura).filter(Factura.estado == "pendiente").order_by(Factura.fecha_vencimiento).all()
    
    def get_vencidas(self, db: Session) -> List[Factura]:
        """Obtiene facturas vencidas"""
        hoy = datetime.utcnow().date()
        return db.query(Factura).filter(
            and_(
                Factura.estado == "pendiente",
                Factura.fecha_vencimiento < hoy
            )
        ).all()
    
    def create(self, db: Session, factura_data: dict) -> Factura:
        """Crea una nueva factura"""
        factura = Factura(**factura_data)
        db.add(factura)
        db.commit()
        db.refresh(factura)
        return factura
    
    def update(self, db: Session, id_factura: int, update_data: dict) -> Optional[Factura]:
        """Actualiza una factura"""
        factura = self.get_by_id(db, id_factura)
        if not factura:
            return None
        
        for key, value in update_data.items():
            if value is not None:
                setattr(factura, key, value)
        
        db.commit()
        db.refresh(factura)
        return factura
    
    def registrar_pago(
        self, 
        db: Session, 
        id_factura: int,
        fecha_pago: datetime,
        metodo_pago: str,
        referencia_pago: str
    ) -> Optional[Factura]:
        """Registra el pago de una factura"""
        factura = self.get_by_id(db, id_factura)
        if not factura:
            return None
        
        factura.estado = "pagada"
        factura.fecha_pago = fecha_pago
        factura.metodo_pago = metodo_pago
        factura.referencia_pago = referencia_pago
        
        db.commit()
        db.refresh(factura)
        return factura
    
    def marcar_vencida(self, db: Session, id_factura: int) -> Optional[Factura]:
        """Marca una factura como vencida"""
        factura = self.get_by_id(db, id_factura)
        if not factura:
            return None
        
        factura.estado = "vencida"
        db.commit()
        db.refresh(factura)
        return factura
    
    def anular(self, db: Session, id_factura: int) -> Optional[Factura]:
        """Anula una factura"""
        factura = self.get_by_id(db, id_factura)
        if not factura:
            return None
        
        factura.estado = "anulada"
        db.commit()
        db.refresh(factura)
        return factura
    
    def generar_numero_factura(self, db: Session) -> str:
        """Genera un número de factura único"""
        año = datetime.utcnow().year
        mes = datetime.utcnow().month
        
        # Obtener el último número del mes
        ultima_factura = db.query(Factura).filter(
            Factura.numero_factura.like(f"FAC-{año}-{mes:02d}-%")
        ).order_by(Factura.numero_factura.desc()).first()
        
        if ultima_factura:
            ultimo_numero = int(ultima_factura.numero_factura.split("-")[-1])
            nuevo_numero = ultimo_numero + 1
        else:
            nuevo_numero = 1
        
        return f"FAC-{año}-{mes:02d}-{nuevo_numero:04d}"
    
    def get_stats(self, db: Session, id_empresa: Optional[int] = None) -> dict:
        """Obtiene estadísticas de facturación"""
        query = db.query(Factura)
        if id_empresa:
            query = query.filter(Factura.id_empresa == id_empresa)
        
        total_facturas = query.count()
        
        # Contar por estado
        facturas_pendientes = query.filter(Factura.estado == "pendiente").count()
        facturas_pagadas = query.filter(Factura.estado == "pagada").count()
        facturas_vencidas = query.filter(Factura.estado == "vencida").count()
        facturas_anuladas = query.filter(Factura.estado == "anulada").count()
        
        # Montos
        monto_total_facturado = db.query(func.coalesce(func.sum(Factura.total), 0)).scalar()
        monto_total_cobrado = db.query(func.coalesce(func.sum(Factura.total), 0)).filter(
            Factura.estado == "pagada"
        ).scalar()
        monto_pendiente = db.query(func.coalesce(func.sum(Factura.total), 0)).filter(
            Factura.estado == "pendiente"
        ).scalar()
        monto_vencido = db.query(func.coalesce(func.sum(Factura.total), 0)).filter(
            Factura.estado == "vencida"
        ).scalar()
        
        # Tasa de cobranza
        tasa_cobranza = (monto_total_cobrado / monto_total_facturado * 100) if monto_total_facturado > 0 else 0
        
        return {
            "total_facturas": total_facturas,
            "facturas_pendientes": facturas_pendientes,
            "facturas_pagadas": facturas_pagadas,
            "facturas_vencidas": facturas_vencidas,
            "facturas_anuladas": facturas_anuladas,
            "monto_total_facturado": int(monto_total_facturado or 0),
            "monto_total_cobrado": int(monto_total_cobrado or 0),
            "monto_pendiente": int(monto_pendiente or 0),
            "monto_vencido": int(monto_vencido or 0),
            "tasa_cobranza": round(tasa_cobranza, 2)
        }
    
    def actualizar_vencidas_automatico(self, db: Session) -> int:
        """Actualiza automáticamente las facturas pendientes que ya vencieron"""
        hoy = datetime.utcnow().date()
        facturas_vencidas = db.query(Factura).filter(
            and_(
                Factura.estado == "pendiente",
                Factura.fecha_vencimiento < hoy
            )
        ).all()
        
        count = 0
        for factura in facturas_vencidas:
            factura.estado = "vencida"
            count += 1
        
        if count > 0:
            db.commit()
        
        return count
    
    def generar_pdf(self, factura: Factura) -> str:
        """Genera un PDF simple de la factura y retorna la ruta del archivo"""
        try:
            from fpdf import FPDF
            import tempfile
            import os
        except ImportError:
            raise RuntimeError("Debes instalar fpdf: pip install fpdf")

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=16, style='B')
        pdf.cell(200, 10, txt=f"FACTURA N° {factura.numero_factura}", ln=True, align='C')
        pdf.ln(10)
        
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"ID Empresa: {factura.id_empresa}", ln=True)
        pdf.cell(200, 10, txt=f"ID Plan: {factura.id_plan}", ln=True)
        pdf.cell(200, 10, txt=f"Fecha emisión: {factura.fecha_emision}", ln=True)
        pdf.cell(200, 10, txt=f"Fecha vencimiento: {factura.fecha_vencimiento}", ln=True)
        pdf.ln(5)
        
        pdf.set_font("Arial", size=12, style='B')
        pdf.cell(200, 10, txt=f"Subtotal: ${factura.subtotal:,}", ln=True)
        pdf.cell(200, 10, txt=f"IVA: ${factura.iva:,}", ln=True)
        pdf.cell(200, 10, txt=f"TOTAL: ${factura.total:,}", ln=True)
        pdf.ln(5)
        
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"Estado: {factura.estado.upper()}", ln=True)
        
        if factura.descripcion:
            pdf.ln(5)
            pdf.multi_cell(200, 10, txt=f"Descripción: {factura.descripcion}")
        
        if factura.periodo_facturado:
            pdf.cell(200, 10, txt=f"Periodo: {factura.periodo_facturado}", ln=True)
        
        # Usar directorio temporal del sistema (funciona en Windows y Linux)
        temp_dir = tempfile.gettempdir()
        pdf_path = os.path.join(temp_dir, f"factura_{factura.id_factura}.pdf")
        pdf.output(pdf_path)
        return pdf_path
