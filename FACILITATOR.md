# Guía del facilitador

## Antes de la sesión

1. Abre la app y reinicia el progreso.
2. Prepara seis pestañas, en este orden:
   - Discover.
   - Catalog Explorer en `diners_governance.tarjetas.transacciones_tarjeta`.
   - SQL editor con `scripts/02_demo_queries.sql`.
   - Consulta como consumidor.
   - Lineage.
   - System tables / audit.
3. Verifica `scripts/01_demo_setup.sql` en un SQL Warehouse.
4. Si usarás dos identidades, confirma que una pertenece a `admins` y la otra no.
5. Captura cada pantalla como respaldo.

## Regla narrativa

Una sola tabla recorre todo:

`Discover → descripción y certificación → tags/PII → GRANT/ABAC → mask/row filter → consulta → lineage → audit`

No abras un segundo caso de uso. Los features avanzados son callouts:

- Volumes: documentos y políticas.
- Federation: Teradata bajo un acceso gobernado sin migración inicial.
- Delta Sharing y Clean Rooms: colaboración con filiales, comercios o terceros.
- Iceberg: interoperabilidad con otros motores.
- IA: modelos, Genie y agentes bajo el mismo gobierno.

## Distribución de tiempo

- 0–8: contexto y objetos.
- 8–23: tres niveles + Discovery.
- 23–65: demo continua.
- 65–80: diseño objetivo para Diners.
- 80–90: cierre y próximo laboratorio.

Si al minuto 55 estás atrasado, omite calidad y Metric Views. No omitas:

1. Discover.
2. Mismo SQL con política de acceso.
3. Lineage.
4. Audit.

## Preguntas de discovery

- ¿Qué evidencia pide con mayor frecuencia auditoría?
- ¿Quién es responsable de certificar un activo de Tarjetas o Fraude?
- ¿Qué grupos llegan hoy desde el IdP?
- ¿La segmentación principal es por país, filial, rol o propósito?
- ¿Qué activos deben coexistir con Teradata?
- ¿Se comparten datos con filiales, adquirentes, comercios o terceros?

## Resultado que debe quedar acordado

- Dos dominios piloto: recomendación `Tarjetas/Fraude` y `Cobranzas/Crédito`.
- Owner y curator por dominio.
- Grupos consumidores y aprobadores.
- Taxonomía inicial: `domain`, `sensitivity`, `criticality`, `contains_pii`.
- Una mask, un row filter y una política ABAC para el lab.
- Fecha del siguiente laboratorio.
