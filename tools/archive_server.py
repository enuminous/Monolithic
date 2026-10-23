#!/usr/bin/env python3
"""Monolithic Atlas optional loopback HTTP archive + bulletin relay.

No accounts/authentication. Binds to 127.0.0.1 only by default. Never expose
write-enabled endpoints to the open Internet without authentication/TLS.
"""
from __future__ import annotations
import argparse
import base64
import hashlib
import http.server
import json
import pathlib
import re
import threading
import time
from urllib.parse import urlparse, parse_qs

MAX_BODY=25_000_000
CID_PATTERN=re.compile(r'^b[a-z2-7]{20,160}$')
BASE=pathlib.Path(__file__).resolve().parents[1]


def varint(n: int)->bytes:
    result=bytearray()
    while True:
        b=n&127;n>>=7
        result.append(b|(128 if n else 0))
        if not n:return bytes(result)


def cid_raw(data: bytes)->str:
    sha=hashlib.sha256(data).digest()
    binary=varint(1)+varint(0x55)+varint(0x12)+varint(len(sha))+sha
    import base64
    return 'b'+base64.b32encode(binary).decode('ascii').lower().rstrip('=')


class ArchiveServer(http.server.ThreadingHTTPServer):
    daemon_threads=True
    allow_reuse_address=True
    def __init__(self,address,root,store):
        super().__init__(address,AtlasHandler)
        self.root=root
        self.store=store
        self.blocks=store/'blocks'
        self.blocks.mkdir(parents=True,exist_ok=True)
        self.messages=[]
        self.lock=threading.Lock()


