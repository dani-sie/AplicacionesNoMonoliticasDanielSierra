# Eventos y comandos

## Decisión

La comunicación entre los cuatro microservicios usa Apache Pulsar. Se eligió JSON Schema para esta POC porque permite inspeccionar los mensajes durante la sustentación y validar contratos sin agregar un compilador al proceso de despliegue. En una implementación productiva con mayor volumen o múltiples lenguajes, Avro sería una alternativa para reducir tamaño y centralizar compatibilidad.

Los comandos expresan una intención dirigida a un servicio. Los eventos expresan un hecho ocurrido y pueden tener varios consumidores:

| Mensaje | Tipo | Productor | Consumidor |
|---|---|---|---|
| `WorkCreated.v1` | Evento de dominio | Gestión de Trabajos | Orquestación y auditoría |
| `AssignProviderCommand.v1` | Comando | Orquestación | Asignación de Proveedores |
| `ProviderAssigned.v1` | Evento de integración | Asignación de Proveedores | Aprobación |
| `ApproveClaimCommand.v1` | Comando | Asignación de Proveedores | Aprobación |
| `ApprovalGranted.v1` | Evento de integración | Aprobación | Pagos |
| `AuthorizePaymentCommand.v1` | Comando | Aprobación | Pagos |
| `PaymentAuthorized.v1` | Evento de integración | Pagos | Futuros consumidores |

## Versionamiento

Cada contrato tiene un sufijo de versión (`.v1`) y un archivo JSON Schema en `contracts/`. Un cambio incompatible crea un nuevo contrato y un nuevo tópico, por ejemplo `ProviderAssigned.v2`; no se modifica el significado de `.v1` después de publicarlo. Los cambios compatibles deben ser aditivos y los consumidores deben ignorar campos desconocidos.

## Preparación para Entrega 5

La Entrega 4 no implementa una Saga. La cadena actual solamente deja los servicios, comandos, eventos, tópicos y modelos de datos listos para que en la Entrega 5 se pueda coordinar una transacción larga con Saga, Saga Log, compensaciones y BFF.

Los eventos `ProviderAssigned.v1`, `ApprovalGranted.v1` y `PaymentAuthorized.v1` son los puntos de observación que permitirán construir esa coordinación sin cambiar los contratos base de esta POC.
