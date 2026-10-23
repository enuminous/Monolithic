import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {harness,bundle} from './archive_harness.mjs';
const h=harness();
await h.import(bundle);
assert.equal(h.run('memoryFiles.size'),99);
assert.equal(h.run('localCoverage.get("enuminous/Circus").status'),'fully-mirrored');
assert.equal(h.run('localCoverage.get("enuminous/Zoo-Monster").status'),'fully-mirrored');
assert.equal(h.run('localCoverage.get("enuminous/Monolithic-Zoo-Lean4").status'),'partially-cached');
assert.equal(h.run('localCoverage.get("enuminous/EFMW-Lagrangian").status'),'metadata-only');
// Exercise the actual reader for every file while fetch always throws.
for(const f of bundle.files){
 h.ctx.readRepo=f.repo;h.ctx.readPath=f.path;
 await h.run(`selected=REPOS.find(r=>r.id===readRepo);$('sourcePath').value=readPath;openCached()`);
 assert.equal(h.nodes.sourceText.textContent,Buffer.from(f.base64,'base64').toString('utf8'));
 assert.ok(h.nodes.sourceLog.textContent.includes(f.provenance.commit));
}
await h.run('exportJson()');
const exported=JSON.parse(h.run('downloads.at(-1).data'));
assert.equal(exported.archives.length,3);
assert.deepEqual(exported.files.map(f=>f.provenance),bundle.files.map(f=>f.provenance));
const fresh=harness();await fresh.import(exported);assert.equal(fresh.run('memoryFiles.size'),99);
const archive=await h.run('buildArchive()'),again=await fresh.run('buildArchive()');
assert.equal(archive.rootHash.text,again.rootHash.text,'DAG-CBOR/CAR root survives JSON round trip');
await h.run('exportCar()');
const car=Buffer.from(h.run('downloads.at(-1).data'));
// Independently parse CAR framing and raw CIDs, check every block digest.
let offset=0;
function varint(){let n=0,shift=0,b;do{b=car[offset++];n+=(b&127)*2**shift;shift+=7;assert.ok(shift<=49)}while(b&128);return n}
const headerLen=varint();const header=car.subarray(offset,offset+headerLen);offset+=headerLen;
assert.equal(header[0],0xa2); // canonical two-key CAR v1 header
const blocks=[];
while(offset<car.length){const len=varint(),end=offset+len;assert.ok(end<=car.length);const version=varint(),codec=varint(),algorithm=varint(),size=varint();
 assert.equal(version,1);assert.ok([0x71,0x55].includes(codec));assert.equal(algorithm,0x12);assert.equal(size,32);
 const hash=car.subarray(offset,offset+size);offset+=size;const bytes=car.subarray(offset,end);offset=end;
 assert.deepEqual(createHash('sha256').update(bytes).digest(),hash);blocks.push({codec,bytes,hash});
}
assert.equal(blocks.length,100);assert.equal(blocks[0].codec,0x71);
assert.deepEqual(blocks[0].bytes,Buffer.from(archive.rootBytes));
for(const f of bundle.files)assert.ok(blocks.some(b=>b.hash.toString('hex')===f.sha256));
// Fail closed before any persistent mutation, including when corruption is last.
const reject=async(edit,pattern)=>{const copy=structuredClone(bundle);edit(copy);const target=harness();await assert.rejects(target.import(copy),pattern);assert.equal(target.run('memoryFiles.size'),0);assert.equal(target.run('memoryArchives.size'),0)};
await reject(b=>b.files.at(-1).base64=Buffer.from('tampered').toString('base64'),/Checksum/);
await reject(b=>b.files.push(b.files[0]),/Duplicate file/);
await reject(b=>b.files[0].path='../escape',/path/);
await reject(b=>b.files[0].repo='someone/else',/path/);
await reject(b=>b.files[0].cid='bwrong',/CID/);
await reject(b=>b.archives[0].entries.pop(),/Git tree/);
await reject(b=>b.archives[0].commit='0'.repeat(40),/Commit/);
await reject(b=>b.archives[1].status='fully-mirrored',/completeness/);
await reject(b=>b.files[0].provenance.license.spdx='unreviewed',/Provenance/);
await reject(b=>b.files=b.files.filter(f=>!(f.repo===b.archives[0].repo&&f.path==='LICENSE')),/License/);
// Legacy v1 bundle remains readable and cannot claim a whole tree.
const legacy=structuredClone(bundle);delete legacy.archives;legacy.files=legacy.files.slice(0,1).map(({provenance,cid,...f})=>f);
const old=harness();await old.import(legacy);assert.equal(old.run('localCoverage.get("enuminous/Circus").status'),'partially-cached');
// Replacing bytes invalidates whole-tree coverage; exports remain importable.
await h.run(`(async()=>{const changed=memoryFiles.get('enuminous/Circus:README.md');changed.bytes=[65];changed.sha256=toHex(await digest(new Uint8Array([65])));delete changed.cid;delete changed.provenance;await refreshCounts();})()`);
assert.equal(h.run('localCoverage.get("enuminous/Circus").status'),'partially-cached');
await h.run('exportJson()');await fresh.import(JSON.parse(h.run('downloads.at(-1).data')));
await h.run('clearFiles();refreshCounts()');assert.equal(h.run('localCoverage.get("enuminous/Circus").status'),'metadata-only');
console.log('PASS: 99 offline reads, JSON round trip, CAR block hashes, Git commit/tree/blob binding, license retention, legacy v1, tamper rejection, coverage transitions');
