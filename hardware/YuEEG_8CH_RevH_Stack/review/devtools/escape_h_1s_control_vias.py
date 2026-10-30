from pathlib import Path
import pcbnew as p,wx,json,sys
wx.DisableAsserts();sys.path.insert(0,'hardware/YuEEG_8CH_RevG/review');from sexpr_io import loads,dumps,sub
path=Path('hardware/YuEEG_8CH_RevH_Stack/power/YuEEG_H_POWER.kicad_pcb');b=p.LoadBoard(str(path));ids=set()
for t in b.GetTracks():
 if t.GetNetname()!='GND':continue
 pts=[(round(p.ToMM(q.x),5),round(p.ToMM(q.y),5)) for q in [t.GetStart(),t.GetEnd()]]
 if (17,8.65) in pts:ids.add(t.m_Uuid.AsString())
d=loads(path.read_text());d[:]=[t for t in d if not(isinstance(t,list) and t[0] in ['segment','via'] and json.loads(sub(t,'uuid')[1]) in ids)];path.write_text(dumps(d))
b=p.LoadBoard(str(path))
def xy(v):return p.VECTOR2I(*[p.FromMM(q) for q in v])
for net,a,c in [('P_ILM',(17.95,7.25),(18.1,7.25)),('P_UV',(16.05,7.25),(15.95,7.25))]:
 n=b.FindNet(net);t=p.PCB_TRACK(b);t.SetStart(xy(a));t.SetEnd(xy(c));t.SetWidth(p.FromMM(.15));t.SetLayer(p.F_Cu);t.SetNet(n);b.Add(t)
 v=p.PCB_VIA(b);v.SetPosition(xy(c));v.SetWidth(p.FromMM(.4));v.SetDrill(p.FromMM(.2));v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetViaType(p.VIATYPE_THROUGH);v.SetNet(n);b.Add(v)
p.SaveBoard(str(path),b)
from h_local_router import load
ns=load('power');b,route,pad,loc=[ns[k] for k in ['b','route','pad','loc']]
for net,a,ref,num in [('P_ILM',(18.1,7.25),'RP3',1),('P_UV',(15.95,7.25),'RP1',2)]:
 q=pad(ref,num);assert q.GetNetname()==net
 route(q.GetNet(),a,loc(q.GetPosition()),width=.15,sl=1,el=0);p.SaveBoard(str(path),b)
print('Two control nets escaped to rear copper')
