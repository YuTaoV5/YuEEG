"""Independent hole-to-SMD check, including same-net pads, for the side-port edit."""
from pathlib import Path
import hashlib,json,math,pcbnew as p,wx
wx.DisableAsserts();H=Path('hardware/YuEEG_8CH_RevH_Stack');M=H/'mechanical/current'
path=H/'power/YuEEG_H_POWER.kicad_pcb';source=M/'side_power_port_adoption.json'
record=json.loads(source.read_text());b=p.LoadBoard(str(path))
selected={v['uuid']:v for v in record['added_vias']};seen=[];hits=[];total=0
for v in b.GetTracks():
 if not isinstance(v,p.PCB_VIA):continue
 total+=1;key=v.m_Uuid.AsString();new=key in selected
 if new:
  q=selected[key];xy=[p.ToMM(v.GetPosition().x),p.ToMM(v.GetPosition().y)]
  assert math.dist(xy,q['xy_mm'])<1e-6 and v.GetNetname()==q['net']
  assert p.ToMM(v.GetDrillValue())==q['drill_mm'] and p.ToMM(v.GetWidth(p.F_Cu))==q['diameter_mm']
  seen.append(key)
 circle=p.SHAPE_CIRCLE(v.GetPosition(),v.GetDrillValue()//2)
 for f in b.GetFootprints():
  if not new and f.GetReference() not in ['JP2','RP4']:continue
  for pad in f.Pads():
   if pad.GetAttribute()==p.PAD_ATTRIB_SMD and p.SHAPE.Collide(circle,pad.GetEffectiveShape(pad.GetLayer()),p.FromMM(.2499)):
    hits.append({'via_uuid':key,'pad':f.GetReference()+'.'+pad.GetNumber()})
assert set(seen)==set(selected) and not hits,hits
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
out={'pcb_sha256':sha(path),'selection_source_sha256':sha(source),'minimum_hole_to_smt_copper_mm':.25,'new_vias':list(selected.values()),'all_current_vias_checked_against_moved_footprints':total,'hits':hits,'scope':'All four newly selected via holes against all SMD pads, plus every current via hole against moved JP2/RP4 pads; same-net pads included. Other pre-existing via/thermal-pad relationships are outside this migration check. Not fabrication qualification.'}
(M/'side_power_via_clearance.json').write_text(json.dumps(out,indent=2),encoding='utf8')
print('PASS new power via holes / all SMD pads and every existing hole / moved pads, >=.25mm including same net')
