"""Rebind unchanged graphic placement after copper-only changes, checking positions."""
from pathlib import Path
import pcbnew as p,json,hashlib,math
R=Path('hardware/YuEEG_8CH_RevH_Stack')
for name in ['afe','digital','power']:
 path=R/name/('YuEEG_H_'+name.upper()+'.kicad_pcb');b=p.LoadBoard(str(path));e=R/name/'review/module_legends.json';d=json.loads(e.read_text())
 for label in d['labels']:
  matches=[t for t in b.GetDrawings() if isinstance(t,p.PCB_TEXT) and t.GetLayer()==p.F_SilkS and t.GetText()==label['text']]
  assert len(matches)==1
  xy=[p.ToMM(matches[0].GetPosition().x),p.ToMM(matches[0].GetPosition().y)]
  assert math.dist(xy,label['center_mm'])<.00001
 d['source_sha256']=hashlib.sha256(path.read_bytes()).hexdigest();e.write_text(json.dumps(d,indent=2))
print('All module text positions match evidence')
