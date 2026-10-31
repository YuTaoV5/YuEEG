"""Source-based original USB envelope and matching shallow rounded board-edge relief."""
from pathlib import Path
import json,sys,hashlib,uuid,shutil
sys.path.insert(0,'hardware/YuEEG_8CH_RevG/review');from sexpr_io import loads,dumps,sub
H=Path('hardware/YuEEG_8CH_RevH_Stack');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();backup=Path('logs/before_usb_mouth');backup.mkdir(exist_ok=True)
model='HRO_TYPE_C_31_M_12_original_envelope.wrl';m=H/'models'/model;shapes=[];boxes=[]
def box(lo,hi,color):
 boxes.append(dict(min=lo,max=hi));pts=[(x/2.54,-y/2.54,z/2.54) for z in [lo[2],hi[2]] for y in [lo[1],hi[1]] for x in [lo[0],hi[0]]];faces=[[0,1,3,2],[4,6,7,5],[0,4,5,1],[2,3,7,6],[0,2,6,4],[1,5,7,3]]
 shapes.append('Shape { appearance Appearance { material Material { diffuseColor '+color+' } } geometry IndexedFaceSet { solid FALSE coord Coordinate { point [ '+', '.join(' '.join(map(str,v)) for v in pts)+' ] } coordIndex [ '+', '.join(' '.join(map(str,f))+', -1' for f in faces)+' ] } }')
# Original hollow dimensional envelope: not internal/contact/shell engineering CAD.
box([-4.47,-3.67,0],[4.47,3.68,.25],'.65 .68 .70');box([-4.47,-3.67,3.01],[4.47,3.68,3.26],'.65 .68 .70')
box([-4.47,-3.67,.25],[-4.17,3.68,3.01],'.65 .68 .70');box([4.17,-3.67,.25],[4.47,3.68,3.01],'.65 .68 .70');box([-4.17,-3.67,.25],[4.17,-3.17,3.01],'.15 .15 .15');box([-3.4,-3.17,1.33],[3.4,3.05,2.03],'.15 .15 .15')
m.write_text('#VRML V2.0 utf8\n# Original nominal visual envelope from HRO drawing page 4 (2020-12-08).\n# Simplified walls/tongue, no exact internal geometry. No solder or protruding tails modeled.\n'+'\n'.join(shapes)+'\n',encoding='utf8')
node=['model',json.dumps('${KIPRJMOD}/../models/'+model),['offset',['xyz','0','0','0']],['scale',['xyz','1','1','1']],['rotate',['xyz','0','0','0']]]
records={}
for board in ['afe','digital']:
 path=H/board/('YuEEG_H_'+board.upper()+'.kicad_pcb');shutil.copy2(path,backup/path.name);before=sha(path);t=loads(path.read_text(encoding='utf8'))
 lines=[v for v in t if isinstance(v,list) and v[0]=='gr_line' and sub(v,'layer')[1]=='"Edge.Cuts"' and {tuple(map(float,sub(v,k)[1:])) for k in ['start','end']}=={(46.,60.),(2.,60.)}];assert len(lines)==1;t.remove(lines[0])
 def edge(kind,start,end,mid=None):
  n=[kind,['start',*map(str,start)]]
  if mid:n.append(['mid',*map(str,mid)])
  n.extend([['end',*map(str,end)],['stroke',['width','.05'],['type','default']],['layer','"Edge.Cuts"'],['uuid',json.dumps(str(uuid.uuid4()))]]);t.append(n)
 edge('gr_line',(46,60),(30.25,60));edge('gr_arc',(30.25,60),(30,59.75),(30.0732233,59.9267767));edge('gr_line',(30,59.75),(30,59.7));edge('gr_arc',(30,59.7),(29.5,59.2),(29.8535534,59.3464466));edge('gr_line',(29.5,59.2),(18.5,59.2));edge('gr_arc',(18.5,59.2),(18,59.7),(18.1464466,59.3464466));edge('gr_line',(18,59.7),(18,59.75));edge('gr_arc',(18,59.75),(17.75,60),(17.9267767,59.9267767));edge('gr_line',(17.75,60),(2,60))
 if board=='digital':
  f=next(f for f in t if isinstance(f,list) and f[0]=='footprint' and any(isinstance(v,list) and v[:3]==['property','"Reference"','"J601"'] for v in f));f[:]=[v for v in f if not(isinstance(v,list) and v[0]=='model')];f.append(node)
 path.write_text(dumps(t),encoding='utf8');records[board]=dict(before_pcb_sha256=before,after_pcb_sha256=sha(path))
libpath=H/'footprints/Connector_USB.pretty/USB_C_Receptacle_HRO_TYPE-C-31-M-12.kicad_mod';t=loads(libpath.read_text(encoding='utf8'));t[:]=[v for v in t if not(isinstance(v,list) and v[0]=='model')];t.append(node);libpath.write_text(dumps(t),encoding='utf8')
envpath=H/'review/component_envelopes.json';env=json.loads(envpath.read_text());source='https://www.krhro.com/Product-Details/726.html';env['models'].append(dict(model=model,boxes_footprint_mm=boxes,source=[source+' linked drawing page 4, TYPE-C-31-M-12, 2020-12-08'],source_pdf_sha256='1c23b78973c56e8dd83f1b46b8c31226f31ba0ea136ce3babd9f80bbaf2e7345',scope='Original nominal visual envelope; package variants on pages 1-3 excluded. Simplified wall/tongue geometry is illustrative. Solder and manufacturing variation separate.',coordinate_convention='VRML Y is negative footprint Y; units 2.54 mm',sha256=sha(m)))
env['bindings']=[r for r in env['bindings'] if not(r['board']=='digital' and r['reference']=='J601')];env['bindings'].append(dict(board='digital',reference='J601',model=model));envpath.write_text(json.dumps(env,indent=2),encoding='utf8')
record=dict(status='IMPLEMENTED_ENGINEERING_RELIEF_NOT_ASSEMBLY_RELEASE',boards=records,source=source,source_pdf_sha256='1c23b78973c56e8dd83f1b46b8c31226f31ba0ea136ce3babd9f80bbaf2e7345',source_page=4,source_drawing_date='2020-12-08',body_nominal_mm=[8.94,7.35,3.26],body_max_assumed_mm=[9.09,7.50,3.36],solder_lift_allowance_mm=.1,board_edge_recommended_y_mm=59.19,implemented_notch_roof_y_mm=59.2,notch_depth_mm=.8,notch_inner_radius_mm=.5,notch_outer_radius_mm=.25,notch_roof_x_mm=[18.5,29.5],overall_outline_mm=[48,60],scope='Web product title says 3.16mm; use matched base-part drawing 3.26mm. Manufacturer tabs extend 1.10mm below mounting plane, not below PCB back. Notch and model require native DRC/refill and delivered connector inspection; external USB plug/case envelope unqualified.')
(H/'mechanical/current/usb_mouth_review.json').write_text(json.dumps(record,indent=2),encoding='utf8');print('Updated both mouth reliefs and original local USB model; refill and check required')
