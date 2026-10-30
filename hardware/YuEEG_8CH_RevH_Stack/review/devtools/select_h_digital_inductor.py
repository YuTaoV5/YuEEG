from pathlib import Path
import sys,json,csv,shutil,copy,pcbnew as p,wx
wx.DisableAsserts();sys.path.insert(0,'hardware/YuEEG_8CH_RevG/review');from sexpr_io import loads,dumps,sub
R=Path('hardware/YuEEG_8CH_RevH_Stack');D=R/'digital';arc=R/'archive/digital_before_l401_selection'
assert not arc.exists(),'One-shot edit already attempted; inspect current board before repeating'
arc.mkdir(parents=True)
for path in list(D.glob('*.kicad_sch'))+[D/'YuEEG_H_DIGITAL.kicad_pcb',D/'BOM.csv']:shutil.copy2(path,arc/path.name)
value='2.2uH / TDK SPM4015T-2R2M-LR';fp='YuEEG:TDK_SPM4015_LR';url='https://product.tdk.com/en/search/inductor/inductor/smd/info?part_no=SPM4015T-2R2M-LR'
for path in D.glob('*.kicad_sch'):
 d=loads(path.read_text());changed=False
 for n in d:
  if not(isinstance(n,list) and n[0]=='symbol' and sub(n,'lib_id')):continue
  props={json.loads(q[1]):q for q in n if isinstance(q,list) and q[0]=='property'}
  if props.get('Reference',[0,0,''])[2]!='"L401"':continue
  props['Value'][2]=json.dumps(value);props['Footprint'][2]=json.dumps(fp);props['Datasheet'][2]=json.dumps(url);changed=True
 if changed:path.write_text(dumps(d))
path=D/'BOM.csv';rows=list(csv.DictReader(path.open(encoding='utf-8-sig')))
for row in rows:
 if row['Reference']=='L401':row.update(Value=value,Footprint=fp,Datasheet=url)
with path.open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
path=D/'YuEEG_H_DIGITAL.kicad_pcb';raw=loads(path.read_text());b=p.LoadBoard(str(path));old=next(f for f in b.GetFootprints() if f.GetReference()=='L401');nets={q.GetNumber():q.GetNetname() for q in old.Pads()}
temp=p.BOARD();new=p.FootprintLoad(str(R/'footprints/YuEEG.pretty'),'TDK_SPM4015_LR');temp.Add(new);new.SetReference('L401');new.SetValue(value);new.SetOrientationDegrees(0);new.SetPosition(p.VECTOR2I(p.FromMM(24.5),p.FromMM(33.4)));new.Reference().SetVisible(False);new.Value().SetVisible(False)
for q in new.Pads():
 n=p.NETINFO_ITEM(temp,nets[q.GetNumber()]);temp.Add(n);q.SetNet(n)
exchange=Path('logs/digital_l401_exchange.kicad_pcb');p.SaveBoard(str(exchange),temp);nf=next(f for f in loads(exchange.read_text()) if isinstance(f,list) and f[0]=='footprint');nf[1]=json.dumps(fp)
of=next(f for f in raw if isinstance(f,list) and f[0]=='footprint' and next(q[2] for q in f if isinstance(q,list) and q[0]=='property' and q[1]=='"Reference"')=='"L401"')
native_nets={json.loads(q[2]):q[1] for q in raw if isinstance(q,list) and q[0]=='net'}
for q in nf:
 if isinstance(q,list) and q[0]=='pad':sub(q,'net')[1]=native_nets[json.loads(sub(q,'net')[2])]
nf.append(copy.deepcopy(sub(of,'path')));raw[raw.index(of)]=nf
for f in raw:
 if not(isinstance(f,list) and f[0]=='footprint'):continue
 props={json.loads(q[1]):q for q in f if isinstance(q,list) and q[0]=='property'}
 if props['Reference'][2]=='"C407"':sub(f,'at')[2]='38.3'
path.write_text(dumps(raw))
gen=Path('logs/build_stack_circuits.py');s=gen.read_text();needle="  if ref=='C406':";assert needle in s
s=s.replace(needle,"  if board=='digital' and ref=='L401':\n   row['Value']='2.2uH / TDK SPM4015T-2R2M-LR';row['Footprint']='YuEEG:TDK_SPM4015_LR'\n"+needle);gen.write_text(s)
(D/'review/l401_selection.json').write_text(json.dumps({'part':'SPM4015T-2R2M-LR','source':url,'inductance_uH':2.2,'tolerance_percent':20,'rated_current_inductance_drop_typ_A':5.7,'inductance_drop_percent':30,'rated_current_temp_rise_typ_A':3.5,'temp_rise_C':40,'DCR_max_ohm':.0627,'body_nominal_mm':[4.4,4.1],'height_max_mm':1.5,'pin_nets':nets,'new_position_mm':[24.5,33.4,0],'C407_position_mm':[24.75,38.3,-90],'note':'Replaces generic NR-40xx. Manufacturer current figures are typical; converter ripple, DC bias and enclosure temperature require validation. Routing is being adapted.'},indent=2))
print('Concrete L401 selected; footprint replaced and C407 shifted 0.2mm for courtyard clearance')
