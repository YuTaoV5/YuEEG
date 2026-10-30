from pathlib import Path
import pcbnew as p,wx,sys,json,csv,copy
wx.DisableAsserts()
sys.path.insert(0,'hardware/YuEEG_8CH_RevG/review');from sexpr_io import loads,dumps,sub
R=Path('hardware/YuEEG_8CH_RevH_Stack');Q=json.dumps
def prop(n,key):return next(z for z in n if isinstance(z,list) and z[:2]==['property',Q(key)])
for board,name,value,ds in [('afe','Samtec_SQT_110_01_Logical','SQT-110-01-L-D / SOCKET / logical pins','https://www.samtec.com/products/sqt-110-01-l-d'),('digital','Samtec_TMM_110_03_BottomLogical','TMM-110-03-L-D / 4mm POST / bottom logical','https://www.samtec.com/products/tmm-110-03-l-d')]:
 base=R/board;path=base/('YuEEG_H_'+board.upper()+'.kicad_pcb');oldboard=p.LoadBoard(str(path));old=next(f for f in oldboard.GetFootprints() if f.GetReference()=='JH1');mapping={q.GetNumber():q for q in old.Pads()}
 tmp=p.BOARD();fp=p.FootprintLoad(str(R/'footprints/YuEEG.pretty'),name);tmp.Add(fp);fp.SetReference('JH1');fp.SetValue(value);fp.SetPosition(old.GetPosition())
 if board=='digital':fp.Flip(fp.GetPosition(),False)
 fp.SetOrientationDegrees(old.GetOrientationDegrees());fp.Reference().SetLayer(p.B_Fab if board=='digital' else p.F_Fab);fp.Value().SetLayer(p.B_Fab if board=='digital' else p.F_Fab)
 for q in fp.Pads():
  a=mapping[q.GetNumber()];assert (q.GetPosition()-a.GetPosition()).EuclideanNorm()<p.FromMM(.001),(board,q.GetNumber());n=p.NETINFO_ITEM(tmp,a.GetNetname());tmp.Add(n);q.SetNet(n)
 temp=Path('logs')/('connector_exchange_'+board+'.kicad_pcb');p.SaveBoard(str(temp),tmp);new=next(z for z in loads(temp.read_text()) if isinstance(z,list) and z[0]=='footprint');new[1]=Q('YuEEG:'+name)
 tree=loads(path.read_text());oldraw=next(z for z in tree if isinstance(z,list) and z[0]=='footprint' and prop(z,'Reference')[2]=='"JH1"');nets={json.loads(sub(q,'net')[2]):sub(q,'net')[1] for q in oldraw if isinstance(q,list) and q[0]=='pad'}
 for q in new:
  if isinstance(q,list) and q[0]=='pad':sub(q,'net')[1]=nets[json.loads(sub(q,'net')[2])]
 if sub(oldraw,'path'):new.append(copy.deepcopy(sub(oldraw,'path')))
 tree[tree.index(oldraw)]=new;path.write_text(dumps(tree))
 for sp in base.glob('circuit_*.kicad_sch'):
  d=loads(sp.read_text());changed=False
  for s in d:
   if isinstance(s,list) and s[0]=='symbol' and prop(s,'Reference')[2]=='"JH1"':
    prop(s,'Value')[2]=Q(value);prop(s,'Footprint')[2]=Q('YuEEG:'+name);prop(s,'Datasheet')[2]=Q(ds);changed=True
  if changed:sp.write_text(dumps(d))
 rows=list(csv.DictReader((base/'BOM.csv').open(encoding='utf-8-sig')))
 for row in rows:
  if row['Reference']=='JH1':row.update(Value=value,Footprint='YuEEG:'+name,Datasheet=ds)
 with (base/'BOM.csv').open('w',encoding='utf-8-sig',newline='') as out:
  w=csv.DictWriter(out,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
 print(board,'mating connector installed; all 20 XY/net positions preserved')
