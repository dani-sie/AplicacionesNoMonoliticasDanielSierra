# Entrega 4: POC de arquitectura basada en eventos

POC técnico para el caso de estudio **Hogar de los Alpes**. La solución implementa una cadena mínima de microservicios para **Gestión de Trabajos**, **Asignación de Proveedores**, **Aprobación de Siniestros** y **Pagos/Compensaciones**, comunicados por comandos y eventos asíncronos sobre Apache Pulsar.

Esta carpeta es autónoma y contiene exclusivamente los artefactos técnicos de la entrega. El contenido académico de la materia se conserva por separado.

## Objetivo

Construir una base ejecutable para experimentar con tres atributos de calidad relevantes para el negocio y cubrir el alcance parcial de la Entrega 4:

- **Disponibilidad:** el trabajo puede continuar ante desconexiones, rechazos y fallos temporales de notificación.
- **Escalabilidad:** el procesamiento de trabajos, consultas y eventos puede crecer sin convertir el flujo en una operación bloqueante.
- **Modificabilidad:** los cambios de priorización, notificación y almacenamiento documental deben aislarse del dominio.

La entrega no pretende implementar todo el negocio. Su objetivo es dejar implementados los límites arquitecturales, el flujo mínimo de comandos y consultas, la persistencia y la comunicación por eventos que permitirán experimentar y evolucionar hacia Saga, BFF y compensaciones en la Entrega 5.

## Escenarios de calidad

La matriz completa se encuentra en [docs/matriz_escenarios_calidad.md](docs/matriz_escenarios_calidad.md). Los nueve escenarios son:

| Atributo | Escenarios |
|---|---|
| Disponibilidad | `DISP-01` Continuidad ante desconexión móvil; `DISP-02` Reasignación ante rechazo del proveedor; `DISP-03` Notificación diferida |
| Escalabilidad | `ESC-01` Procesamiento paralelo de lotes; `ESC-02` Escalamiento de consultas; `ESC-03` Recuperación paralela de eventos |
| Modificabilidad | `MOD-01` Cambio aislado de priorización; `MOD-02` Incorporación de canal de notificación; `MOD-03` Reemplazo del almacenamiento documental |

Cada escenario documenta fuente, estímulo, ambiente, artefacto, respuesta, medida de respuesta, decisiones arquitecturales, puntos de sensibilidad, trade-offs, riesgos y justificación.

## Arquitectura

La solución usa un contexto acotado de Gestión de Trabajos y una arquitectura de capas con inversión de dependencias:

- **Dominio:** agregado `Work`, entidad, objetos valor `WorkId` y `Location`, estado y evento `WorkCreated.v1`.
- **Aplicación:** comando `CreateWork` y consulta `GetWork`, siguiendo CQS.
- **Infraestructura:** adaptador de persistencia PostgreSQL, outbox transaccional y relay hacia Apache Pulsar.
- **Orquestación:** consumidor independiente del dominio que reacciona al evento y registra una auditoría.
- **Interfaces:** API HTTP con `POST /works` y `GET /works/{id}`.
- **Servicios de negocio:** Asignación de Proveedores, Aprobación de Siniestros y Pagos/Compensaciones consumen eventos de forma independiente y persisten sus propios modelos.

El dominio no depende de FastAPI, PostgreSQL ni Pulsar. La comunicación entre módulos se realiza mediante el evento de dominio, no mediante llamadas directas entre sus agregados.

El flujo ejecutable es:

```text
POST /works
  -> CreateWork
  -> agregado Work
  -> PostgreSQL: works + outbox_events
  -> outbox-relay
  -> Apache Pulsar
  -> event-consumer
  -> AssignProviderCommand.v1
  -> provider-assignment
  -> ProviderAssigned.v1 + ApproveClaimCommand.v1
  -> claim-approval
  -> ApprovalGranted.v1 + AuthorizePaymentCommand.v1
  -> payment-compensation
  -> PaymentAuthorized.v1
```

