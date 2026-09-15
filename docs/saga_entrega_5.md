# Saga de Entrega 5

La Entrega 5 extiende la POC con una Saga orquestada. El orquestador controla la transacción larga y utiliza los eventos existentes como confirmaciones de cada paso.

## Flujo exitoso

```text
WorkCreated -> AssignProviderCommand -> ProviderAssigned
-> ApproveClaimCommand -> ApprovalGranted
-> AuthorizePaymentCommand -> PaymentAuthorized
-> TRANSACTION_COMPLETED
```

Cada transición se registra en `saga_log` con `saga_id`, `work_id`, paso, acción, estado, detalle y fecha. El estado final de una transacción exitosa es `COMPLETED`.

## Flujo fallido y compensación

El fallo controlado se activa con `SAGA_FAIL_STEP=APPROVAL`. La Saga registra el fallo, publica `CancelProviderAssignmentCommand` y el handler de compensación cambia la asignación a `CANCELLED`.

```text
ProviderAssigned -> APPROVAL FAILED
-> CancelProviderAssignmentCommand
-> provider assignment CANCELLED
-> TRANSACTION_COMPENSATED
```

El estado final es `COMPENSATED`. La compensación es idempotente por `work_id` y queda registrada en `saga_log`.

## Justificación

Se eligió orquestación porque la transacción tiene pasos secuenciales y requiere visibilidad centralizada. El orquestador facilita consultar el progreso, aplicar una política uniforme de errores y ejecutar compensaciones.

## Evidencia

```bash
docker compose exec postgres psql -U hda -d hda \
  -c "select step, action, status from saga_log order by id;"
```

Para demostrar el fallo controlado:

```bash
SAGA_FAIL_STEP=APPROVAL docker compose up -d --force-recreate event-consumer provider-compensation
```
