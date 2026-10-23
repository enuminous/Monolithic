import {chromium,firefox,webkit} from 'playwright';
import {createServer} from 'node:http';
import {readFileSync,mkdirSync} from 'node:fs';
import {join,resolve,sep} from 'node:path';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
const root=resolve(new URL('../',import.meta.url).pathname);
const pack=join(root,'source-packs/central-efmw-v1.bundle.json');
const bundle=JSON.parse(readFileSync(pack,'utf8'));
const output=join(root,'test-results');mkdirSync(output,{recursive:true});
const server=createServer((req,res)=>{
 if(req.url==='/blank'){res.setHeader('Content-Type','text/html');res.end('<!doctype html><title>Storage migration fixture</title>');return}
 const path=resolve(root,'.'+decodeURIComponent(new URL(req.url,'http://localhost').pathname));
 if(!path.startsWith(root+sep)){res.writeHead(403).end();return}
 try{res.setHeader('Content-Type',path.endsWith('.html')?'text/html; charset=utf-8':'application/octet-stream');res.end(readFileSync(path))}catch{res.writeHead(404).end()}
});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const base='http://127.0.0.1:'+server.address().port;
const engines=process.env.ATLAS_BROWSERS?.split(',')||['chromium','firefox','webkit'];
try{
 for(const name of engines){
  console.log('RUN '+name);
  const watchdog=setTimeout(()=>{console.error('Browser check timed out: '+name);process.exit(1)},180000);
  const browser=await ({chromium,firefox,webkit}[name]).launch({headless:true,timeout:60000});
  try{
   let externalRequests=0;
   async function context(){const c=await browser.newContext({reducedMotion:'reduce'});await c.route('**/*',route=>{
    const url=route.request().url();
    // WebKit routes local blob reads through its resource loader. These URLs
    // resolve to memory/file bytes and are not external network connections.
    if(url.startsWith(base+'/')||url.startsWith('blob:'+base+'/')||url.startsWith('data:'))return route.continue();
    externalRequests++;console.error('Unexpected external request: '+url);return route.abort();
   });return c}
   const c=await context(),page=await c.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
   await page.goto(base+'/blank');
   const legacyBytes=[111,108,100],legacyHash=createHash('sha256').update(Buffer.from(legacyBytes)).digest('hex');
   await page.evaluate(async({bytes,sha})=>new Promise((resolve,reject)=>{
    const r=indexedDB.open('MonolithicAtlas',1);r.onupgradeneeded=()=>r.result.createObjectStore('files',{keyPath:'id'});r.onerror=()=>reject(r.error);
    r.onsuccess=()=>{const db=r.result,tx=db.transaction('files','readwrite');tx.objectStore('files').put({id:'enuminous/EFMW:legacy.txt',repo:'enuminous/EFMW',path:'legacy.txt',bytes,mime:'text/plain',sha256:sha,source:'legacy v1 fixture'});tx.oncomplete=()=>{db.close();resolve()}};
   }),{bytes:legacyBytes,sha:legacyHash});
   await page.goto(base+'/index.html');
   await page.waitForFunction(()=>document.getElementById('metricLocal').textContent==='1');
   assert.equal(await page.evaluate(async()=>{const db=await idb();const version=db.version;db.close();return version}),2);
   await c.setOffline(true);
   await page.evaluate(async()=>{await clearFiles();await refreshCounts()});
   await page.locator('[data-tab="archive"]').click();
   await page.locator('#bundleInput').setInputFiles(pack);
   await page.waitForFunction(()=>/^(Validated and imported|Import rejected:)/.test(document.getElementById('archiveLog').textContent));
   assert.match(await page.locator('#archiveLog').textContent(),/^Validated and imported 99/);
   const facts=await page.evaluate(async()=>{
    const rows=[];
    for(const f of await getAllFiles()){
     selected=REPOS.find(r=>r.id===f.repo);$('sourcePath').value=f.path;await openCached();
     rows.push({repo:f.repo,path:f.path,text:$('sourceText').textContent,sha:toHex(await digest(new Uint8Array(f.bytes)))});
    }
    return {rows,statuses:[...localCoverage].map(([k,v])=>[k,v.status])};
   });
   assert.equal(facts.rows.length,99);
   for(const f of bundle.files){const got=facts.rows.find(r=>r.repo===f.repo&&r.path===f.path);assert.equal(got.sha,f.sha256);assert.equal(got.text,Buffer.from(f.base64,'base64').toString('utf8'))}
   const statuses=new Map(facts.statuses);assert.equal(statuses.get('enuminous/Circus'),'fully-mirrored');assert.equal(statuses.get('enuminous/Monolithic-Zoo-Lean4'),'partially-cached');assert.equal(statuses.get('enuminous/EFMW'),'metadata-only');
   const download=page.waitForEvent('download');await page.locator('#exportJson').click();const saved=join(output,name+'-export.json');await (await download).saveAs(saved);
   const exported=JSON.parse(readFileSync(saved,'utf8'));assert.equal(exported.files.length,99);assert.equal(exported.archives.length,3);
   const carDownload=page.waitForEvent('download');await page.locator('#exportCar').click();const carPath=join(output,name+'-export.car');await (await carDownload).saveAs(carPath);
   const expected=readFileSync(join(root,'source-packs/central-efmw-v1.car'));assert.deepEqual(readFileSync(carPath),expected);
   // New browser storage partition represents the receiving device.
   const receiver=await context(),p=await receiver.newPage();p.on('pageerror',e=>errors.push(e.message));await p.goto(base+'/index.html');await receiver.setOffline(true);
   await p.locator('[data-tab="archive"]').click();await p.locator('#bundleInput').setInputFiles(saved);
   await p.waitForFunction(()=>document.getElementById('metricLocal').textContent==='99');
   await p.evaluate(()=>changeRepo('Circus'));await p.locator('[data-tab="atlas"]').click();await p.locator('#listCached').click();
   await p.waitForFunction(()=>document.querySelectorAll('#treeList button').length===9);assert.equal(await p.locator('#treeList button').count(),9);
   await p.locator('#sourcePath').fill('README.md');await p.locator('#loadCached').click();await p.waitForFunction(()=>document.getElementById('sourceText').textContent.includes('CIRCUS'));
   await p.screenshot({path:join(output,name+'-offline.png'),fullPage:true});
   // Reload shell from the included loopback server with external routes still blocked.
   await receiver.setOffline(false);await p.reload();await p.waitForFunction(()=>document.getElementById('metricLocal').textContent==='99');await receiver.setOffline(true);
   // Quota/write failure must roll back the entire real IndexedDB transaction.
   await p.evaluate(async()=>{await clearFiles();await refreshCounts();globalThis.originalPut=IDBObjectStore.prototype.put;let count=0;IDBObjectStore.prototype.put=function(...args){if(++count===3)throw new DOMException('test quota','QuotaExceededError');return originalPut.apply(this,args)}});
   await p.locator('[data-tab="archive"]').click();await p.locator('#bundleInput').setInputFiles(saved);
   await p.waitForFunction(()=>document.getElementById('archiveLog').textContent.startsWith('Import rejected:'));
   assert.equal(await p.evaluate(async()=>(await getAllFiles()).length),0);assert.equal(await p.evaluate(async()=>(await getArchives()).length),0);
   await p.evaluate(()=>{IDBObjectStore.prototype.put=originalPut});
   const bad=structuredClone(bundle);bad.files.at(-1).sha256='0'.repeat(64);
   await p.locator('#bundleInput').setInputFiles({name:'tampered.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(bad))});
   await p.waitForFunction(()=>document.getElementById('archiveLog').textContent.includes('Checksum mismatch'));
   assert.equal(await p.evaluate(async()=>(await getAllFiles()).length),0);
   assert.deepEqual(errors,[]);assert.equal(externalRequests,0);
   await receiver.close();await c.close();
   console.log('PASS '+name+': v1 storage upgrade, offline import/read/export, fresh-device import, reload, quota rollback, tamper rejection; zero external requests');
  }finally{await browser.close();clearTimeout(watchdog)}
 }
}finally{server.close()}
