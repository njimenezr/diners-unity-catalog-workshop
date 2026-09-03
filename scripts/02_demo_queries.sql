-- Consultas preparadas para el recorrido de demo.

-- 1. Consumidor: mismo objeto gobernado para SQL, dashboards y Genie.
SELECT *
FROM diners_governance.tarjetas.transacciones_riesgo
ORDER BY transaction_ts DESC;

-- 2. Metadatos visibles programáticamente.
DESCRIBE EXTENDED diners_governance.tarjetas.transacciones_tarjeta;

-- 3. Inventario de tags. Requiere visibilidad sobre information_schema.
SELECT
  catalog_name,
  schema_name,
  table_name,
  tag_name,
  tag_value
FROM diners_governance.information_schema.table_tags
WHERE schema_name = 'tarjetas'
ORDER BY table_name, tag_name;

SELECT
  catalog_name,
  schema_name,
  table_name,
  column_name,
  tag_name,
  tag_value
FROM diners_governance.information_schema.column_tags
WHERE schema_name = 'tarjetas'
ORDER BY table_name, column_name, tag_name;

-- 4. Lineage reciente del objeto. También abrir la pestaña Lineage en Catalog Explorer.
SELECT
  event_time,
  source_table_full_name,
  target_table_full_name,
  source_type,
  target_type,
  created_by
FROM system.access.table_lineage
WHERE event_date >= current_date() - INTERVAL 7 DAYS
  AND (
    source_table_full_name LIKE 'diners_governance.%'
    OR target_table_full_name LIKE 'diners_governance.%'
  )
ORDER BY event_time DESC;

-- 5. Auditoría: inspeccionar primero las acciones reales del workshop.
SELECT
  event_time,
  user_identity.email AS actor,
  action_name,
  service_name,
  request_params,
  response.status_code AS status_code,
  source_ip_address
FROM system.access.audit
WHERE event_date >= current_date() - INTERVAL 1 DAY
  AND (
    request_params['full_name_arg'] LIKE 'diners_governance.%'
    OR request_params['name'] LIKE 'diners_governance.%'
    OR request_params['catalog_name'] = 'diners_governance'
  )
ORDER BY event_time DESC
LIMIT 100;

-- 6. Cambios de permisos recientes.
SELECT
  event_time,
  user_identity.email AS actor,
  action_name,
  request_params,
  response
FROM system.access.audit
WHERE event_date >= current_date() - INTERVAL 7 DAYS
  AND (
    upper(action_name) LIKE '%GRANT%'
    OR upper(action_name) LIKE '%REVOKE%'
    OR upper(action_name) LIKE '%PERMISSION%'
  )
ORDER BY event_time DESC
LIMIT 100;
