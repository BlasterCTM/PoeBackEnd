-- Eliminar factura duplicada de testing
DELETE FROM factura WHERE numero_factura = 'FAC-2025-11-0001';

-- Verificar que se eliminó
SELECT COUNT(*) as facturas_restantes FROM factura;
