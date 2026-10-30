from pathlib import Path
import sys,json,math,shutil,pcbnew as p,wx
wx.DisableAsserts();sys.path.insert(0,'hardware/YuEEG_8CH_RevG/review');from sexpr_io import loads,dumps,sub
R=Path('hardware/YuEEG_8CH_RevH_Stack');a=R/'archive/interfaces_before_npbx1'
if a.exists():raise RuntimeError('One-shot migration already started; inspect current files before repeating')
for board in ['afe','digital']:
 dest=a/board;dest.mkdir(parents=True)
 for f in (R/board).glob('*.kicad_*'):shutil.copy2(f,dest/f.name)
 for n in ['BOM.csv','review/expected_connections.json']:shutil.copy2(R/board/n,dest/Path(n).name)
 for f in list((R/board).glob('*.kicad_sch'))+list((R/board).glob('*.kicad_pcb'))+[R/board/'review/expected_connections.json']:
  f.write_text(f.read_text(encoding='utf8').replace('"VBAT_SW"','"SYS_5V"'),encoding='utf8')
 exp=R/board/'review/expected_connections.json';d=json.loads(exp.read_text())
 if board=='digital':
  d['JH2.2']=d['R309.1']='BAT_PROTECTED_SENSE'
 exp.write_text(json.dumps(d,indent=2))
# Change labels attached to exactly the selected symbol pin, preserving UUIDs.
for ref,pin in [('R309','1'),('JH2','2')]:
 found=False
 for path in (R/'digital').glob('*.kicad_sch'):
  tree=loads(path.read_text());syms=[s for s in tree if isinstance(s,list) and s[0]=='symbol' and sub(s,'lib_id')]
  for sym in syms:
   props={json.loads(v[1]):v for v in sym if isinstance(v,list) and v[0]=='property'}
   if json.loads(props['Reference'][2])!=ref:continue
   lib=next(s for s in sub(tree,'lib_symbols')[1:] if s[1]==sub(sym,'lib_id')[1]);pins=[]
   def visit(n):
    if not isinstance(n,list):return
    if n and n[0]=='pin' and sub(n,'number'):pins.append(n)
    for c in n:visit(c)
   visit(lib);sp=next(s for s in pins if json.loads(sub(s,'number')[1])==pin)
   x,y,rot=map(float,sub(sym,'at')[1:]);px,py,ang=map(float,sub(sp,'at')[1:]);r=math.radians(rot)
   start=(round(x+px*math.cos(r)-py*math.sin(r),4),round(y-px*math.sin(r)-py*math.cos(r),4))
   wires=[s for s in tree if isinstance(s,list) and s[0]=='wire'];end=None
   for w in wires:
    pts=[tuple(round(float(v),4) for v in q[1:]) for q in sub(w,'pts')[1:]]
    if start in pts:end=next(v for v in pts if v!=start);break
   assert end,(ref,start)
   labels=[s for s in tree if isinstance(s,list) and s[0]=='global_label' and tuple(round(float(v),4) for v in sub(s,'at')[1:3])==end]
   assert len(labels)==1 and labels[0][1]=='"SYS_5V"',(ref,labels)
   labels[0][1]='"BAT_PROTECTED_SENSE"';path.write_text(dumps(tree));found=True
 assert found,ref
path=R/'digital/YuEEG_H_DIGITAL.kicad_pcb';tree=loads(path.read_text())
remove={'8050d3b7-40c9-423e-b142-8c7f5110e205','9d2d49fb-cc02-4629-adae-59882217a8cf','caa2def7-f9d8-4ac3-9236-8d4d49b43d89'}
actual={json.loads(sub(t,'uuid')[1]) for t in tree if isinstance(t,list) and t[0]=='segment' and sub(t,'uuid')}
assert remove<=actual
tree[:]=[t for t in tree if not(isinstance(t,list) and t[0]=='segment' and json.loads(sub(t,'uuid')[1]) in remove)];path.write_text(dumps(tree))
b=p.LoadBoard(str(path));net=p.NETINFO_ITEM(b,'BAT_PROTECTED_SENSE');b.Add(net)
for f in b.GetFootprints():
 for q in f.Pads():
  if (f.GetReference(),q.GetNumber()) in [('R309','1'),('JH2','2')]:q.SetNet(net)
p.SaveBoard(str(path),b)
c=R/'review/interboard_contract.json';d=json.loads(c.read_text().replace('"VBAT_SW"','"SYS_5V"'));d['POWER_DIGITAL']['2']='BAT_PROTECTED_SENSE';d['battery']='Sony NP-BX1 / 1S / external charger';c.write_text(json.dumps(d,indent=2))
print('AFE and digital system bus renamed SYS_5V; PH4 pin2 now protected cell voltage; 3 old branch segments removed')
