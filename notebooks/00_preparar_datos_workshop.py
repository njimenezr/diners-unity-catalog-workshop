# Databricks notebook source
# MAGIC %md
# MAGIC # Preparación — Workshop Unity Catalog para Diners
# MAGIC
# MAGIC Ejecuta **Run All** antes del workshop. El notebook crea un entorno sintético e idempotente para mostrar:
# MAGIC
# MAGIC - Catálogo, schemas, tablas, vista y volumen.
# MAGIC - Comentarios y governed tags compatibles con el sandbox.
# MAGIC - PII sintético, column masks y row filter.
# MAGIC - Lineage tabla/columna mediante una vista gobernada.
# MAGIC - Resultados de calidad y glosario de negocio.
# MAGIC - Consultas de verificación para Catalog Explorer, Discover y auditoría.
# MAGIC
# MAGIC **No contiene información real de Diners ni números de tarjeta válidos.**

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Configuración

# COMMAND ----------

CATALOG = "diners_governance"
DATA_SCHEMA = "tarjetas"
GOV_SCHEMA = "governance"
AUDITOR_GROUP = "admins"  # Grupo local del sandbox. En producción usar un account group.
CURRENT_USER = spark.sql("SELECT current_user()").first()[0]
# Opcional: reemplazar por un account group sincronizado vía SCIM.
# Los grupos locales del workspace pueden no ser principals válidos en Unity Catalog.
CONSUMER_PRINCIPAL = CURRENT_USER

