from pathlib import Path
import json,csv,sys
sys.path.insert(0,'hardware/YuEEG_8CH_RevG/review');from sexpr_io import loads,dumps,sub
R=Path('hardware/YuEEG_8CH_RevH_Stack/digital');value='22u 25V X5R / C3216X5R1E226M160AB H1.8max';ds='https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=C3216X5R1E226M160AB'
for path in [*R.glob('circuit_*.kicad_sch'),R/'YuEEG_H_DIGITAL.kicad_pcb']:
 d=loads(path.read_text());changed=False
 for s in d:
  if not isinstance(s,list) or s[0] not in ['symbol','footprint']:continue
  props={json.loads(z[1]):z for z in s if isinstance(z,list) and z[0]=='property'}
  if props.get('Reference',[None,None,''])[2]!='"C406"':continue
  props['Value'][2]=json.dumps(value)
  if 'Datasheet' in props:props['Datasheet'][2]=json.dumps(ds)
  changed=True
 if changed:path.write_text(dumps(d))
rows=list(csv.DictReader((R/'BOM.csv').open(encoding='utf-8-sig')))
for row in rows:
 if row['Reference']=='C406':row.update(Value=value,Datasheet=ds)
with (R/'BOM.csv').open('w',encoding='utf-8-sig',newline='') as out:
 w=csv.DictWriter(out,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
(R/'review/input_cap_selection.json').write_text(json.dumps({'reference':'C406','part':'C3216X5R1E226M160AB','manufacturer':'TDK','capacitance_uF':22,'tolerance_percent':20,'voltage_V':25,'dielectric':'X5R','temperature_C':[-55,85],'maximum_height_mm':1.8,'source':ds,'changed_from':'Generic 22u 25V X7R; replaced by a verifiable X5R part for the specified package/height. X5R is adequate only within the product operating temperature limit.','remaining':'Verify effective Cin at 8.4V including DC bias, tolerance, temperature and aging; TPS62160 recommends 10uF typical input. No measured transient data claimed.'},indent=2))
