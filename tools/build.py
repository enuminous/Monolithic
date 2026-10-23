#!/usr/bin/env python3
"""Build the standalone Monolithic Atlas index from a fixed observed inventory."""
import json, re, pathlib, datetime
ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW='''
accelerando-8192|90070
Alchemy-of-Emergence|100
Ant|125
aok|30520
Archimedes-3D|472
Archimedes-Engine|279
Archimedes-Field-Lab|50
Aristotle_EFMW_Lean|75
Aristotle-102-Monolithic-Lean|55
Aristotle-165-Einsteinian-Tensors|104
Aristotle-Agreement-and-Surprise-Global-Equalibrium-from-Local-Repair|322
Aristotle-eNuminous|121
Aristotle-Ramtastic-Audit|284
Avenue5|31
Axolotl|14
BackroomsProtocol-EFMW-Analysis|10
Bat|34
Beaver|14
Bison|14
Bonobo|14
Borges-Library-CollapseOmega|133
Butterfly|16
Cadence-Zoo-Evidence|130
Cat|32
Cat-Physics|1930
Chameleon|15
Chimera|20
Circus|24
Cobra|14
Codex-888|89
Coherence-Prediction-Engine|2299
Crab|34
Crocodile|33
DePIN|26
Devs2.0|819
docs|373
Dolphin|35
Dragon|36
Eagle|39
EFMW|183
EFMW_Post156_Zoo_Audit|903
EFMW-108-Minute-Tests|24
EFMW-Axioms|50
EFMW-Bounded-Test-1|20
EFMW-Constants-Problem|51
EFMW-CTX-001b|9438
efmw-equation-review|4734
EFMW-EXP-001|1543
EFMW-FULL|58
EFMW-Grid|20
EFMW-Lagrangian|477
EFMW-Neutron-Star-Glitch-Resonance|60
efmw-research-cache|17
EFMW-Safety-001|87
EFMW-Scientific-Claims|362
Einsteinian-156-Aristotle|68
Elephant|15
Emergentology|39
Extrauniversal-Warren-Report|162
Falcon|14
fieldcore|153
FieldSpace|105
Fox|38
Gecko|39
Harlequinn|2
Hedgehog|61
Hive|38
Horse|15
I-Have-Guts|19
Jellyfish|15
JEV-EFMW-Syncretic-Layer|17
lean-worker|54
Ligo_EFMW_Search|59
Lynx|14
Magpie|16
Mantis|15
Mathematics-and-Elite-Squad-Dynamics|7545
medium|9436
Medium2|2966
Medium3|514
meta-meme|72888
Mole|14
Monlithic_EFMW_102_Lean4|190
Monolithic_102_EFMW|104
Monolithic_Zoo_Run|80
Monolithic-102-Zoo-Lean4|602
Monolithic-Zoo-Lean4|337
monster|297210
Moth|35
MultiValuedClassicalAction-Lean4|17
Multiverse-Simulator|277
Nightengale|25
Nightengale-Full-Zoo-Audit|544
Octopus|34
OpenAI-math|796839
oph-lab|2032
Orca|15
Oroboros|3148
Owl|34
P-NP|99
papers|22040
Penguin|33
Phoenix|15
Pulse|54
Ramtastic|801
Raven|32
Research-Program|15
Rhino|15
Salmon|14
Shark|63
Shepherd|54
simself|792
Spider|42
Termite|14
Tortoise|607
Turtle|19
Universal-Cognitive-Attractor|34
Universe5|16
Verbinski-Protocol|52
Weasel|15
Weaver_Os|1095
Whale|15
Wolf|19
woodpecker|44
Wrights-Law|88
Zoo-Monster|24
'''
ANIMALS=set('Ant Axolotl Bat Beaver Bison Bonobo Butterfly Cat Chameleon Chimera Cobra Crab Crocodile Dolphin Dragon Eagle Elephant Falcon Fox Gecko Hedgehog Horse Jellyfish Lynx Magpie Mantis Mole Moth Octopus Orca Owl Penguin Phoenix Pulse Raven Rhino Salmon Shark Shepherd Spider Termite Tortoise Turtle Weasel Whale Wolf'.split())
NOTES={
 'EFMW':'Canonical entry point and reviewer navigation; links to the claims-to-evidence register.',
 'Monolithic_102_EFMW':'Canonical catalogue of 102 Monolithic equations; classification is not empirical validation.',
 'Monolithic-102-Zoo-Lean4':'Formal models and coverage ledger. Its README explicitly limits ME-003 to a flat Cartesian specialization.',
 'Monolithic-Zoo-Lean4':'Lean-formalized Zoo animal checks; verify current GitHub Actions status before citing builds.',
 'EFMW-Lagrangian':'Frozen C1 candidate-action audit; 585 FieldSpace statements catalogued, not 585 proofs of physical truth.',
 'Devs2.0':'Versioned corpus assistant and benchmark specification. DEV2-001 remains draft, not a completed confirmatory experiment.',
 'papers':'Papers and prose archive; individual claims require separate evidentiary assessment.',
 'EFMW-Grid':'Pre-registration and synthetic residual-coherence monitoring; not independent grid-operations validation.',
 'Oroboros':'Exact recurrences, normalized two-cycle, and a Lean theorem catalogue.',
 'EFMW-EXP-001':'Frozen experimental research design and reports; check primary files before making result claims.',
 'EFMW_Post156_Zoo_Audit':'Reviewer starting point, claims register, and reproducibility boundaries.',
 'FieldSpace':'Einsteinian triplet and field-space catalogue.',
 'Tortoise':'Zoo entry point.',
 'Circus':'Circularity and provenance checks.',
 'monster':'Stress and robustness tooling; lowercase repository distinct from Zoo-Monster.',
 'Zoo-Monster':'Additional Zoo robustness project.',
 'Mathematics-and-Elite-Squad-Dynamics':'Mathematical satire; satire must not be confused with theorems.',
 'Ramtastic':'Work related to Ramtastic, originally associated with Chris Forrester; distinguish contributors and licensing.',
 'Aristotle-Ramtastic-Audit':'Formal audit and tutorial of a Ramtastic fork; review attribution and build evidence.',
 'Weaver_Os':'OS/prototype collaboration; verify provenance and licensing before redistribution.',
}
READMES={
 'EFMW':('b6e62bea9f9d844e5ee18061b928b62c668bf1e3','README.md'),
 'Monolithic_102_EFMW':('2c6513c94dec03540cd3a19993f5902bb38b18ed','README.md'),
 'Monolithic-102-Zoo-Lean4':('5f0293adf5b86656518051efe69b873f3ca72b80','README.md'),
 'Monolithic-Zoo-Lean4':('3405f72c4dd355f3e80bd448dc6e2e0c9d10efee','README.md'),
 'EFMW-Lagrangian':('4fcd15c8100f7487143ec616ad438271556e4584','README.md'),
 'Devs2.0':('21cffc97b5d6c6a17f4ac8811399e80c9a8f2f54','README.md'),
 'papers':('eda004eedd2f75728981cc285be083bd13dda4d6','README.md'),
 'EFMW-Grid':('d4c08c0c2435b091283404e5381578cdb2380ec1','README.md'),
 'Oroboros':('de90a943625edff7b6c01bb37a7989939aa59082','README.md'),
 'EFMW-EXP-001':('409cf8144da1525a97de898624dfd238358a5cd9','README.md'),
}
def category(name):
 if name in ANIMALS or name.lower() in ('monster','woodpecker','zoo-monster','circus'): return 'Zoo'
 n=name.lower()
 if 'aristotle' in n or 'lean' in n or 'codex' in n or 'axioms' in n or 'lagrangian' in n or 'fieldspace' in n: return 'Formal methods'
 if 'paper' in n or n.startswith('medium') or n in ('docs','mathematics-and-elite-squad-dynamics','extrauniversal-warren-report'):return 'Publications'
 if 'audit' in n or 'review' in n or 'claims' in n: return 'Audits'
 if 'experiment' in n or 'exp-' in n or 'test' in n or 'grid' in n or 'resonance' in n or 'ligo' in n: return 'Experiments'
 if 'archimedes' in n or 'worker' in n or 'devs' in n or 'os' in n or 'engine' in n or 'simulat' in n: return 'Applications'
 return 'Research'
