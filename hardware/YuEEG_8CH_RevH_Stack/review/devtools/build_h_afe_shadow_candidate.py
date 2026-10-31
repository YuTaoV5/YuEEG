"""Independent AFE power/isolation-shadow candidate, no main-board mutation."""
from pathlib import Path
import json,hashlib,shutil,sys,subprocess,copy,pcbnew as p,wx
wx.DisableAsserts();sys.path.insert(0,'hardware/YuEEG_8CH_RevG/review');from sexpr_io import loads,dumps,sub
H=Path('hardware/YuEEG_8CH_RevH_Stack');D=Path('logs/afe_shadow_candidate');D.mkdir(exist_ok=True);path=D/'YuEEG_H_AFE.kicad_pcb';project=path.with_suffix('.kicad_pro');base=H/'afe/YuEEG_H_AFE.kicad_pcb';shutil.copy2(base.with_suffix('.kicad_pro'),project);pro=project.read_bytes();(D/'fp-lib-table').write_text((base.parent/'fp-lib-table').read_text().replace('${KIPRJMOD}/../footprints',(H/'footprints').resolve().as_posix()),encoding='utf8')
b=p.LoadBoard(str(base));positions={'C405':(3.9,42.5,180),'R401':(7.05,40.65,0),'R402':(5.2,44.5,0),'D403':(19,42.0,0)};fs={f.GetReference():f for f in b.GetFootprints()}
for ref,(x,y,a) in positions.items():f=fs[ref];f.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)));f.SetOrientationDegrees(a)
# Use native shapes to rip only copper conflicting with moved pads.
newpads=[v for ref in positions for v in fs[ref].Pads()];ripped=[];layers=[p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]
for t in list(b.GetTracks()):
 if any(t.GetNetCode()!=pad.GetNetCode() and any(t.IsOnLayer(ly) and pad.IsOnLayer(ly) and t.GetEffectiveShape(ly).Collide(pad.GetEffectiveShape(ly),p.FromMM(.1499)) for ly in layers) for pad in newpads) or t.GetBoundingBox().GetBottom()>p.FromMM(47.5):ripped.append(dict(uuid=t.m_Uuid.AsString(),net=t.GetNetname()));b.Remove(t)
p.SaveBoard(str(path),b);project.write_bytes(pro);t=loads(path.read_text(encoding='utf8'));zones=[z for z in t if isinstance(z,list) and z[0]=='zone' and sub(z,'name') and sub(z,'name')[1]=='"STACK_USB_HOST_EXCLUSION"'];assert len(zones)==1
for point in sub(sub(zones[0],'polygon'),'pts')[1:]:
 if point[2]=='49.05':point[2]='47.5'
path.write_text(dumps(t),encoding='utf8')
subprocess.run(['X:/SoftWare/Kicad/bin/python.exe',str(Path(__file__).with_name('fill_h_afe_shadow_candidate.py'))],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
cli='X:/SoftWare/Kicad/bin/kicad-cli.exe';subprocess.run([cli,'pcb','drc','--format','json','-o',str(D/'drc.json'),str(path)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True)
r=json.loads((D/'drc.json').read_text());(D/'candidate.json').write_text(json.dumps(dict(status='ROUTING_IN_PROGRESS_NOT_MAIN_DESIGN',baseline_pcb_sha256=hashlib.sha256(base.read_bytes()).hexdigest(),positions=positions,ripped=ripped,exclusion_y_min_mm=47.5),indent=2))
print('AFE candidate ripped',len(ripped),'violations',len(r['violations']),'unconnected',len(r['unconnected_items']));print([(v['type'],v['description']) for v in r['violations']][:10])
