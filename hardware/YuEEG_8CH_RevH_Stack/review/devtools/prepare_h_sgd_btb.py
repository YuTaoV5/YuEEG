"""Prepare a separate SGDCONN candidate from the published SMT boards.
Never overwrites current boards. Uses Taobao item860586965302 attached drawings.
Project logical numbering is retained; supplier PIN1/PIN2 marks are not net names.
"""
from pathlib import Path
import sys, json, shutil, hashlib, csv
import pcbnew as p,wx
wx.DisableAsserts()
sys.path.insert(0,'hardware/YuEEG_8CH_RevG/review')
from sexpr_io import loads,dumps,sub
H=Path('hardware/YuEEG_8CH_RevH_Stack');C=Path(sys.argv[1]) if len(sys.argv)>1 else Path('logs/revh_sgd_btb_candidate')
for name,digest in [('afe','a21378ccdee99483476029f1a83178f06f04ec7765870b2a36bc914ee907312b'),('digital','9407948570a5ba2f7ba6700888929932599c12ad0884c823c179237d57320851')]:
 assert hashlib.sha256((H/name/('YuEEG_H_'+name.upper()+'.kicad_pcb')).read_bytes()).hexdigest()==digest,'Historical e5df79c baseline required; no current files changed'
assert not C.exists(),'Inspect the existing candidate instead of replacing it'
C.mkdir(parents=True)
for name in ['afe','digital','models','footprints']:
 shutil.copytree(H/name,C/name)
