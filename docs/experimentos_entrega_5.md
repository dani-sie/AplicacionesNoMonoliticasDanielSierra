# Experimentos de Entrega 5

## Objetivo

Validar que la arquitectura basada en eventos ejecuta una transacción distribuida mediante una Saga orquestada, registra su avance y compensa los pasos completados cuando ocurre un fallo.

La hipótesis es: **si el flujo se coordina mediante un orquestador, eventos de dominio y un Saga Log persistente, entonces una transacción exitosa llegará a un estado consistente y una transacción fallida podrá compensar los pasos previos sin intervención manual.**

## Escenario exitoso

Se creó un trabajo mediante el BFF con la clave `entrega5-demo-002`.

| Campo | Resultado |
|---|---|
| Identificador | `50a91816-afd2-4f8b-8d0b-04b705d6913b` |
| Fuente | BFF REST público |
| Estímulo | `POST /api/v1/sagas/works` |
| Ambiente | VM Debian en Google Cloud, Docker Compose, Apache Pulsar y PostgreSQL |
| Respuesta inicial | HTTP `202`, estado `STARTED` y Saga `PENDING` |
| Resultado final | Saga `COMPLETED` |
| Tiempo observado | Aproximadamente 0,67 segundos |

El flujo observado fue `START_SAGA`, `ASSIGN_PROVIDER`, `APPROVAL`, `PAYMENT` y `TRANSACTION_COMPLETED`. Esto confirma que el BFF acepta la solicitud sin bloquear la ejecución y que los servicios avanzan mediante comandos y eventos asíncronos.

## Escenario fallido y compensación

Se habilitó el fallo controlado en `APPROVAL` mediante `SAGA_FAIL_STEP=APPROVAL` y se creó un trabajo con la clave `entrega5-fallo-001`.

| Campo | Resultado |
|---|---|
| Identificador | `26eba04c-6338-479a-b02d-2c67035046a9` |
| Fuente | BFF REST público |
| Estímulo | Fallo inyectado durante la aprobación |
| Ambiente | VM Debian con el consumidor configurado para fallar en `APPROVAL` |
| Resultado final | Saga `COMPENSATED` |
| Tiempo observado | Aproximadamente 0,33 segundos |
| Evidencia | Asignación de proveedor en estado `CANCELLED` |

La secuencia observada fue `ASSIGN_PROVIDER` completado, `APPROVAL` fallido, `COMPENSATION_REQUESTED`, `COMPENSATION_COMPLETED` y `TRANSACTION_COMPENSATED`. La operación de compensación fue idempotente y el estado final permaneció consistente.

## Evidencia SQL

```bash
docker-compose exec postgres psql -U hda -d hda \
  -c "select step, action, status, occurred_at from saga_log where work_id='50a91816-afd2-4f8b-8d0b-04b705d6913b' order by occurred_at;"
```

```bash
docker-compose exec postgres psql -U hda -d hda \
  -c "select step, action, status, occurred_at from saga_log where work_id='26eba04c-6338-479a-b02d-2c67035046a9' order by occurred_at;"
```

```bash
docker-compose exec postgres psql -U hda -d hda \
  -c "select work_id, provider_id, status from provider_assignments where work_id='26eba04c-6338-479a-b02d-2c67035046a9';"
```

## Conclusión

La hipótesis se confirma para el alcance de la POC. La transacción exitosa alcanzó `COMPLETED`; ante un fallo en aprobación, el orquestador solicitó la compensación y la asignación quedó en `CANCELLED`. El resultado demuestra consistencia eventual, trazabilidad mediante Saga Log y recuperación controlada sin llamadas síncronas entre servicios.

La medición corresponde a una POC de un solo nodo y no representa capacidad productiva global. Para evaluar escalabilidad se requieren cargas mayores, múltiples réplicas y métricas bajo concurrencia.
