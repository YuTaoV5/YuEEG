from pathlib import Path
import pcbnew as p,wx,json,sys
wx.DisableAsserts();R=Path('hardware/YuEEG_8CH_RevH_Stack/digital');path=R/'YuEEG_H_DIGITAL.kicad_pcb';b=p.LoadBoard(str(path));f=next(f for f in b.GetFootprints() if f.GetReference()=='R843');f.SetPosition(p.VECTOR2I(p.FromMM(20.5),p.FromMM(29.2)));f.SetOrientationDegrees(0);ripped={}
for q in f.Pads():
 shape=q.GetEffectiveShape(p.F_Cu)
 for ff in b.GetFootprints():
  if ff.GetReference()=='R843':continue
  for a in ff.Pads():
   if a.IsOnLayer(p.F_Cu) and q.GetNetCode()!=a.GetNetCode():assert not a.GetEffectiveShape(p.F_Cu).Collide(shape,p.FromMM(.1499)),(ff.GetReference(),a.GetNumber())
 for t in b.GetTracks():
  if t.IsOnLayer(p.F_Cu) and q.GetNetCode()!=t.GetNetCode() and t.GetEffectiveShape(p.F_Cu).Collide(shape,p.FromMM(.1499)):ripped[t.m_Uuid.AsString()]=t.GetNetname()
for q in b.GetDrawings():
 if q.Type()!=p.PCB_SHAPE_T or q.GetLayer()!=p.B_SilkS:continue
 for get,set_ in [(q.GetStart,q.SetStart),(q.GetEnd,q.SetEnd)]:
  pt=get();y=p.ToMM(pt.y)
  if abs(y-24.8)<.001:set_(p.VECTOR2I(pt.x,p.FromMM(23.8)))
  elif abs(y-26)<.001:set_(p.VECTOR2I(pt.x,p.FromMM(27.5)))
p.SaveBoard(str(path),b);sys.path.insert(0,'hardware/YuEEG_8CH_RevG/review');from sexpr_io import loads,dumps,sub
d=loads(path.read_text());d[:]=[q for q in d if not(isinstance(q,list) and q[0] in ['segment','via','arc'] and sub(q,'uuid') and json.loads(sub(q,'uuid')[1]) in ripped)];path.write_text(dumps(d));print('R843 moved into freed front-side capacitor space; affected',ripped)
s=Path('logs/route_h_digital.py').read_text().replace("=='In1.Cu'","in ['In1.Cu','In3.Cu']");exec(s)
