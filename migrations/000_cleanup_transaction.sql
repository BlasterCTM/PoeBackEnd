-- ============================================
-- LIMPIEZA DE TRANSACCIONES ABORTADAS
-- ============================================
-- Ejecutar PRIMERO si ves error:
-- "ERROR: transacción abortada, las órdenes serán ignoradas"
-- ============================================

ROLLBACK;

-- Ahora puedes ejecutar 002_backoffice_y_auditoria_FINAL.sql
