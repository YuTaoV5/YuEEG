from pathlib import Path
import pcbnew as p,wx,json,subprocess
wx.DisableAsserts();path=Path('hardware/YuEEG_8CH_RevH_Stack/power/YuEEG_H_POWER.kicad_pcb');backup=path.read_bytes();b=p.LoadBoard(str(path));fs={f.GetReference():f for f in b.GetFootprints()}
def xy(v):return p.VECTOR2I(*[p.FromMM(q) for q in v])
out=[]
for ref,pin,end in [('UP2','4',(25.75,9.65)),('CP2','2',(21.725,4.9)),('CP4','2',(27,10.65)),('CP5','2',(31.25,8.25)),('CP6','2',(32,11))]:
 q=next(q for q in fs[ref].Pads() if q.GetNumber()==pin);assert q.GetNetname()=='GND'
 t=p.PCB_TRACK(b);t.SetStart(q.GetPosition());t.SetEnd(xy(end));t.SetWidth(p.FromMM(.25));t.SetLayer(p.F_Cu);t.SetNet(q.GetNet());b.Add(t)
 v=p.PCB_VIA(b);v.SetPosition(xy(end));v.SetWidth(p.FromMM(.45));v.SetDrill(p.FromMM(.2));v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetViaType(p.VIATYPE_THROUGH);v.SetNet(q.GetNet());b.Add(v)
 out.append({'pin':ref+'.'+pin,'via_xy_mm':end,'stub_mm':p.ToMM(t.GetLength()),'objects':[t.m_Uuid.AsString(),v.m_Uuid.AsString()]})
p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(path),b)
report=path.parent/'review/drc_local_vias.json';subprocess.run(['X:/SoftWare/Kicad/bin/kicad-cli.exe','pcb','drc','--schematic-parity','--format','json','--output',str(report),str(path)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True)
d=json.loads(report.read_text());fail=d['violations']+d['unconnected_items']+d['schematic_parity']
if fail:
 path.write_bytes(backup);print(json.dumps(fail,ensure_ascii=False));raise RuntimeError('Candidate local vias failed DRC; restored PCB')
(path.parent/'review/local_ground_vias_1s.json').write_text(json.dumps(out,indent=2));print('Five local ground vias passed native DRC')
