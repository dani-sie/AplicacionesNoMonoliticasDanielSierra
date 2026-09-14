# Entrega 3: diseño de experimentación

POC técnico del servicio **Gestión de Trabajos** para el caso de estudio Hogar de los Alpes. Esta carpeta es independiente del repositorio que contiene el material académico de la materia.

## Alcance

El POC acepta un trabajo, valida el agregado de dominio, persiste la operación en PostgreSQL, publica un evento de dominio mediante Apache Pulsar y permite consultar su estado. El alcance es mínimo y prepara los contratos y límites que se probarán en las siguientes entregas.

## Atributos y escenarios

| Atributo | Escenarios |
|---|---|
| Disponibilidad | `DISP-01` Continuidad ante desconexión móvil; `DISP-02` Reasignación ante rechazo del proveedor; `DISP-03` Notificación diferida |
| Escalabilidad | `ESC-01` Procesamiento paralelo de lotes; `ESC-02` Escalamiento de consultas; `ESC-03` Recuperación paralela de eventos |
| Modificabilidad | `MOD-01` Cambio aislado de priorización; `MOD-02` Incorporación de canal de notificación; `MOD-03` Reemplazo del almacenamiento documental |

La matriz completa está en [docs/matriz_escenarios_calidad.md](docs/matriz_escenarios_calidad.md). Cada escenario documenta fuente, estímulo, ambiente, artefacto, respuesta, medida, decisiones arquitecturales, puntos de sensibilidad, trade-offs, riesgos y justificación.

## Decisiones de diseño

- **Contexto acotado:** Gestión de Trabajos.
- **DDD:** entidad `Work`, objetos valor `WorkId` y `Location`, agregado `Work`, repositorios y eventos de dominio.
- **Módulos:** `work` contiene dominio y aplicación; `orchestration` consume eventos sin llamadas directas a `work`.
- **Arquitectura:** capas/cebolla y puertos y adaptadores. El dominio no depende de HTTP, PostgreSQL ni Pulsar.
- **Eventos:** PostgreSQL conserva el cambio y el evento en una outbox transaccional; un relay publica el evento en `persistent://public/default/hda-work-created-v1` y el consumidor de orquestación registra su recepción.
- **CQS:** `POST /works` ejecuta `CreateWork`; `GET /works/{id}` ejecuta `GetWork`.
- **Persistencia:** PostgreSQL real. No se usa SQLite, H2 ni otra base de prueba.
- **Idempotencia:** la creación recibe una clave de operación para evitar duplicados en reintentos.

El detalle visual está en [docs/architecture.md](docs/architecture.md). Los nueve diagramas están en `docs/diagramas/` y también se incluyen en el PPTX.

## Ejecución local

Requisitos: Docker y Docker Compose.

```bash
docker compose up --build
```

El compose levanta cinco procesos: PostgreSQL, Pulsar, la API, el relay de outbox y el consumidor de orquestación. Los dos últimos reintentan la conexión mientras las dependencias terminan de iniciar.

Crear un trabajo:

```bash
curl -X POST http://localhost:8000/works -H 'Content-Type: application/json' -H 'Idempotency-Key: demo-001' -d '{"source":"CLAIM","category":"PLUMBING","urgency":"HIGH","city":"Bogota","partner_id":"partner-001"}'
```

Consultar el trabajo con el identificador retornado:

```bash
curl http://localhost:8000/works/{work_id}
```

Verificar la publicación y auditoría del evento:

```bash
docker compose exec postgres psql -U hda -d hda -c "select event_type, published_at from outbox_events;"
docker compose exec postgres psql -U hda -d hda -c "select work_id, event_type, occurred_at from orchestration_audit;"
```

Ejecutar pruebas:

```bash
pytest
```

## Artefactos

- `outputs/Entrega3DanielSierra_entrega3_completa.pptx`
- `outputs/entrega_3_matriz_escenarios_calidad_con_diagramas.xlsx`
- Código fuente del POC.
- Matriz, diagramas y contrato `contracts/work_created.v1.json`.

El flujo ejecutable es: `POST /works` -> agregado `Work` -> transacción PostgreSQL (`works` + `outbox_events`) -> relay -> Pulsar -> `event-consumer` -> `orchestration_audit`. La consulta `GET /works/{id}` pertenece al lado de lectura de CQS.

## Continuidad

La Entrega 4 agregará Asignación de Proveedores, Aprobación de Partner/Siniestros y Pagos/Compensaciones, cada uno con su persistencia y comunicación por comandos y eventos.

La Entrega 5 podrá coordinar `WorkCreated`, `ProviderAssigned`, `ApprovalGranted` y `PaymentAuthorized` mediante una Saga, Saga Log y BFF HTTP. Esos componentes no forman parte del alcance de esta entrega.

## Limitaciones

Los conectores reales a CRM, pasarela de pagos, certificadoras y ERP, la observabilidad productiva, las pruebas de carga distribuidas y el despliegue externo quedan para iteraciones posteriores.
