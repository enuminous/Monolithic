import {readFileSync,writeFileSync} from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import {webcrypto} from 'node:crypto';
const root=new URL('../',import.meta.url).pathname;
const html=readFileSync(root+'index.html','utf8');
const json=JSON.parse(html.match(/<script type="application\/json" id="corpus">([\s\S]*?)<\/script>/)[1]);
assert.equal(json.repositories.length,126);
assert.equal(new Set(json.repositories.map(r=>r.id)).size,126);
const js=html.match(/<script>\s*([\s\S]*?)<\/script>/)[1];
const nodes={corpus:{textContent:JSON.stringify(json)},rootCid:{textContent:''},ipfsLink:{href:''},archiveLog:{textContent:''}};
const fakeDocument={getElementById:(x)=>nodes[x]??(nodes[x]={textContent:''})};
const ctx=vm.createContext({TextEncoder,TextDecoder,Uint8Array,crypto:webcrypto,document:fakeDocument,URL,Blob,console,WebAssembly,atob,btoa,Buffer,setTimeout,clearTimeout});
// suppress live UI startup; tests exercise pure archiving layer against virtual IndexedDB.
vm.runInContext(js.replace(/\nwire\(\);\s*$/,''),ctx);
const values=await vm.runInContext(`(async()=>{
 const result=await cid(bytesText(''),0x55);
 const rootCbor=cbor({z:1,a:2,links:[{__cidRaw:result.raw}]});
 const c=await cid(rootCbor,0x71);
 return {empty:result.text,rootLength:rootCbor.length,rootCid:c.text,rootBytes:Array.from(rootCbor),crc:crcJs(bytesText('123456789'))};
})()`,ctx);
assert.equal(values.empty,'bafkreihdwdcefgh4dqkjv67uzcmw7ojee6xedzdetojuzjevtenxquvyku');
assert.equal(values.crc,0xcbf43926);
assert.ok(values.rootCid.startsWith('bafyrei'));
// strict ordering (a, z, links by UTF-8 length) encoded into root CBOR
assert.equal(values.rootBytes[0],0xa3); // 3-pair CBOR map
const wasm64=html.match(/const CRC_WASM_B64='([^']*)'/)[1];
const wasm=(await WebAssembly.instantiate(Buffer.from(wasm64,'base64'))).instance;
const test=Buffer.from('123456789');
new Uint8Array(wasm.exports.memory.buffer).set(test,0);
assert.equal(wasm.exports.crc32(0,test.length)>>>0,0xcbf43926);
const a=await vm.runInContext(`(async()=>{getAllFiles=async()=>[];return await buildArchive()})()`,ctx);
assert.equal(a.blocks.length,1);
assert.equal(a.root.repositories.length,126);
assert.equal(a.root.files.length,0);
assert.equal(a.blocks[0].cid.text,a.rootHash.text);
writeFileSync(root+'tests/verified-root.dag-cbor',Buffer.from(a.rootBytes));
console.log('PASS: 126 inventory IDs, SHA-256 CIDv1 known vector, canonical DAG-CBOR, export root, wasm CRC-32');
