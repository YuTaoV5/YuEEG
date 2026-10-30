from pathlib import Path
import sys,json,pcbnew as p,wx
wx.DisableAsserts();sys.path.insert(0,'hardware/YuEEG_8CH_RevG/review');from sexpr_io import loads,dumps,sub
path=Path('hardware/YuEEG_8CH_RevH_Stack/power/YuEEG_H_POWER.kicad_pcb');b=p.LoadBoard(str(path));ids=set()
for t in b.GetTracks():
 if t.GetNetname()!='GND':continue
 coords=[(p.ToMM(q.x),p.ToMM(q.y)) for q in [t.GetStart(),t.GetEnd()]]
 if any(16.3<x<18.3 and 6<y<8.5 for x,y in coords):ids.add(t.m_Uuid.AsString())
d=loads(path.read_text());d[:]=[t for t in d if not(isinstance(t,list) and t[0] in ['segment','via'] and json.loads(sub(t,'uuid')[1]) in ids)];path.write_text(dumps(d))
b=p.LoadBoard(str(path));net=b.FindNet('GND')
def xy(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
for a,c in [((17.95,6.75),(18.05,6.25)),((17,7.5),(17,8.65))]:
 t=p.PCB_TRACK(b);t.SetStart(xy(*a));t.SetEnd(xy(*c));t.SetWidth(p.FromMM(.25));t.SetLayer(p.F_Cu);t.SetNet(net);b.Add(t)
 v=p.PCB_VIA(b);v.SetPosition(xy(*c));v.SetWidth(p.FromMM(.4));v.SetDrill(p.FromMM(.2));v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetViaType(p.VIATYPE_THROUGH);v.SetNet(net);b.Add(v)
p.SaveBoard(str(path),b);print('Replaced',len(ids),'ground route objects to open control escapes')
