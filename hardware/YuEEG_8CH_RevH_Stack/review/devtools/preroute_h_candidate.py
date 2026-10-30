from pathlib import Path
import pcbnew as p,wx,json,math
wx.DisableAsserts()
R=Path('logs/RevH_DigitalCandidate');path=R/'YuEEG_H_DIGITAL.kicad_pcb';b=p.LoadBoard(str(path));fs={f.GetReference():f for f in b.GetFootprints()};nets={n.GetNetname():n for n in b.GetNetInfo().NetsByNetcode().values()};new=[]
def xy(a):return p.VECTOR2I(p.FromMM(a[0]),p.FromMM(a[1]))
def pt(q):return p.ToMM(q.GetPosition().x),p.ToMM(q.GetPosition().y)
def pad(r,n):return next(q for q in fs[r].Pads() if q.GetNumber()==str(n))
def tracks(net,pts,layer=p.F_Cu,width=.15):
 for a,c in zip(pts,pts[1:]):
  if math.dist(a,c)<.00001:continue
  t=p.PCB_TRACK(b);t.SetStart(xy(a));t.SetEnd(xy(c));t.SetWidth(p.FromMM(width));t.SetLayer(layer);t.SetNet(nets[net]);new.append(t)
def via(net,a):
 v=p.PCB_VIA(b);v.SetPosition(xy(a));v.SetWidth(p.FromMM(.4));v.SetDrill(p.FromMM(.2));v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetViaType(p.VIATYPE_THROUGH);v.SetNet(nets[net]);new.append(v)
for r in ['R301','R302','R303','R304','R305','R306','C301']:
 q=pad(r,1);d=next(q0 for q0 in fs['U2'].Pads() if q0.GetNetname()==q.GetNetname());x,y=pt(d)
 v=(7.25,y) if x<10 else (x-.6,20.25) if y>20 else (22.65,y)
 via(q.GetNetname(),v);tracks(q.GetNetname(),[pt(d),v]);tracks(q.GetNetname(),[v,pt(q)],p.B_Cu)
tracks('+3V3',[pt(pad('C303',1)),pt(pad('C302',1)),pt(pad('U2',2))],width=.35)
for r,n in [('R703',14),('R704',13)]:
 a,c=pad(r,2),pad('U2',n);assert a.GetNetname()==c.GetNetname();tracks(a.GetNetname(),[pt(a),pt(c)])
dm=[(2.35,18.83),(1.15,18.83),(.8,19.18),(.8,34.95),(2.3,36.45),(10.1,36.45),(13.905,38.65)]
dp=[(2.35,20.1),(2.1,20.1),(1.5,20.1),(1.15,20.45),(1.15,34.6),(2.65,36.1),(10.45,36.1),(15.175,38.65)]
def length(a):return sum(math.dist(x,y) for x,y in zip(a,a[1:]))
h=(length(dm)-length(dp))/2;assert 0<h<1.5,h
dp[2:2]=[(2.1,20.1-h),(1.5,20.1-h)]
for r,n,points in [('R704',11,dm),('R703',10,dp)]:
 net=pad(r,1).GetNetname();via(net,points[0]);via(net,points[-1]);tracks(net,[pt(pad(r,1)),points[0]]);tracks(net,points,p.In2_Cu);tracks(net,[points[-1],pt(pad('U701',n))])
tracks('BUCK_SW',[pt(pad('U402',7)),(25.325,31.425),pt(pad('L401',1))],width=.5)
tracks('+3V3',[pt(pad('L401',2)),pt(pad('C407',1))],width=.5)
# The regulator VOS pin must sense the filtered output, not the switch node.
tracks('+3V3',[pt(pad('U402',6)),(24.675,30.9),(22.55,30.9),(22.55,35.6),pt(pad('C407',1))],width=.15)
# Check actual pad copper, not bounding-box placement, before preserving these routes.
issues=[]
for i,q in enumerate(new):
 for layer in [p.F_Cu,p.In1_Cu,p.In2_Cu,p.In3_Cu,p.In4_Cu,p.B_Cu]:
  if not q.IsOnLayer(layer):continue
  shape=q.GetEffectiveShape(layer)
  for f in b.GetFootprints():
   for a in f.Pads():
    if a.GetNetCode()!=q.GetNetCode() and a.IsOnLayer(layer) and a.GetEffectiveShape(layer).Collide(shape,p.FromMM(.1499)):issues.append([i,q.GetNetname(),f.GetReference(),a.GetNumber()])
  for j,t in enumerate(new[:i]):
   if t.GetNetCode()!=q.GetNetCode() and t.IsOnLayer(layer) and t.GetEffectiveShape(layer).Collide(shape,p.FromMM(.1499)):issues.append([i,q.GetNetname(),'proposed',j,t.GetNetname()])
assert not issues,issues
for q in new:b.Add(q)
p.SaveBoard(str(path),b)
(R/'preroutes.json').write_text(json.dumps({'objects':len(new),'downstream_usb_lengths_mm':{'DM':length(dm),'DP':length(dp)},'status':'Protected local routes; final impedance depends on fabricator stackup'},indent=2))
print('Pre-routes saved',len(new),'USB lengths',length(dm),length(dp))
