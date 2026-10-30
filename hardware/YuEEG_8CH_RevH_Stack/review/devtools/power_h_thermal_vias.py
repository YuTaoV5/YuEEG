from pathlib import Path
import pcbnew as p,json,math,sys
sys.path.insert(0,'hardware/YuEEG_8CH_RevG/review')
from sexpr_io import loads,dumps,sub
R=Path('hardware/YuEEG_8CH_RevH_Stack/power');path=R/'YuEEG_H_POWER.kicad_pcb'
old=json.loads((R/'review/thermal_vias.json').read_text())['xy_mm'] if (R/'review/thermal_vias.json').exists() else []
d=loads(path.read_text());rtn=next(n[1] for n in d if isinstance(n,list) and n[0]=='net' and json.loads(n[2])=='P_RTN')
d[:]=[n for n in d if not(isinstance(n,list) and n[0]=='via' and sub(n,'net')[1]==rtn and any(math.dist(tuple(map(float,sub(n,'at')[1:3])),q)<.001 for q in old))]
path.write_text(dumps(d));b=p.LoadBoard(str(path))
ep=next(q for f in b.GetFootprints() if f.GetReference()=='UP1' for q in f.Pads() if q.GetNumber()=='17')
net=ep.GetNet();vias=[]
for x,y in [(x,y) for y in [4.9,9.1,5.5,8.5,6.1,7.9,7] for x in [21.7,24.3,22.3,23.7,23]]:
 if len(vias)==4:break
 pos=p.VECTOR2I(p.FromMM(x),p.FromMM(y));circ=p.SHAPE_CIRCLE(pos,p.FromMM(.2));bad=False
 for f in b.GetFootprints():
  for pad in f.Pads():
   if pad.GetNetCode()==net.GetNetCode():continue
   for layer in [p.F_Cu,p.B_Cu]:
    if pad.IsOnLayer(layer) and pad.GetEffectiveShape(layer).Collide(circ,p.FromMM(.151)):bad=True
 for t in b.GetTracks():
  if isinstance(t,p.PCB_VIA) and math.dist((x,y),(p.ToMM(t.GetPosition().x),p.ToMM(t.GetPosition().y)))<p.ToMM(t.GetDrillValue())/2+.1+.251:bad=True
  if t.GetNetCode()==net.GetNetCode():continue
  for layer in [p.F_Cu,p.B_Cu]:
   if t.IsOnLayer(layer) and t.GetEffectiveShape(layer).Collide(circ,p.FromMM(.151)):bad=True
 if bad:continue
 v=p.PCB_VIA(b);v.SetPosition(pos);v.SetWidth(p.FromMM(.4));v.SetDrill(p.FromMM(.2));v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetViaType(p.VIATYPE_THROUGH);v.SetNet(net);b.Add(v);vias.append([x,y])
assert len(vias)==4,('Only this many safe thermal vias',vias)
p.SaveBoard(str(path),b)
(R/'review/thermal_vias.json').write_text(json.dumps({'part':'UP1 TPS26600','net':'P_RTN','via_diameter_mm':.4,'drill_mm':.2,'xy_mm':vias,'note':'Tent vias under the package; fabrication/assembly must review the exposed-pad solder mask and paste geometry. Thermal resistance is not measured.'},indent=2))
print('Added',len(vias),'RTN thermal vias')
