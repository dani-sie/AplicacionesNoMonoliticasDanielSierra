# Actividades de la entrega individual

La entrega es desarrollada por **Daniel Sierra** como único integrante. Las contribuciones se documentan por actividad para facilitar la revisión del tutor y la sustentación.

| Responsable | Actividad | Evidencia |
|---|---|---|
| Daniel Sierra | Diseño de escenarios de calidad, documentación de decisiones arquitecturales, estructura del repositorio y validación de la POC. | `README.md`, `docs/matriz_escenarios_calidad.md`, `docs/experimentos_entrega_4.md`, `docs/entrega_4_checklist.md` |
| Daniel Sierra | Implementación del microservicio de Gestión de Trabajos con DDD, CQS, API HTTP, persistencia PostgreSQL y outbox transaccional. | `app/domain/`, `app/application/`, `app/interfaces/http.py`, `app/infrastructure/persistence/work_postgres.py`, `db/init.sql` |
| Daniel Sierra | Implementación de comunicación asíncrona con Apache Pulsar y servicios de Asignación, Aprobación y Pagos/Compensaciones. | `docker-compose.yml`, `app/infrastructure/messaging/outbox_relay.py`, `app/orchestration/pulsar_consumer.py`, `services/`, `contracts/` |
| Daniel Sierra | Preparación de evidencia de ejecución, comandos de verificación, consultas SQL e instrucciones de despliegue local. | `docs/evidencia_ejecucion.md`, `docker-compose.yml`, `README.md` |