El diagrama completo está en [docs/architecture.md](docs/architecture.md). Las decisiones de mensajería y almacenamiento están en [docs/eventos_y_contratos.md](docs/eventos_y_contratos.md) y [docs/topologia_de_datos.md](docs/topologia_de_datos.md).

## Alcance de Entrega 4

| Requisito | Evidencia |
|---|---|
| Mínimo cuatro microservicios en Python | `api`, `provider-assignment`, `claim-approval`, `payment-compensation` |
| Comunicación asíncrona por Apache Pulsar | `docker-compose.yml`, workers en `services/`, contratos en `contracts/` |
| Comandos y eventos | `AssignProviderCommand.v1`, `ApproveClaimCommand.v1`, `AuthorizePaymentCommand.v1`, `WorkCreated.v1`, `ProviderAssigned.v1`, `ApprovalGranted.v1`, `PaymentAuthorized.v1` |
| Consulta síncrona solo para lectura | `GET /works/{work_id}` |
| Persistencia en al menos cuatro servicios | Tablas `works`, `provider_assignments`, `claim_approvals`, `payments` |
| CQS | `POST /works` como comando y `GET /works/{id}` como consulta |
| Decisiones de eventos, esquema y versionamiento | [docs/eventos_y_contratos.md](docs/eventos_y_contratos.md) |
| Topología de datos | [docs/topologia_de_datos.md](docs/topologia_de_datos.md) |
| Escenarios de calidad seleccionados para validar | [docs/experimentos_entrega_4.md](docs/experimentos_entrega_4.md) |
| Actividades de la entrega individual | [docs/actividades_equipo.md](docs/actividades_equipo.md) |

## Servicios Docker

| Servicio | Responsabilidad | Puerto |
|---|---|---:|
| `postgres` | Persistencia, outbox y auditoría | `5432` |
| `pulsar` | Transporte de eventos | `6650`, `8080` |
| `api` | Comandos y consultas HTTP | `8000` |
| `outbox-relay` | Publicación de eventos pendientes | interno |
| `event-consumer` | Consumo y auditoría de eventos | interno |
| `provider-assignment` | Asignación de proveedores | interno |
| `claim-approval` | Aprobación de siniestros | interno |
| `payment-compensation` | Pagos y compensaciones | interno |

El tópico utilizado por el POC es `persistent://public/default/hda-work-created-v1`.

Los comandos viajan por `hda-assign-provider-command-v1`, `hda-approve-claim-command-v1` y `hda-authorize-payment-command-v1`. Sus respuestas son los eventos `ProviderAssigned.v1`, `ApprovalGranted.v1` y `PaymentAuthorized.v1`.

## Requisitos

- Docker Desktop o Docker Engine con Docker Compose.
- Python 3.11 o superior para ejecutar las pruebas localmente.
- Puertos `8000`, `5432`, `6650` y `8080` disponibles.

## Ejecución

Levantar todos los servicios:

```bash
docker compose up --build
```

La API quedará disponible en `http://localhost:8000`. La documentación interactiva estará en `http://localhost:8000/docs`.

Crear un trabajo. El encabezado `Idempotency-Key` es obligatorio para que los reintentos no creen duplicados:

```bash
curl -X POST http://localhost:8000/works \
  -H 'Content-Type: application/json' \
  -H 'Idempotency-Key: demo-001' \
  -d '{"source":"CLAIM","category":"PLUMBING","urgency":"HIGH","city":"Bogota","partner_id":"partner-001"}'
```

Consultar el trabajo usando el identificador retornado:

```bash
curl http://localhost:8000/works/{work_id}
```

Detener los servicios:

```bash
docker compose down
```

## Verificación

Ejecutar las pruebas unitarias:

```bash
pytest -q
```

Consultar la outbox y la auditoría:

