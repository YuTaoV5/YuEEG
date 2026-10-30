from pathlib import Path
import shutil,csv,sys,json
sys.path.insert(0,'hardware/YuEEG_8CH_RevG/review')
from sexpr_io import loads,dumps,sub
R=Path('hardware/YuEEG_8CH_RevH_Stack');D=R/'digital';C=Path('logs/RevH_DigitalCandidate')
report=json.loads((C/'drc_complete.json').read_text(encoding='utf8'));assert not report['violations'] and not report['unconnected_items']
shutil.copy2(D/'YuEEG_H_DIGITAL.kicad_pcb',D/'review/before_functional_candidate.kicad_pcb')
shutil.copy2(C/'YuEEG_H_DIGITAL.kicad_pcb',D/'YuEEG_H_DIGITAL.kicad_pcb')
for name in ['functional_placement.json','preroutes.json','endpoint_route_results.json','drc_complete.json']:
 shutil.copy2(C/name,D/'review'/name)
value='AFE-DIGITAL / bottom logical mapping; connector pending';fp='YuEEG:Interboard_2x10_Male_BottomLogical'
bom=list(csv.DictReader((D/'BOM.csv').open(encoding='utf-8-sig')))
for row in bom:
 if row['Reference']=='JH1':row.update(Value=value,Footprint=fp)
with (D/'BOM.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=bom[0]);w.writeheader();w.writerows(bom)
for path in D.glob('circuit_*.kicad_sch'):
 tree=loads(path.read_text(encoding='utf8'));changed=False
 for s in tree:
  if not isinstance(s,list) or s[0]!='symbol':continue
  props={json.loads(x[1]):x for x in s if isinstance(x,list) and x[0]=='property'}
  if props.get('Reference',[None,None,''])[2]=='"JH1"':props['Footprint'][2]=json.dumps(fp);props['Value'][2]=json.dumps(value);changed=True
 if changed:path.write_text(dumps(tree),encoding='utf8')
# Keep the project footprint library in agreement with the USB shell drawing.
path=R/'footprints/Connector_USB.pretty/USB_C_Receptacle_HRO_TYPE-C-31-M-12.kicad_mod';tree=loads(path.read_text())
for g in tree:
 if isinstance(g,list) and g[0].startswith('fp_'):
  layer=sub(g,'layer')
  if layer and layer[1]=='"F.SilkS"':layer[1]='"F.Fab"'
path.write_text(dumps(tree))
f=D/'review/functional_placement.json';v=json.loads(f.read_text());v['placements']['SW1001'][1]=38.;v['front_courtyards']['SW1001']=[x-.4 if i%2 else x for i,x in enumerate(v['front_courtyards']['SW1001'])];f.write_text(json.dumps(v,indent=2))
print('Adopted candidate with zero routing DRC; source connector footprint aligned')
