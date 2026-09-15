# Checklist de Entrega 4

Este documento resume cómo la POC cubre los puntos obligatorios de la Entrega 4 y qué queda fuera del alcance parcial.

## Cumplimiento

| Punto de la guía | Estado | Evidencia |
|---|---|---|
| Implementar una arquitectura con mínimo cuatro microservicios en Python | Cubierto | `api`, `provider-assignment`, `claim-approval`, `payment-compensation` |
| Comunicación entre microservicios por comandos y eventos asíncronos | Cubierto | Apache Pulsar en `docker-compose.yml`; workers en `services/` |
| Uso de Apache Pulsar | Cubierto | Servicio `pulsar`, productores y consumidores con `pulsar-client` |
| Consultas síncronas solo para lectura | Cubierto | `GET /works/{work_id}` no dispara cambios de estado |
| Modelo de datos CRUD o Event Sourcing en cuatro servicios | Cubierto | CRUD en `works`, `provider_assignments`, `claim_approvals`, `payments` |
| Justificación de eventos, esquemas y versionamiento | Cubierto | `docs/eventos_y_contratos.md` y contratos JSON Schema en `contracts/` |
| Justificación de topología de datos | Cubierto con decisión explícita | `docs/topologia_de_datos.md` |
| Tres escenarios de calidad para validar | Cubierto documentalmente | `docs/experimentos_entrega_4.md` |
| Actividades del responsable | Documentado para entrega individual | `docs/actividades_equipo.md` |
| Despliegue en plataforma de preferencia | Preparado localmente | Docker Compose levanta API, PostgreSQL, Pulsar y workers; si el tutor exige URL pública, debe publicarse en la plataforma elegida |

## Fuera del alcance de Entrega 4

- Saga completa con compensaciones.
- Saga Log.
- BFF HTTP o GraphQL para CSaaS.
- Resultados finales cuantitativos y cualitativos de experimentación.
- Refinamiento final de mapas de contexto y vistas arquitectónicas.

Estos puntos se preparan con la cadena actual de eventos, pero corresponden principalmente a la Entrega 5.

## Evidencia mínima para sustentación

1. Levantar la POC con `docker compose up --build`.
2. Crear un trabajo con `POST /works`.
3. Consultar el trabajo con `GET /works/{work_id}`.
4. Consultar las tablas `works`, `provider_assignments`, `claim_approvals` y `payments`.
5. Mostrar los contratos versionados en `contracts/`.
6. Explicar por qué la POC usa eventos asíncronos, outbox y propiedad lógica de datos por servicio.
7. Aclarar que esta entrega prepara la transacción larga, pero no implementa todavía Saga, Saga Log ni BFF.