class AtlasHandler(http.server.SimpleHTTPRequestHandler):
    server_version='MonolithicAtlas/1.0'
    def __init__(self,*a,**kw):
        super().__init__(*a,directory=str(BASE),**kw)

    def end_headers(self):
        # The server is local and opt-in; CORS makes file:// and localhost clients work.
        self.send_header('Access-Control-Allow-Origin','*')
        self.send_header('Access-Control-Allow-Methods','GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers','Content-Type')
        self.send_header('X-Content-Type-Options','nosniff')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def send_json(self,code:int,obj):
        data=json.dumps(obj,ensure_ascii=False,separators=(',',':')).encode()
        self.send_response(code)
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Content-Length',str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def body_json(self):
        length=int(self.headers.get('Content-Length','0'))
        if length<1 or length>MAX_BODY:raise ValueError('body size outside limit')
        return json.loads(self.rfile.read(length))

    def do_GET(self):
        url=urlparse(self.path)
        p=url.path
        if p=='/api/status':
            self.send_json(200,{'product':'Monolithic Atlas','version':1,'transport':'http-archive-relay','blocks':len(list(self.server.blocks.glob('*.meta.json'))),'localOnlyByDefault':True})
            return
        if p=='/api/blocks':
            items=[]
            for m in list(self.server.blocks.glob('*.meta.json'))[:3000]:
                try:
                    meta=json.loads(m.read_text())
                    for alias in meta.get('aliases',[meta]):
                        items.append({**meta,**alias})
                except (ValueError,OSError):pass
            self.send_json(200,{'blocks':items,'truncated':len(items)>=3000});return
        if p.startswith('/api/blocks/'):
            cid=p.rsplit('/',1)[-1]
            if not CID_PATTERN.fullmatch(cid):self.send_json(400,{'error':'invalid cid'});return
            raw=self.server.blocks/(cid+'.bin')
            metadata=self.server.blocks/(cid+'.meta.json')
            if not raw.exists():self.send_json(404,{'error':'block not found'});return
            dat=raw.read_bytes()
            if cid_raw(dat)!=cid:self.send_json(500,{'error':'stored bytes fail CID verification'});return
            try:meta=json.loads(metadata.read_text())
            except (ValueError,OSError):meta={}
            self.send_json(200,{**meta,'cid':cid,'base64':base64.b64encode(dat).decode()});return
        if p=='/api/relay':
            topic=parse_qs(url.query).get('topic',['monolithic-corpus'])[0]
            with self.server.lock:msgs=[m for m in self.server.messages if m['topic']==topic][-100:]
            self.send_json(200,{'topic':topic,'messages':msgs});return
        if p.startswith('/api/'):
            self.send_json(404,{'error':'unknown endpoint'});return
        return super().do_GET()

    def do_POST(self):
        p=urlparse(self.path).path
        try:body=self.body_json()
        except (ValueError,json.JSONDecodeError) as exc:
            self.send_json(400,{'error':'invalid JSON: '+str(exc)});return
        if p.startswith('/api/blocks/'):
            expected=p.rsplit('/',1)[-1]
            if not CID_PATTERN.fullmatch(expected):self.send_json(400,{'error':'invalid cid'});return
            try:data=base64.b64decode(body['base64'],validate=True)
            except (KeyError,ValueError,TypeError):self.send_json(400,{'error':'invalid base64'});return
            if len(data)>10_000_000:self.send_json(413,{'error':'block exceeds 10 MB'});return
            actual=cid_raw(data)
            if expected!=actual:self.send_json(422,{'error':'content CID mismatch','actual':actual});return
            repo=body.get('repo','');path=body.get('path','');mime=body.get('mime','application/octet-stream')
            if (not isinstance(repo,str) or not re.fullmatch(r'enuminous/[A-Za-z0-9_.-]+',repo)
                or not isinstance(path,str) or not path or path.startswith('/') or '..' in path.split('/')
                or len(path)>700 or not isinstance(mime,str) or len(mime)>100):
                self.send_json(400,{'error':'invalid metadata'});return
            meta={'cid':actual,'repo':repo,'path':path,'mime':mime,'size':len(data),'sha256':hashlib.sha256(data).hexdigest(),'source':'uploaded from browser'}
            (self.server.blocks/(actual+'.bin')).write_bytes(data)
            metadata_file=self.server.blocks/(actual+'.meta.json')
            aliases=[]
            if metadata_file.exists():
                try:
                    old=json.loads(metadata_file.read_text());aliases=old.get('aliases',[])
                except (ValueError,OSError):pass
            if not aliases:aliases=[{'repo':repo,'path':path,'mime':mime}]
            if not any(x.get('repo')==repo and x.get('path')==path for x in aliases):
                aliases.append({'repo':repo,'path':path,'mime':mime})
            meta['aliases']=aliases
            metadata_file.write_text(json.dumps(meta))
            self.send_json(201,{'saved':True,'cid':actual});return
        if p=='/api/relay':
            topic=body.get('topic','');message=body.get('message','')
            if not isinstance(topic,str) or not re.fullmatch('[A-Za-z0-9_.-]{1,80}',topic) or not isinstance(message,str) or len(message)>2000:
                self.send_json(400,{'error':'invalid topic or message'});return
            msg={'id':int(time.time()*1000),'at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'topic':topic,'message':message}
            with self.server.lock:
                self.server.messages.append(msg)
                if len(self.server.messages)>1000:self.server.messages=self.server.messages[-500:]
            self.send_json(201,{'received':True,'messageId':msg['id']});return
        self.send_json(404,{'error':'unknown endpoint'})


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host',default='127.0.0.1',help='Default loopback; non-loopback requires your own access controls')
    parser.add_argument('--port',type=int,default=8765)
    parser.add_argument('--store',type=pathlib.Path,default=BASE/'.atlas_store')
    a=parser.parse_args()
    if a.host not in ('127.0.0.1','::1','localhost'):
        print('WARNING: no authentication or TLS; do not expose this server to the Internet.')
    with ArchiveServer((a.host,a.port),BASE,a.store) as server:
        print(f'Monolithic Atlas: http://{a.host}:{a.port}/index.html')
        print(f'Blocks: {server.blocks}')
        try:server.serve_forever()
        except KeyboardInterrupt:print('\nStopping...')

if __name__=='__main__':main()
