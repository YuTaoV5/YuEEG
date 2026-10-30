from pathlib import Path
import sys,json,math,pcbnew as p,wx
wx.DisableAsserts();sys.path.insert(0,'hardware/YuEEG_8CH_RevG/review');from sexpr_io import loads,dumps,sub
R=Path('hardware/YuEEG_8CH_RevH_Stack/digital');path=R/'YuEEG_H_DIGITAL.kicad_pcb';d=loads(path.read_text());nets={n[1]:json.loads(n[2]) for n in d if isinstance(n,list) and n[0]=='net'}
d[:]=[t for t in d if not(isinstance(t,list) and t[0] in ['segment','via'] and nets[sub(t,'net')[1]]=='TP_SDA_IDLE')];path.write_text(dumps(d))
b=p.LoadBoard(str(path));fs={f.GetReference():f for f in b.GetFootprints()};moving={'TP404','R2003'}
def bb(f):
 boxes=[q.GetBoundingBox() for q in f.GraphicalItems() if q.GetLayer()==p.F_CrtYd]
 return [min(p.ToMM(q.GetX()) for q in boxes),min(p.ToMM(q.GetY()) for q in boxes),max(p.ToMM(q.GetRight()) for q in boxes),max(p.ToMM(q.GetBottom()) for q in boxes)]
def ov(a,c):return a[0]<c[2]+.025 and a[2]>c[0]-.025 and a[1]<c[3]+.025 and a[3]>c[1]-.025
fixed=[bb(f) for ref,f in fs.items() if ref not in moving and f.GetLayer()==p.F_Cu]
obs=[]
for f in fs.values():
 if f.GetReference() in moving:continue
 for q in f.Pads():
  if q.IsOnLayer(p.F_Cu):sh=q.GetEffectiveShape(p.F_Cu);obs.append((q.GetNetCode(),sh,sh.BBox()))
for t in b.GetTracks():
 if t.IsOnLayer(p.F_Cu):sh=t.GetEffectiveShape(p.F_Cu);obs.append((t.GetNetCode(),sh,sh.BBox()))
out={}
for ref,target in [('TP404',(44,8)),('R2003',(20,39.5))]:
 f=fs[ref];candidates=[]
 for angle in [0,90,180,270]:
  for xi in range(4,188):
   for yi in range(4,160):
    x,y=xi/4,yi/4;cost=math.dist((x,y),target)
    if cost<6:candidates.append((cost,x,y,angle))
 for cost,x,y,a in sorted(candidates):
  f.SetOrientationDegrees(a);f.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)));qbox=bb(f)
  if qbox[0]<.7 or qbox[2]>47.3 or qbox[1]<.7 or qbox[3]>40.4 or any(ov(qbox,q) for q in fixed):continue
  ok=True
  for q in f.Pads():
   sh=q.GetEffectiveShape(p.F_Cu);sb=sh.BBox();sb.Inflate(p.FromMM(.151))
   if any(code!=q.GetNetCode() and box.Intersects(sb) and other.Collide(sh,p.FromMM(.151)) for code,other,box in obs):ok=False;break
  if not ok:continue
  fixed.append(qbox);out[ref]=[x,y,a];break
 else:raise RuntimeError('No placement found for '+ref)
 for q in f.Pads():
  sh=q.GetEffectiveShape(p.F_Cu);obs.append((q.GetNetCode(),sh,sh.BBox()))
p.SaveBoard(str(path),b);(R/'review/l401_neighbor_adjustment.json').write_text(json.dumps(out,indent=2));print(out)
