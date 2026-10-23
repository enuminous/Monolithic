import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import {webcrypto} from 'node:crypto';
export const root=new URL('../',import.meta.url).pathname;
export function harness(){
 const html=readFileSync(root+'index.html','utf8');
 const index=JSON.parse(html.match(/<script type="application\/json" id="corpus">([\s\S]*?)<\/script>/)[1]);
 const js=html.match(/<script>\s*([\s\S]*?)<\/script>/)[1].replace(/\nwire\(\);\s*$/,'');
 const nodes={corpus:{textContent:JSON.stringify(index)}};
 const document={getElementById:id=>nodes[id]??(nodes[id]={textContent:'',value:''})};
 const ctx=vm.createContext({TextEncoder,TextDecoder,Uint8Array,crypto:webcrypto,document,URL,Blob,console,WebAssembly,atob,btoa,Buffer,setTimeout,clearTimeout,
  fetch:()=>{throw Error('NETWORK FORBIDDEN')}});
 vm.runInContext(js,ctx);
 // Only IndexedDB and live rendering are replaced here; importer, validators, reader,
 // JSON, DAG-CBOR and CAR exporters are the real embedded application code.
 vm.runInContext(`globalThis.memoryFiles=new Map();globalThis.memoryArchives=new Map();globalThis.downloads=[];
 getAllFiles=async()=>[...memoryFiles.values()];getFile=async id=>memoryFiles.get(id);getArchives=async()=>[...memoryArchives.values()];
 saveBundle=async(records,archives)=>{for(const r of records)memoryFiles.set(r.id,r);for(const a of archives)memoryArchives.set(a.repo,a)};
 clearFiles=async()=>{memoryFiles.clear();memoryArchives.clear()};refreshCounts=async()=>{localCoverage=await coverageFor(await getAllFiles(),await getArchives())};
 download=(data,name,type)=>downloads.push({data,name,type});`,ctx);
 return {ctx,nodes,run:code=>vm.runInContext(code,ctx),import:async data=>{
  ctx.input=JSON.stringify(data);return vm.runInContext(`importJson({size:input.length,text:async()=>input})`,ctx);
 }};
}
