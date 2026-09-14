# Vista de arquitectura

```mermaid
flowchart LR
  Partner[Partner / API] --> Command[Command handler]
  Command --> Domain[Work aggregate\nDomain model]
  Domain --> Repo[Repository port]
  Repo --> PG[(PostgreSQL)]
  Repo --> Outbox[(Outbox events)]
  Outbox --> Relay[Outbox relay]
  Relay --> Broker[Apache Pulsar\npublic/default/hda-work-created-v1]
  Broker --> Audit[Orchestration module\nEvent consumer]
  Audit --> AuditDB[(PostgreSQL\nAudit projection)]
  Query[Query handler] --> Repo
```

El comando y la consulta entran por la interfaz HTTP, pero el dominio no depende de HTTP, PostgreSQL ni Pulsar. El módulo de orquestación solo conoce el contrato del evento; no importa la agregación de trabajo ni consulta sus tablas.

## Puntos de sensibilidad

- El pool, los índices y el particionamiento de PostgreSQL afectan escalabilidad.
- La transacción PostgreSQL + outbox afecta fiabilidad y no debe reemplazarse por dos escrituras independientes.
- El tópico y las particiones de Apache Pulsar afectan escalabilidad y orden de eventos.
- El contrato y la clave de idempotencia afectan la consistencia del módulo `orchestration`.
- La frontera entre dominio e infraestructura afecta modificabilidad y testabilidad.
