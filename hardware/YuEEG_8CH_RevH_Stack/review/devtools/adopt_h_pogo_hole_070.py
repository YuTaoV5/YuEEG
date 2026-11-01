"""Independently compare and adopt only the checked JP1 drill-only candidate."""
from pathlib import Path
import json,sys,copy,hashlib,shutil,pcbnew as p,wx
wx.DisableAsserts();sys.path.insert(0,'hardware/YuEEG_8CH_RevG/review');from sexpr_io import loads,sub
H=Path('hardware/YuEEG_8CH_RevH_Stack');C=Path('logs/pogo_hole_070_candidate');source=H/'power/YuEEG_H_POWER.kicad_pcb';target=C/'power/YuEEG_H_POWER.kicad_pcb';sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();sel=json.loads((C/'selection.json').read_text());assert sha(source)==sel['before_pcb_sha256'] and sha(target)==sel['candidate_pcb_sha256']
drc=json.loads((C/'power/drc_hole070.json').read_text());assert not any(drc[k] for k in ['violations','unconnected_items','schematic_parity'])
a=loads(source.read_text());b=loads(target.read_text())
def grouped(tree,key):return sorted([json.dumps(q) for q in tree if isinstance(q,list) and q[0] in key])
assert grouped(a,['segment','arc','via'])==grouped(b,['segment','arc','via'])
def fps(t):
 out={}
 for f in t:
  if isinstance(f,list) and f[0]=='footprint':
   ref=next(json.loads(v[2]) for v in f if isinstance(v,list) and v[:2]==['property','"Reference"']);out[ref]=f
 return out
old=fps(a);new=fps(b);assert old.keys()==new.keys() and all(old[k]==new[k] for k in old if k!='JP1')
x=copy.deepcopy(old['JP1']);y=new['JP1'];sub(x,'descr')[1]=sub(y,'descr')[1]
px={q[1]:q for q in x if isinstance(q,list) and q[0]=='pad'};py={q[1]:q for q in y if isinstance(q,list) and q[0]=='pad'};assert set(px)==set(py)=={'"1"','"2"'}
for key in px:
 assert float(sub(px[key],'drill')[1])==.6 and float(sub(py[key],'drill')[1])==.7;sub(px[key],'drill')[1]=sub(py[key],'drill')[1]
assert x==y,'JP1 changed outside description and drill diameters'
bb=p.LoadBoard(str(target));part=next(f for f in bb.GetFootprints() if f.GetReference()=='JP1');hits=[]
for hole in part.Pads():
 circle=p.SHAPE_CIRCLE(hole.GetPosition(),hole.GetDrillSize().x//2)
 for f in bb.GetFootprints():
  for pad in f.Pads():
   if pad.GetAttribute()==p.PAD_ATTRIB_SMD and p.SHAPE.Collide(circle,pad.GetEffectiveShape(pad.GetLayer()),p.FromMM(.2499)):hits.append([hole.GetNumber(),f.GetReference(),pad.GetNumber()])
assert not hits,hits
backup=Path('logs/before_pogo_hole_070');assert not backup.exists();backup.mkdir()
for file in [source,H/'footprints/YuEEG.pretty/NPBX1_MillMax0906_Dplus_Bminus_10mm.kicad_mod',H/'mechanical/current/side_power_port_adoption.json']:
 shutil.copy2(file,backup/file.name)
record={'status':'ADOPTED_DRILL_ONLY_ENGINEERING_NOT_HOLDER_RELEASE','baseline_git_commit':'87b5082a271e9986d702b8e01193958f1f626a15','before_pcb_sha256':sha(source),'current_pcb_sha256':sha(target),'changed_reference':'JP1','old_finished_hole_mm':.6,'new_finished_hole_mm':.7,'all_tracks_vias_unchanged':True,'all_other_footprints_unchanged':True,'JP1_only_description_and_drill_changed':True,'pad_nets_centers_copper_sizes_unchanged':True,'all2_holes_vs_all_SMD_pads_minimum_mm':.25,'same_net_smt_hole_hits':hits,'native_checks':{k:len(drc[k]) for k in ['violations','unconnected_items','schematic_parity']},'scope':'TwoPTH diameters and metadata only; current pad/nets/centers,all tracks/vias/other footprints retained. Does not qualify solder process,holder,force,battery fit or production.'}
shutil.copy2(target,source);shutil.copy2(C/'footprints/YuEEG.pretty/NPBX1_MillMax0906_Dplus_Bminus_10mm.kicad_mod',H/'footprints/YuEEG.pretty/NPBX1_MillMax0906_Dplus_Bminus_10mm.kicad_mod')
report=H/'mechanical/current/pogo_hole_tolerance_adoption.json';report.write_text(json.dumps(record,indent=2),encoding='utf8')
pf=H/'mechanical/current/side_power_port_adoption.json';d=json.loads(pf.read_text());d['before_pogo_hole_change_pcb_sha256']=d['current_pcb_sha256'];d['current_pcb_sha256']=sha(source);d['pogo_hole_followup_proof_sha256']=sha(report);pf.write_text(json.dumps(d,indent=2),encoding='utf8')
print('Adopted2 drill diameters only:0.60->0.70mm; nativeDRC/parity0;hole/SMT>=.25 including same-net')
