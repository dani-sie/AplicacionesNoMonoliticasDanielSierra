import fs from 'node:fs/promises';
import path from 'node:path';
import { FileBlob, PresentationFile } from '@oai/artifact-tool';

const sourcePath = 'C:/Users/dsierra/OneDrive - ngds.biz/Escritorio/Entrega3DanielSierra.pptx';
const workspaceDir = 'C:/Users/dsierra';
const deliveryRoot = '\\\\wsl.localhost\\Debian\\home\\debian\\PROYECTOS\\DANIEL\\daniel-uniandes\\MISO\\NoMonoliticas\\Proyecto\\Modulo_3\\entregas\\semana_03';
const diagramDir = `${deliveryRoot}\\docs\\diagramas`;
const outputPath = `${deliveryRoot}\\outputs\\Entrega3DanielSierra_entrega3_completa.pptx`;

const scenarios = [
  {
    attribute: 'Disponibilidad', id: 'DISP-01', name: 'Continuidad ante desconexión móvil',
    statement: 'Si la aplicación móvil de un proveedor pierde conectividad mientras reporta el inicio o cierre de un trabajo, el sistema debe conservar la solicitud y procesarla cuando la conexión se restablezca, sin duplicar la operación.',
    source: 'Aplicación móvil del proveedor', stimulus: 'Se pierde la conectividad durante el inicio o cierre de un trabajo', environment: 'Producción, red móvil inestable', artifact: 'API de trabajos, outbox y consumidor de eventos', response: 'La operación se conserva, se procesa al recuperar la conexión y no se generan duplicados', measure: '0 operaciones duplicadas y al menos 99,9% de eventos pendientes procesados después de la reconexión', decision: 'Idempotencia mediante clave de operación, outbox transaccional y reintentos', sensitivity: 'Persistencia de la clave de idempotencia y duración de la retención', tradeoff: 'Aumenta el almacenamiento temporal y la complejidad del seguimiento', risk: 'Reenvíos con claves diferentes pueden duplicar operaciones; se mitiga con validación de correlación', justification: 'La aplicación móvil puede perder conectividad en cualquier momento. La clave de idempotencia permite reconocer reenvíos, mientras el outbox conserva el evento junto con la operación y los reintentos completan el procesamiento cuando la red se recupera. Así se mantiene la continuidad sin duplicar trabajos ni exigir una conexión permanente.', diagram: 'DISP-01_continuidad_desconexion_movil.png'
  },
  {
    attribute: 'Disponibilidad', id: 'DISP-02', name: 'Reasignación ante rechazo del proveedor',
    statement: 'Si el proveedor asignado rechaza un trabajo o no confirma su aceptación dentro del tiempo establecido, el sistema debe mantener la solicitud activa y permitir reasignarla a otro proveedor elegible.',
    source: 'Proveedor asignado', stimulus: 'Rechaza el trabajo o no confirma aceptación dentro del SLA', environment: 'Producción, operación activa', artifact: 'Módulo de asignación y catálogo de proveedores', response: 'El trabajo permanece activo, se registra el rechazo y se inicia una nueva selección', measure: '100% de rechazos trazables y nueva asignación iniciada dentro de 60 segundos', decision: 'Estado explícito de asignación, eventos de dominio y política de reintento y reasignación', sensitivity: 'SLA de confirmación y consistencia del catálogo de elegibles', tradeoff: 'La reasignación puede aumentar costos o tiempos de atención', risk: 'Reasignaciones repetitivas; se mitiga con límite de intentos y escalamiento manual', justification: 'El rechazo o la falta de respuesta de un proveedor no debe cerrar la solicitud del cliente. Un estado explícito permite distinguir pendiente, rechazado y reasignado, mientras los eventos de dominio activan una nueva selección sin acoplar el módulo de asignación al catálogo. El límite de intentos evita ciclos automáticos indefinidos.', diagram: 'DISP-02_reasignacion_proveedor.png'
  },
  {
    attribute: 'Disponibilidad', id: 'DISP-03', name: 'Notificación diferida',
    statement: 'Si el servicio de notificaciones no está disponible, el sistema debe registrar el cambio de estado del trabajo y entregar la notificación cuando el canal vuelva a estar operativo.',
    source: 'Servicio de notificaciones', stimulus: 'El canal de notificación queda fuera de servicio al cambiar el estado', environment: 'Producción, operación parcialmente degradada', artifact: 'Publicador de notificaciones y cola de eventos', response: 'El estado del trabajo se confirma aunque la notificación falle y esta se entrega posteriormente', measure: '0 cambios de estado perdidos y 99% de notificaciones entregadas en menos de 10 minutos tras la recuperación', decision: 'Comunicación asíncrona, cola durable, retry con backoff y DLQ', sensitivity: 'Capacidad de la cola y orden de notificaciones por trabajo', tradeoff: 'El usuario puede recibir la información con retraso', risk: 'Notificaciones obsoletas; se mitiga con versión de estado y coalescencia', justification: 'El cambio de estado pertenece al flujo principal y no debe depender de la disponibilidad temporal de un canal externo. Una cola durable desacopla la confirmación del trabajo de la entrega de la notificación, y el backoff con DLQ evita perder mensajes o bloquear el procesamiento. La versión del estado permite descartar avisos obsoletos.', diagram: 'DISP-03_notificacion_diferida.png'
  },
  {
    attribute: 'Escalabilidad', id: 'ESC-01', name: 'Procesamiento paralelo de lotes',
    statement: 'Cuando varios centros de atención cargan simultáneamente lotes de trabajos pendientes, el sistema debe procesarlos en paralelo sin bloquear la creación individual de nuevos trabajos.',
    source: 'Centros de atención', stimulus: 'Se cargan simultáneamente lotes de trabajos pendientes', environment: 'Producción, jornada de alta demanda', artifact: 'API de comandos, broker y consumidores de trabajos', response: 'Los lotes se procesan en paralelo sin bloquear la creación individual', measure: 'Procesar 10 lotes concurrentes manteniendo p95 de creación menor a 2 segundos', decision: 'Comandos asíncronos, particionamiento por centro y consumidores escalables', sensitivity: 'Número de particiones y tamaño de lote', tradeoff: 'Mayor paralelismo eleva el consumo de recursos y dificulta el orden global', risk: 'Una partición caliente puede generar espera; se mitiga con claves balanceadas', justification: 'Las cargas masivas y la creación de trabajos individuales compiten por recursos durante las jornadas de alta demanda. Los comandos asíncronos trasladan el procesamiento al broker, donde las particiones permiten distribuir los lotes entre consumidores. De esta forma el ingreso de nuevas solicitudes conserva una ruta independiente y el sistema puede aumentar consumidores según la demanda.', diagram: 'ESC-01_procesamiento_paralelo_lotes.png'
  },
  {
    attribute: 'Escalabilidad', id: 'ESC-02', name: 'Escalamiento de consultas',
    statement: 'Cuando aumenta la cantidad de consultas de seguimiento realizadas por clientes y agentes, el sistema debe escalar las lecturas sin aumentar proporcionalmente la capacidad de escritura.',
    source: 'Clientes y agentes', stimulus: 'Aumenta la consulta de estado y ubicación de trabajos activos', environment: 'Producción, predominio de lecturas', artifact: 'API de consulta, réplicas de lectura y caché', response: 'Las lecturas se escalan sin afectar el procesamiento de comandos', measure: 'Mantener p95 de consultas menor a 300 ms con 10 veces más lecturas que escrituras', decision: 'CQS, separación de modelos de lectura, réplicas y caché con expiración', sensitivity: 'Frescura aceptable del estado mostrado y política de invalidación', tradeoff: 'Se acepta consistencia eventual en las consultas', risk: 'Mostrar un estado desactualizado; se mitiga con marca de tiempo y versión del agregado', justification: 'El seguimiento genera un volumen de lectura muy superior al de cambios de estado. CQS separa la ruta de consulta de la ruta de comandos, y las réplicas junto con la caché permiten escalar la lectura de forma independiente. La marca de tiempo y la versión del agregado hacen visible la eventual desactualización para que el cliente interprete correctamente la respuesta.', diagram: 'ESC-02_escalamiento_consultas.png'
  },
  {
    attribute: 'Escalabilidad', id: 'ESC-03', name: 'Recuperación paralela de eventos',
    statement: 'Cuando se reprocesan eventos después de una interrupción del broker, el sistema debe recuperar el atraso de forma paralela sin detener la recepción de nuevos trabajos.',
    source: 'Plataforma de mensajería', stimulus: 'Se acumulan eventos durante una interrupción y deben reprocesarse', environment: 'Producción, recuperación del broker', artifact: 'Consumidores, tópicos y almacenamiento de offsets', response: 'El atraso se recupera en paralelo mientras continúan llegando nuevos trabajos', measure: 'Recuperar 100.000 eventos pendientes sin detener la recepción y con menos de 1% de errores', decision: 'Consumer groups, particionamiento, procesamiento idempotente y control de backpressure', sensitivity: 'Capacidad de consumidores, tamaño de lote y offsets', tradeoff: 'El orden global no está garantizado entre particiones', risk: 'Reprocesamiento fuera de orden; se mitiga con claves por agregado y estados versionados', justification: 'Una interrupción del broker puede dejar un atraso considerable mientras el negocio sigue recibiendo trabajos. Los grupos de consumidores y el particionamiento distribuyen la recuperación, mientras los offsets permiten reanudar sin perder eventos. El procesamiento idempotente y las versiones por agregado controlan los reintentos y limitan el impacto de un orden distinto entre particiones.', diagram: 'ESC-03_recuperacion_paralela_eventos.png'
  },
  {
    attribute: 'Modificabilidad', id: 'MOD-01', name: 'Cambio aislado de priorización',
    statement: 'Si el negocio cambia la regla para priorizar trabajos urgentes según zona, tipo de servicio y tiempo de espera, la modificación debe quedar aislada de la persistencia y de la API.',
    source: 'Negocio y operaciones', stimulus: 'Cambia la regla de prioridad según zona, tipo de servicio y tiempo de espera', environment: 'Desarrollo y despliegue controlado', artifact: 'Motor de decisión del dominio', response: 'La regla puede sustituirse sin modificar repositorios, API ni infraestructura', measure: 'Agregar una regla en menos de 3 días-persona y modificar 0 adaptadores', decision: 'Strategy o especificación de dominio, separada de persistencia y transporte', sensitivity: 'Contrato de entrada de la regla y precedencia entre criterios', tradeoff: 'Aumentan las clases y la necesidad de pruebas de reglas', risk: 'Reglas contradictorias; se mitiga con prioridad explícita y validación de escenarios', justification: 'Las reglas de priorización cambian con las políticas operativas y no deberían obligar a modificar la persistencia ni los contratos externos. Una estrategia o especificación de dominio concentra la decisión detrás de un contrato estable. El sistema gana modificabilidad porque el reemplazo de la regla queda localizado, aunque requiere ordenar criterios y ampliar las pruebas del dominio.', diagram: 'MOD-01_cambio_priorizacion.png'
  },
  {
    attribute: 'Modificabilidad', id: 'MOD-02', name: 'Incorporación de canal de notificación',
    statement: 'Si se incorpora un nuevo canal de notificación, como WhatsApp, el canal debe agregarse sin modificar el módulo que cambia el estado del trabajo ni los consumidores existentes.',
    source: 'Producto y operaciones', stimulus: 'Se incorpora WhatsApp como nuevo canal de notificación', environment: 'Evolución de producción', artifact: 'Adaptador de notificaciones y contrato WorkStatusChanged', response: 'El nuevo canal consume el evento sin cambiar el módulo de trabajos ni consumidores actuales', measure: '0 cambios en el productor y despliegue del adaptador en menos de un sprint', decision: 'Pub/Sub, eventos versionados, puerto de notificación y adaptador por canal', sensitivity: 'Compatibilidad del contrato y límites del proveedor externo', tradeoff: 'Aumenta la gobernanza de contratos y la observabilidad', risk: 'Un cambio incompatible afecta varios canales; se mitiga con versionamiento y pruebas de contrato', justification: 'Un nuevo canal debe evolucionar de manera independiente del módulo que registra el estado del trabajo. Publicar un evento versionado y ofrecer un puerto de notificación permite conectar un adaptador específico para WhatsApp sin alterar productores ni consumidores existentes. Las pruebas de contrato reducen el riesgo de propagar cambios incompatibles.', diagram: 'MOD-02_incorporacion_canal_notificacion.png'
  },
  {
    attribute: 'Modificabilidad', id: 'MOD-03', name: 'Reemplazo del almacenamiento documental',
    statement: 'Si la organización cambia el proveedor de almacenamiento de documentos asociados a un trabajo, debe ser posible reemplazar el adaptador sin modificar la entidad ni las reglas del dominio.',
    source: 'Arquitectura e infraestructura', stimulus: 'Se reemplaza el almacenamiento de documentos asociados al trabajo', environment: 'Desarrollo y migración', artifact: 'Puerto de documentos y adaptador de almacenamiento', response: 'Se cambia el adaptador y se migran documentos sin modificar la entidad Work ni sus reglas', measure: '0 cambios en la capa de dominio y migración verificable por checksum', decision: 'Inversión de dependencias, puerto de almacenamiento y adaptadores intercambiables', sensitivity: 'Contrato del puerto, compatibilidad de metadatos y estrategia de migración', tradeoff: 'La abstracción agrega código y puede ocultar diferencias entre proveedores', risk: 'Pérdida o corrupción durante migración; se mitiga con checksum, doble lectura y rollback', justification: 'La entidad Work y sus reglas representan el negocio, mientras que el proveedor de almacenamiento es una decisión externa. La inversión de dependencias deja un puerto estable en el núcleo y mueve cada proveedor a un adaptador intercambiable. La migración con checksum, doble lectura y rollback protege los documentos sin contaminar el dominio con detalles de infraestructura.', diagram: 'MOD-03_reemplazo_almacenamiento_documental.png'
  },
];

