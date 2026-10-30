"""Unrouted 43x23.6 USB/power placement experiment; never modifies baseline PCBs.

Battery probe circles are clearance reservations using an unverified sample datum.
They have no electrical pads or polarity assignment and are not a finished holder.
"""
from pathlib import Path
import pcbnew as p,wx,json,math,hashlib,subprocess,collections
wx.DisableAsserts();R=Path('hardware/YuEEG_8CH_RevH_Stack');out=R/'mechanical/current';out.mkdir(exist_ok=True);power=p.LoadBoard(str(R/'power/YuEEG_H_POWER.kicad_pcb'));digital=p.LoadBoard(str(R/'digital/YuEEG_H_DIGITAL.kicad_pcb'));b=p.BOARD();b.SetCopperLayerCount(2);b.GetDesignSettings().SetBoardThickness(p.FromMM(1));partlist=json.loads((out/'usb_partition_feasibility.json').read_text())['proposed_move_components'];sources={}
def xy(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
ns={}
for f in list(power.GetFootprints())+list(digital.GetFootprints()):
 if f.GetParent()==digital and f.GetReference() not in {r['reference'] for r in partlist}:continue
 q=f.Duplicate();b.Add(q);sources[q.GetReference()]='power' if f.GetParent()==power else 'digital'
 for pad in q.Pads():
  name=pad.GetNetname()
  if not name:continue
  if name not in ns:
   n=p.NETINFO_ITEM(b,name);b.Add(n);ns[name]=n
  pad.SetNet(ns[name])
fs={f.GetReference():f for f in b.GetFootprints()}
for a,c in [((0,0),(43,0)),((43,0),(43,23.6)),((43,23.6),(0,23.6)),((0,23.6),(0,0))]:
 g=p.PCB_SHAPE(b);g.SetShape(p.SHAPE_T_SEGMENT);g.SetStart(xy(*a));g.SetEnd(xy(*c));g.SetLayer(p.Edge_Cuts);g.SetWidth(p.FromMM(.05));b.Add(g)
poses={'JP2':(6.5,7,90,'F'),'JP1':(21.5,19.5,90,'F'),'LP1':(19.5,4,270,'F'),'UP2':(18.5,8.5,0,'F'),'UP1':(13,16,0,'F'),'QP1':(10,21.5,180,'F'),'SWP1':(3.0,18.15,90,'F'),'U701':(37,6.8,90,'F'),'J601':(37,19.4,0,'F'),'C703':(29,1.5,0,'F')}
targets={'FP1':(21,14),'RP1':(14.5,15.5),'RP2':(16.5,15.5),'RP3':(14.5,18),'RP4':(4.5,15),'RP5':(17,11.3),'RP6':(17,13.5),'CP1':(12,19.5),'CP2':(14.5,4),'CP3':(14.5,20.5),'CP4':(19,11.3),'CP5':(22,8),'CP6':(22,11),'CP7':(19,14),'R701':(40.5,13.35),'R702':(38,13.35),'C701':(33,13.35),'C702':(35.5,13.35),'C901':(38,12.8),'D602':(35,16),'D603':(39,16),'D604':(33,19),'D605':(36,19),'R901':(33,21),'R902':(36,22.5),'F901':(41,19),'D901':(40,21)}
back={'D602','D603','D604','D605','R901','R902','F901','D901','C901'}
host={r['pattern'] for r in json.loads((R/'digital/YuEEG_H_DIGITAL.kicad_pro').read_text())['net_settings']['netclass_patterns'] if r['netclass']=='USB_HOST'}
def box(f):
 gs=[g.GetBoundingBox() for g in f.GraphicalItems() if g.GetLayer() in (p.F_CrtYd,p.B_CrtYd)]
 if not gs:gs=[q.GetBoundingBox() for q in f.Pads()]
 return tuple(p.ToMM(n) for n in (min(g.GetX() for g in gs),min(g.GetY() for g in gs),max(g.GetRight() for g in gs),max(g.GetBottom() for g in gs)))
def overlap(a,c,gap=.05):return a[0]<c[2]+gap and a[2]+gap>c[0] and a[1]<c[3]+gap and a[3]+gap>c[1]
def pb(q):
 z=q.GetBoundingBox();return tuple(p.ToMM(n) for n in [z.GetX(),z.GetY(),z.GetRight(),z.GetBottom()])
def padfree(f,x,y,side,body):
 for ref in used:
  other=fs[ref]
  for q in other.Pads():
   # No backside part body above a connector's locating boss or solder tail.
   if side=='B' and q.GetDrillSize().x and overlap(body,pb(q),.25):return False
   for c in f.Pads():
    cc=pb(c);cc=(cc[0]+x,cc[1]+y,cc[2]+x,cc[3]+y)
    common=any(c.IsOnLayer(ly) and q.IsOnLayer(ly) for ly in [p.F_Cu,p.B_Cu])
    if common and c.GetNetname()!=q.GetNetname() and overlap(cc,pb(q),.15):return False
 return True
def setpose(f,x,y,a,side):
 if (f.GetLayer()==p.B_Cu)!=(side=='B'):f.Flip(f.GetPosition(),False)
 f.SetOrientationDegrees(a);f.SetPosition(xy(x,y));f.Reference().SetVisible(False);f.Value().SetVisible(False)
used={};failures=[]
# Circles reserve through-hole solder/probe/tool space on both faces, not contacts.
reservations=[(6.5,15.9,9.5,18.9),(16.5,15.9,19.5,18.9)]
for ref,(x,y,a,side) in poses.items():
 f=fs[ref];setpose(f,x,y,a,side);bb=box(f);used[ref]=(bb,side)
 if any(overlap(bb,q) for q in reservations):failures.append([ref,'probe reservation overlap'])
for ref,target in sorted(targets.items(),key=lambda item:({'D901':0,'F901':1,'D602':2,'D603':3}.get(item[0],4))):
 f=fs[ref];side='B' if ref in back else 'F';ishost=any(q.GetNetname() in host for q in f.Pads());region=(31.5,11.05,42.6,23.2) if ishost else (.4,.4,23.4,23.2);best=None
 for a in [0,90,180,270]:
  setpose(f,0,0,a,side);q=box(f)
  for ix in range(math.ceil((region[0]-q[0])*4),math.floor((region[2]-q[2])*4)+1):
   x=ix/4
   for iy in range(math.ceil((region[1]-q[1])*4),math.floor((region[3]-q[3])*4)+1):
    y=iy/4;cost=math.dist((x,y),target)
    if best and cost>=best[0]:continue
    bb=(x+q[0],y+q[1],x+q[2],y+q[3])
    if any(overlap(bb,z) for z in reservations):continue
    if any(s==side and overlap(bb,z) for z,s in used.values()):continue
    if not padfree(f,x,y,side,bb):continue
    best=(cost,x,y,a,bb)
 if not best:
  failures.append([ref,'no placement in assigned domain']);setpose(f,*target,0,side);used[ref]=(box(f),side);continue
 _,x,y,a,bb=best;setpose(f,x,y,a,side);poses[ref]=(x,y,a,side);used[ref]=(bb,side)
for i,(ref,(bb,side)) in enumerate(used.items()):
 if bb[0]<0 or bb[1]<0 or bb[2]>43 or bb[3]>23.6:failures.append([ref,'courtyard outside outline',bb])
 for other,(cc,s) in list(used.items())[i+1:]:
  if side==s and overlap(bb,cc,0):failures.append([ref,other,'same-face courtyard overlap'])
# Actual native pad-shape cross-domain minimum. Mechanical body bounds cannot prove it.
pads=[q for f in b.GetFootprints() for q in f.Pads() if q.GetNetname()];isolation=[]
for i,a in enumerate(pads):
 for c in pads[i+1:]:
  if (a.GetNetname() in host)==(c.GetNetname() in host):continue
  if a.GetEffectiveShape(p.F_Cu).Collide(c.GetEffectiveShape(p.F_Cu),p.FromMM(8)):
   isolation.append([a.GetParentFootprint().GetReference()+'.'+a.GetNumber(),c.GetParentFootprint().GetReference()+'.'+c.GetNumber()])
for x1,y1,x2,y2 in reservations:
 g=p.PCB_SHAPE(b);g.SetShape(p.SHAPE_T_RECT);g.SetStart(xy(x1,y1));g.SetEnd(xy(x2,y2));g.SetLayer(p.Dwgs_User);g.SetWidth(p.FromMM(.15));b.Add(g)
t=p.PCB_TEXT(b);t.SetText('PLACEMENT ONLY / UNROUTED / NOT FOR ORDER');t.SetTextSize(xy(1,1));t.SetPosition(xy(21.5,-3));t.SetLayer(p.Dwgs_User);b.Add(t)
candidate=out/'usb_power_fit_candidate.kicad_pcb';p.SaveBoard(str(candidate),b)
candidate.write_text(candidate.read_text().replace('${KIPRJMOD}/../models/','${KIPRJMOD}/../../models/'))
(out/'fp-lib-table').write_text((R/'digital/fp-lib-table').read_text().replace('${KIPRJMOD}/../footprints/','${KIPRJMOD}/../../footprints/'))
candidate.with_suffix('.kicad_pro').write_bytes((R/'digital/YuEEG_H_DIGITAL.kicad_pro').read_bytes())
candidate.with_suffix('.kicad_dru').write_bytes((R/'digital/YuEEG_H_DIGITAL.kicad_dru').read_bytes())
native_report=out/'usb_power_fit_drc.json'
subprocess.run(['X:/SoftWare/Kicad/bin/kicad-cli.exe','pcb','drc','--format','json','-o',str(native_report),str(candidate)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True)
drc=json.loads(native_report.read_text());types=dict(collections.Counter(v['type'] for v in drc['violations']))
report={'status':'UNROUTED_PLACEMENT_EXPERIMENT_NOT_A_DESIGN_RELEASE','outline_mm':[43,23.6],'components':len(fs),'back_smt':sorted(back),'poses':poses,'courtyards':{ref:{'bounds_mm':bb,'side':side} for ref,(bb,side) in used.items()},'courtyard_failures':failures,'pad_isolation_pairs_under_8mm':isolation,'probe_reservations_mm':reservations,'probe_datum_status':'10 mm pitch and 6.2 mm height from third-party sample only; origin/polarity/tip fit NOT verified; no electrical probe footprint added.','native_drc_violation_types':types,'native_unconnected_items':len(drc['unconnected_items']),'baseline_sha256':{name:hashlib.sha256((R/name/('YuEEG_H_'+name.upper()+'.kicad_pcb')).read_bytes()).hexdigest() for name in ['digital','power']},'candidate_sha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),'scope':'Only a native-footprint packing experiment. No schematic/parity check, new cable selection, routes, ground planes, enclosure or manufacturing output. Native placement DRC is reported with all remaining warnings and unrouted items. JP1 and JP2 remain old temporary interfaces. Results cannot prove screen-sized digital/AFE feasibility.'}
(out/'usb_power_fit_candidate.json').write_text(json.dumps(report,indent=2));print('parts',len(fs),'placement issues',failures,'pad cross-domain pairs under8mm',len(isolation));print(isolation[:12])




