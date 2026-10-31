"""Read native PH4 ports without modifying either board."""
from pathlib import Path
import json,hashlib,pcbnew as p,wx
wx.DisableAsserts();H=Path('hardware/YuEEG_8CH_RevH_Stack');out={}
for name,ref in [('digital','JH2'),('power','JP2')]:
 path=H/name/('YuEEG_H_'+name.upper()+'.kicad_pcb');b=p.LoadBoard(str(path));f=next(f for f in b.GetFootprints() if f.GetReference()==ref);pads={}
 for pad in f.Pads():
  if pad.GetNumber() in ['1','2','3','4']:
   bb=pad.GetBoundingBox();pads[pad.GetNumber()]={'net':pad.GetNetname(),'xy_mm':[p.ToMM(pad.GetPosition().x),p.ToMM(pad.GetPosition().y)],'native_pad_bbox_xy_mm':[p.ToMM(bb.GetX()),p.ToMM(bb.GetY()),p.ToMM(bb.GetRight()),p.ToMM(bb.GetBottom())]}
 pts=[v for g in f.GraphicalItems() if g.GetLayer()==p.F_CrtYd for v in [g.GetStart(),g.GetEnd()]];ct=[min(p.ToMM(v.x) for v in pts),min(p.ToMM(v.y) for v in pts),max(p.ToMM(v.x) for v in pts),max(p.ToMM(v.y) for v in pts)]
 out[name]=dict(reference=ref,pcb_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),xy_mm=[p.ToMM(f.GetPosition().x),p.ToMM(f.GetPosition().y)],rotation_deg=f.GetOrientationDegrees(),courtyard_xy_mm=ct,pads=pads)
 if name=='digital':
  header=next(f for f in b.GetFootprints() if f.GetReference()=='JH1');boxes=[]
  for pad in header.Pads():
   bb=pad.GetBoundingBox();boxes.append([p.ToMM(bb.GetX()),p.ToMM(bb.GetY()),p.ToMM(bb.GetRight()),p.ToMM(bb.GetBottom())])
  out[name]['interboard_header']=dict(reference='JH1',native_pad_bbox_xy_mm=[min(v[0] for v in boxes),min(v[1] for v in boxes),max(v[2] for v in boxes),max(v[3] for v in boxes)],pad_centers_mm={v.GetNumber():[p.ToMM(v.GetPosition().x),p.ToMM(v.GetPosition().y)] for v in header.Pads()})
assert {k:v['net'] for k,v in out['digital']['pads'].items()}=={k:v['net'] for k,v in out['power']['pads'].items()}
dest=H/'mechanical/current/power_ports_native.json';dest.write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
