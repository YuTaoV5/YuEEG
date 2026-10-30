from pathlib import Path
import pcbnew as p,json,sys,csv
sys.path.insert(0,'hardware/YuEEG_8CH_RevG/review')
from sexpr_io import loads,dumps,sub
R=Path('hardware/YuEEG_8CH_RevH_Stack');base=R/'afe';path=base/'YuEEG_H_AFE.kicad_pcb';d=loads(path.read_text());Q=json.dumps
def prop(n,key):return next(x for x in n if isinstance(x,list) and x[:2]==['property',Q(key)])
old=next(x for x in d if isinstance(x,list) and x[0]=='footprint' and prop(x,'Reference')[2]=='"J1301"')
maps={json.loads(sub(z,'net')[2]):sub(z,'net')[1] for z in old if isinstance(z,list) and z[0]=='pad'}
pinmap={json.loads(z[1]):json.loads(sub(z,'net')[2]) for z in old if isinstance(z,list) and z[0]=='pad'}
temp=p.BOARD();f=p.FootprintLoad(str(R/'footprints/YuEEG.pretty'),'Electrode_1x10_Horizontal_ReverseLogical');f.SetReference('J1301');value='1x10 2.54mm RIGHT ANGLE / ELECTRODES';f.SetValue(value);f.SetPosition(p.VECTOR2I(p.FromMM(2),p.FromMM(26.86)));f.SetOrientationDegrees(180);f.Reference().SetLayer(p.F_Fab);f.Value().SetLayer(p.F_Fab);temp.Add(f)
for pad in f.Pads():
 n=pinmap[pad.GetNumber()];net=p.NETINFO_ITEM(temp,n);temp.Add(net);pad.SetNet(net)
 want=(2,4+(int(pad.GetNumber())-1)*2.54);assert abs(p.ToMM(pad.GetPosition().x)-want[0])<.0001 and abs(p.ToMM(pad.GetPosition().y)-want[1])<.0001
tmp=base/'review/side_header_exchange.kicad_pcb';p.SaveBoard(str(tmp),temp);nd=loads(tmp.read_text());new=next(x for x in nd if isinstance(x,list) and x[0]=='footprint');new[1]='"YuEEG:Electrode_1x10_Horizontal_ReverseLogical"'
for z in new:
 if isinstance(z,list) and z[0]=='pad':sub(z,'net')[1]=maps[json.loads(sub(z,'net')[2])]
if sub(old,'path'):new.append(sub(old,'path'))
d[d.index(old)]=new;path.write_text(dumps(d))
for sf in base.glob('circuit_*.kicad_sch'):
 tree=loads(sf.read_text());changed=False
 for s in tree:
  if isinstance(s,list) and s[0]=='symbol' and prop(s,'Reference')[2]=='"J1301"':
   prop(s,'Footprint')[2]=new[1];prop(s,'Value')[2]=Q(value);changed=True
 if changed:sf.write_text(dumps(tree))
rows=list(csv.DictReader((base/'BOM.csv').open(encoding='utf-8-sig')))
for row in rows:
 if row['Reference']=='J1301':row['Value']=value;row['Footprint']=json.loads(new[1])
with (base/'BOM.csv').open('w',encoding='utf-8-sig',newline='') as out:
 w=csv.DictWriter(out,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
(base/'review/electrode_side_entry.json').write_text(json.dumps({'reference':'J1301','orientation_deg':180,'position_mm':[2,26.86],'electrical_pin_xy_preserved':True,'pins':pinmap,'note':'Generic single-row 2.54mm right-angle male header; logical pin numbering reverses the standard library row to preserve the original wiring. Connector body/pins exit the left side; verify chosen vendor dimensions and enclosure lead clearance.'},indent=2))
print('Side-entry header installed; all 10 electrode pad positions preserved')