rows=[]
for line in RAW.strip().splitlines():
 name,sz=line.strip().split('|')
 item={'id':'enuminous/'+name,'name':name,'owner':'enuminous','branch':'master' if name=='Harlequinn' else 'main','sizeKb':int(sz),'category':category(name),'note':NOTES.get(name,''),'source':'GitHub connected account inventory, 2026-10-23','url':'https://github.com/enuminous/'+name,'status':'index-only','rights':'undetermined'}
 if name in READMES: item['readme']={'path':READMES[name][1],'gitBlobSha':READMES[name][0]}
 rows.append(item)
assert len(rows)==126 and len({x['id'] for x in rows})==126
inventory={'@context':{'@vocab':'https://schema.org/','id':'@id','type':'@type'},'app':'Monolithic Atlas','snapshotDate':'2026-10-23','scope':'126 public repositories accessible in GitHub search for user:enuminous. Metadata only; complete file contents NOT mirrored.','license':'No blanket license inferred. Original per-repository rights and contribution terms apply.','repositories':rows}
report_path=ROOT/'source-packs/central-efmw-v1.report.json'
if report_path.exists():
 report=json.loads(report_path.read_text())
 inventory['scope']='126 repository metadata records; central-efmw-v1 is a separate, bounded source pack. See per-repository archive coverage. The HTML alone contains no source files.'
 inventory['sourcePack']={k:report[k] for k in ('id','bundleFile','bundleSha256','capturedFiles','capturedBytes')}
 coverage={r['repo']:r for r in report['repositories']}
 for item in rows:
  item['status']='metadata-only'
  if item['id'] in coverage:
   c=coverage[item['id']]
   item['archive']={k:c[k] for k in ('commit','status','treeFiles','capturedFiles','capturedBytes')}
   item['archive']['license']=c['license']['spdx']
   item['archive']['pack']=report['id']
   item['status']=c['status']
(ROOT/'corpus-index.json').write_text(json.dumps(inventory,indent=2,ensure_ascii=False)+'\n')
import base64
html=(ROOT/'template.html').read_text().replace('/*__CORPUS_JSON__*/',json.dumps(inventory,ensure_ascii=False,separators=(',',':')).replace('</','<\\/'))
wasm=(ROOT/'tools/crc.wasm').read_bytes()
html=html.replace('/*__WASM_BASE64__*/',base64.b64encode(wasm).decode('ascii'))
html=html.replace('/*__SOURCE_ARCHIVE__*/',(ROOT/'tools/source_archive.js').read_text())
(ROOT/'index.html').write_text(html)
print('Built',len(rows),'repos; index.html', (ROOT/'index.html').stat().st_size,'bytes')
