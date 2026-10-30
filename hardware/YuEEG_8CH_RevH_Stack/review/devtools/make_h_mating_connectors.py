from pathlib import Path
import sys,json,copy
sys.path.insert(0,'hardware/YuEEG_8CH_RevG/review');from sexpr_io import loads,dumps,sub
R=Path('hardware/YuEEG_8CH_RevH_Stack');D=R/'footprints/YuEEG.pretty';Q=json.dumps
base=Path('X:/SoftWare/Kicad/share/kicad/footprints/Connector_PinHeader_2.00mm.pretty/PinHeader_2x10_P2.00mm_Vertical.kicad_mod')
def model(name,body,post,tail):
 out=['#VRML V2.0 utf8','# Original simplified dimensional envelope from Samtec drawings, NOT supplier CAD.']
 def box(c,s,col):
  vertices=[((c[0]+x*s[0]/2)/2.54,(c[1]+y*s[1]/2)/2.54,(c[2]+z*s[2]/2)/2.54) for x,y,z in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
  points=', '.join(' '.join(map(str,v)) for v in vertices)
  out.append('Shape { appearance Appearance { material Material { diffuseColor '+col+' } } geometry IndexedFaceSet { solid FALSE coord Coordinate { point [ '+points+' ] } coordIndex [ 3,2,1,0,-1, 4,5,6,7,-1, 0,1,5,4,-1, 1,2,6,5,-1, 2,3,7,6,-1, 3,0,4,7,-1 ] } }')
 box((1,-9,body[2]/2),body,'.06 .065 .07')
 for x in [0,2]:
  for i in range(10):
   if post:box((x,-i*2,(body[2]+post-tail)/2),(.5,.5,body[2]+post+tail),'.72 .61 .25')
   else:box((x,-i*2,-tail/2),(.5,.5,tail),'.65 .65 .65')
 (R/'models'/name).write_text('\n'.join(out)+'\n')
model('SQT_110_01_envelope.wrl',(4,20.3,6.35),0,2.29);model('TMM_110_03_envelope.wrl',(3.94,20,1.5),4,2.7)
for name,source,body,modelname in [('Samtec_SQT_110_01_Logical',base,(4,20.3),'SQT_110_01_envelope.wrl'),('Samtec_TMM_110_03_BottomLogical',D/'Interboard_2x10_Male_BottomLogical.kicad_mod',(3.94,20),'TMM_110_03_envelope.wrl')]:
 d=loads(source.read_text());d[1]=Q(name);d[:]=[n for n in d if not(isinstance(n,list) and (n[0].startswith('fp_') or n[0]=='model'))]
 for pad in d:
  if isinstance(pad,list) and pad[0]=='pad':sub(pad,'drill')[1]='.9'
 for layer,extra in [('F.Fab',0),('F.CrtYd',.25),('F.SilkS',.1)]:
  w,h=body;x0,x1=1-w/2-extra,1+w/2+extra;y0,y1=9-h/2-extra,9+h/2+extra
  d.append(['fp_rect',['start',str(x0),str(y0)],['end',str(x1),str(y1)],['stroke',['width','.05' if layer=='F.CrtYd' else '.1'],['type','default']],['fill','none'],['layer',Q(layer)]])
 d.append(['model',Q('${KIPRJMOD}/../models/'+modelname),['offset',['xyz','0','0','0']],['scale',['xyz','1','1','1']],['rotate',['xyz','0','0','0']]])
 (D/(name+'.kicad_mod')).write_text(dumps(d))
data={'afe_socket_reference':'SQT-110-01-L-D','digital_header_reference':'TMM-110-03-L-D','pitch_mm':2,'finished_hole_mm':.9,'female_body_mm':[4,20.3,6.35],'male_body_mm':[3.94,20,1.5],'male_mating_post_mm':4,'male_solder_tail_mm':2.7,'socket_tail_mm':2.29,'pcb_surface_gap_mm':8.5,'nominal_insertion_mm':3.35,'socket_insertion_range_mm':[2.62,5.03],'nominal_housing_gap_mm':.65,'sources':['https://suddendocs.samtec.com/catalog_english/sqw.pdf','https://suddendocs.samtec.com/catalog_english/tmm_th.pdf','https://suddendocs.samtec.com/prints/tmm-th.pdf'],'procurement_status':'Manufacturer dimensional reference selected; exact Taobao seller/stock or qualified equivalent not verified','numbering':'Project logical numbers; unkeyed physical rows. Assembly XY/net contract remains mandatory. No vendor pin-1 marking relied upon.','models':'Original bounding envelopes; not manufacturer STEP or internal contact model'}
(R/'review/mating_connector_selection.json').write_text(json.dumps(data,indent=2));print('Selected mating reference with 4mm posts and 3.35mm insertion at 8.5mm gap')
