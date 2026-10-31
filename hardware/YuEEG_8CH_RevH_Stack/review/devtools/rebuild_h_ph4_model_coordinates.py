"""Correct footprint-Y-down to VRML-Y-up for the project TH-PH4 envelope."""
from pathlib import Path
import json,hashlib
H=Path('hardware/YuEEG_8CH_RevH_Stack');path=H/'review/component_envelopes.json';d=json.loads(path.read_text());row=next(v for v in d['models'] if v['model']=='JST_S4B_PH_TH_envelope.wrl');out=['#VRML V2.0 utf8','# Original dimensional envelope. Footprint Y down -> VRML Y up. NOT supplier CAD.'];boxes=[(v,'.86 .84 .73',0) for v in row['boxes_footprint_mm']]+[(v,'.9 .5 .15',.35) for v in row.get('additional_tail_reservation_boxes_footprint_mm',[])]
for box,color,alpha in boxes:
 lo,hi=box['min'],box['max'];raw=[(lo[0],lo[1],lo[2]),(hi[0],lo[1],lo[2]),(hi[0],hi[1],lo[2]),(lo[0],hi[1],lo[2]),(lo[0],lo[1],hi[2]),(hi[0],lo[1],hi[2]),(hi[0],hi[1],hi[2]),(lo[0],hi[1],hi[2])];pts=[(x/2.54,-y/2.54,z/2.54) for x,y,z in raw]
 out.append('Shape { appearance Appearance { material Material { diffuseColor '+color+' transparency '+str(alpha)+' } } geometry IndexedFaceSet { solid FALSE coord Coordinate { point [ '+', '.join(' '.join(map(str,v)) for v in pts)+' ] } coordIndex [ 0,1,2,3,-1, 7,6,5,4,-1, 4,5,1,0,-1, 5,6,2,1,-1, 6,7,3,2,-1, 7,4,0,3,-1 ] } }')
model=H/'models'/row['model'];model.write_text('\n'.join(out)+'\n',encoding='utf8');row['sha256']=hashlib.sha256(model.read_bytes()).hexdigest();row['coordinate_convention']='Footprint X/Y dimensions, converted to VRML X/-Y; Z from F mounting plane';path.write_text(json.dumps(d,indent=2),encoding='utf8')
for name,old,new in [('adopt_h_right_power_port.py','x/2.54,y/2.54,z/2.54','x/2.54,-y/2.54,z/2.54'),('model_h_right_port_trimmed_tails.py','a/2.54,b/2.54,c/2.54','a/2.54,-b/2.54,c/2.54')]:
 f=Path('logs')/name;s=f.read_text(encoding='utf8');assert old in s;s=s.replace(old,new);f.write_text(s,encoding='utf8')
print('PH4 model coordinates corrected; electrical PCB and native pads untouched')