shutil.copy2(H/'YuEEG.kicad_sym',C/'YuEEG.kicad_sym')
source='https://itemcdn.tmall.com/attachment/icoss234754281bbb74bf255ec8c29'
Q=json.dumps;records={}
for board,male in [('afe',False),('digital',True)]:
 oldname='JME_BTB0840_20MR_Logical' if male else 'JME_BTB0845_20FR_Logical'
 name='SGD_BM08_020_H40_Logical' if male else 'SGD_BF08_020_H45_Logical'
 mpn='SGDBM-08-020P-H40' if male else 'SGDBF-08-020P-H45'
 fp=(H/'footprints/YuEEG.pretty'/(oldname+'.kicad_mod')).read_text()
 fp=fp.replace(oldname,name).replace('JMEconn 0.8mm','SGDCONN 0.8mm').replace('(size .35 1.8)','(size .30 2.00)').replace('JME_BTB_SURFACE_NO_CIRCUIT','SGD_PROJECT_SURFACE_NO_CIRCUIT').replace('(xy -4 -1.1) (xy 4 -1.1) (xy 4 1.1) (xy -4 1.1)','(xy -4 -.99) (xy 4 -.99) (xy 4 .99) (xy -4 .99)')
 fp=fp.replace('(start -4.95 -2.2) (end 4.95 2.2)','(start -4.95 -2.6) (end 4.95 2.6)')
 (C/'footprints/YuEEG.pretty'/(name+'.kicad_mod')).write_text(fp,encoding='utf8')
 # Own nominal illustration: supplier nominal width5.2; contact extension1.9.
 boxes=[([-4.95,-2.6,0],[4.95,2.6,4.0 if male else 4.5],'.08 .08 .08')]
 if male:
  for yy in [-.95,.95]:boxes.append(([-4.1,yy-.15,4.0],[4.1,yy+.15,5.9],'.65 .55 .25'))
 for xx in [-4.5,4.5]:boxes.append(([xx-.3,.95,-.6],[xx+.3,1.55,0],'.08 .08 .08'))
 vr=['#VRML V2.0 utf8','# Project nominal illustration; not supplier CAD or tolerance model.']
 for lo,hi,col in boxes:
  cen=[(lo[i]+hi[i])/2/2.54 for i in range(3)];size=[(hi[i]-lo[i])/2.54 for i in range(3)]
  vr.append('Transform { translation '+' '.join(map(str,cen))+' children [ Shape { appearance Appearance { material Material { diffuseColor '+col+' } } geometry Box { size '+' '.join(map(str,size))+' } } ] }')
 (C/'models'/(name+'.wrl')).write_text('\n'.join(vr)+'\n',encoding='utf8')
 path=C/board/('YuEEG_H_'+board.upper()+'.kicad_pcb');tree=loads(path.read_text(encoding='utf8'))
 f=next(z for z in tree if isinstance(z,list) and z[0]=='footprint' and any(v[:3]==['property','"Reference"','"JH1"'] for v in z if isinstance(v,list)))
 assert json.loads(f[1])=='YuEEG:'+oldname
 f[1]=Q('YuEEG:'+name)
 if sub(f,'descr'):sub(f,'descr')[1]=sub(f,'descr')[1].replace('JMEconn','SGDCONN')
 for v in f:
  if not isinstance(v,list):continue
  if v[:2]==['property','"Value"']:v[2]=Q(mpn+' / SMT BTB')
  if v[:2]==['property','"Datasheet"']:v[2]=Q(source)
  if v[0]=='pad' and json.loads(v[1]):sub(v,'size')[1:]=['.30','2.00']
  if v[0]=='model':v[1]=Q('${KIPRJMOD}/../models/'+name+'.wrl')
  if v[0]=='fp_rect' and sub(v,'layer')[1] in ['"F.Fab"','"B.Fab"']:
   # In a flipped native footprint the signs may be inverted. Expand only width.
   for key in ['start','end']:
    a=sub(v,key)
    if abs(abs(float(a[2]))-2.2)<1e-6:a[2]=str(2.6 if float(a[2])>0 else -2.6)
  if v[0]=='zone':
   sub(v,'name')[1]=Q('SGD_PROJECT_SURFACE_NO_CIRCUIT')
   for xy in sub(sub(v,'polygon'),'pts')[1:]:
    # Embedded native footprint zone vertices are board coordinates.
    if abs(abs(float(xy[1])-43.7)-1.1)<1e-6:xy[1]=str(43.7+(.99 if float(xy[1])>43.7 else -.99))
 path.write_text(dumps(tree),encoding='utf8')
 b=p.LoadBoard(str(path));p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(path),b)
 for sp in (C/board).glob('circuit_*.kicad_sch'):
  d=loads(sp.read_text(encoding='utf8'));changed=False
  for sym in d:
   if not isinstance(sym,list) or sym[0]!='symbol':continue
   props={json.loads(v[1]):v for v in sym if isinstance(v,list) and v[0]=='property'}
   if props.get('Reference',[None,None,None])[2]!='"JH1"':continue
   props['Value'][2]=Q(mpn+' / SMT BTB');props['Footprint'][2]=Q('YuEEG:'+name);props['Datasheet'][2]=Q(source);changed=True
  if changed:sp.write_text(dumps(d),encoding='utf8')
 rows=list(csv.DictReader((C/board/'BOM.csv').open(encoding='utf-8-sig')))
 for row in rows:
  if row['Reference']=='JH1':row.update(Value=mpn+' / SMT BTB',Footprint='YuEEG:'+name,Datasheet=source)
 with (C/board/'BOM.csv').open('w',encoding='utf-8-sig',newline='') as out:
  writer=csv.DictWriter(out,fieldnames=rows[0]);writer.writeheader();writer.writerows(rows)
 # Scratch symbol table must resolve its own copy for CLI parity.
 table=C/board/'sym-lib-table'
 table.write_text(table.read_text(encoding='utf8').replace('${KIPRJMOD}/../YuEEG.kicad_sym',(C/'YuEEG.kicad_sym').resolve().as_posix()),encoding='utf8')
 records[board]={'baseline_pcb_sha256':hashlib.sha256((H/board/path.name).read_bytes()).hexdigest(),'candidate_pcb_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'footprint':name,'mpn':mpn}
(C/'selection.json').write_text(json.dumps(records,indent=2),encoding='utf8')
print('Separate SGDCONN candidate prepared; source boards unchanged')
