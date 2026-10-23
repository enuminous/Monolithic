// Export using the same validated importer and IPLD code as the standalone page.
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {harness,root} from './atlas_runtime.mjs';
const prefix='source-packs/central-efmw-v1';
const runtime=harness();
await runtime.import(JSON.parse(readFileSync(root+prefix+'.bundle.json','utf8')));
await runtime.run('exportCar()');
const car=runtime.run('downloads.at(-1)');
if(car?.name!=='monolithic-corpus.car')throw Error('CAR export did not complete');
writeFileSync(root+prefix+'.car',Buffer.from(car.data));
const archive=await runtime.run('buildArchive()');
writeFileSync(root+prefix+'.dag-cbor',Buffer.from(archive.rootBytes));
writeFileSync(root+prefix+'.cid',archive.rootHash.text+'\n');
const sums=['lock.json','report.json','bundle.json','car','dag-cbor','cid'].map(ext=>{
 const path=prefix+'.'+ext;return createHash('sha256').update(readFileSync(root+path)).digest('hex')+'  '+path;
});
writeFileSync(root+'source-packs/SHA256SUMS',sums.join('\n')+'\n');
console.log('Exported CAR v1 and DAG-CBOR; root '+archive.rootHash.text);
