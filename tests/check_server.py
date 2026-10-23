#!/usr/bin/env python3
"""Local archive-server smoke tests without exposing any network interface."""
import base64,hashlib,json,pathlib,subprocess,sys,tempfile,time,urllib.error,urllib.request
from http.client import HTTPConnection
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'tools'))
from archive_server import cid_raw
root=pathlib.Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as store:
 port=9876
 p=subprocess.Popen([sys.executable,str(root/'tools/archive_server.py'),'--port',str(port),'--store',store],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 try:
  for i in range(30):
   try:
    with urllib.request.urlopen(f'http://127.0.0.1:{port}/api/status',timeout=1) as r:
     assert json.load(r)['blocks']==0
     break
   except Exception:
    time.sleep(.1)
  else:raise AssertionError('Local server did not start')
  b=b'This is a test / Monolithic Atlas';c=cid_raw(b)
  def req(method,path,obj):
   data=json.dumps(obj).encode();r=urllib.request.Request(f'http://127.0.0.1:{port}{path}',data=data,headers={'Content-Type':'application/json'},method=method)
   with urllib.request.urlopen(r,timeout=4) as f:return json.load(f)
  res=req('POST','/api/blocks/'+c,{'base64':base64.b64encode(b).decode(),'repo':'enuminous/EFMW','path':'README.md','mime':'text/plain'})
  assert res['cid']==c
  res=req('POST','/api/blocks/'+c,{'base64':base64.b64encode(b).decode(),'repo':'enuminous/FieldSpace','path':'NOTES.md','mime':'text/plain'})
  with urllib.request.urlopen(f'http://127.0.0.1:{port}/api/blocks') as r:
   x=json.load(r)
  assert len(x['blocks'])==2, x
  with urllib.request.urlopen(f'http://127.0.0.1:{port}/api/blocks/{c}') as r:
   x=json.load(r)
  assert base64.b64decode(x['base64'])==b
  assert cid_raw(b)==c
  try:req('POST','/api/blocks/'+c,{'base64':base64.b64encode(b+b'!').decode(),'repo':'enuminous/EFMW','path':'README.md'})
  except urllib.error.HTTPError as e:assert e.code==422
  else:raise AssertionError('server accepted checksum mismatch')
  req('POST','/api/relay',{'topic':'monolithic-corpus','message':'hello immutable archive'})
  with urllib.request.urlopen(f'http://127.0.0.1:{port}/api/relay?topic=monolithic-corpus') as r:x=json.load(r)
  assert x['messages'][-1]['message']=='hello immutable archive'
  print('PASS: loopback HTTP status, CID validation, dedup aliases, archive inventory, relay messaging')
 finally:p.terminate();p.wait(timeout=5)
