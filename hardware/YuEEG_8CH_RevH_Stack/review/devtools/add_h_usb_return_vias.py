from pathlib import Path
import pcbnew as p,wx,math,json,subprocess
wx.DisableAsserts();R=Path('hardware/YuEEG_8CH_RevH_Stack/digital');path=R/'YuEEG_H_DIGITAL.kicad_pcb';original=path.read_bytes();b=p.LoadBoard(str(path));layers=list(b.GetEnabledLayers().CuStack());net=b.FindNet('GND');mm=p.FromMM
def xy(t):return p.VECTOR2I(mm(t[0]),mm(t[1]))
def loc(v):return p.ToMM(v.x),p.ToMM(v.y)
obs={ly:{} for ly in layers};holes=[]
def index(ly,shape):
 box=shape.BBox()
 for x in range(box.GetX()//mm(2),(box.GetRight()//mm(2))+1):
  for y in range(box.GetY()//mm(2),(box.GetBottom()//mm(2))+1):obs[ly].setdefault((x,y),[]).append((shape,box))
for f in b.GetFootprints():
 for q in f.Pads():
  for ly in layers:
   if q.IsOnLayer(ly):index(ly,q.GetEffectiveShape(ly))
  if q.GetDrillSize().x:holes.append((loc(q.GetPosition()),p.ToMM(q.GetDrillSize().x)/2))
for t in b.GetTracks():
 for ly in layers:
  if t.IsOnLayer(ly) and t.GetNetname()!='GND':index(ly,t.GetEffectiveShape(ly))
 if isinstance(t,p.PCB_VIA):holes.append((loc(t.GetPosition()),p.ToMM(t.GetDrillValue())/2))
keepouts=[z for z in list(b.Zones())+[z for f in b.GetFootprints() for z in f.Zones()] if z.GetIsRuleArea() and z.GetDoNotAllowVias()]
def free(pos):
 if not(.7<pos[0]<47.3 and .7<pos[1]<40.25):return False
 if any(math.dist(pos,c)<.1+r+.25 for c,r in holes):return False
 shape=p.SHAPE_CIRCLE(xy(pos),mm(.225));box=shape.BBox();box.Inflate(mm(.15))
 if any(z.Outline().Collide(shape) for z in keepouts):return False
 for ly in layers:
  for x in range(box.GetX()//mm(2),box.GetRight()//mm(2)+1):
   for y in range(box.GetY()//mm(2),box.GetBottom()//mm(2)+1):
    if any(bb.Intersects(box) and other.Collide(shape,mm(.15)) for other,bb in obs[ly].get((x,y),[])):return False
 return True
signals=[t for t in b.GetTracks() if isinstance(t,p.PCB_VIA) and t.GetNetname() in ['USB_DOWN_DM','USB_DOWN_DP']];oldgrounds=[loc(t.GetPosition()) for t in b.GetTracks() if isinstance(t,p.PCB_VIA) and t.GetNetname()=='GND'];records=[]
for label,points in [('mcu',[loc(t.GetPosition()) for t in signals if p.ToMM(t.GetPosition().x)<5]),('isolator',[loc(t.GetPosition()) for t in signals if p.ToMM(t.GetPosition().x)>5])]:
 assert len(points)==2;cx=sum(q[0] for q in points)/2;cy=sum(q[1] for q in points)/2;candidates=[]
 for ix in range(round((cx-2)*20),round((cx+2)*20)+1):
  for iy in range(round((cy-2)*20),round((cy+2)*20)+1):
   pos=(ix/20,iy/20);candidates.append((max(math.dist(pos,q) for q in points),pos))
 pos=next(pos for _,pos in sorted(candidates) if free(pos));v=p.PCB_VIA(b);v.SetPosition(xy(pos));v.SetWidth(mm(.45));v.SetDrill(mm(.2));v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetViaType(p.VIATYPE_THROUGH);v.SetNet(net);b.Add(v);holes.append((pos,.1))
 records.append({'end':label,'signal_vias_mm':points,'new_return_via_mm':pos,'before_nearest_return_mm':[min(math.dist(q,g) for g in oldgrounds) for q in points],'after_local_return_mm':[math.dist(q,pos) for q in points]})
p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(path),b);report=R/'review/drc_usb_return_vias.json';subprocess.run(['X:/SoftWare/Kicad/bin/kicad-cli.exe','pcb','drc','--schematic-parity','--format','json','-o',str(report),str(path)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True);d=json.loads(report.read_text())
if d['violations'] or d['unconnected_items'] or d['schematic_parity']:path.write_bytes(original);raise RuntimeError('Return vias failed native checks; restored original PCB')
(R/'review/usb_return_vias.json').write_text(json.dumps({'vias':records,'diameter_mm':.45,'drill_mm':.2,'reference_planes':['In1.Cu GND','In3.Cu GND'],'scope':'Local reference-plane stitching at USB layer transitions. Does not verify impedance, USB eye margin or system isolation.'},indent=2));print(json.dumps(records))
