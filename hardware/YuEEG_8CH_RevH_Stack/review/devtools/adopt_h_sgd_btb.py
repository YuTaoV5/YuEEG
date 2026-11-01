"""Adopt only a separately checked SGDCONN candidate; no routing is generated here."""
from pathlib import Path
import json,sys,shutil,hashlib,csv,subprocess
H=Path('hardware/YuEEG_8CH_RevH_Stack');C=Path(sys.argv[1]);B=Path('logs/pre_sgd_btb_adoption');assert not B.exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
proof=json.loads((C/'native_migration_proof.json').read_text());selection=json.loads((C/'selection.json').read_text())
for name,row in proof.items():
 p=H/name/('YuEEG_H_'+name.upper()+'.kicad_pcb');assert sha(p)==row['baseline_pcb_sha256'] and sha(C/name/p.name)==row['candidate_pcb_sha256']
 assert not row['hits'] and all(v==0 for v in row['checks'].values()) and row['all_other_component_electrical_and_pose_geometry_unchanged'] and row['all20_JH1_pad_centers_and_nets_unchanged'] and row['locator_holes_unchanged']
 drc=json.loads((C/name/'drc_sgd.json').read_text());assert all(not drc[k] for k in ['violations','unconnected_items','schematic_parity'])
B.mkdir(parents=True)
for name in ['afe','digital']:
 (B/name).mkdir()
 for file in (H/name).glob('*'):
  if file.is_file() and (file.suffix in ['.kicad_pcb','.kicad_sch'] or file.name=='BOM.csv'):shutil.copy2(file,B/name/file.name)
 shutil.copy2(C/name/('YuEEG_H_'+name.upper()+'.kicad_pcb'),H/name/('YuEEG_H_'+name.upper()+'.kicad_pcb'))
 shutil.copy2(C/name/'BOM.csv',H/name/'BOM.csv')
 for file in (C/name).glob('circuit_*.kicad_sch'):
  target=H/name/file.name
  if file.read_bytes()!=target.read_bytes():shutil.copy2(file,target)
 fp=selection[name]['footprint']
 for folder,suffix in [('footprints/YuEEG.pretty','.kicad_mod'),('models','.wrl')]:shutil.copy2(C/folder/(fp+suffix),H/folder/(fp+suffix))
record={'status':'SGDCONN_DRAWING_AND_SKU_ADOPTED_ENGINEERING_NOT_ASSEMBLY_RELEASE','baseline_git_commit':'e5df79c5b5a603c2e0c9b75f851ded95b042c890','boards':proof,'source_review':'review/sgd_btb_procurement.json','scope':'Only JH1 library/value/lands plus4AFE and8digital via moves and listed attached/rerouted traces. Other electrical parts and poses,20logical contact centers/nets and locator holes independently checked unchanged. No physical assembly, EEG or production qualification.'}
(H/'review/sgd_btb_adoption.json').write_text(json.dumps(record,indent=2),encoding='utf8');proofsha=sha(H/'review/sgd_btb_adoption.json')
# Preserve historical facts, and attach the independently checked follow-up chain.
p=H/'review/smt_btb_adoption.json';d=json.loads(p.read_text());shutil.copy2(p,B/p.name)
for name,row in d['boards'].items():row['pre_sgd_pcb_sha256']=row['pcb_sha256'];row['pcb_sha256']=proof[name]['candidate_pcb_sha256'];row['sgd_followup_proof_sha256']=proofsha
# This means selected SKU options and linked drawing, not delivered hardware qualification.
d['exact_taobao_sku_confirmed']=True;d['procurement_scope']='Both exact PH0.8/H40-H45 UI options and supplier drawing verified; not a purchase or delivered fit acceptance.';p.write_text(json.dumps(d,indent=2),encoding='utf8')
for name in ['merge_contract.json','r1101_height_selection.json']:
 p=H/'digital/review'/name;d=json.loads(p.read_text());shutil.copy2(p,B/name)
 if name=='merge_contract.json':d['pre_sgd_pcb_sha256']=d['pcb_sha256'];d['pcb_sha256']=proof['digital']['candidate_pcb_sha256']
 else:d['current_pcb_sha256']=proof['digital']['candidate_pcb_sha256']
 d['sgd_followup_proof_sha256']=proofsha;p.write_text(json.dumps(d,indent=2),encoding='utf8')
# Export the real original pre-SMT board, never relabel the current PCB as baseline.
p=B/'pre_smt_digital.kicad_pcb';data=subprocess.run(['git','show','b67843f:'+str(H/'digital/YuEEG_H_DIGITAL.kicad_pcb').replace('\\','/')],capture_output=True,check=True).stdout;p.write_bytes(data)
assert sha(p)==json.loads((H/'review/smt_btb_adoption.json').read_text())['boards']['digital']['baseline_pcb_sha256']
print('Adopted checked SGDCONN pair; now refresh all native source checks and exports')
