"""Recheck the three IMU ground vias after the SMT connector migration."""
from pathlib import Path
import json,hashlib,math,pcbnew as p,wx
wx.DisableAsserts();H=Path('hardware/YuEEG_8CH_RevH_Stack');D=H/'digital';path=D/'YuEEG_H_DIGITAL.kicad_pcb';b=p.LoadBoard(str(path));source=D/'review/new_ground_via_smd_clearance.json';old=json.loads(source.read_text(encoding='utf8'));rows=[]
for item in old['new_vias']:
 matches=[v for v in b.GetTracks() if v.Type()==p.PCB_VIA_T and v.GetNetname()=='GND' and math.dist([p.ToMM(v.GetPosition().x),p.ToMM(v.GetPosition().y)],item['xy_mm'])<.003]
 assert len(matches)==1
 via=matches[0];circle=p.SHAPE_CIRCLE(via.GetPosition(),via.GetDrillValue()//2);hits=[]
 for f in b.GetFootprints():
  for pad in f.Pads():
   if pad.GetAttribute()==p.PAD_ATTRIB_SMD and p.SHAPE.Collide(circle,pad.GetEffectiveShape(pad.GetLayer()),p.FromMM(.2499)):hits.append(f.GetReference()+'.'+pad.GetNumber())
 assert not hits,hits
 rows.append({'xy_mm':[p.ToMM(via.GetPosition().x),p.ToMM(via.GetPosition().y)],'uuid':via.m_Uuid.AsString(),'hits':hits})
out={'pcb_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'historical_via_selection_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'minimum_hole_to_smt_copper_mm':.25,'vias':rows,'scope':'Current native check of the three previously selected IMU ground vias, including same-net SMT pads. Migration new vias are checked separately in smt_btb_adoption.json. Not fabrication qualification.'}
(D/'review/imu_ground_via_current_clearance.json').write_text(json.dumps(out,indent=2),encoding='utf8');print('PASS three current IMU ground via hole/SMT clearances')
