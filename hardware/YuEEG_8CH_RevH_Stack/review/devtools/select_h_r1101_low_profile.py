"""Freeze the resistor used by the display-fold height calculation, no reroute."""
from pathlib import Path
import json,csv,sys,hashlib,copy,subprocess
sys.path.insert(0,'hardware/YuEEG_8CH_RevG/review');from sexpr_io import loads,dumps,sub
H=Path('hardware/YuEEG_8CH_RevH_Stack');D=H/'digital';pcb=D/'YuEEG_H_DIGITAL.kicad_pcb';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();before=sha(pcb);t=loads(pcb.read_text(encoding='utf8'));f=next(f for f in t if isinstance(f,list) and f[0]=='footprint' and any(isinstance(v,list) and v[:3]==['property','"Reference"','"R1101"'] for v in f));pads=copy.deepcopy([v for v in f if isinstance(v,list) and v[0]=='pad']);at=copy.deepcopy(sub(f,'at'));tracks=copy.deepcopy([v for v in t if isinstance(v,list) and v[0] in ['segment','via','arc','zone']])
mpn='RC0402FR-0722RL';name='YAGEO_RC0402FR_0722RL';value='22R 1% / '+mpn;source='https://www.yageogroup.com/component-documentation/download/specsheet/'+mpn;model=name+'_max_envelope.wrl';lo=[-.525,-.275,0];hi=[.525,.275,.4];pts=[(x/2.54,-y/2.54,z/2.54) for z in [lo[2],hi[2]] for y in [lo[1],hi[1]] for x in [lo[0],hi[0]]];faces=[[0,1,3,2],[4,6,7,5],[0,4,5,1],[2,3,7,6],[0,2,6,4],[1,5,7,3]]
m=H/'models'/model;m.write_text('#VRML V2.0 utf8\n# Original maximum resistor envelope from YAGEO specification, not supplier CAD.\nShape { appearance Appearance { material Material { diffuseColor .20 .20 .20 } } geometry IndexedFaceSet { solid FALSE coord Coordinate { point [ '+', '.join(' '.join(map(str,v)) for v in pts)+' ] } coordIndex [ '+', '.join(' '.join(map(str,v))+', -1' for v in faces)+' ] } }\n',encoding='utf8')
node=['model',json.dumps('${KIPRJMOD}/../models/'+model),['offset',['xyz','0','0','0']],['scale',['xyz','1','1','1']],['rotate',['xyz','0','0','0']]]
f[1]=json.dumps('YuEEG:'+name)
for prop in f:
 if isinstance(prop,list) and prop[0]=='property' and json.loads(prop[1]) in ['Value','Datasheet']:prop[2]=json.dumps(value if prop[1]=='"Value"' else source)
f[:]=[v for v in f if not(isinstance(v,list) and v[0]=='model')];f.append(node)
assert [v for v in f if isinstance(v,list) and v[0]=='pad']==pads and sub(f,'at')==at
assert [v for v in t if isinstance(v,list) and v[0] in ['segment','via','arc','zone']]==tracks
pcb.write_text(dumps(t),encoding='utf8')
lib=loads((H/'footprints/Resistor_SMD.pretty/R_0402_1005Metric.kicad_mod').read_text(encoding='utf8'));lib[1]=json.dumps(name);lib[:]=[v for v in lib if not(isinstance(v,list) and v[0]=='model')];lib.append(node);(H/'footprints/YuEEG.pretty'/(name+'.kicad_mod')).write_text(dumps(lib),encoding='utf8')
sp=D/'circuit_14.kicad_sch';sch=loads(sp.read_text(encoding='utf8'));count=0
for s in sch:
 if not(isinstance(s,list) and s[0]=='symbol'):continue
 props={json.loads(v[1]):v for v in s if isinstance(v,list) and v[0]=='property'}
 if props.get('Reference',[None,None,None])[2]=='"R1101"':
  for key,val in [('Value',value),('Footprint','YuEEG:'+name),('Datasheet',source)]:props[key][2]=json.dumps(val)
  count+=1
assert count==1;sp.write_text(dumps(sch),encoding='utf8')
with (D/'BOM.csv').open(encoding='utf-8-sig',newline='') as stream:r=csv.DictReader(stream);fields=r.fieldnames;rows=list(r)
for row in rows:
 if row['Reference']=='R1101':row.update(Value=value,Footprint='YuEEG:'+name,Datasheet=source)
with (D/'BOM.csv').open('w',encoding='utf-8-sig',newline='') as stream:w=csv.DictWriter(stream,fields);w.writeheader();w.writerows(rows)
ep=H/'review/component_envelopes.json';env=json.loads(ep.read_text());env['models'].append(dict(model=model,boxes_footprint_mm=[dict(min=lo,max=hi)],source=[source],scope='Maximum body incl manufacturer tolerance. Separate .10mm solder-lift allowance is used by fold screening.',coordinate_convention='VRML Y is negative footprint Y; units 2.54 mm',sha256=sha(m)));env['bindings'].append(dict(board='digital',reference='R1101',model=model));ep.write_text(json.dumps(env,indent=2),encoding='utf8')
record=dict(status='SELECTED_DIMENSION_CONSTRAINED_PART_NOT_ASSEMBLY_RELEASE',reference='R1101',mpn=mpn,manufacturer='YAGEO',source=source,resistance_ohm=22,tolerance_percent=1,rated_power_W_at_70C=.063,body_nominal_mm=[1.,.5,.35],body_max_mm=[1.05,.55,.4],assumed_solder_lift_mm=.1,maximum_mounted_height_for_fold_screen_mm=.5,before_pcb_sha256=before,after_pcb_sha256=sha(pcb),pad_geometry_and_pose_unchanged=True,tracks_vias_and_zones_unchanged=True,procurement_scope='Exact MPN selected from manufacturer data; no Taobao stock assertion. Substitutions require equivalent electrical rating and maximum envelope, including installed solder height.',scope='Closes the unselected resistor MPN used by fold screening; not full display assembly qualification.');(D/'review/r1101_height_selection.json').write_text(json.dumps(record,indent=2),encoding='utf8')
subprocess.run(['X:/SoftWare/Kicad/bin/kicad-cli.exe','sch','export','netlist','--format','kicadxml','-o',str(D/'review/netlist.xml'),str(D/'YuEEG_H_DIGITAL.kicad_sch')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
print('Selected R1101 and maximum height; no pad/pose/copper changes')
