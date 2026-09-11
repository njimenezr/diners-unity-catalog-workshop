# Banco Pichincha — Unity Catalog: Visión de Gobierno

Workshop interactivo de 90 minutos para presentar gobierno de datos con Unity Catalog. El recorrido cubre:

- Modelo operativo: consumidor, curator y administrador.
- Discover page, Domains, Pages, Genie One y Catalog Explorer.
- Metastore, catálogos, schemas y activos gobernados.
- RBAC, ABAC, governed tags, row filters y column masks.
- Clasificación, certificación, lineage, calidad y auditoría.
- Federation, Delta Sharing, Clean Rooms, Iceberg y gobierno de IA.
- Coexistencia gradual entre Teradata y Databricks.
- Patrón didáctico en cada paso: conversación → explicación → Genie Code.
- 15 prompts copiables para que los participantes consulten, diseñen o validen.

Los datos y nombres usados en la demo son sintéticos.

## Estructura

```text
.
├── app.yaml
├── databricks.yml
├── main.py
├── requirements.txt
├── FACILITATOR.md
├── data/
│   └── workshop.json
├── frontend/
│   └── index.html
├── notebooks/
│   └── 00_preparar_datos_workshop.py
└── scripts/
    ├── 01_demo_setup.sql
    └── 02_demo_queries.sql
```

La estructura sigue el patrón del workshop `banco-popular-genie-workshop`: FastAPI sirve contenido estructurado desde JSON y un frontend single-page guarda el progreso localmente.

## Ejecutar localmente

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Abre <http://localhost:8000>.

## Preparar la demo de Unity Catalog

La opción recomendada es abrir y ejecutar **Run All** en:

```text
/Workspace/Users/nicolas.jimenez@databricks.com/diners-unity-catalog-workshop/00_preparar_datos_workshop
```

El notebook crea 200 clientes, 50 comercios y 1.000 transacciones sintéticas; configura governed tags, comentarios, masks, row filter, vistas con lineage, resultados DQ, glosario y un documento en UC Volume.

Después:

1. Ejecuta una consulta sobre `diners_governance.tarjetas.transacciones_riesgo` para generar actividad.
2. Configura Discovery desde la UI:
   - Crea o usa el dominio `Tarjetas`.
   - Asigna la tabla y la vista del catálogo `diners_governance`.
   - Agrega owner, descripción y una Page de definición.
   - Certifica la vista de riesgo si la funcionalidad está habilitada.
3. Valida audit y lineage con `scripts/02_demo_queries.sql`.

Como alternativa reducida, `scripts/01_demo_setup.sql` prepara únicamente la tabla principal y las máscaras.

Las funciones de mask revelan valores completos al grupo local `admins` y enmascaran para los demás. Esto permite validar la demo en el sandbox solicitado. Para producción, reemplaza ese grupo por un grupo de cuenta sincronizado desde el IdP y usa `is_account_group_member()`.

El notebook acepta widgets para adaptarse a las políticas del metastore:

- `catalog` y `create_catalog`
- `domain_general` y `domain_risk`
- `sensitivity_high`, `sensitivity_medium` y `sensitivity_low`
- `data_product` y `pii_card`

Los defaults del sandbox original son `diners_governance`, `payments` /
`risk_fraud`, `HIGH` / `MEDIUM` / `LOW`, `data_product=true` y
`pii_card=other`.

El dominio de negocio visible en Discover puede seguir llamándose **Tarjetas**; el governed tag `domain` utiliza la taxonomía corporativa existente.

## Interacción con Genie Code

Quince pasos incluyen un botón **Copiar prompt**. Los prompts están diseñados para tres tipos de interacción:

1. Inspeccionar y explicar objetos existentes sin modificarlos.
2. Generar SQL o propuestas de políticas para revisión.
3. Producir entregables del workshop: RACI, plan piloto, queries de lineage/audit y minuta.

Los prompts con DDL indican explícitamente que no deben ejecutar cambios automáticamente.

## Desplegar en Databricks Apps

Targets configurados:

- `dev`: `fe-sandbox-serverless-tko-nj.cloud.databricks.com`, perfil
  `fe-sandbox-tko-nj`.
- `demo`: `fevm-serverless-demo-nj.cloud.databricks.com`, perfil `fevm-demo`.

Validación y despliegue:

```bash
databricks bundle validate -t dev --profile fe-sandbox-tko-nj
databricks apps deploy -t dev --profile fe-sandbox-tko-nj

databricks bundle validate -t demo --profile fevm-demo
databricks apps deploy -t demo --profile fevm-demo
```

El target `demo` sustituye en la app el catálogo por
`serverless_demo_nj_catalog` y usa los governed tags permitidos por ese
metastore: `domain=finance`, `sensitivity=pii|internal|public` y
`pii_type=credit_card` para PAN.

## Documentación

- [Discover data](https://docs.databricks.com/aws/en/discover/)
- [Data discovery in Unity Catalog](https://docs.databricks.com/aws/en/data-governance/unity-catalog/data-discovery)
- [Unity Catalog](https://docs.databricks.com/aws/en/data-governance/unity-catalog/)
- [Row filters and column masks](https://docs.databricks.com/aws/en/data-governance/unity-catalog/filters-and-masks/)
- [Audit log system table](https://docs.databricks.com/aws/en/admin/system-tables/audit-logs)
