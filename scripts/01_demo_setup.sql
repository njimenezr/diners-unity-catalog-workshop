-- Banco Pichincha Unity Catalog Workshop
-- Datos 100% sintéticos. Ejecutar como administrador en un SQL Warehouse.

CREATE CATALOG IF NOT EXISTS diners_governance
COMMENT 'Activos sintéticos para el workshop de gobierno de Banco Pichincha';

CREATE SCHEMA IF NOT EXISTS diners_governance.tarjetas
COMMENT 'Dominio de tarjetas y transacciones sintéticas';

CREATE SCHEMA IF NOT EXISTS diners_governance.governance
COMMENT 'Funciones y metadatos de gobierno del workshop';

CREATE OR REPLACE TABLE diners_governance.tarjetas.transacciones_tarjeta (
  transaction_id STRING COMMENT 'Identificador sintético de la transacción',
  transaction_ts TIMESTAMP COMMENT 'Fecha y hora de la transacción',
  card_pan STRING COMMENT 'PAN sintético; no corresponde a una tarjeta real',
  customer_email STRING COMMENT 'Correo sintético del cliente',
  country_code STRING COMMENT 'País de la transacción',
  merchant_category STRING COMMENT 'Categoría del comercio',
  amount_usd DECIMAL(12,2) COMMENT 'Monto sintético en USD',
  fraud_score DOUBLE COMMENT 'Score sintético entre 0 y 1',
  decision STRING COMMENT 'Decisión de autorización'
)
USING DELTA
COMMENT 'Transacciones sintéticas certificables para el workshop; no contiene PII real';

INSERT OVERWRITE diners_governance.tarjetas.transacciones_tarjeta VALUES
  ('TX-1001', timestamp'2026-09-03 08:15:00', 'PAN-DEMO-0001', 'user01@demo.invalid', 'EC', 'RETAIL',  125.40, 0.08, 'APPROVED'),
  ('TX-1002', timestamp'2026-09-03 08:17:00', 'PAN-DEMO-0002', 'user02@demo.invalid', 'PE', 'TRAVEL',  980.00, 0.72, 'REVIEW'),
  ('TX-1003', timestamp'2026-09-03 08:20:00', 'PAN-DEMO-0003', 'user03@demo.invalid', 'EC', 'ONLINE', 2450.90, 0.91, 'DECLINED'),
  ('TX-1004', timestamp'2026-09-03 08:22:00', 'PAN-DEMO-0004', 'user04@demo.invalid', 'CO', 'RETAIL',   76.25, 0.11, 'APPROVED'),
  ('TX-1005', timestamp'2026-09-03 08:29:00', 'PAN-DEMO-0005', 'user05@demo.invalid', 'EC', 'DINING',  210.10, 0.20, 'APPROVED');

ALTER TABLE diners_governance.tarjetas.transacciones_tarjeta
SET TAGS (
  'domain' = 'payments',
  'sensitivity' = 'HIGH',
  'contains_pii' = 'true',
  'data_product' = 'true'
);

ALTER TABLE diners_governance.tarjetas.transacciones_tarjeta
ALTER COLUMN card_pan SET TAGS ('pii_type' = 'other');

ALTER TABLE diners_governance.tarjetas.transacciones_tarjeta
ALTER COLUMN customer_email SET TAGS ('pii_type' = 'email');

CREATE OR REPLACE FUNCTION diners_governance.governance.mask_pan(value STRING)
RETURNS STRING
RETURN CASE
  -- Demo workspace: `admins` is a workspace-local group.
  -- In production, prefer an account group with is_account_group_member().
  WHEN is_member('admins') THEN value
  ELSE concat('************', right(value, 4))
END;

CREATE OR REPLACE FUNCTION diners_governance.governance.mask_email(value STRING)
RETURNS STRING
RETURN CASE
  WHEN is_member('admins') THEN value
  ELSE concat(left(value, 1), '***@', split(value, '@')[1])
END;

ALTER TABLE diners_governance.tarjetas.transacciones_tarjeta
ALTER COLUMN card_pan
SET MASK diners_governance.governance.mask_pan;

ALTER TABLE diners_governance.tarjetas.transacciones_tarjeta
ALTER COLUMN customer_email
SET MASK diners_governance.governance.mask_email;

CREATE OR REPLACE VIEW diners_governance.tarjetas.transacciones_riesgo AS
SELECT
  transaction_id,
  transaction_ts,
  card_pan,
  customer_email,
  country_code,
  merchant_category,
  amount_usd,
  fraud_score,
  decision,
  CASE
    WHEN fraud_score >= 0.80 THEN 'ALTO'
    WHEN fraud_score >= 0.50 THEN 'MEDIO'
    ELSE 'BAJO'
  END AS risk_band
FROM diners_governance.tarjetas.transacciones_tarjeta;

COMMENT ON VIEW diners_governance.tarjetas.transacciones_riesgo IS
  'Vista certificable para analistas de fraude; hereda las máscaras de las columnas fuente';

-- Ajustar grupos reales antes del workshop:
-- GRANT USE CATALOG ON CATALOG diners_governance TO `diners_workshop_users`;
-- GRANT USE SCHEMA ON SCHEMA diners_governance.tarjetas TO `diners_workshop_users`;
-- GRANT SELECT ON VIEW diners_governance.tarjetas.transacciones_riesgo TO `diners_workshop_users`;
