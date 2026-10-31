"""Move R401 off the regulator silk and rip only conflicting feedback tracks."""
from pathlib import Path
import pcbnew as p,wx,json,subprocess
print('imports complete',flush=True)
wx.DisableAsserts();D=Path('logs/afe_shadow_candidate');path=D/'YuEEG_H_AFE.kicad_pcb';pro=path.with_suffix('.kicad_pro').read_bytes();b=p.LoadBoard(str(path));f=next(f for f in b.GetFootprints() if f.GetReference()=='R401');f.SetPosition(p.VECTOR2I(p.FromMM(7.05),p.FromMM(40.45)));removed=[]
for t in list(b.GetTracks()):
 if any(t.IsOnLayer(p.F_Cu) and t.GetNetCode()!=v.GetNetCode() and t.GetEffectiveShape(p.F_Cu).Collide(v.GetEffectiveShape(p.F_Cu),p.FromMM(.1499)) for v in f.Pads()):removed.append(t.GetNetname());b.Remove(t)
print('Removed conflicting tracks',removed,flush=True)
p.SaveBoard(str(path),b);path.with_suffix('.kicad_pro').write_bytes(pro)
print('Saved before separate fill',flush=True)
subprocess.run(['X:/SoftWare/Kicad/bin/python.exe',str(Path(__file__).with_name('fill_h_afe_shadow_candidate.py'))],check=True)
r=json.loads((D/'candidate.json').read_text());r['positions']['R401']=[7.05,40.45,0];r['c405_local_gnd_via_mm']=[1.5,42.5];r['c405_ground_return_track_width_mm']=.5;(D/'candidate.json').write_text(json.dumps(r,indent=2));print('R401 clearance refinement ripped',removed)
