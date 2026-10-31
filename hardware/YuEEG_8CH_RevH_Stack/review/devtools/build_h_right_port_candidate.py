"""Independent native routing candidate; main-board files remain untouched."""
from pathlib import Path
import json,shutil,subprocess,hashlib,pcbnew as p,wx
wx.DisableAsserts();H=Path('hardware/YuEEG_8CH_RevH_Stack');D=Path('logs/right_power_port_candidate');D.mkdir(exist_ok=True);name='YuEEG_H_DIGITAL';base=H/'digital';path=D/(name+'.kicad_pcb');project=path.with_suffix('.kicad_pro');shutil.copy2(base/(name+'.kicad_pro'),project);pro=project.read_bytes();b=p.LoadBoard(str(base/(name+'.kicad_pcb')));old=next(f for f in b.GetFootprints() if f.GetReference()=='JH2');nets={v.GetNumber():v.GetNet() for v in old.Pads() if v.GetNumber() in ['1','2','3','4']};oldpos=[(p.ToMM(v.GetPosition().x),p.ToMM(v.GetPosition().y)) for v in old.Pads() if v.GetNumber() in nets]
fp='JST_PH_S4B-PH-K_1x04_P2.00mm_Horizontal';f=p.FootprintLoad('X:/SoftWare/Kicad/share/kicad/footprints/Connector_JST.pretty',fp);f.SetReference('JH2');f.SetValue('S4B-PH-K-S / 5V+CELL SENSE / RIGHT');f.SetFPID(p.LIB_ID('Connector_JST',fp));f.SetPath(old.GetPath());f.SetOrientationDegrees(90);f.SetPosition(p.VECTOR2I(p.FromMM(32.4),p.FromMM(38.5)));f.Reference().SetVisible(False);f.Value().SetVisible(False)
for pad in f.Pads():pad.SetNet(nets[pad.GetNumber()])
b.Remove(old);b.Add(f);removed=[];layers=[p.F_Cu,p.In1_Cu,p.In2_Cu,p.In3_Cu,p.In4_Cu,p.B_Cu]
for t in list(b.GetTracks()):
 if any(v.GetNetCode()!=t.GetNetCode() and any(t.IsOnLayer(ly) and t.GetEffectiveShape(ly).Collide(v.GetEffectiveShape(ly),p.FromMM(.1499)) for ly in layers) for v in f.Pads()):
  removed.append(dict(uuid=t.m_Uuid.AsString(),net=t.GetNetname()));b.Remove(t)
p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(path),b);project.write_bytes(pro);cli='X:/SoftWare/Kicad/bin/kicad-cli.exe';subprocess.run([cli,'pcb','drc','--format','json','-o',str(D/'drc.json'),str(path)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
r=json.loads((D/'drc.json').read_text());(D/'candidate.json').write_text(json.dumps(dict(status='ROUTING_IN_PROGRESS_NOT_MAIN_DESIGN',baseline_pcb_sha256=hashlib.sha256((base/(name+'.kicad_pcb')).read_bytes()).hexdigest(),removed=removed),indent=2));print('Candidate only: ripped',len(removed),'tracks/vias; violations',len(r['violations']),'unconnected',len(r['unconnected_items']));print([(v['type'],v['description']) for v in r['violations']][:8])
