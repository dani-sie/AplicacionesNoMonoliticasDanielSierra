import { FileBlob, PresentationFile } from '@oai/artifact-tool';

const sourcePath = 'C:/Users/dsierra/OneDrive - ngds.biz/Escritorio/Entrega3DanielSierra.pptx';
const presentation = await PresentationFile.importPptx(await FileBlob.load(sourcePath));
console.log('slides', presentation.slides.items.length);
console.log('size', presentation.slideSize);
console.log('deck', (await presentation.inspect({ kind: 'deck', maxChars: 2000 })).ndjson);
const snapshot = await presentation.inspect({
  kind: 'slide,textbox,shape,image,table,chart,notes,layout',
  maxChars: 30000,
});
console.log(snapshot.ndjson);
const table = presentation.resolve('tb/zq1ozepc');
for (let r = 0; r < 11; r += 1) {
  const row = [];
  for (let c = 0; c < 4; c += 1) {
    const cell = table.getCell(r, c);
    row.push({ value: cell.value, text: cell.text?.text, keys: Object.keys(cell) });
  }
  console.log('ROW', r, JSON.stringify(row));
}
