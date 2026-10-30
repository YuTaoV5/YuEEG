"""Fresh 6-layer digital candidate: local decoupling, source termination, reserved USB pair corridor."""
from pathlib import Path
import json,math,shutil,sys
ns={};exec(Path('logs/layout_h_digital.py').read_text().split("used={'JH1'")[0],ns)
p,R,xy,box,overlap,b,fs,host=[ns[k] for k in ['p','R','xy','box','overlap','b','fs','host']]
O=Path('logs/RevH_DigitalCandidate');O.mkdir(exist_ok=True)
used={'JH1_TOP_PINS':(41,11,45,31)};poses={'JH1':[42,30,0,'B']};back={};back_used={}
fs['U2'].SetOrientationDegrees(0);fs['U2'].SetPosition(xy(15,12))
def bbox(f,layer):
 rr=[g.GetBoundingBox() for g in f.GraphicalItems() if g.GetLayer()==layer]
 return (min(p.ToMM(r.GetX()) for r in rr),min(p.ToMM(r.GetY()) for r in rr),max(p.ToMM(r.GetRight()) for r in rr),max(p.ToMM(r.GetBottom()) for r in rr))
def b_overlap(a,c):return a[0]<c[2] and a[2]>c[0] and a[1]<c[3] and a[3]>c[1]
for ref in ['R301','R302','R303','R304','R305','R306']:
 q=next(q for q in fs[ref].Pads() if q.GetNumber()=='1');driver=next(q0 for q0 in fs['U2'].Pads() if q0.GetNetname()==q.GetNetname());x,y=p.ToMM(driver.GetPosition().x),p.ToMM(driver.GetPosition().y)
 if x<10:back[ref]=(8.3,y,0)
 elif y>20:back[ref]=(x,19.5,90)
 else:back[ref]=(21.5,y,180)
back.update({'C301':(9.5,6.13,0),'R307':(12,6.9,0)})
for ref,(x,y,a) in back.items():
 f=fs[ref];f.SetPosition(xy(x,y));f.Flip(f.GetPosition(),False);f.SetOrientationDegrees(a);bb=bbox(f,p.B_CrtYd)
 for other,ob in back_used.items():assert not b_overlap(bb,ob),('Back courtyard overlap',ref,other,bb,ob)
 back_used[ref]=bb;poses[ref]=[x,y,a,'B']
hard={'U2':(15,12,0),'J1101':(7.5,30,270),'U701':(12,44.8,90),'J601':(24,56,0),'J2002':(30.19,22.38,0),'JH2':(34,35.3,0),'U1004':(29,11,0),'U402':(25,27.6,270),'L401':(24.75,33.4,270),'C406':(20.5,29.2,180),'C407':(24.75,38.1,270),'SW301':(2.2,7.5,90),'SW302':(2.2,13.5,90),'SW1001':(2.2,38,90),'C302':(3.3,3.75,180),'C303':(3.25,1.5,180),'C304':(17,25,0),'R703':(3.6,20.1,0),'R704':(3.6,18.83,0),'C701':(7.5,51.55,0),'C702':(10.1,51.55,0),'R701':(17,51.8,180),'R702':(14.8,51.8,180)}
for ref,(x,y,a) in hard.items():
 f=fs[ref];f.SetOrientationDegrees(a);f.SetPosition(xy(x,y));bb=box(f)
 for other,ob in used.items():assert not b_overlap(bb,ob),('Front courtyard overlap',ref,other,bb,ob)
 used[ref]=bb;poses[ref]=[x,y,a,'F']
used['USB_PAIR_LEFT']=(.5,18.4,1.7,35.7);used['USB_PAIR_BOTTOM']=(1.7,35.9,11.0,36.7)
targets={'C406':(21,29.7),'C407':(28.2,37.5),'R403':(24.5,23.8),'R404':(22.5,23.8),
 'C2001':(27,20),'C2002':(29,20),'C2003':(33,20),'C2004':(35,20),'C2005':(36,23),
 'C703':(10,38),'C704':(14,38),'C1006':(34,18),'C1007':(37,18),'C1008':(24,14),'C1009':(34,14),'U1003':(35,26),'U1001':(35,29),
 'R901':(33,54),'R902':(33,56),'D602':(28,51),'D603':(30,51),'D604':(35,53),'D605':(35,57),'F901':(39,54),'D901':(44,55),'C901':(40,58),
 'C1101':(17,28),'C1102':(17,30),'C1103':(17,32),'FB1101':(17,34),'D1101':(18,36),'D1102':(18,39)}
for i in range(6):targets['R'+str(1111+i)]=(4.2,24.8+i*1.65)
def ishost(f):return f.GetReference()!='U701' and any(q.GetNetname() in host for q in f.Pads())
order=[r for r in fs if r not in hard and r not in back and r!='JH1'];order.sort(key=lambda r:(0 if ishost(fs[r]) else 1,0 if r in targets else 1,-((box(fs[r])[2]-box(fs[r])[0])*(box(fs[r])[3]-box(fs[r])[1]))))
for ref in order:
 f=fs[ref];tx,ty=targets.get(ref,(30,30));reg=(.7,49.05,47.3,59.3) if ishost(f) else (.7,.7,47.3,40.55);best=None
 for ang in [0,90]:
  f.SetOrientationDegrees(ang);f.SetPosition(xy(0,0));a=box(f)
  for ix in range(math.ceil((reg[0]-a[0])*4),math.floor((reg[2]-a[2])*4)+1):
   x=ix/4
   for iy in range(math.ceil((reg[1]-a[1])*4),math.floor((reg[3]-a[3])*4)+1):
    y=iy/4;cost=math.hypot(x-tx,y-ty);bb=(x+a[0],y+a[1],x+a[2],y+a[3])
    if best and cost>=best[0]:continue
    if any(overlap(bb,z) for z in used.values()):continue
    best=cost,x,y,ang,bb
 if not best:raise RuntimeError(('No front placement',ref))
 _,x,y,ang,bb=best;f.SetOrientationDegrees(ang);f.SetPosition(xy(x,y));used[ref]=bb;poses[ref]=[x,y,ang,'F']
p.SaveBoard(str(O/'YuEEG_H_DIGITAL.kicad_pcb'),b)
for name in ['YuEEG_H_DIGITAL.kicad_pro','YuEEG_H_DIGITAL.kicad_dru']:shutil.copy2(R/'digital'/name,O/name)
for name in ['fp-lib-table','sym-lib-table']:(O/name).write_text((R/'digital'/name).read_text().replace('${KIPRJMOD}/../',R.resolve().as_posix()+'/'))
(O/'functional_placement.json').write_text(json.dumps({'board_mm':[48,60],'copper_layers':6,'back_smd':list(back),'placements':poses,'front_courtyards':used,'back_courtyards':back_used},indent=2))
print('Fresh candidate saved:',len(fs),'components;',len(back),'back-side small passives',flush=True)

