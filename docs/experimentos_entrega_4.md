# Experimentos de Entrega 4

La Entrega 4 valida un escenario por cada atributo de calidad definido en la Entrega 3. Los escenarios elegidos son relevantes para la POC porque se pueden observar con la cadena actual de comandos, eventos, persistencia y consultas.

## Escenario 1: `DISP-02` Reasignación ante rechazo del proveedor

| Campo | Definición |
|---|---|
| Atributo | Disponibilidad |
| Hipótesis | Si la asignación y aprobación están desacopladas por eventos, un fallo temporal de un consumidor no impide que el trabajo quede aceptado y pueda continuar cuando el consumidor vuelva a estar disponible. |
| Estímulo | Detener temporalmente `provider-assignment` o `claim-approval` después de crear trabajos. |
| Ambiente | Operación local de la POC con Apache Pulsar y PostgreSQL. |
| Artefacto | Servicios `api`, `outbox-relay`, `provider-assignment`, `claim-approval` y `payment-compensation`. |
| Respuesta esperada | Los eventos quedan durables en Pulsar/outbox y el flujo continúa cuando el consumidor se recupera. |
| Medida | El trabajo existe en `works`; al recuperar el consumidor, aparecen registros en `provider_assignments`, `claim_approvals` y `payments` sin recrear el trabajo. |
| Decisiones arquitecturales | Comunicación asíncrona, outbox transaccional, consumidores idempotentes con `ON CONFLICT DO NOTHING`. |
| Punto de sensibilidad | Retención de mensajes, política de suscripción, tiempo de recuperación del consumidor y unicidad por `work_id`. |
| Trade-off | Aumenta la complejidad operativa frente a llamadas síncronas directas. |
| Riesgo | Una mala configuración de retención o suscripciones puede perder eventos antes de que el consumidor vuelva. |

Consulta de evidencia:

```bash
docker compose exec postgres psql -U hda -d hda \
  -c "select count(*) from works; select count(*) from provider_assignments; select count(*) from claim_approvals; select count(*) from payments;"
```

## Escenario 2: `ESC-01` Procesamiento paralelo de lotes

| Campo | Definición |
|---|---|
| Atributo | Escalabilidad |
| Hipótesis | Si los servicios procesan comandos y eventos de forma independiente, el sistema puede aceptar múltiples trabajos sin bloquear la API mientras los consumidores avanzan de manera eventual. |
| Estímulo | Enviar un lote de solicitudes `POST /works` con claves de idempotencia distintas. |
| Ambiente | POC local con Docker Compose. |
| Artefacto | API, PostgreSQL, outbox, Pulsar y workers de negocio. |
| Respuesta esperada | La API responde a los comandos de creación y el procesamiento posterior se distribuye por los consumidores. |
| Medida | Para `N` trabajos creados, las tablas de los servicios alcanzan `N` registros por etapa después de un periodo de convergencia. |
| Decisiones arquitecturales | CQS, outbox, broker de eventos, servicios independientes y persistencia por servicio. |
| Punto de sensibilidad | Número de consumidores, particiones de tópicos, conexión a PostgreSQL y velocidad del relay. |
| Trade-off | La consistencia deja de ser inmediata y debe validarse como consistencia eventual. |
| Riesgo | Si todos los servicios comparten una sola base sin límites de conexión, PostgreSQL puede convertirse en cuello de botella de la POC. |

Consulta de evidencia:

```bash
docker compose exec postgres psql -U hda -d hda \
  -c "select 'works' tabla, count(*) from works union all select 'provider_assignments', count(*) from provider_assignments union all select 'claim_approvals', count(*) from claim_approvals union all select 'payments', count(*) from payments;"
```

## Escenario 3: `MOD-01` Cambio aislado de priorización

| Campo | Definición |
|---|---|
| Atributo | Modificabilidad |
| Hipótesis | Si el dominio depende de puertos y contratos, una regla de priorización o asignación puede cambiar en el servicio correspondiente sin modificar el agregado `Work` ni la API de creación. |
| Estímulo | Cambiar la lógica interna de `provider-assignment` para elegir proveedor o prioridad. |
| Ambiente | Desarrollo y prueba local. |
| Artefacto | Servicio `provider-assignment`, contrato `AssignProviderCommand.v1` y dominio `Work`. |
| Respuesta esperada | El cambio queda contenido en el worker/adaptador de asignación y no requiere cambios en `app/domain/work_model.py`. |
| Medida | Pruebas unitarias siguen pasando; `git diff` no muestra cambios en la capa de dominio para modificar la política del servicio de asignación. |
| Decisiones arquitecturales | Arquitectura hexagonal, contratos versionados, separación por microservicios y dominio sin dependencias de infraestructura. |
| Punto de sensibilidad | Estabilidad del contrato `AssignProviderCommand.v1` y frontera entre dominio y política operativa de asignación. |
| Trade-off | Hay más archivos y contratos que mantener. |
| Riesgo | Si se filtran reglas del servicio de asignación hacia el agregado `Work`, se rompe el aislamiento del dominio. |

Comando de evidencia:

```bash
pytest -q
git diff -- app/domain
```