const matrixRows = (s, index) => [
  [`Atributo de calidad ${Math.floor(index / 3) + 1}: ${s.attribute}`, '', '', ''],
  [`Escenario #: ${index + 1}`, `${s.id} - ${s.name}: ${s.statement}`, '', ''],
  ['Fuente', s.source, '', ''],
  ['Estímulo', s.stimulus, '', ''],
  ['Ambiente', s.environment, '', ''],
  ['Artefacto', s.artifact, '', ''],
  ['Respuesta', s.response, '', ''],
  ['Medida de la respuesta', s.measure, '', ''],
  ['Decisiones Arquitecturales', 'Punto de sensibilidad', 'Tradeoff', 'Riesgo'],
  [s.decision, s.sensitivity, s.tradeoff, s.risk],
  ['Justificación', s.justification, '', ''],
];

const fillTable = (table, rows) => {
  for (let r = 0; r < rows.length; r += 1) {
    for (let c = 0; c < rows[r].length; c += 1) {
      if (rows[r][c] !== '') table.cells.set(r, c, rows[r][c]);
    }
  }
};

const presentation = await PresentationFile.importPptx(await FileBlob.load(sourcePath));
const slides = presentation.slides.items;
if (slides.length !== 19) throw new Error(`Se esperaba la plantilla de 19 diapositivas, se encontraron ${slides.length}.`);