```bash
docker compose exec postgres psql -U hda -d hda \
  -c "select event_type, published_at from outbox_events;"

docker compose exec postgres psql -U hda -d hda \
  -c "select work_id, event_type, occurred_at from orchestration_audit;"

docker compose exec postgres psql -U hda -d hda \
  -c "select count(*) as works from works; select count(*) as provider_assignments from provider_assignments; select count(*) as claim_approvals from claim_approvals; select count(*) as payments from payments;"
```

La prueba manual validada para esta entrega confirma:

- `POST /works` crea y persiste un trabajo.
- Repetir el mismo comando con la misma clave devuelve el mismo identificador.
- `GET /works/{id}` recupera el agregado desde PostgreSQL.
- El relay publica el evento en Pulsar.
- El consumidor registra el evento en `orchestration_audit`.
- Los servicios de asignación, aprobación y pagos consumen comandos, persisten sus modelos y publican eventos de respuesta.

## Estructura

```text
app/
  domain/              Modelo, agregado, objetos valor y puertos
  application/         Comandos y consultas CQS
  infrastructure/      PostgreSQL, outbox, relay y Pulsar
  interfaces/          API HTTP
  orchestration/       Consumidor y reacción al evento
services/              Microservicios de negocio independientes
contracts/             Contratos versionados de eventos
db/                    Esquema PostgreSQL
docs/                  Matriz, arquitectura y diagramas
tests/                 Pruebas automatizadas
outputs/               PPTX y Excel de la Entrega 3
```

## Decisiones y trade-offs

- **Outbox transaccional:** evita confirmar el agregado sin registrar el evento. Agrega un proceso relay y consistencia eventual.
- **Pulsar:** desacopla los módulos y permite que los consumidores evolucionen de forma independiente. Aumenta la complejidad operativa frente a una llamada síncrona.
- **CQS:** separa la escritura de la lectura y prepara el escalamiento independiente. Requiere mantener modelos y flujos de prueba separados.
- **Arquitectura hexagonal/cebolla:** protege el dominio frente a cambios de infraestructura. Aumenta la cantidad de interfaces y adaptadores.
- **Idempotencia:** permite reintentos seguros, a cambio de conservar una clave única por operación.

## Continuidad

La Entrega 5 podrá coordinar `WorkCreated`, `ProviderAssigned`, `ApprovalGranted` y `PaymentAuthorized` mediante una Saga, Saga Log y BFF HTTP. Esos componentes no forman parte del alcance parcial de esta entrega, pero los comandos y eventos actuales ya dejan los puntos de integración preparados.

## Limitaciones

Este POC no incluye conectores reales con CRM, pasarela de pagos, certificadoras o ERP; despliegue externo; pruebas de carga distribuidas; observabilidad productiva ni una Saga completa. Esas capacidades se implementarán o validarán en las entregas posteriores.

## Artefactos

- [Presentación PPTX](outputs/Entrega3DanielSierra_entrega3_completa.pptx)
- [Matriz Excel con diagramas](outputs/entrega_3_matriz_escenarios_calidad_con_diagramas.xlsx)
- [Matriz en Markdown](docs/matriz_escenarios_calidad.md)
- [Vista de arquitectura](docs/architecture.md)
- [Eventos y contratos](docs/eventos_y_contratos.md)
- [Topología de datos](docs/topologia_de_datos.md)
- [Experimentos Entrega 4](docs/experimentos_entrega_4.md)
- [Checklist Entrega 4](docs/entrega_4_checklist.md)
- [Evidencia de ejecución](docs/evidencia_ejecucion.md)
- [Actividades de la entrega individual](docs/actividades_equipo.md)
- [Contrato `WorkCreated.v1`](contracts/work_created.v1.json)
- Contratos `ProviderAssigned.v1`, `ApprovalGranted.v1` y `PaymentAuthorized.v1`.
- Contratos de comandos `AssignProviderCommand.v1`, `ApproveClaimCommand.v1` y `AuthorizePaymentCommand.v1`.

Repositorio público: https://github.com/dani-sie/AplicacionesNoMonoliticasDanielSierra
