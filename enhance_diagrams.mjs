import fs from 'node:fs/promises';

const root = '\\\\wsl.localhost\\Debian\\home\\debian\\PROYECTOS\\DANIEL\\daniel-uniandes\\MISO\\NoMonoliticas\\Proyecto\\Modulo_3\\entregas\\semana_03\\docs\\diagramas';

const data = [
  ['DISP-01_continuidad_desconexion_movil.svg', '0 duplicados · 99,9% procesado tras reconexión', ['Señal offline', 'Clave única', 'Outbox', 'Reintento']],
  ['DISP-02_reasignacion_proveedor.svg', '100% rechazos trazables · reasignación en 60 s', ['Rechazo / SLA', 'Estado activo', 'Elegibles', 'Reasignar']],
  ['DISP-03_notificacion_diferida.svg', '0 cambios perdidos · 99% entregas en 10 min', ['Cambio de estado', 'Cola durable', 'Backoff', 'Entrega']],
  ['ESC-01_procesamiento_paralelo_lotes.svg', '10 lotes concurrentes · p95 de creación menor a 2 s', ['10 lotes', 'Particiones', 'Consumidores', 'p95: 2 s']],
  ['ESC-02_escalamiento_consultas.svg', '10× lecturas · p95 de consulta menor a 300 ms', ['10× lecturas', 'CQS', 'Réplicas', 'p95: 300 ms']],
  ['ESC-03_recuperacion_paralela_eventos.svg', '100.000 eventos · menos de 1% de errores', ['100.000 eventos', 'Offsets', 'Consumer groups', 'Error máximo 1%']],
  ['MOD-01_cambio_priorizacion.svg', 'Nueva regla en 3 días-persona · 0 adaptadores modificados', ['Nueva regla', 'Strategy', 'Dominio', '0 adaptadores']],
  ['MOD-02_incorporacion_canal_notificacion.svg', '0 cambios en productor · nuevo adaptador en un sprint', ['WhatsApp', 'Evento v1', 'Adaptador', '0 productor']],
  ['MOD-03_reemplazo_almacenamiento_documental.svg', '0 cambios en dominio · migración verificada por checksum', ['Nuevo storage', 'Puerto', 'Migración', 'Checksum']],
];

const esc = (value) => value.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');

const flowSvg = (metric, steps) => {
  const boxes = steps.map((step, index) => {
    const x = 990 + index * 135;
    const arrow = index < steps.length - 1
      ? `<line x1="${x + 112}" y1="533" x2="${x + 127}" y2="533" stroke="#405466" stroke-width="2" marker-end="url(#arrow)"/>`
      : '';
    return `<rect x="${x}" y="505" width="112" height="56" rx="10" fill="#eef4fa" stroke="#6d8497" stroke-width="2"/>
      <text x="${x + 56}" y="529" text-anchor="middle" class="flow">${esc(step)}</text>${arrow}`;
  }).join('\n');
  return `<g id="scenario-flow">
    <rect x="970" y="444" width="570" height="140" rx="14" fill="#f7f9fb" stroke="#c3d1dc" stroke-width="2"/>
    <text x="990" y="473" class="tiny">FLUJO DEL ESCENARIO</text>
    ${boxes}
    <text x="990" y="578" class="small">Meta: ${esc(metric)}</text>
  </g>`;
};

for (const [filename, metric, steps] of data) {
  const filePath = `${root}\\${filename}`;
  let svg = await fs.readFile(filePath, 'utf8');
  svg = svg.replace(/<g id="scenario-flow">[\s\S]*?<\/g>/, flowSvg(metric, steps));
  if (!svg.includes('.flow')) svg = svg.replace('</style>', '      .flow { font: 400 14px Arial, sans-serif; fill: #334756; }\n    </style>');
  if (filename.startsWith('DISP-01_')) {
    svg = svg.replace('class="small">proveedor</text>', 'class="small">proveedor / cola offline</text>');
  }
  await fs.writeFile(filePath, svg, 'utf8');
}

console.log(`Actualizados ${data.length} diagramas SVG.`);
