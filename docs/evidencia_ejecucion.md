# Evidencia de ejecución

Este documento describe cómo demostrar la POC de Entrega 4 durante la sustentación. El objetivo no es probar que Apache Pulsar funciona, sino evidenciar que la arquitectura soporta comunicación desacoplada por comandos y eventos, persistencia por servicio y preparación para una transacción larga futura.

## 1. Levantar la POC

```bash
docker compose up --build
```

Servicios esperados:

| Servicio | Rol |
|---|---|
| `api` | Recibe comandos HTTP y consultas de lectura |
| `postgres` | Persistencia de modelos y outbox |
| `pulsar` | Broker de comandos y eventos |
| `outbox-relay` | Publica eventos pendientes desde la outbox |
| `event-consumer` | Consume `WorkCreated.v1` y publica `AssignProviderCommand.v1` |
| `provider-assignment` | Consume comando de asignación, persiste asignación y publica evento/comando posterior |
| `claim-approval` | Consume comando de aprobación, persiste aprobación y publica evento/comando posterior |
| `payment-compensation` | Consume comando de pago, persiste autorización y publica evento final |

## 2. Crear un trabajo

```bash
curl -X POST http://localhost:8000/works \
  -H 'Content-Type: application/json' \
  -H 'Idempotency-Key: demo-entrega-4-001' \
  -d '{"source":"CLAIM","category":"PLUMBING","urgency":"HIGH","city":"Bogota","partner_id":"partner-001"}'
```

Respuesta esperada:

```json
{
  "id": "<uuid>",
  "status": "ACCEPTED",
  "source": "CLAIM"
}
```

## 3. Consultar el trabajo

```bash
curl http://localhost:8000/works/<uuid>
```

Respuesta esperada:

```json
{
  "id": "<uuid>",
  "status": "ACCEPTED",
  "source": "CLAIM",
  "category": "PLUMBING",
  "urgency": "HIGH",
  "city": "Bogota",
  "partner_id": "partner-001"
}
```

## 4. Verificar persistencia y eventos

```bash
docker compose exec postgres psql -U hda -d hda \
  -c "select id, status, source, category from works;"
```

```bash
docker compose exec postgres psql -U hda -d hda \
  -c "select event_type, published_at from outbox_events;"
```

```bash
docker compose exec postgres psql -U hda -d hda \
  -c "select work_id, provider_id, status from provider_assignments;"
```

```bash
docker compose exec postgres psql -U hda -d hda \
  -c "select work_id, provider_id, status from claim_approvals;"
```

```bash
docker compose exec postgres psql -U hda -d hda \
  -c "select work_id, status from payments;"
```

Resultado esperado:

- `works` contiene el trabajo creado.
- `outbox_events` contiene `WorkCreated.v1` con `published_at` no nulo.
- `provider_assignments` contiene una asignación `ASSIGNED`.
- `claim_approvals` contiene una aprobación `APPROVED`.
- `payments` contiene una autorización `AUTHORIZED`.

## 5. Verificar idempotencia

Ejecutar nuevamente el mismo `POST /works` con el mismo encabezado `Idempotency-Key`.

Resultado esperado:

- La API devuelve el mismo identificador.
- No se duplica el trabajo.
- Las tablas de los servicios mantienen un único registro por `work_id`.

Consulta:

```bash
docker compose exec postgres psql -U hda -d hda \
  -c "select idempotency_key, count(*) from works group by idempotency_key;"
```

## 6. Verificar pruebas automatizadas

```bash
pytest -q
```

Resultado esperado:

```text
4 passed
```

## 7. Lectura arquitectural para la sustentación

Esta POC demuestra:

- Uso de comandos y eventos asíncronos entre servicios.
- Ausencia de llamadas HTTP o gRPC entre microservicios.
- Persistencia por servicio con propiedad lógica de datos.
- Separación CQS entre comando de creación y consulta de lectura.
- Contratos versionados con JSON Schema.
- Preparación de la cadena para una Saga futura en Entrega 5, sin implementar todavía Saga, Saga Log ni BFF.
