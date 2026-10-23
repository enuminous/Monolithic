// Embedded by build.py into the existing standalone application. No runtime dependency.
const COVERAGE_LABELS={'fully-mirrored':'Fully mirrored','partially-cached':'Partially cached','metadata-only':'Metadata only'};
let localCoverage=new Map();
function validArchivePath(path){return typeof path==='string'&&path.length>0&&!path.startsWith('/')&&!/[\\\x00\r\n]/.test(path)&&path.split('/').every(p=>p&&p!=='.'&&p!=='..')}
async function gitObjectHash(kind,bytes){return toHex(new Uint8Array(await crypto.subtle.digest('SHA-1',concat(bytesText(kind+' '+bytes.length+'\0'),bytes))))}
async function gitTreeHash(entries){
 const root=new Map();
 for(const e of entries){
  if(!validArchivePath(e.path)||!['100644','100755','120000','160000'].includes(e.mode)||!/^[a-f0-9]{40}$/.test(e.gitBlobSha)||e.type!==(e.mode==='160000'?'commit':'blob'))throw Error('Invalid Git tree entry');
  const parts=e.path.split('/');let node=root;
  for(const part of parts.slice(0,-1)){if(!node.has(part))node.set(part,new Map());node=node.get(part);if(!(node instanceof Map))throw Error('Tree path conflict')}
  const name=parts[parts.length-1];if(node.has(name))throw Error('Duplicate tree path');node.set(name,e);
 }
 async function encode(node){
  const pairs=[];
  for(const [name,value] of node){const dir=value instanceof Map,hash=dir?await encode(value):value.gitBlobSha;
   pairs.push({key:bytesText(name+(dir?'/':'')),value:concat(bytesText((dir?'40000':value.mode)+' '+name+'\0'),Uint8Array.from(hash.match(/../g),x=>parseInt(x,16)))})}
  pairs.sort((a,b)=>cmpBytes(a.key,b.key));return gitObjectHash('tree',concat(...pairs.map(x=>x.value)));
 }
 return encode(root);
}
async function getArchives(){return dbOp('readonly',s=>s.getAll(),'archives')}
async function exportArchives(files){
 const byId=new Map(files.map(f=>[f.id,f])),out=[];
 for(const a of await getArchives()){
  const notice=byId.get(a.repo+':'+a.license.path);
  if(!notice||toHex(await digest(new Uint8Array(notice.bytes)))!==a.license.sha256)continue;
  const entries=[];let count=0;
  for(const e of a.entries){const f=byId.get(a.repo+':'+e.path);
   const matches=e.disposition==='included'&&f?.provenance?.commit===a.commit&&f.sha256===e.sha256&&toHex(await digest(new Uint8Array(f.bytes)))===e.sha256;
   if(matches){entries.push(e);count++}else{entries.push({...e,disposition:'omitted',reason:e.reason||'Pinned bytes are not present in this export'})}
  }
  out.push({...a,entries,status:count===entries.length?'fully-mirrored':count?'partially-cached':'metadata-only'});
 }return out;
}
async function saveBundle(records,archives){
 const db=await idb();return new Promise((resolve,reject)=>{
  const tx=db.transaction(['files','archives'],'readwrite');
  tx.oncomplete=()=>{db.close();resolve()};tx.onabort=()=>{db.close();reject(tx.error||Error('Import transaction aborted'))};tx.onerror=()=>{};
  try{for(const r of records)tx.objectStore('files').put(r);for(const a of archives)tx.objectStore('archives').put(a)}catch(e){tx.abort();reject(e)}
 });
}
async function validateArchive(a,records){
 if(!a||!REPOS.some(r=>r.id===a.repo)||!/^[a-f0-9]{40}$/.test(a.commit)||!/^[a-f0-9]{40}$/.test(a.gitTreeSha)||!Array.isArray(a.entries)||!a.entries.length)throw Error('Invalid archive manifest');
 const raw=unb64(a.commitObject);
 if(await gitObjectHash('commit',raw)!==a.commit||textBytes(raw).split('\n')[0]!=='tree '+a.gitTreeSha)throw Error('Commit/tree binding mismatch');
 if(await gitTreeHash(a.entries)!==a.gitTreeSha)throw Error('Incomplete or changed Git tree');
 const license=a.license;
 if(!license||typeof license.spdx!=='string'||!validArchivePath(license.path))throw Error('Missing license evidence');
 const notice=records.get(a.repo+':'+license.path);
 if(!notice||notice.sha256!==license.sha256||await gitObjectHash('blob',new Uint8Array(notice.bytes))!==license.gitBlobSha)throw Error('License notice missing or changed');
 let included=0;
 const paths=new Set();
 for(const e of a.entries){
  paths.add(e.path);
  if(e.disposition==='omitted'){if(typeof e.reason!=='string'||!e.reason)throw Error('Missing omission reason');continue}
  if(e.disposition!=='included'||!['100644','100755'].includes(e.mode)||!Number.isSafeInteger(e.size)||e.size<0)throw Error('Invalid included entry');
  const f=records.get(a.repo+':'+e.path),p=f?.provenance;
  if(!f||f.sha256!==e.sha256||f.bytes.length!==e.size||await gitObjectHash('blob',new Uint8Array(f.bytes))!==e.gitBlobSha)throw Error('Manifest file missing or changed: '+e.path);
  if((await cid(new Uint8Array(f.bytes))).text!==e.cid||f.cid!==e.cid)throw Error('Manifest CID mismatch');
  if(!p||p.repository!==a.repo||p.commit!==a.commit||p.gitBlobSha!==e.gitBlobSha||p.gitMode!==e.mode||
    !p.license||['spdx','path','gitBlobSha','sha256'].some(k=>p.license[k]!==license[k])||
    p.sourceUrl!=='https://github.com/'+a.repo+'/blob/'+a.commit+'/'+e.path.split('/').map(encodeURIComponent).join('/'))throw Error('Provenance mismatch: '+e.path);
  included++;
 }
 for(const f of records.values())if(f.repo===a.repo&&!paths.has(f.path))throw Error('File absent from pinned tree');
 const expected=included===a.entries.length?'fully-mirrored':included?'partially-cached':'metadata-only';
 if(a.status!==expected)throw Error('False archive completeness claim');
}
async function importJson(file){
 if(file.size>100e6)throw Error('Import file larger than 100 MB. Split exports.');
 const obj=JSON.parse(await file.text());
 if(obj.format!=='monolithic-atlas-bundle-v1'||!Array.isArray(obj.files)||!Array.isArray(obj.repositories)||
    (obj.archives!==undefined&&!Array.isArray(obj.archives)))throw Error('Not a supported Monolithic Atlas bundle');
 const checked=new Map();let size=0;
 for(const f of obj.files){
  if(!f||!REPOS.some(r=>r.id===f.repo)||!validArchivePath(f.path)||typeof f.base64!=='string'||!/^[a-f0-9]{64}$/.test(f.sha256))throw Error('Malformed file entry or untrusted path');
  const id=f.repo+':'+f.path;if(checked.has(id))throw Error('Duplicate file: '+id);
  const bytes=unb64(f.base64);size+=bytes.length;if(size>75e6)throw Error('Decoded import exceeds 75 MB');
  if(toHex(await digest(bytes))!==f.sha256)throw Error('Checksum mismatch: '+id);
  if(f.size!==undefined&&f.size!==bytes.length)throw Error('Size mismatch: '+id);
  if(f.cid!==undefined&&(await cid(bytes)).text!==f.cid)throw Error('CID mismatch: '+id);
  checked.set(id,{id,repo:f.repo,path:f.path,mime:typeof f.mime==='string'?f.mime:'application/octet-stream',
   source:String(f.source||'unknown'),sha256:f.sha256,bytes:Array.from(bytes),
   ...(f.cid?{cid:f.cid}:{}),...(f.provenance?{provenance:f.provenance}:{}),savedAt:new Date().toISOString()});
 }
 const seen=new Set(),archives=obj.archives||[];
 for(const a of archives){if(seen.has(a.repo))throw Error('Duplicate archive manifest');seen.add(a.repo);await validateArchive(a,checked)}
 // All validation precedes the single IndexedDB transaction, including license/provenance checks.
 await saveBundle([...checked.values()],archives);await refreshCounts();
 log('archiveLog',`Validated and imported ${checked.size} files and ${archives.length} pinned tree manifests. Source attribution is unsigned; licenses remain those of the original repositories.`);
}
async function coverageFor(files,archives){
 const byRepo=new Map(),result=new Map();
 for(const f of files){if(!byRepo.has(f.repo))byRepo.set(f.repo,new Map());
  const actual=toHex(await digest(new Uint8Array(f.bytes)));if(actual===f.sha256)byRepo.get(f.repo).set(f.path,f)}
 const manifests=new Map(archives.map(a=>[a.repo,a]));
 for(const r of REPOS){const have=byRepo.get(r.id)||new Map(),a=manifests.get(r.id);let matching=0;
  if(a)for(const e of a.entries){const f=have.get(e.path);if(e.disposition==='included'&&f?.sha256===e.sha256&&f?.provenance?.commit===a.commit)matching++}
  result.set(r.id,{status:a&&matching===a.entries.length&&a.entries.length>0?'fully-mirrored':have.size?'partially-cached':'metadata-only',
   files:have.size,matching,treeFiles:a?.entries.length||null,commit:a?.commit||null});
 }return result;
}
function coverageText(repo){const s=localCoverage.get(repo.id);return COVERAGE_LABELS[s?.status||'metadata-only']}
async function listCached(){
 const files=(await getAllFiles()).filter(f=>f.repo===selected.id).sort((a,b)=>a.path.localeCompare(b.path));
 $('treeList').replaceChildren();for(const f of files){const b=el('button','repo',f.path+' · '+human(f.bytes.length));b.onclick=()=>{$('sourcePath').value=f.path;openCached()};$('treeList').append(b)}
 log('sourceLog',files.length+' local files for '+selected.id+'. No network request made.');
}
async function downloadCached(){const f=await getFile(selected.id+':'+$('sourcePath').value.trim());
 if(!f){log('sourceLog','Import or cache this file first.');return}
 const bytes=new Uint8Array(f.bytes);if(toHex(await digest(bytes))!==f.sha256)throw Error('Local checksum mismatch');
 download(bytes,f.path.split('/').pop(),f.mime||'application/octet-stream');
}
