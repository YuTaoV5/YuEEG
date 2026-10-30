"""Sample centerline coverage by the intended adjacent filled ground planes."""
from pathlib import Path
import pcbnew as p,math,json,hashlib
R=Path('hardware/YuEEG_8CH_RevH_Stack/digital');path=R/'YuEEG_H_DIGITAL.kicad_pcb';b=p.LoadBoard(str(path));rows=[]
vias=[t for t in b.GetTracks() if isinstance(t,p.PCB_VIA)]
usb={'USB_DOWN_DM','USB_DOWN_DP','USB_MCU_DM','USB_MCU_DP','USB_UP_DM','USB_UP_DP','USB_HOST_DM','USB_HOST_DP'}
for t in b.GetTracks():
 if isinstance(t,p.PCB_VIA) or t.GetNetname() not in usb:continue
 net=t.GetNetname();gnd='GND' if net.startswith(('USB_DOWN','USB_MCU')) else 'HOST_GND';refs=[p.In1_Cu,p.In3_Cu] if t.GetLayer()==p.In2_Cu else [p.In1_Cu];a=t.GetStart();c=t.GetEnd();steps=max(1,math.ceil(p.ToMM(t.GetLength())/.1));samples=[]
 for i in range(steps+1):
  pt=p.VECTOR2I(round(a.x+(c.x-a.x)*i/steps),round(a.y+(c.y-a.y)*i/steps));missing=[]
  for ly in refs:
   zs=[z for z in b.Zones() if not z.GetIsRuleArea() and z.GetNetname()==gnd and z.IsOnLayer(ly)]
   if not any(z.GetFilledPolysList(ly).Contains(pt) for z in zs):missing.append(b.GetLayerName(ly))
  if missing:
   nearby=[t.GetNetname() for t in vias if t.GetNetname()!=gnd and math.hypot(pt.x-t.GetPosition().x,pt.y-t.GetPosition().y)<=t.GetWidth(p.In1_Cu)/2+p.FromMM(.17)]
   samples.append({'xy_mm':[p.ToMM(pt.x),p.ToMM(pt.y)],'missing_planes':missing,'near_via_antipad_nets':nearby,'classification':'near_signal_via_antipad' if nearby else 'requires_review'})
 rows.append({'net':net,'layer':b.GetLayerName(t.GetLayer()),'from_mm':[p.ToMM(a.x),p.ToMM(a.y)],'to_mm':[p.ToMM(c.x),p.ToMM(c.y)],'reference_net':gnd,'sample_count':steps+1,'uncovered_samples':samples})
out={'pcb_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'sample_pitch_max_mm':.1,'segments':rows,'scope':'Static centerline sampling of native filled-zone copper only. Does not prove continuous return around holes, field distribution, full trace-width coverage, impedance or USB compliance.'}
(R/'review/usb_reference_coverage.json').write_text(json.dumps(out,indent=2));print('segments',len(rows),'uncovered',sum(len(r['uncovered_samples']) for r in rows),'outside via-antipad neighborhoods',sum(s['classification']=='requires_review' for r in rows for s in r['uncovered_samples']));print([(r['net'],s) for r in rows for s in r['uncovered_samples'] if s['classification']=='requires_review'])
