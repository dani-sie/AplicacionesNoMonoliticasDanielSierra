# Entrega 3: diseño de experimentación

POC técnico para el caso de estudio **Hogar de los Alpes**. El servicio implementado representa la capacidad inicial de **Gestión de Trabajos** y prepara la evolución hacia asignación de proveedores, aprobación y pagos.

Esta carpeta es autónoma y contiene exclusivamente los artefactos técnicos de la entrega. El contenido académico de la materia se conserva por separado.

## Objetivo

Construir una base ejecutable para experimentar con tres atributos de calidad relevantes para el negocio:

- **Disponibilidad:** el trabajo puede continuar ante desconexiones, rechazos y fallos temporales de notificación.
- **Escalabilidad:** el procesamiento de trabajos, consultas y eventos puede crecer sin convertir el flujo en una operación bloqueante.
- **Modificabilidad:** los cambios de priorización, notificación y almacenamiento documental deben aislarse del dominio.

La entrega no pretende implementar todo el negocio. Su objetivo es dejar implementados los límites arquitecturales, el flujo mínimo de comandos y consultas, la persistencia y la comunicación por eventos que permitirán experimentar en las siguientes entregas.

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
  -> orchestration_audit
```

El diagrama completo está en [docs/architecture.md](docs/architecture.md).

## Servicios Docker

| Servicio | Responsabilidad | Puerto |
|---|---|---:|
| `postgres` | Persistencia, outbox y auditoría | `5432` |
| `pulsar` | Transporte de eventos | `6650`, `8080` |
| `api` | Comandos y consultas HTTP | `8000` |
| `outbox-relay` | Publicación de eventos pendientes | interno |
| `event-consumer` | Consumo y auditoría de eventos | interno |

El tópico utilizado por el POC es `persistent://public/default/hda-work-created-v1`.

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
```

La prueba manual validada para esta entrega confirma:

- `POST /works` crea y persiste un trabajo.
- Repetir el mismo comando con la misma clave devuelve el mismo identificador.
- `GET /works/{id}` recupera el agregado desde PostgreSQL.
- El relay publica el evento en Pulsar.
- El consumidor registra el evento en `orchestration_audit`.

## Estructura

```text
app/
  domain/              Modelo, agregado, objetos valor y puertos
  application/         Comandos y consultas CQS
  infrastructure/      PostgreSQL, outbox, relay y Pulsar
  interfaces/          API HTTP
  orchestration/       Consumidor y reacción al evento
contracts/             Contratos versionados de eventos
db/                    Esquema PostgreSQL
docs/                  Matriz, arquitectura y diagramas
tests/                 Pruebas automatizadas
outputs/               PPTX y Excel de la entrega
```

## Decisiones y trade-offs

- **Outbox transaccional:** evita confirmar el agregado sin registrar el evento. Agrega un proceso relay y consistencia eventual.
- **Pulsar:** desacopla los módulos y permite que los consumidores evolucionen de forma independiente. Aumenta la complejidad operativa frente a una llamada síncrona.
- **CQS:** separa la escritura de la lectura y prepara el escalamiento independiente. Requiere mantener modelos y flujos de prueba separados.
- **Arquitectura hexagonal/cebolla:** protege el dominio frente a cambios de infraestructura. Aumenta la cantidad de interfaces y adaptadores.
- **Idempotencia:** permite reintentos seguros, a cambio de conservar una clave única por operación.

## Continuidad

La Entrega 4 puede agregar los contextos de Asignación de Proveedores, Aprobación de Partner/Siniestros y Pagos/Compensaciones, cada uno con su persistencia, comandos y eventos.

La Entrega 5 podrá coordinar `WorkCreated`, `ProviderAssigned`, `ApprovalGranted` y `PaymentAuthorized` mediante una Saga, Saga Log y BFF HTTP. Esos componentes no forman parte del alcance de esta entrega.

## Limitaciones

Este POC no incluye conectores reales con CRM, pasarela de pagos, certificadoras o ERP; despliegue externo; pruebas de carga distribuidas; observabilidad productiva ni una Saga completa. Esas capacidades se implementarán o validarán en las entregas posteriores.

## Artefactos

- [Presentación PPTX](outputs/Entrega3DanielSierra_entrega3_completa.pptx)
- [Matriz Excel con diagramas](outputs/entrega_3_matriz_escenarios_calidad_con_diagramas.xlsx)
- [Matriz en Markdown](docs/matriz_escenarios_calidad.md)
- [Vista de arquitectura](docs/architecture.md)
- [Contrato `WorkCreated.v1`](contracts/work_created.v1.json)

Al publicar el repositorio, agregar aquí el enlace público de GitHub.
