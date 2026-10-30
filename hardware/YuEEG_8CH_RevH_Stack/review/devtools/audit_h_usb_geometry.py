"""Measure native USB track geometry. This is not an impedance field solver."""
from pathlib import Path
import json,hashlib,collections
import pcbnew as p
R=Path('hardware/YuEEG_8CH_RevH_Stack');path=R/'digital/YuEEG_H_DIGITAL.kicad_pcb';b=p.LoadBoard(str(path));records={}
for net in ['USB_DOWN_DM','USB_DOWN_DP','USB_MCU_DM','USB_MCU_DP','USB_UP_DM','USB_UP_DP','USB_HOST_DM','USB_HOST_DP']:
 tracks=[t for t in b.GetTracks() if t.GetNetname()==net];groups=collections.defaultdict(list);vias=[]
 for t in tracks:
  if isinstance(t,p.PCB_VIA):vias.append([p.ToMM(t.GetPosition().x),p.ToMM(t.GetPosition().y)]);continue
  groups[(b.GetLayerName(t.GetLayer()),round(p.ToMM(t.GetWidth()),4))].append(p.ToMM(t.GetLength()))
 records[net]={'planar_track_length_mm':sum(sum(v) for v in groups.values()),'segments_by_layer_width':[{'layer':ly,'width_mm':w,'segments':len(ls),'length_mm':sum(ls)} for (ly,w),ls in sorted(groups.items())],'signal_vias_xy_mm':vias}
(R/'digital/review/usb_geometry.json').write_text(json.dumps({'pcb_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'nets':records,'scope':'Sum of all planar track centerline lengths in each net, including branches and loops; not end-to-end propagation path length or differential skew. Excludes via barrels, pads and package. Not an impedance, reference-plane continuity or USB compliance check.'},indent=2))
for n,r in records.items():print(n,round(r['planar_track_length_mm'],4),r['segments_by_layer_width'])
