import path from 'node:path';
import { pathToFileURL } from 'node:url';
const { finalizePresentation } = await import(pathToFileURL('C:/Users/dsierra/.codex/plugins/cache/openai-primary-runtime/presentations/26.905.11957/skills/presentations/container_tools/artifact_tool_utils.mjs').href);

const workspaceDir = 'C:/Users/dsierra/pptx_build';
const candidatePath = 'C:/Users/dsierra/pptx_build/finalized_delivery_v3/entrega3_candidate.pptx';
const finalPath = 'C:/Users/dsierra/pptx_build/finalized_delivery_v3/Entrega3DanielSierra_entrega3_completa_v3.pptx';
const skillDir = 'C:/Users/dsierra/.codex/plugins/cache/openai-primary-runtime/presentations/26.905.11957/skills/presentations';

const result = await finalizePresentation({
  explicitTotalSlideCount: 19,
  workspaceDir,
  candidatePath,
  finalPath,
  pythonExecutable: 'C:/Users/dsierra/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',
  integrityValidatorPath: path.join(skillDir, 'container_tools/inspect_presentation_package_integrity.py'),
  layoutValidatorPath: path.join(skillDir, 'container_tools/inspect_presentation_layout_geometry.py'),
  layoutArgs: ['--expected-slide-size-emu', '20104100,12141200', '--validate-bullet-geometry', '--validate-heading-fit'],
  verifyArtifactToolImport: true,
  receiptPath: `${workspaceDir}\\Entrega3DanielSierra_entrega3_completa_v3.validation.json`,
});
console.log(JSON.stringify(result, null, 2));
