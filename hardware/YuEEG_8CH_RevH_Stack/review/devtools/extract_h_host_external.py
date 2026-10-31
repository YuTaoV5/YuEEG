"""Read external copper primitives in the native USB_HOST class."""
from pathlib import Path
import pcbnew as p,wx,json,hashlib
wx.DisableAsserts();H=Path('hardware/YuEEG_8CH_RevH_Stack');path=H/'digital/YuEEG_H_DIGITAL.kicad_pcb';b=p.LoadBoard(str(path));pro=json.loads(path.with_suffix('.kicad_pro').read_text());host={v['pattern'] for v in pro['net_settings']['netclass_patterns'] if v['netclass']=='USB_HOST'};items=[];nets={}
def bb(shape):r=shape.BBox();return [p.ToMM(v) for v in [r.GetX(),r.GetY(),r.GetRight(),r.GetBottom()]]
for f in b.GetFootprints():
 for pad in f.Pads():
  if f.GetReference() in ['F901','JH1','J601','U701']:nets[f.GetReference()+'.'+pad.GetNumber()]=pad.GetNetname()
  if pad.GetNetname() in host:
   for ly in [p.F_Cu,p.B_Cu]:
    if pad.IsOnLayer(ly):items.append(dict(kind='pad',ref=f.GetReference()+'.'+pad.GetNumber(),net=pad.GetNetname(),layer=b.GetLayerName(ly),bounds_mm=bb(pad.GetEffectiveShape(ly))))
for t in b.GetTracks():
 if t.GetNetname() in host:
  for ly in [p.F_Cu,p.B_Cu]:
   if t.IsOnLayer(ly):items.append(dict(kind='via' if isinstance(t,p.PCB_VIA) else 'track',ref=t.m_Uuid.AsString(),net=t.GetNetname(),layer=b.GetLayerName(ly),bounds_mm=bb(t.GetEffectiveShape(ly))))
record=dict(status='NATIVE_EXTERNAL_COPPER_EXTRACT_NOT_ASSEMBLY_RELEASE',pcb_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),host_nets=sorted(host),selected_component_pad_nets=nets,external_items=items);Path('logs/host_external.json').write_text(json.dumps(record,indent=2));print('HOST classes',sorted(host));print('F901',[(k,v) for k,v in nets.items() if k.startswith('F901')]);print('Back copper',[(v['net'],v['bounds_mm']) for v in items if v['layer']=='B.Cu'])
