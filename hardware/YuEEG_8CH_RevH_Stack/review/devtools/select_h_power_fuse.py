from pathlib import Path
import csv,json,sys
sys.path.insert(0,'hardware/YuEEG_8CH_RevG/review');from sexpr_io import loads,dumps,sub
R=Path('hardware/YuEEG_8CH_RevH_Stack/power');value='2A / Littelfuse 0466002.NRHF / 63V fast';url='https://www.littelfuse.com/assetdocs/fuse-466-datasheet?assetguid=dbe9bcd7-6072-4adf-bf5b-d33e52a6b90f'
for path in list(R.glob('*.kicad_sch'))+list(R.glob('*.kicad_pcb')):
 d=loads(path.read_text());changed=False
 for n in d:
  if not(isinstance(n,list) and n[0] in ['symbol','footprint']):continue
  props={json.loads(q[1]):q for q in n if isinstance(q,list) and q[0]=='property'}
  if props.get('Reference',[0,0,''])[2]!='"FP1"':continue
  props['Value'][2]=json.dumps(value)
  if 'Datasheet' in props:props['Datasheet'][2]=json.dumps(url)
  changed=True
 if changed:path.write_text(dumps(d))
path=R/'BOM.csv';rows=list(csv.DictReader(path.open(encoding='utf-8-sig')))
for row in rows:
 if row['Reference']=='FP1':row['Value']=value;row['Datasheet']=url
with path.open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
path=Path('logs/build_h_1s_power.py');s=path.read_text();assert '1.5A / final time-current coordination pending' in s or value in s;s=s.replace('1.5A / final time-current coordination pending',value);path.write_text(s)
(R/'review/fuse_selection.json').write_text(json.dumps({'part':'0466002.NRHF','current_A':2,'rated_voltage_V':63,'cold_resistance_nominal_ohm':.030,'melting_I2t_nominal_A2s':.2326,'interrupting_rating_A':50,'source':url,'source_revision':'2023-06-21','purpose':'Backup for pre-eFuse faults; not the normal load current limiter','normal_limit':'TPS259530 nominal 1.50A; tolerances and fuse ambient derating must be checked','manufacturer_continuous_derating':.75,'ambient_derating_required':True,'footprint':'Existing KiCad generic 1206 IPC land, not a claimed exact copy of manufacturer recommended land','validation_pending':['Battery prospective short circuit current and fuse breaking coordination','Actual enclosure temperature, continuous/peak load and inrush I2t','Assembly land/paste validation with selected fuse']},indent=2))
print('Selected 1206 2A fast fuse; separate from 1.5A eFuse current limit')
