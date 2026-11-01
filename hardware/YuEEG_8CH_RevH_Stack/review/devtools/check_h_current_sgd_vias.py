"""Current SGDCONN hole-to-SMD screening, including same-net pads."""
from pathlib import Path
import json,hashlib,math,pcbnew as p,wx
wx.DisableAsserts();H=Path('hardware/YuEEG_8CH_RevH_Stack');source=H/'review/sgd_btb_adoption.json';adopt=json.loads(source.read_text());out={};sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest()
for name,row in adopt['boards'].items():
 path=H/name/('YuEEG_H_'+name.upper()+'.kicad_pcb');assert sha(path)==row['candidate_pcb_sha256'];b=p.LoadBoard(str(path));moved={v['uuid']:v for v in row['via_moves']};jh=next(f for f in b.GetFootprints() if f.GetReference()=='JH1');hits=[];seen=[];count=0
 for v in b.GetTracks():
  if not isinstance(v,p.PCB_VIA):continue
  count+=1;key=v.m_Uuid.AsString();circle=p.SHAPE_CIRCLE(v.GetPosition(),v.GetDrillValue()//2)
  if key in moved:
   q=moved[key];assert math.dist([p.ToMM(v.GetPosition().x),p.ToMM(v.GetPosition().y)],q['new_xy_mm'])<1e-6 and v.GetNetname()==q['net'];seen.append(key)
  for f in b.GetFootprints():
   if f.GetReference()!='JH1' and key not in moved:continue
   for pad in f.Pads():
    if pad.GetAttribute()==p.PAD_ATTRIB_SMD and p.SHAPE.Collide(circle,pad.GetEffectiveShape(pad.GetLayer()),p.FromMM(.2499)):
     hits.append({'via_uuid':key,'pad':f.GetReference()+'.'+pad.GetNumber()})
 assert set(seen)==set(moved) and not hits,hits
 out[name]={'pcb_sha256':sha(path),'all_current_vias_against_JH1_pads':count,'moved_vias_against_all_SMD_pads':len(seen),'hits':hits}
record={'adoption_sha256':sha(source),'minimum_hole_to_smt_copper_mm':.25,'boards':out,'scope':'Every via hole versus20SGD JH1lands and12moved via holes versus all SMD pads, same-net included. Other unchanged intentional via/pad relationships outside this migration scope.'}
(H/'review/sgd_btb_current_via_clearance.json').write_text(json.dumps(record,indent=2),encoding='utf8');print('PASS current SGDCONN via holes including same-net SMT pads')
