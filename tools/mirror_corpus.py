#!/usr/bin/env python3
"""Opt-in, reproducible source snapshotter for the Monolithic Atlas repository catalog.

Requires git and outbound access. Does not run automatically. Creates per-repo
JSON bundles importable into the offline Atlas and a provenance/status manifest.
By default enforces byte limits. Use --unbounded only with adequate storage and
explicit rights review. Does not clone Git histories beyond shallow snapshots.
"""
import argparse
import base64
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from urllib.parse import quote

ROOT=Path(__file__).resolve().parents[1]


def run(cmd,timeout,cwd=None):
    return subprocess.run(cmd,cwd=cwd,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout)


def valid_repo(repo):
    return (repo.get('owner')=='enuminous' and isinstance(repo.get('name'),str)
            and repo['name'].replace('-','').replace('_','').replace('.','').isalnum())


def scan_repo(repo,target,args,remain):
    name=repo['name'];url=repo['url'];dst=target/name
    git_cmd=['git','-c','core.askPass=','clone','--quiet','--depth','1','--single-branch','--branch',repo['branch'],url+'.git',str(dst)]
    env=os.environ.copy();env['GIT_TERMINAL_PROMPT']='0'
    subprocess.run(git_cmd,env=env,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=args.timeout)
    commit=run(['git','rev-parse','HEAD'],args.timeout,dst).stdout.decode().strip()
    listing=run(['git','ls-files','-z'],args.timeout,dst).stdout.split(b'\0')
    file_entries=[];omissions=[];total=0
    for raw in listing:
        if not raw:continue
        path=os.fsdecode(raw)
        src=dst/path
        if not src.is_file() or src.is_symlink():
            omissions.append({'path':path,'reason':'not a regular file or a symlink'});continue
        size=src.stat().st_size
        if not args.unbounded and size>args.max_file_mib*1048576:
            omissions.append({'path':path,'reason':'individual file size limit','bytes':size});continue
        if not args.unbounded and total+size>args.max_repo_mib*1048576:
            omissions.append({'path':path,'reason':'per-repository byte cap','bytes':size});continue
        if not args.unbounded and remain-total<size:
            omissions.append({'path':path,'reason':'total byte cap','bytes':size});continue
        data=src.read_bytes();total+=len(data)
        sha=hashlib.sha256(data).hexdigest()
        ext=src.suffix.lower()
        mime={'.md':'text/markdown','.txt':'text/plain','.lean':'text/plain','.json':'application/json','.html':'text/html','.js':'application/javascript','.css':'text/css','.svg':'image/svg+xml','.py':'text/x-python','.toml':'text/plain','.yaml':'text/plain','.yml':'text/plain','.png':'image/png','.gif':'image/gif','.mp4':'video/mp4','.mpeg':'video/mpeg','.mp3':'audio/mpeg','.wasm':'application/wasm'}.get(ext,'application/octet-stream')
        file_entries.append({'repo':repo['id'],'path':path,'mime':mime,'source':f'GitHub repo {repo["id"]} commit {commit} path {path}','sha256':sha,'base64':base64.b64encode(data).decode('ascii')})
    return {'name':name,'commit':commit,'url':url,'capturedFiles':len(file_entries),'capturedBytes':total,'omitted':omissions},file_entries


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan',action='store_true',help='Only list target repositories and reported sizes; no network')
    parser.add_argument('--repo',action='append',help='Restrict to name(s), e.g. --repo EFMW --repo papers')
    parser.add_argument('--out',type=Path,default=ROOT/'mirror_output')
    parser.add_argument('--max-file-mib',type=int,default=10)
    parser.add_argument('--max-repo-mib',type=int,default=100)
    parser.add_argument('--max-total-mib',type=int,default=500)
    parser.add_argument('--timeout',type=int,default=240)
    parser.add_argument('--unbounded',action='store_true',help='Remove size caps, may need gigabytes of disk and time')
    parser.add_argument('--keep-clones',action='store_true')
    a=parser.parse_args()
    catalog=json.loads((ROOT/'corpus-index.json').read_text())
    wanted=set(a.repo or [])
    repos=[r for r in catalog['repositories'] if not wanted or r['name'] in wanted]
    unknown=wanted-{r['name'] for r in repos}
    if unknown:parser.error('Names absent from inventory: '+', '.join(sorted(unknown)))
    assert all(valid_repo(r) for r in repos)
    print(f'Plan: {len(repos)} repos; GitHub reported size sum {sum(r["sizeKb"] for r in repos)/1024:.1f} MiB (rough metadata, not local clone estimate).')
    if a.plan:
        for r in repos:print(' -',r['id'],r['branch'])
        return 0
    out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
    work=out/'working_clones';work.mkdir(exist_ok=True)
    report={'tool':'Monolithic Atlas mirror_corpus.py','started':dt.datetime.now(dt.timezone.utc).isoformat(),'indexSnapshot':catalog['snapshotDate'],'repoCount':len(repos),'rightsNotice':catalog['license'],'limits':{'unbounded':a.unbounded,'maxFileMiB':a.max_file_mib,'maxRepoMiB':a.max_repo_mib,'maxTotalMiB':a.max_total_mib},'repositories':[]}
    used=0
    for ix,repo in enumerate(repos,1):
        print(f'[{ix}/{len(repos)}] {repo["id"]}',flush=True)
        import shutil
        clone=work/repo['name']
        try:
            if clone.exists():shutil.rmtree(clone)
            remain=float('inf') if a.unbounded else max(0,a.max_total_mib*1048576-used)
            if remain<=0:raise RuntimeError('total byte cap reached')
            status,entries=scan_repo(repo,work,a,remain)
            used+=status['capturedBytes']
            bundle={'format':'monolithic-atlas-bundle-v1','snapshotDate':catalog['snapshotDate'],'createdAt':dt.datetime.now(dt.timezone.utc).isoformat(),'scope':f'Shallow committed-tree snapshot of {repo["id"]} at {status["commit"]}, potentially truncated; inspect mirror report','repositories':[repo],'files':entries}
            path=out/f'{repo["name"]}.bundle.json';path.write_text(json.dumps(bundle,ensure_ascii=False))
            status['bundleFile']=path.name;status['completeAtDeclaredLimits']=not status['omitted']
            print(f'    {status["capturedFiles"]} files, {status["capturedBytes"]} bytes, {len(status["omitted"])} omitted')
            report['repositories'].append(status)
        except (subprocess.CalledProcessError,subprocess.TimeoutExpired,RuntimeError,OSError) as e:
            report['repositories'].append({'name':repo['name'],'error':str(e)[:500]})
            print('    ERROR:',str(e)[:200],file=sys.stderr)
        finally:
            if not a.keep_clones and clone.exists():shutil.rmtree(clone)
            report['finishedSoFar']=dt.datetime.now(dt.timezone.utc).isoformat();report['capturedBytesTotal']=used
            (out/'mirror-report.json').write_text(json.dumps(report,indent=2))
    if not a.keep_clones and work.exists():
        try:work.rmdir()
        except OSError:pass
    print('Done. Review mirror-report.json for failures, byte caps and omissions. No rights assignment inferred.')
    return 0

if __name__=='__main__':raise SystemExit(main())
