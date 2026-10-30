from pathlib import Path
import pcbnew as p,wx,json
wx.DisableAsserts();H=Path('hardware/YuEEG_8CH_RevH_Stack');b=p.LoadBoard(str(H/'digital/YuEEG_H_DIGITAL.kicad_pcb'));out=[]
for f in b.GetFootprints():
 if f.GetLayer()!=p.F_Cu:continue
 points=[q for g in f.GraphicalItems() if g.GetLayer()==p.F_CrtYd for q in [g.GetStart(),g.GetEnd()]]
 if not points:continue
 x,y=min(p.ToMM(q.x) for q in points),min(p.ToMM(q.y) for q in points);w=max(p.ToMM(q.x) for q in points)-x;h=max(p.ToMM(q.y) for q in points)-y
 if x<34.5 and x+w>25.8 and y<26.5 and y+h>20.3:
  out.append(dict(ref=f.GetReference(),value=f.GetValue(),fp=str(f.GetFPID().GetLibItemName()),xy=[p.ToMM(f.GetPosition().x),p.ToMM(f.GetPosition().y)],angle=f.GetOrientationDegrees(),courtyard=[x,y,x+w,y+h]))
print(json.dumps(out,indent=2));(H/'display_link/review/neighbor_native.json').write_text(json.dumps(out,indent=2))
