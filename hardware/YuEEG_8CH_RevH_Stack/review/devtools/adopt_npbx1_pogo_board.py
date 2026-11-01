"""Integrate only the checked, locally derived pogo candidate. No git/network operations."""
from pathlib import Path
import sys,json,csv,hashlib,shutil,subprocess
sys.path.insert(0,'hardware/YuEEG_8CH_RevG/review');from sexpr_io import loads,dumps,sub
H=Path('hardware/YuEEG_8CH_RevH_Stack');D=H/'power';C=Path('logs/npbx1_pogo_candidate');dst=D/'YuEEG_H_POWER.kicad_pcb';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();r=json.loads((C/'candidate.json').read_text());d=json.loads((C/'drc.json').read_text());assert not d['violations'] and not d['unconnected_items'];assert sha(dst)==r['baseline_pcb_sha256'];assert sha(C/dst.name)==r['candidate_pcb_sha256'];assert json.loads((H/'mechanical/current/npbx1_user_terminal_order.json').read_text(encoding='utf8'))['confirmed_model_labels']=={'A':'C','B':'BAT-','C':'T','D':'BAT+'}
backup=Path('logs/before_pogo_adoption');backup.mkdir(exist_ok=True)
for path in [dst,D/'power_1.kicad_sch',D/'BOM.csv',D/'review/netlist.xml']:shutil.copy2(path,backup/path.name)
name='NPBX1_MillMax0906_Dplus_Bminus_10mm';fp='YuEEG:'+name;value='2x Mill-Max 0906-1-15-20-75-14-11-0 / D+ B-';source='https://www.mill-max.com/sites/default/files/external/catalog/2019-04/023M-028M.pdf'
lib=loads((C/'Candidate.pretty/NPBX1_Dplus_Bminus_10mm.kicad_mod').read_text(encoding='utf8'));lib[1]=json.dumps(name)
for v in lib:
 if isinstance(v,list) and v[:2]==['property','"Reference"']:sub(sub(sub(v,'effects'),'font'),'size')[1:]=['.8','.8']
(H/'footprints/YuEEG.pretty'/(name+'.kicad_mod')).write_text(dumps(lib),encoding='utf8')
t=loads((C/dst.name).read_text(encoding='utf8'));f=next(f for f in t if isinstance(f,list) and f[0]=='footprint' and any(isinstance(v,list) and v[:3]==['property','"Reference"','"JP1"'] for v in f));f[1]=json.dumps(fp)
for prop in f:
 if isinstance(prop,list) and prop[0]=='property' and json.loads(prop[1]) in ['Value','Datasheet']:prop[2]=json.dumps(value if prop[1]=='"Value"' else source)
assert sub(sub(t,'general'),'thickness')[1]=='1';setup=sub(t,'setup');assert sub(setup,'stackup') is None
setup.append(['stackup',['layer','"F.Mask"',['type','"Top Solder Mask"'],['thickness','.01']],['layer','"F.Cu"',['type','"copper"'],['thickness','.035']],['layer','"dielectric 1"',['type','"core"'],['thickness','.91'],['material','"FR4"'],['epsilon_r','4.5'],['loss_tangent','.02']],['layer','"B.Cu"',['type','"copper"'],['thickness','.035']],['layer','"B.Mask"',['type','"Bottom Solder Mask"'],['thickness','.01']],['dielectric_constraints','no']])
dst.write_text(dumps(t),encoding='utf8');sp=D/'power_1.kicad_sch';sch=loads(sp.read_text(encoding='utf8'));count=0
for s in sch:
 if not(isinstance(s,list) and s[0]=='symbol'):continue
 props={json.loads(v[1]):v for v in s if isinstance(v,list) and v[0]=='property'}
 if props.get('Reference',[None,None,None])[2]=='"JP1"':
  for key,val in [('Value',value),('Footprint',fp),('Datasheet',source)]:props[key][2]=json.dumps(val)
  count+=1
assert count==1;sp.write_text(dumps(sch),encoding='utf8')
with (D/'BOM.csv').open(encoding='utf-8-sig',newline='') as stream:reader=csv.DictReader(stream);fields=reader.fieldnames;rows=list(reader)
if 'Quantity' not in fields:fields.append('Quantity')
for row in rows:
 row['Quantity']='2' if row['Reference']=='JP1' else '1'
 if row['Reference']=='JP1':row.update(Value=value,Footprint=fp,Datasheet=source)
with (D/'BOM.csv').open('w',encoding='utf-8-sig',newline='') as stream:w=csv.DictWriter(stream,fields);w.writeheader();w.writerows(rows)
ep=H/'review/component_envelopes.json';env=json.loads(ep.read_text());model='MillMax_0906_1_midstroke.wrl'
if not any(v['model']==model for v in env['models']):env['models'].append(dict(model=model,boxes_footprint_mm=[dict(min=[-.915,-.915,-1.75],max=[.915,.915,3.8])],source=[source+' metric page25'],scope='Original nominal single probe model at .7mm compression. Pair footprint has two instances. Not maximum free-height geometry or supplier CAD.',sha256=sha(H/'models'/model)))
env['bindings']=[v for v in env['bindings'] if not(v['board']=='power' and v['reference']=='JP1')];env['bindings'].append(dict(board='power',reference='JP1',model=model));ep.write_text(json.dumps(env,indent=2),encoding='utf8')
pp=H/'mechanical/current/pogo_reference.json';q=json.loads(pp.read_text());q.update(not_yet_installed_on_power_pcb=False,scope='Selected pair footprint installed and routed; nominal battery pose, procurement and full assembly qualification remain conditional.',confirmed_pin_map={'JP1.1':'D / BAT+ / PACK_POS','JP1.2':'B / BAT- / GND'},power_pcb_nominal_thickness_mm=1.0);pp.write_text(json.dumps(q,indent=2),encoding='utf8')
r.update(status='INSTALLED_ROUTED_ENGINEERING_DESIGN_NOT_ASSEMBLY_RELEASE',after_pcb_sha256=sha(dst),part_quantity_at_JP1=2,logical_power_references=21,physical_power_parts=22,physical_all_three_parts=270,stackup_target_mm={'F.Mask':.01,'F.Cu':.035,'FR4_core':.91,'B.Cu':.035,'B.Mask':.01},scope='Local engineering integration. Dimensions derive partly from user-supplied model; not authorized for publication. Assembly pose, delivered battery/holder tolerances, screen support and production release remain open.')
(D/'review/pogo_integration.json').write_text(json.dumps(r,indent=2),encoding='utf8');subprocess.run(['X:/SoftWare/Kicad/bin/kicad-cli.exe','sch','export','netlist','--format','kicadxml','-o',str(D/'review/netlist.xml'),str(D/'YuEEG_H_POWER.kicad_sch')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);print('Integrated local pogo board, schematic, BOM quantity and explicit 1mm stackup; reports must be refreshed')
