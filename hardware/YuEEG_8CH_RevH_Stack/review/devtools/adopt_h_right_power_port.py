"""Adopt only a routed, DRC-clean candidate and synchronize schematic/BOM/model."""
from pathlib import Path
import json,hashlib,csv,sys,shutil,subprocess
sys.path.insert(0,'hardware/YuEEG_8CH_RevG/review');from sexpr_io import loads,dumps,sub
H=Path('hardware/YuEEG_8CH_RevH_Stack');D=H/'digital';C=Path('logs/right_power_port_candidate');stem='YuEEG_H_DIGITAL';dst=D/(stem+'.kicad_pcb');src=C/dst.name
r=json.loads((C/'drc.json').read_text());assert not r['violations'] and not r['unconnected_items'];data=json.loads((C/'candidate.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert data['baseline_pcb_sha256']==sha(dst),'Main source changed since candidate creation'
backup=Path('logs/before_right_power_adoption');backup.mkdir(exist_ok=True)
for f in [dst,D/'circuit_19.kicad_sch',D/'BOM.csv',H/'review/component_envelopes.json']:
 shutil.copy2(f,backup/f.name)
if (H/'mechanical/current/power_ports_native.json').exists():shutil.copy2(H/'mechanical/current/power_ports_native.json',backup/'power_ports_native.json')
fp='JST_PH_S4B-PH-K_1x04_P2.00mm_Horizontal';value='S4B-PH-K-S / 5V+CELL SENSE / RIGHT';model='JST_S4B_PH_TH_envelope.wrl';lo=[-1.95,-1.35,0];hi=[7.95,6.25,4.8];pts=[(x/2.54,-y/2.54,z/2.54) for z in [lo[2],hi[2]] for y in [lo[1],hi[1]] for x in [lo[0],hi[0]]];faces=[[0,1,3,2],[4,6,7,5],[0,4,5,1],[2,3,7,6],[0,2,6,4],[1,5,7,3]]
M=H/'models'/model;M.write_text('#VRML V2.0 utf8\n# Original nominal JST S4B-PH-K-S envelope, ePH p1/p3; not supplier CAD.\nShape { appearance Appearance { material Material { diffuseColor .86 .84 .73 } } geometry IndexedFaceSet { solid FALSE coord Coordinate { point [ '+', '.join(' '.join(map(str,v)) for v in pts)+' ] } coordIndex [ '+', '.join(' '.join(map(str,f))+', -1' for f in faces)+' ] } }\n',encoding='utf8')
modelnode=['model',json.dumps('${KIPRJMOD}/../models/'+model),['offset',['xyz','0','0','0']],['scale',['xyz','1','1','1']],['rotate',['xyz','0','0','0']]]
tree=loads(src.read_text(encoding='utf8'));f=next(f for f in tree if isinstance(f,list) and f[0]=='footprint' and any(isinstance(v,list) and v[:2]==['property','"Reference"'] and json.loads(v[2])=='JH2' for v in f));f[:]=[v for v in f if not(isinstance(v,list) and v[0]=='model')];f.append(modelnode);assert list(map(float,sub(f,'at')[1:]))==[32.4,38.5,90.0]
dst.write_text(dumps(tree),encoding='utf8');libpath=H/'footprints/Connector_JST.pretty'/(fp+'.kicad_mod');lib=loads(libpath.read_text(encoding='utf8'));lib[:]=[v for v in lib if not(isinstance(v,list) and v[0]=='model')];lib.append(modelnode);libpath.write_text(dumps(lib),encoding='utf8')
schpath=D/'circuit_19.kicad_sch';sch=loads(schpath.read_text(encoding='utf8'));count=0
for s in sch:
 if not(isinstance(s,list) and s[0]=='symbol'):continue
 props={json.loads(v[1]):v for v in s if isinstance(v,list) and v[0]=='property'}
 if props.get('Reference',[None,None,None])[2]=='"JH2"':props['Value'][2]=json.dumps(value);props['Footprint'][2]=json.dumps('Connector_JST:'+fp);props['Datasheet'][2]=json.dumps('https://www.jst-mfg.com/product/pdf/eng/ePH.pdf');count+=1
assert count==1;schpath.write_text(dumps(sch),encoding='utf8')
with (D/'BOM.csv').open(encoding='utf-8-sig',newline='') as stream:reader=csv.DictReader(stream);fields=reader.fieldnames;rows=list(reader)
for row in rows:
 if row['Reference']=='JH2':row.update(Value=value,Footprint='Connector_JST:'+fp,Datasheet='https://www.jst-mfg.com/product/pdf/eng/ePH.pdf')
with (D/'BOM.csv').open('w',encoding='utf-8-sig',newline='') as stream:w=csv.DictWriter(stream,fields);w.writeheader();w.writerows(rows)
env=json.loads((H/'review/component_envelopes.json').read_text());env['models'].append(dict(model=model,boxes_footprint_mm=[dict(min=lo,max=hi)],source=['https://www.jst-mfg.com/product/pdf/eng/ePH.pdf pages 1/3'],scope='Nominal side-entry TH header body only; mated plug, tails, solder and wires are separate envelopes.',sha256=sha(M)))
for row in env['bindings']:
 if row['board']=='digital' and row['reference']=='JH2':row['model']=model
(H/'review/component_envelopes.json').write_text(json.dumps(env,indent=2),encoding='utf8')
cli='X:/SoftWare/Kicad/bin/kicad-cli.exe';subprocess.run([cli,'sch','export','netlist','--format','kicadxml','-o',str(D/'review/netlist.xml'),str(D/(stem+'.kicad_sch'))],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
record=dict(status='IMPLEMENTED_ENGINEERING_CHANGE_NOT_ASSEMBLY_RELEASE',before_pcb_sha256=data['baseline_pcb_sha256'],after_pcb_sha256=sha(dst),reference='JH2',mpn='S4B-PH-K-S',position_mm=[32.4,38.5],rotation_deg=90,mating_direction='+X',mated_reference_body_box_mm=[31.05,30.55,0,40.65,40.45,4.8],nominal_header_height_mm=4.8,old_header_height_mm=5.5,reason='Reserve a cable path toward the adjacent battery without entering the display FPC bend. Smaller TH PH header avoids rotating the wider SMT header across neighboring parts.',pin_map={'1':'SYS_5V','2':'BAT_PROTECTED_SENSE','3':'GND','4':'GND'},scope='Electrical reroute and model/source synchronization; mating housing dimensions are reference-only. Wire-axis height, solder-tail/plug clearance, below-board AFE, enclosure support and delivered parts require verification.')
(D/'review/right_power_port.json').write_text(json.dumps(record,indent=2),encoding='utf8');print('Adopted right-facing PH4; source/BOM/model synchronized, reports must now be regenerated')
