"""Add reversible module legends; clip silk at front component courtyards/pads.

Full rounded boundaries are also retained on Dwgs.User for assembly review.
This script touches graphics only and checks native DRC/parity before accepting.
"""
from pathlib import Path
import math,json,subprocess,hashlib
import pcbnew as p,wx
wx.DisableAsserts()
ROOT=Path('hardware/YuEEG_8CH_RevH_Stack')
def v(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
plans={
 'afe':{'labels':[('INPUT',8,6),('ADS1299',29,3),('POWER',20,48.8)],'regions':[(1,7,17,28.5),(17.5,9,34,29),(1,29,34,49)]},
 'digital':{'labels':[('MCU / RF',35,5.8),('DISPLAY',36,9.8),('SD',3,22.5),('3V3',24.5,40.4),('POWER',34,42)],'regions':[(5.3,1.5,24.8,22.5),(25.5,6,40,29.5),(4.5,24,22,39),(21.7,24,27.5,40.1)]},
 'power':{'labels':[('1S POWER',6,2),('PROTECT',6,4.4)],'regions':[(9,1,21.5,11),(22,1,33,16)]}}
for name,plan in plans.items():
 path=ROOT/name/('YuEEG_H_'+name.upper()+'.kicad_pcb');old=path.read_bytes()
 evidence=ROOT/name/'review/module_legends.json'
 if evidence.exists():
  assert json.loads(evidence.read_text())['source_sha256']==hashlib.sha256(old).hexdigest(),'Board changed after legends; review rather than duplicate'
  print(name,'already applied');continue
 b=p.LoadBoard(str(path));obstacles=[];new=[]
 def block(box,margin=.25):
  box=p.BOX2I(box.GetPosition(),box.GetSize());box.Inflate(p.FromMM(margin));obstacles.append(box)
 for f in b.GetFootprints():
  if f.GetLayer()==p.F_Cu:
   # Native courtyard graphic bounds include the complete mechanical body.
   boxes=[g.GetBoundingBox() for g in f.GraphicalItems() if g.GetLayer()==p.F_CrtYd]
   if boxes:
    left=min(q.GetX() for q in boxes);top=min(q.GetY() for q in boxes);right=max(q.GetRight() for q in boxes);bottom=max(q.GetBottom() for q in boxes)
    block(p.BOX2I(p.VECTOR2I(left,top),p.VECTOR2I(right-left,bottom-top)),.22)
  for q in f.Pads():
   if q.IsOnLayer(p.F_Mask):block(q.GetBoundingBox(),.25)
 for g in b.GetDrawings():
  if g.GetLayer()==p.F_SilkS:block(g.GetBoundingBox(),.25)
 def overlaps(box):return any(box.Intersects(q) for q in obstacles)
 labels=[]
 for text,x,y in plan['labels']:
  t=p.PCB_TEXT(b);t.SetText(text);t.SetLayer(p.F_SilkS);size=.8;t.SetTextSize(v(size,size));t.SetTextThickness(p.FromMM(.12))
  candidates=sorted((math.hypot(ix,iy),x+ix/10,y+iy/10) for ix in range(-15,16) for iy in range(-12,13))
  for _,cx,cy in candidates:
   t.SetPosition(v(cx,cy));box=t.GetBoundingBox();box.Inflate(p.FromMM(.18))
   if box.GetX()<p.FromMM(.3) or box.GetY()<p.FromMM(.3):continue
   if box.GetRight()>p.FromMM(33.4 if name=='power' else 47.4) or box.GetBottom()>p.FromMM(17.4 if name=='power' else 59.4):continue
   if not overlaps(box):break
  else:
   t.SetPosition(v(x,y));bb=t.GetBoundingBox()
   print('failed label bounds',text,[p.ToMM(a) for a in [bb.GetX(),bb.GetY(),bb.GetRight(),bb.GetBottom()]],'obstacles',[[p.ToMM(a) for a in [q.GetX(),q.GetY(),q.GetRight(),q.GetBottom()]] for q in obstacles if bb.Intersects(q)])
   raise RuntimeError('No free silk location: '+name+' '+text)
  b.Add(t);new.append(t);block(t.GetBoundingBox(),.3);labels.append({'text':text,'center_mm':[cx,cy]})
 def line(a,c,layer):
  g=p.PCB_SHAPE(b);g.SetShape(p.SHAPE_T_SEGMENT);g.SetStart(v(*a));g.SetEnd(v(*c));g.SetLayer(layer);g.SetWidth(p.FromMM(.1));b.Add(g);new.append(g)
 count=0
 for x1,y1,x2,y2 in plan['regions']:
  r=.8;pts=[]
  for cx,cy,start in [(x2-r,y1+r,-90),(x2-r,y2-r,0),(x1+r,y2-r,90),(x1+r,y1+r,180)]:
   pts.extend([(cx+r*math.cos(math.radians(start+a)),cy+r*math.sin(math.radians(start+a))) for a in range(0,91,10)])
  pts.append(pts[0])
  for a,c in zip(pts,pts[1:]):
   line(a,c,p.Dwgs_User)
   # Short visible runs create a restrained dashed border; do not cross bodies.
   length=math.dist(a,c);steps=max(1,math.ceil(length/.2));run=[]
   for i in range(steps+1):
    q=(a[0]+(c[0]-a[0])*i/steps,a[1]+(c[1]-a[1])*i/steps)
    box=p.BOX2I(v(q[0]-.1,q[1]-.1),v(.2,.2))
    good=not overlaps(box) and (int(i*.2/1.7)%2==0)
    if good:run.append(q)
    if (not good or i==steps) and run:
     if math.dist(run[0],run[-1])>=.6:line(run[0],run[-1],p.F_SilkS);count+=1
     run=[]
 p.SaveBoard(str(path),b)
 report=ROOT/name/'review/drc_module_legends.json'
 subprocess.run(['X:/SoftWare/Kicad/bin/kicad-cli.exe','pcb','drc','--schematic-parity','--format','json','-o',str(report),str(path)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True)
 d=json.loads(report.read_text())
 if any(d[k] for k in ['violations','unconnected_items','schematic_parity']):
  path.write_bytes(old);raise RuntimeError('Native checks failed; restored '+name)
 (ROOT/name/'review/module_legends.json').write_text(json.dumps({'labels':labels,'regions_mm':plan['regions'],'silk_border_segments':count,'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'scope':'Functional grouping marks, clipped around front courtyards, pads and existing legends. Full outlines on Dwgs.User are assembly guides, not electrical isolation boundaries.'},indent=2))
 print(name,labels,'border segments',count)





