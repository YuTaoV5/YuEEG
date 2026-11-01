"""One-time adoption of the checked side-facing power-port candidate.

Fails before mutation unless the baseline, candidate and fresh native parity
report match. Candidate routing lives in ignored scratch storage, not a second
authoritative hardware project. Publication and assembly release are separate.
"""
from pathlib import Path
import collections
import hashlib
import json
import shutil
import pcbnew as p
import wx
wx.DisableAsserts()
H=Path('hardware/YuEEG_8CH_RevH_Stack');D=Path('logs/power_side_port_candidate/v5')
src=H/'power/YuEEG_H_POWER.kicad_pcb';candidate=D/src.name
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
review=json.loads((D/'change_review.json').read_text())
assert sha(src)==review['baseline_sha256']=='07b9161688a09dfbe1dbef2a7237308e407affba4f59a0fe9e27f99c976f8695'
assert sha(candidate)==review['candidate_sha256']=='37bd0a3087d20760dc784c89024cb8c6144ad6833b5efe219a2365d07d92b3e1'
drc=json.loads((D/'drc_parity.json').read_text())
assert all(not drc[k] for k in ['violations','unconnected_items','schematic_parity'])
via_review=json.loads((D/'via_clearance.json').read_text());assert not via_review['hits']
a,b=[p.LoadBoard(str(f)) for f in [src,candidate]]
def netmap(board):
 return sorted((f.GetReference(),q.GetNumber(),q.GetNetname()) for f in board.GetFootprints() for q in f.Pads())
assert netmap(a)==netmap(b)
def geometry(board,net):
 return collections.Counter((t.GetClass(),t.GetLayer(),t.GetStart().x,t.GetStart().y,t.GetEnd().x,t.GetEnd().y,t.GetWidth()) for t in board.GetTracks() if t.GetNetname()==net)
for net in ['P_SW','P_FB']:assert geometry(a,net)==geometry(b,net)
af={f.GetReference():f for f in a.GetFootprints()};changed=[]
for f in b.GetFootprints():
 g=af[f.GetReference()]
 if f.GetPosition()!=g.GetPosition() or f.GetOrientationDegrees()!=g.GetOrientationDegrees():changed.append(f.GetReference())
assert set(changed)=={'JP2','RP4'}
backup=Path('logs/before_side_power_port_adoption');backup.mkdir(exist_ok=False)
shutil.copy2(src,backup/src.name)
shutil.copy2(candidate,src)
legend_path=H/'power/review/module_legends.json';legends=json.loads(legend_path.read_text())
for label in legends['labels']:
 assert label['text'] in ['1S POWER','PROTECT']
 label.update(center_mm=[.9,6 if label['text']=='1S POWER' else 13],rotation_deg=90,font_height_mm=.8)
legend_path.write_text(json.dumps(legends,indent=2),encoding='utf8')
review.update(status='ADOPTED_SIDE_PORT_ENGINEERING_NOT_ASSEMBLY_RELEASE',current_pcb_sha256=sha(src),baseline_git_commit='21618f34c2ccfb7e3641fe9aaab040dd30c9e255',native_drc_report_sha256=sha(D/'drc_parity.json'),checks={'drc':0,'unconnected':0,'schematic_parity':0,'all_pad_nets_preserved':True},positions_mm={'JP2':[7.5,11.4,270],'RP4':[7.,2.8,90]},added_vias=via_review['added_vias'],same_net_via_correction={'from_mm':[24.5,11.65],'to_mm':[25.4,12.9],'reason':'Move new SYS_5V hole outside RP5 SMD pad clearance; .25mm checked including same net.'},scope='Local power-port and gate-pulldown repositioning. P_SW/P_FB track geometry preserved exactly; GND,protected-battery,5V and gate branches rerouted. Nominal assembly comparison is separate and does not qualify parts,holder,screen,wire bend capability or acquisition performance.')
(H/'mechanical/current/side_power_port_adoption.json').write_text(json.dumps(review,indent=2),encoding='utf8')
print('Adopted side-facing power JP2, RP4 moved; netmap and P_SW/P_FB preserved. Refresh source-bound evidence and exports.')
