"""Ground only the flat reinforced ends; keep the bend free of poured planes."""
from pathlib import Path
import pcbnew as p,wx,json,subprocess
wx.DisableAsserts();D=Path('hardware/YuEEG_8CH_RevH_Stack/display_link');path=D/'YuEEG_H_DISPLAY_LINK.kicad_pcb';old=path.read_bytes();project=path.with_suffix('.kicad_pro');pro=project.read_bytes();b=p.LoadBoard(str(path));q=json.loads((D/'review/design_contract.json').read_text());W,B=q['outline_mm'];a,c=q['bend_interval_flat_y_mm'];net=b.FindNet('GND')
assert not any(not z.GetIsRuleArea() for z in b.Zones()),'Ground planes already present'
for lo,hi in [(.25,a-.15),(c+.15,B-.25)]:
 for ly in [p.F_Cu,p.B_Cu]:
  z=p.ZONE(b);z.SetLayer(ly);z.SetNet(net);z.SetLocalClearance(p.FromMM(.1));z.SetMinThickness(p.FromMM(.1));z.SetPadConnection(p.ZONE_CONNECTION_FULL);z.Outline().NewOutline()
  for x,y in [(.25,lo),(W-.25,lo),(W-.25,hi),(.25,hi)]:z.Outline().Append(p.FromMM(x),p.FromMM(y))
  b.Add(z)
for x,y in [(.6,q['connector_centers_flat_mm']['JF1'][1]),(W-.6,q['connector_centers_flat_mm']['JF2'][1])]:
 v=p.PCB_VIA(b);v.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)));v.SetWidth(p.FromMM(.3));v.SetDrill(p.FromMM(.1));v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetViaType(p.VIATYPE_THROUGH);v.SetNet(net);b.Add(v)
p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(path),b);project.write_bytes(pro);report=D/'review/drc_current.json';subprocess.run(['X:/SoftWare/Kicad/bin/kicad-cli.exe','pcb','drc','--schematic-parity','--format','json','-o',str(report),str(path)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True);d=json.loads(report.read_text(encoding='utf8'));bad=[v for v in d['violations'] if v['type']!='track_dangling']
if bad:path.write_bytes(old);raise RuntimeError([(v['type'],v['description']) for v in bad])
print('End planes: DRC',len(d['violations']),'unconnected',len(d['unconnected_items']),'parity',len(d['schematic_parity']))