slides[0].placeholders.getItem('title').text = 'Entrega 3: Gestión de Trabajos';

for (let i = 0; i < scenarios.length; i += 1) {
  const s = scenarios[i];
  const matrixSlide = slides[1 + i * 2];
  const diagramSlide = slides[2 + i * 2];
  matrixSlide.placeholders.getItem('title').text = `Atributo de calidad ${Math.floor(i / 3) + 1}: ${s.attribute}`;
  fillTable(matrixSlide.tables.items[0], matrixRows(s, i));
  diagramSlide.background.fill = '#FFFFFF';
  const imageBytes = await fs.readFile(`${diagramDir}\\${s.diagram}`);
  diagramSlide.images.add({
    blob: imageBytes,
    contentType: 'image/png',
    alt: `Diagrama de arquitectura para ${s.id} ${s.name}`,
    fit: 'contain',
    position: { left: 0, top: 44, width: 2111, height: 1187 },
  });
}

const candidateDir = `${deliveryRoot}\\.codex-finalizer`;
await fs.mkdir(candidateDir, { recursive: true });
await fs.mkdir(`${deliveryRoot}\\outputs`, { recursive: true });
const candidatePath = `${candidateDir}\\entrega3_candidate.pptx`;
await (await PresentationFile.exportPptx(presentation)).save(candidatePath);
console.log(JSON.stringify({ candidatePath, outputPath, slides: slides.length }, null, 2));
