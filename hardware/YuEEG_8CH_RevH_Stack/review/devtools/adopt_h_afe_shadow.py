"""Adopt the separately routed AFE candidate, with a sourced C405 height bound."""
from pathlib import Path
import sys,json,csv,hashlib,shutil,subprocess
sys.path.insert(0,'hardware/YuEEG_8CH_RevG/review')
from sexpr_io import loads,dumps,sub
H=Path('hardware/YuEEG_8CH_RevH_Stack');D=H/'afe';C=Path('logs/afe_shadow_candidate');dst=D/'YuEEG_H_AFE.kicad_pcb';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((C/'drc.json').read_text());assert not any(r[k] for k in ['violations','unconnected_items','schematic_parity'])
data=json.loads((C/'candidate.json').read_text());assert sha(dst)==data['baseline_pcb_sha256']
backup=Path('logs/before_afe_shadow_adoption');backup.mkdir(exist_ok=True)
for f in [dst,D/'BOM.csv',D/'circuit_20.kicad_sch']:shutil.copy2(f,backup/f.name)
name='TY_MSASE31LBB7226MTNA01_1206';model=name+'_max_envelope.wrl';value='22u 16V X7R MSASE31LBB7226MTNA01';source='https://ds.yuden.co.jp/TYCOMPAS/ap/detail?pn=MSASE31LBB7226MTNA01&u=M'
lo=[-1.75,-.95,0];hi=[1.75,.95,1.9];pts=[(x/2.54,-y/2.54,z/2.54) for z in [lo[2],hi[2]] for y in [lo[1],hi[1]] for x in [lo[0],hi[0]]];faces=[[0,1,3,2],[4,6,7,5],[0,4,5,1],[2,3,7,6],[0,2,6,4],[1,5,7,3]]
m=H/'models'/model;m.write_text('#VRML V2.0 utf8\n# Original maximum dimensional envelope, not supplier CAD.\nShape { appearance Appearance { material Material { diffuseColor .55 .35 .17 } } geometry IndexedFaceSet { solid FALSE coord Coordinate { point [ '+', '.join(' '.join(map(str,v)) for v in pts)+' ] } coordIndex [ '+', '.join(' '.join(map(str,f))+', -1' for f in faces)+' ] } }\n',encoding='utf8')
node=['model',json.dumps('${KIPRJMOD}/../models/'+model),['offset',['xyz','0','0','0']],['scale',['xyz','1','1','1']],['rotate',['xyz','0','0','0']]]
t=loads((C/dst.name).read_text(encoding='utf8'));f=next(f for f in t if isinstance(f,list) and f[0]=='footprint' and any(isinstance(v,list) and v[:3]==['property','"Reference"','"C405"'] for v in f))
assert list(map(float,sub(f,'at')[1:]))==[3.9,42.5,180.]
f[1]=json.dumps('YuEEG:'+name)
for prop in f:
 if isinstance(prop,list) and prop[0]=='property' and json.loads(prop[1]) in ['Value','Datasheet']:prop[2]=json.dumps(value if prop[1]=='"Value"' else source)
f[:]=[v for v in f if not(isinstance(v,list) and v[0]=='model')];f.append(node);dst.write_text(dumps(t),encoding='utf8')
lib=loads((H/'footprints/Capacitor_SMD.pretty/C_1206_3216Metric.kicad_mod').read_text(encoding='utf8'));lib[1]=json.dumps(name);lib[:]=[v for v in lib if not(isinstance(v,list) and v[0]=='model')];lib.append(node);(H/'footprints/YuEEG.pretty'/(name+'.kicad_mod')).write_text(dumps(lib),encoding='utf8')
sp=D/'circuit_20.kicad_sch';sch=loads(sp.read_text(encoding='utf8'));count=0
for s in sch:
 if not(isinstance(s,list) and s[0]=='symbol'):continue
 props={json.loads(v[1]):v for v in s if isinstance(v,list) and v[0]=='property'}
 if props.get('Reference',[None,None,None])[2]=='"C405"':
  for key,val in [('Value',value),('Footprint','YuEEG:'+name),('Datasheet',source)]:props[key][2]=json.dumps(val)
  count+=1
assert count==1;sp.write_text(dumps(sch),encoding='utf8')
with (D/'BOM.csv').open(encoding='utf-8-sig',newline='') as stream:reader=csv.DictReader(stream);fields=reader.fieldnames;rows=list(reader)
for row in rows:
 if row['Reference']=='C405':row.update(Value=value,Footprint='YuEEG:'+name,Datasheet=source)
with (D/'BOM.csv').open('w',encoding='utf-8-sig',newline='') as stream:w=csv.DictWriter(stream,fields);w.writeheader();w.writerows(rows)
ep=H/'review/component_envelopes.json';env=json.loads(ep.read_text());env['models'].append(dict(model=model,boxes_footprint_mm=[dict(min=lo,max=hi)],source=[source],scope='Maximum L/W/T incl manufacturer tolerance; excludes solder lift. Original envelope, not supplier CAD.',coordinate_convention='VRML Y is negative footprint Y; units 2.54 mm',sha256=sha(m)));env['bindings'].append(dict(board='afe',reference='C405',model=model));ep.write_text(json.dumps(env,indent=2),encoding='utf8')
ip=H/'review/isolation_plan.json';iso=json.loads(ip.read_text());iso['afe']['all_layer_copper_exclusion_y_mm']=[47.5,60];ip.write_text(json.dumps(iso,indent=2),encoding='utf8')
data.update(status='IMPLEMENTED_ROUTED_ENGINEERING_CHANGE_NOT_ASSEMBLY_RELEASE',after_pcb_sha256=sha(dst),reason='Move high capacitor away from actual external HOST copper and extend lower-board copper exclusion; not a safety qualification.',source=source,cap_dimensions_max_mm=[3.5,1.9,1.9]);(D/'review/power_shadow_change.json').write_text(json.dumps(data,indent=2),encoding='utf8')
subprocess.run(['X:/SoftWare/Kicad/bin/kicad-cli.exe','sch','export','netlist','--format','kicadxml','-o',str(D/'review/netlist.xml'),str(D/'YuEEG_H_AFE.kicad_sch')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
print('Adopted AFE shadow candidate; refresh reports before publishing')