print(f"Destino: {CATALOG}.{DATA_SCHEMA}")
print(f"Auditores demo: {AUDITOR_GROUP} | Principal con acceso: {CONSUMER_PRINCIPAL}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Namespace de Unity Catalog

# COMMAND ----------

spark.sql(f"""
CREATE CATALOG IF NOT EXISTS {CATALOG}
COMMENT 'Activos 100% sintéticos para el workshop de gobierno de Diners'
""")

spark.sql(f"""
CREATE SCHEMA IF NOT EXISTS {CATALOG}.{DATA_SCHEMA}
COMMENT 'Dominio sintético de tarjetas, fraude y comercios'
""")

spark.sql(f"""
CREATE SCHEMA IF NOT EXISTS {CATALOG}.{GOV_SCHEMA}
COMMENT 'Funciones, glosario y evidencias de gobierno del workshop'
""")

spark.sql(f"""
CREATE VOLUME IF NOT EXISTS {CATALOG}.{GOV_SCHEMA}.politicas
COMMENT 'Documentos sintéticos de políticas para demostrar gobierno de archivos'
""")

print("✓ Catálogo, schemas y volumen listos")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Datos sintéticos
# MAGIC
# MAGIC Los identificadores `PAN-DEMO-*`, correos `.invalid` y teléfonos `000-*` no representan personas ni tarjetas reales.

# COMMAND ----------

spark.sql(f"""
CREATE OR REPLACE TABLE {CATALOG}.{DATA_SCHEMA}.clientes
USING DELTA
COMMENT 'Clientes sintéticos para demostrar PII, clasificación y acceso dinámico'
AS
SELECT
  concat('CLI-', lpad(cast(id AS STRING), 5, '0')) AS customer_id,
  concat('Cliente Demo ', cast(id AS STRING)) AS customer_name,
  concat('user', lpad(cast(id AS STRING), 4, '0'), '@demo.invalid') AS customer_email,
  concat('000-', lpad(cast(id AS STRING), 7, '0')) AS phone_number,
  CASE pmod(id, 3) WHEN 0 THEN 'EC' WHEN 1 THEN 'PE' ELSE 'CO' END AS country_code,
  CASE pmod(id, 4)
    WHEN 0 THEN 'Premium'
    WHEN 1 THEN 'Clásico'
    WHEN 2 THEN 'Corporativo'
    ELSE 'Emprendedor'
  END AS segment,
  CASE
    WHEN pmod(id * 17, 100) >= 85 THEN 'ALTO'
    WHEN pmod(id * 17, 100) >= 55 THEN 'MEDIO'
    ELSE 'BAJO'
  END AS risk_profile,
  CASE WHEN pmod(id, 17) = 0 THEN 'VENCIDO' ELSE 'VIGENTE' END AS kyc_status,
  date_sub(current_date(), cast(pmod(id * 13, 720) AS INT)) AS last_review_date
FROM range(1, 201)
""")

spark.sql(f"""
CREATE OR REPLACE TABLE {CATALOG}.{DATA_SCHEMA}.comercios
USING DELTA
COMMENT 'Comercios sintéticos para análisis de transacciones'
AS
SELECT
  concat('MER-', lpad(cast(id AS STRING), 4, '0')) AS merchant_id,
  concat('Comercio Demo ', cast(id AS STRING)) AS merchant_name,
  CASE pmod(id, 5)
    WHEN 0 THEN 'RETAIL'
    WHEN 1 THEN 'TRAVEL'
    WHEN 2 THEN 'DINING'
    WHEN 3 THEN 'ONLINE'
    ELSE 'SERVICES'
  END AS merchant_category,
  CASE pmod(id, 3) WHEN 0 THEN 'EC' WHEN 1 THEN 'PE' ELSE 'CO' END AS country_code,
  CASE WHEN pmod(id, 11) = 0 THEN true ELSE false END AS enhanced_monitoring
FROM range(1, 51)
""")

spark.sql(f"""
CREATE OR REPLACE TABLE {CATALOG}.{DATA_SCHEMA}.transacciones_tarjeta
USING DELTA
COMMENT 'Transacciones sintéticas de tarjeta; producto de datos principal del workshop'
AS
SELECT
  concat('TX-', lpad(cast(id AS STRING), 7, '0')) AS transaction_id,
  concat('CLI-', lpad(cast(pmod(id, 200) + 1 AS STRING), 5, '0')) AS customer_id,
  concat('MER-', lpad(cast(pmod(id * 7, 50) + 1 AS STRING), 4, '0')) AS merchant_id,
  timestampadd(MINUTE, -cast(id * 3 AS INT), current_timestamp()) AS transaction_ts,
  concat('PAN-DEMO-', lpad(cast(pmod(id, 200) + 1 AS STRING), 4, '0')) AS card_pan,
  concat('user', lpad(cast(pmod(id, 200) + 1 AS STRING), 4, '0'), '@demo.invalid') AS customer_email,
  CASE pmod(id, 3) WHEN 0 THEN 'EC' WHEN 1 THEN 'PE' ELSE 'CO' END AS country_code,
  CASE pmod(id, 5)
    WHEN 0 THEN 'RETAIL'
    WHEN 1 THEN 'TRAVEL'
    WHEN 2 THEN 'DINING'
    WHEN 3 THEN 'ONLINE'
    ELSE 'SERVICES'
  END AS merchant_category,
  cast(5 + pmod(id * 7919, 500000) / 100.0 AS DECIMAL(12,2)) AS amount_usd,
  cast(pmod(id * 37, 100) / 100.0 AS DOUBLE) AS fraud_score,
  CASE
    WHEN pmod(id * 37, 100) >= 85 THEN 'DECLINED'
    WHEN pmod(id * 37, 100) >= 65 THEN 'REVIEW'
    ELSE 'APPROVED'
  END AS decision
FROM range(1, 1001)
""")

print("✓ 200 clientes, 50 comercios y 1.000 transacciones creadas")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Comentarios y tags
# MAGIC
# MAGIC El sandbox ya tiene políticas para algunos governed tags. Usamos sus valores permitidos:
# MAGIC
# MAGIC - `domain`: `payments` / `risk_fraud`
# MAGIC - `sensitivity`: `HIGH` / `MEDIUM` / `LOW`
# MAGIC - `pii_type`: `name`, `email`, `phone`, `other`

# COMMAND ----------

tag_statements = [
    f"""ALTER TABLE {CATALOG}.{DATA_SCHEMA}.clientes SET TAGS (
      'domain' = 'payments', 'sensitivity' = 'HIGH',
      'contains_pii' = 'true', 'data_product' = 'true')""",
    f"""ALTER TABLE {CATALOG}.{DATA_SCHEMA}.comercios SET TAGS (
      'domain' = 'payments', 'sensitivity' = 'LOW',
      'contains_pii' = 'false', 'data_product' = 'true')""",
    f"""ALTER TABLE {CATALOG}.{DATA_SCHEMA}.transacciones_tarjeta SET TAGS (
      'domain' = 'risk_fraud', 'sensitivity' = 'HIGH',
      'contains_pii' = 'true', 'data_product' = 'true')""",
    f"""ALTER TABLE {CATALOG}.{DATA_SCHEMA}.clientes
      ALTER COLUMN customer_name SET TAGS ('pii_type' = 'name')""",
    f"""ALTER TABLE {CATALOG}.{DATA_SCHEMA}.clientes
      ALTER COLUMN customer_email SET TAGS ('pii_type' = 'email')""",
    f"""ALTER TABLE {CATALOG}.{DATA_SCHEMA}.clientes
      ALTER COLUMN phone_number SET TAGS ('pii_type' = 'phone')""",
    f"""ALTER TABLE {CATALOG}.{DATA_SCHEMA}.transacciones_tarjeta
      ALTER COLUMN card_pan SET TAGS ('pii_type' = 'other')""",
    f"""ALTER TABLE {CATALOG}.{DATA_SCHEMA}.transacciones_tarjeta
      ALTER COLUMN customer_email SET TAGS ('pii_type' = 'email')""",
]

for statement in tag_statements:
    spark.sql(statement)

column_comments = [
    ("clientes", "customer_id", "Identificador sintético del cliente"),
    ("clientes", "customer_email", "Correo sintético; dominio .invalid"),
    ("clientes", "risk_profile", "Perfil sintético usado únicamente para el workshop"),
    ("transacciones_tarjeta", "card_pan", "Token PAN-DEMO; no es un número de tarjeta"),
    ("transacciones_tarjeta", "fraud_score", "Score sintético entre 0 y 1"),
    ("transacciones_tarjeta", "decision", "Resultado sintético de autorización"),
]

for table, column, comment in column_comments:
    spark.sql(
        f"COMMENT ON COLUMN {CATALOG}.{DATA_SCHEMA}.{table}.{column} IS '{comment}'"
    )

print("✓ Governed tags y comentarios aplicados")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Privacidad dinámica: máscaras y filtro de filas

# COMMAND ----------

spark.sql(f"""
CREATE OR REPLACE FUNCTION {CATALOG}.{GOV_SCHEMA}.mask_pan(value STRING)
RETURNS STRING
COMMENT 'Muestra el token completo a admins; enmascara para consumidores'
RETURN CASE
  WHEN is_member('{AUDITOR_GROUP}') THEN value
  ELSE concat('*********', right(value, 4))
END
""")

spark.sql(f"""
CREATE OR REPLACE FUNCTION {CATALOG}.{GOV_SCHEMA}.mask_email(value STRING)
RETURNS STRING
COMMENT 'Muestra email sintético a admins; enmascara para consumidores'
RETURN CASE
  WHEN is_member('{AUDITOR_GROUP}') THEN value
  ELSE concat(left(value, 1), '***@', split(value, '@')[1])
END
""")

spark.sql(f"""
CREATE OR REPLACE FUNCTION {CATALOG}.{GOV_SCHEMA}.filter_country(country STRING)
RETURNS BOOLEAN
COMMENT 'Admins ven todos los países; consumidores demo ven Ecuador'
RETURN is_member('{AUDITOR_GROUP}') OR country = 'EC'
""")

spark.sql(f"""
ALTER TABLE {CATALOG}.{DATA_SCHEMA}.transacciones_tarjeta
ALTER COLUMN card_pan SET MASK {CATALOG}.{GOV_SCHEMA}.mask_pan
""")

spark.sql(f"""
ALTER TABLE {CATALOG}.{DATA_SCHEMA}.transacciones_tarjeta
ALTER COLUMN customer_email SET MASK {CATALOG}.{GOV_SCHEMA}.mask_email
""")

spark.sql(f"""
ALTER TABLE {CATALOG}.{DATA_SCHEMA}.transacciones_tarjeta
SET ROW FILTER {CATALOG}.{GOV_SCHEMA}.filter_country ON (country_code)
""")

print("✓ Column masks y row filter activos")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Producto de datos y lineage

# COMMAND ----------

spark.sql(f"""
CREATE OR REPLACE VIEW {CATALOG}.{DATA_SCHEMA}.transacciones_riesgo
COMMENT 'Producto sintético para analistas de fraude; conserva políticas de la tabla fuente'
AS
SELECT
  t.transaction_id,
  t.transaction_ts,
  t.card_pan,
  t.customer_email,
  t.country_code,
  t.merchant_category,
  m.merchant_name,
  t.amount_usd,
  t.fraud_score,
  t.decision,
  c.segment,
  c.risk_profile,
  CASE
    WHEN t.fraud_score >= 0.80 THEN 'ALTO'
    WHEN t.fraud_score >= 0.50 THEN 'MEDIO'
    ELSE 'BAJO'
  END AS risk_band
FROM {CATALOG}.{DATA_SCHEMA}.transacciones_tarjeta t
JOIN {CATALOG}.{DATA_SCHEMA}.clientes c USING (customer_id)
JOIN {CATALOG}.{DATA_SCHEMA}.comercios m USING (merchant_id)
""")

spark.sql(f"""
CREATE OR REPLACE VIEW {CATALOG}.{DATA_SCHEMA}.fraud_kpis
COMMENT 'KPIs sintéticos por país y categoría para dashboards y Genie'
AS
SELECT
  country_code,
  merchant_category,
  count(*) AS transaction_count,
  sum(amount_usd) AS total_amount_usd,
  avg(fraud_score) AS avg_fraud_score,
  sum(CASE WHEN decision <> 'APPROVED' THEN 1 ELSE 0 END) AS flagged_transactions,
  sum(CASE WHEN decision <> 'APPROVED' THEN 1 ELSE 0 END) / count(*) AS flagged_rate
FROM {CATALOG}.{DATA_SCHEMA}.transacciones_tarjeta
GROUP BY country_code, merchant_category
""")

# Materializa lecturas para que aparezcan relaciones y actividad.
display(spark.table(f"{CATALOG}.{DATA_SCHEMA}.transacciones_riesgo").limit(20))
display(spark.table(f"{CATALOG}.{DATA_SCHEMA}.fraud_kpis"))

print("✓ Vistas creadas; la actividad alimentará lineage y audit")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Calidad y glosario gobernado

# COMMAND ----------

spark.sql(f"""
CREATE OR REPLACE TABLE {CATALOG}.{GOV_SCHEMA}.dq_results
USING DELTA
COMMENT 'Resultados sintéticos de controles de calidad para el workshop'
AS
SELECT * FROM VALUES
  ('transacciones_tarjeta', 'transaction_id_not_null', 'PASS', 0, 'HIGH', current_timestamp()),
  ('transacciones_tarjeta', 'valid_country_code',       'PASS', 0, 'MEDIUM', current_timestamp()),
  ('transacciones_tarjeta', 'fraud_score_between_0_1',  'PASS', 0, 'HIGH', current_timestamp()),
  ('clientes',              'kyc_current',              'WARN', 11, 'HIGH', current_timestamp()),
  ('clientes',              'last_review_under_365d',   'WARN', 96, 'MEDIUM', current_timestamp())
AS dq(table_name, check_name, status, failed_records, regulatory_impact, run_timestamp)
""")

spark.sql(f"""
CREATE OR REPLACE TABLE {CATALOG}.{GOV_SCHEMA}.business_glossary
USING DELTA
COMMENT 'Glosario sintético; usar como respaldo cuando Pages no esté habilitado'
AS
SELECT * FROM VALUES
  ('Transacción marcada', 'Transacción en REVIEW o DECLINED por controles sintéticos', 'Fraude', 'Owner Fraude'),
  ('Tasa de marcación', 'Porcentaje de transacciones en REVIEW o DECLINED', 'Fraude', 'Owner Fraude'),
  ('Cliente KYC vigente', 'Cliente cuya revisión KYC está dentro de la política definida', 'Cumplimiento', 'Owner Compliance'),
  ('Monto procesado', 'Suma del monto autorizado o revisado en USD', 'Tarjetas', 'Owner Tarjetas')
AS glossary(term, definition, domain, business_owner)
""")

spark.sql(f"""
ALTER TABLE {CATALOG}.{GOV_SCHEMA}.dq_results
SET TAGS ('domain' = 'risk_fraud', 'sensitivity' = 'MEDIUM', 'data_product' = 'true')
""")

spark.sql(f"""
ALTER TABLE {CATALOG}.{GOV_SCHEMA}.business_glossary
SET TAGS ('domain' = 'payments', 'sensitivity' = 'LOW', 'data_product' = 'true')
""")

display(spark.table(f"{CATALOG}.{GOV_SCHEMA}.dq_results"))
print("✓ Calidad y glosario preparados")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8. Documento sintético en UC Volume

# COMMAND ----------

policy_text = """# Política sintética de acceso a transacciones

- Los analistas consultan únicamente países asignados.
- PAN y email se muestran enmascarados salvo autorización de auditoría.
- Todo acceso debe quedar registrado para revisión.
- Este documento existe solo para el workshop y no representa una política real de Diners.
"""

dbutils.fs.put(
    f"/Volumes/{CATALOG}/{GOV_SCHEMA}/politicas/politica_acceso_demo.md",
    policy_text,
    overwrite=True,
)
print(f"✓ /Volumes/{CATALOG}/{GOV_SCHEMA}/politicas/politica_acceso_demo.md")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 9. Permisos para participantes del sandbox

# COMMAND ----------

grants = [
    f"GRANT USE CATALOG ON CATALOG {CATALOG} TO `{CONSUMER_PRINCIPAL}`",
    f"GRANT USE SCHEMA ON SCHEMA {CATALOG}.{DATA_SCHEMA} TO `{CONSUMER_PRINCIPAL}`",
    f"GRANT USE SCHEMA ON SCHEMA {CATALOG}.{GOV_SCHEMA} TO `{CONSUMER_PRINCIPAL}`",
    f"GRANT SELECT ON TABLE {CATALOG}.{DATA_SCHEMA}.clientes TO `{CONSUMER_PRINCIPAL}`",
    f"GRANT SELECT ON TABLE {CATALOG}.{DATA_SCHEMA}.comercios TO `{CONSUMER_PRINCIPAL}`",
    f"GRANT SELECT ON TABLE {CATALOG}.{DATA_SCHEMA}.transacciones_tarjeta TO `{CONSUMER_PRINCIPAL}`",
    f"GRANT SELECT ON VIEW {CATALOG}.{DATA_SCHEMA}.transacciones_riesgo TO `{CONSUMER_PRINCIPAL}`",
    f"GRANT SELECT ON VIEW {CATALOG}.{DATA_SCHEMA}.fraud_kpis TO `{CONSUMER_PRINCIPAL}`",
    f"GRANT SELECT ON TABLE {CATALOG}.{GOV_SCHEMA}.dq_results TO `{CONSUMER_PRINCIPAL}`",
    f"GRANT SELECT ON TABLE {CATALOG}.{GOV_SCHEMA}.business_glossary TO `{CONSUMER_PRINCIPAL}`",
    f"GRANT READ VOLUME ON VOLUME {CATALOG}.{GOV_SCHEMA}.politicas TO `{CONSUMER_PRINCIPAL}`",
]

for statement in grants:
    spark.sql(statement)

print(f"✓ Acceso de lectura validado para `{CONSUMER_PRINCIPAL}`")
print("ℹ Para participantes, asigna un account group SCIM a CONSUMER_PRINCIPAL y vuelve a ejecutar esta sección.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 10. Verificación final

# COMMAND ----------

checks = {
    "clientes": spark.table(f"{CATALOG}.{DATA_SCHEMA}.clientes").count(),
    "comercios": spark.table(f"{CATALOG}.{DATA_SCHEMA}.comercios").count(),
    "transacciones_visibles_para_usuario_actual": spark.table(
        f"{CATALOG}.{DATA_SCHEMA}.transacciones_tarjeta"
    ).count(),
    "transacciones_riesgo": spark.table(
        f"{CATALOG}.{DATA_SCHEMA}.transacciones_riesgo"
    ).count(),
    "dq_checks": spark.table(f"{CATALOG}.{GOV_SCHEMA}.dq_results").count(),
}

for name, count in checks.items():
    print(f"{name}: {count:,}")

assert checks["clientes"] == 200
assert checks["comercios"] == 50
assert checks["dq_checks"] == 5

print("""
✅ PREPARACIÓN COMPLETA

Siguiente:
1. Catalog Explorer → diners_governance → tarjetas.
2. Discover → crear/usar Domain “Tarjetas y Fraude”.
3. Asignar transacciones_riesgo y fraud_kpis al Domain.
4. Agregar una Page con las definiciones de business_glossary.
5. Certificar transacciones_riesgo si la feature está habilitada.
6. Abrir lineage y system.access.audit antes de presentar.
""")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Consultas de respaldo

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT *
# MAGIC FROM diners_governance.tarjetas.transacciones_riesgo
# MAGIC ORDER BY transaction_ts DESC
# MAGIC LIMIT 20;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT *
# MAGIC FROM diners_governance.governance.dq_results
# MAGIC ORDER BY regulatory_impact, status;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   event_time,
# MAGIC   source_table_full_name,
# MAGIC   target_table_full_name,
# MAGIC   source_type,
# MAGIC   target_type,
# MAGIC   created_by
# MAGIC FROM system.access.table_lineage
# MAGIC WHERE event_date >= current_date() - INTERVAL 7 DAYS
# MAGIC   AND (
# MAGIC     source_table_full_name LIKE 'diners_governance.%'
# MAGIC     OR target_table_full_name LIKE 'diners_governance.%'
# MAGIC   )
# MAGIC ORDER BY event_time DESC;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   event_time,
# MAGIC   user_identity.email AS actor,
# MAGIC   action_name,
# MAGIC   service_name,
# MAGIC   request_params
# MAGIC FROM system.access.audit
# MAGIC WHERE event_date >= current_date() - INTERVAL 1 DAY
# MAGIC   AND (
# MAGIC     request_params['full_name_arg'] LIKE 'diners_governance.%'
# MAGIC     OR request_params['name'] LIKE 'diners_governance.%'
# MAGIC     OR request_params['catalog_name'] = 'diners_governance'
# MAGIC   )
# MAGIC ORDER BY event_time DESC
# MAGIC LIMIT 100;
