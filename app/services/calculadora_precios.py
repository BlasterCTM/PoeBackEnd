"""
Service para cálculo de precios de planes personalizados.
Define la lógica de negocio para cotizar planes según parámetros.
"""
from typing import Dict, Any, Optional


class CalculadoraPreciosService:
    """
    Servicio para calcular precios de planes personalizados.
    
    IMPORTANTE: Los valores aquí son REFERENCIALES y deben ajustarse
    según la estrategia de pricing real del negocio.
    
    NOTA: El sistema gestiona 1 Empresa = 1 Supermercado.
    """
    
    # ============================================
    # CONFIGURACIÓN DE PRECIOS BASE (CLP)
    # ============================================
    
    # Precio base mensual (fijo por supermercado)
    PRECIO_BASE_MENSUAL = 150000  # $150k CLP base por supermercado
    
    # Costos por recurso
    COSTO_POR_SUPERVISOR = 20000   # $20k CLP por supervisor
    COSTO_POR_REPONEDOR = 10000    # $10k CLP por reponedor
    
    # Costos opcionales
    COSTO_POR_1000_PRODUCTOS = 10000  # $10k CLP por cada 1000 productos
    COSTO_POR_100_PUNTOS = 5000       # $5k CLP por cada 100 puntos
    
    # Descuento por pago anual
    DESCUENTO_ANUAL = 0.15         # 15% descuento en pago anual
    
    
    @staticmethod
    def calcular_precio_mensual(
        cantidad_supervisores: int,
        cantidad_reponedores: int,
        cantidad_productos: Optional[int] = None,
        cantidad_puntos: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Calcula el precio mensual basado en parámetros.
        
        Args:
            cantidad_supervisores: Cantidad de supervisores
            cantidad_reponedores: Cantidad de reponedores
            cantidad_productos: Cantidad de productos (opcional)
            cantidad_puntos: Cantidad de puntos de reposición (opcional)
        
        Returns:
            dict con desglose de precio
        """
        # Precio base
        subtotal = CalculadoraPreciosService.PRECIO_BASE_MENSUAL
        
        # Costos por recursos
        costo_supervisores = cantidad_supervisores * CalculadoraPreciosService.COSTO_POR_SUPERVISOR
        costo_reponedores = cantidad_reponedores * CalculadoraPreciosService.COSTO_POR_REPONEDOR
        
        subtotal += costo_supervisores + costo_reponedores
        
        # Costos opcionales
        costo_productos = 0
        if cantidad_productos:
            bloques_productos = (cantidad_productos // 1000) + (1 if cantidad_productos % 1000 > 0 else 0)
            costo_productos = bloques_productos * CalculadoraPreciosService.COSTO_POR_1000_PRODUCTOS
            subtotal += costo_productos
        
        costo_puntos = 0
        if cantidad_puntos:
            bloques_puntos = (cantidad_puntos // 100) + (1 if cantidad_puntos % 100 > 0 else 0)
            costo_puntos = bloques_puntos * CalculadoraPreciosService.COSTO_POR_100_PUNTOS
            subtotal += costo_puntos
        
        # Total mensual (sin descuentos por volumen)
        total_mensual = subtotal
        
        # Total anual (con descuento adicional)
        total_anual_sin_descuento = total_mensual * 12
        descuento_anual = int(total_anual_sin_descuento * CalculadoraPreciosService.DESCUENTO_ANUAL)
        total_anual = total_anual_sin_descuento - descuento_anual
        
        return {
            "desglose": {
                "precio_base": CalculadoraPreciosService.PRECIO_BASE_MENSUAL,
                "costo_supervisores": costo_supervisores,
                "costo_reponedores": costo_reponedores,
                "costo_productos": costo_productos,
                "costo_puntos": costo_puntos,
                "subtotal": subtotal
            },
            "precio_mensual": total_mensual,
            "precio_anual": {
                "sin_descuento": total_anual_sin_descuento,
                "descuento": descuento_anual,
                "total": total_anual,
                "ahorro": descuento_anual
            },
            "parametros": {
                "cantidad_supervisores": cantidad_supervisores,
                "cantidad_reponedores": cantidad_reponedores,
                "cantidad_productos": cantidad_productos,
                "cantidad_puntos": cantidad_puntos
            }
        }
    
    
    @staticmethod
    def sugerir_features(
        cantidad_supervisores: int,
        cantidad_reponedores: int,
        integraciones: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Sugiere features según el tamaño de la operación.
        
        Args:
            cantidad_supervisores: Cantidad de supervisores
            cantidad_reponedores: Cantidad de reponedores
            integraciones: Lista de integraciones requeridas
        
        Returns:
            dict con features sugeridos
        """
        features = {
            # Features básicos (todos los planes)
            "dashboard": True,
            "optimizacion_rutas": True,
            "reportes_pdf": True,
            "notificaciones_email": True,
            "historial_dias": 90
        }
        
        # Determinar tamaño de operación por cantidad de usuarios
        total_usuarios = cantidad_supervisores + cantidad_reponedores
        
        # Operación pequeña (1-10 usuarios)
        if total_usuarios <= 10:
            features.update({
                "reportes_excel": False,
                "app_movil": False,
                "soporte": "email_48h"
            })
        
        # Operación mediana (11-30 usuarios)
        elif total_usuarios <= 30:
            features.update({
                "reportes_excel": True,
                "app_movil": True,
                "soporte": "email_24h",
                "soporte_telefonico": "horario_oficina",
                "notificaciones_push": True,
                "reportes_comparativos": True,
                "metricas_avanzadas": True,
                "exportacion_masiva": True,
                "historial_dias": 180
            })
        
        # Operación grande (31+ usuarios)
        else:
            features.update({
                "reportes_excel": True,
                "reportes_personalizados": True,
                "app_movil": True,
                "soporte": "24x7",
                "soporte_telefonico": "24x7",
                "notificaciones_push": True,
                "notificaciones_sms": True,
                "reportes_comparativos": True,
                "metricas_avanzadas": True,
                "exportacion_masiva": True,
                "api_acceso": True,
                "gestor_cuenta_dedicado": True,
                "sla_99_9": True,
                "historial_dias": -1,  # -1 = ilimitado
                "capacitacion_presencial": True,
                "capacitacion_continua": True
            })
        
        # Features especiales por integraciones
        if integraciones:
            if "ERP" in integraciones or "SAP" in integraciones:
                features["integracion_erp"] = True
            if "WMS" in integraciones:
                features["integracion_wms"] = True
        
        return features
    
    
    @staticmethod
    def generar_cotizacion_completa(
        cantidad_supervisores: int,
        cantidad_reponedores: int,
        cantidad_productos: Optional[int] = None,
        cantidad_puntos: Optional[int] = None,
        integraciones: Optional[list] = None,
        tiempo_servicio: str = "mensual"
    ) -> Dict[str, Any]:
        """
        Genera una cotización completa con precio y features sugeridos.
        
        Args:
            cantidad_supervisores: Cantidad de supervisores
            cantidad_reponedores: Cantidad de reponedores
            cantidad_productos: Cantidad de productos
            cantidad_puntos: Cantidad de puntos
            integraciones: Lista de integraciones
            tiempo_servicio: 'mensual' o 'anual'
        
        Returns:
            dict con cotización completa
        """
        # Calcular precio
        pricing = CalculadoraPreciosService.calcular_precio_mensual(
            cantidad_supervisores,
            cantidad_reponedores,
            cantidad_productos,
            cantidad_puntos
        )
        
        # Sugerir features
        features = CalculadoraPreciosService.sugerir_features(
            cantidad_supervisores,
            cantidad_reponedores,
            integraciones
        )
        
        # Determinar precio según tiempo de servicio
        if tiempo_servicio == "anual":
            precio_sugerido = pricing["precio_anual"]["total"]
            precio_info = {
                "tipo": "anual",
                "precio_total_anual": pricing["precio_anual"]["total"],
                "precio_mensual_equivalente": pricing["precio_mensual"],
                "ahorro_anual": pricing["precio_anual"]["ahorro"],
                "porcentaje_ahorro": int(CalculadoraPreciosService.DESCUENTO_ANUAL * 100)
            }
        else:
            precio_sugerido = pricing["precio_mensual"]
            precio_info = {
                "tipo": "mensual",
                "precio_mensual": pricing["precio_mensual"]
            }
        
        return {
            "precio_sugerido": precio_sugerido,
            "precio_info": precio_info,
            "desglose": pricing["desglose"],
            "features_sugeridos": features,
            "parametros": pricing["parametros"]
        }
