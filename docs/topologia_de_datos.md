# Topología de datos

La topología elegida es **descentralizada por propiedad lógica**. Cada microservicio escribe únicamente en sus propias tablas y expone cambios por comandos y eventos. Ningún servicio consulta las tablas de otro servicio.

| Servicio | Modelo | Tablas propias |
|---|---|---|
| Gestión de Trabajos | CRUD + outbox | `works`, `outbox_events` |
| Asignación de Proveedores | CRUD | `provider_assignments` |
| Aprobación de Siniestros | CRUD | `claim_approvals` |
| Pagos y Compensaciones | CRUD | `payments` |

Para mantener pequeño el entorno local, las tablas comparten un clúster PostgreSQL. Esto es una decisión de despliegue de la POC, no una dependencia de diseño: los adaptadores, permisos y conexiones pueden separarse en bases o instancias independientes sin cambiar el dominio.

El modelo CRUD es suficiente para esta entrega porque el objetivo es probar límites de comunicación, persistencia y escalamiento. La outbox añade durabilidad al evento de creación. Event Sourcing podrá evaluarse posteriormente si la trazabilidad completa de pagos o compensaciones se vuelve un requerimiento del negocio.
