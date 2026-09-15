# BFF REST de CSaaS

El BFF expone una interfaz HTTP para iniciar una transacción de Hogar de los Alpes y consultar el estado de la Saga. La interfaz está separada de la lógica de dominio y delega la creación del trabajo al caso de uso existente.

## Iniciar una Saga

```http
POST http://localhost:8001/api/v1/sagas/works
Content-Type: application/json
Idempotency-Key: bff-demo-001
```

```json
{
  "source": "CLAIM",
  "category": "PLUMBING",
  "urgency": "HIGH",
  "city": "Bogota",
  "partner_id": "partner-bff"
}
```

Respuesta esperada:

```json
{
  "work_id": "<uuid>",
  "status": "STARTED",
  "saga_status": "PENDING"
}
```

## Consultar la Saga

```http
GET http://localhost:8001/api/v1/sagas/<work_id>
```

La respuesta contiene el estado final y el historial de pasos registrado en `saga_log`. En una transacción exitosa el estado final es `COMPLETED`; en una transacción con fallo controlado es `COMPENSATED`.

La documentación interactiva está disponible en `http://localhost:8001/docs`.

## Ejecución

```bash
docker compose up --build -d
```

Para probar la compensación, iniciar el orquestador con `SAGA_FAIL_STEP=APPROVAL` y crear un trabajo nuevo. El resultado debe registrar `APPROVAL FAILED`, `COMPENSATION_COMPLETED` y `TRANSACTION_COMPENSATED`.
