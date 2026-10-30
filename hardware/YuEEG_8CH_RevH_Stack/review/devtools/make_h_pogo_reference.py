from pathlib import Path
import json,hashlib,math
R=Path('hardware/YuEEG_8CH_RevH_Stack');name='MillMax_0906_1_TH_1Pin';M=R/'models'/('MillMax_0906_1_midstroke.wrl');out=['#VRML V2.0 utf8','# Original envelope from Mill-Max catalog page 25 metric. MIDSTROKE, not supplier CAD.']
def cylinder(radius,z0,z1,color):
 n=24;pts=[(radius*math.cos(i*2*math.pi/n)/2.54,radius*math.sin(i*2*math.pi/n)/2.54,z/2.54) for z in [z0,z1] for i in range(n)];faces=[]
 faces.append(','.join(map(str,reversed(range(n))))+',-1');faces.append(','.join(str(i+n) for i in range(n))+',-1')
 faces.extend(f'{i},{(i+1)%n},{(i+1)%n+n},{i+n},-1' for i in range(n))
 out.append('Shape { appearance Appearance { material Material { diffuseColor '+color+' } } geometry IndexedFaceSet { solid FALSE coord Coordinate { point [ '+', '.join(' '.join(map(str,q)) for q in pts)+' ] } coordIndex [ '+', '.join(faces)+' ] } }')
for r,z0,z1 in [(.215,-1.75,0),(.915,0,.41),(.815,.41,.71),(.75,.71,2.69),(.535,2.69,3.8)]:cylinder(r,z0,z1,'.74 .60 .22')
M.write_text('\n'.join(out)+'\n')
fp=f'''(footprint "{name}" (version 20241229) (generator "pcbnew") (layer "F.Cu") (attr through_hole)
 (descr "Mill-Max 0906-1-15-20-75-14-11-0, 2A continuous, hole min .51mm; .60mm finished project hole; model at .7mm compression")
 (property "Reference" "REF**" (at 0 -1.8) (layer "F.SilkS") (effects (font (size .7 .7) (thickness .1))))
 (property "Value" "0906-1-15-20-75-14-11-0" (at 0 1.8) (layer "F.Fab") (effects (font (size .7 .7) (thickness .1))))
 (fp_circle (center 0 0) (end .915 0) (stroke (width .1) (type default)) (fill none) (layer "F.Fab"))
 (fp_circle (center 0 0) (end 1.25 0) (stroke (width .05) (type default)) (fill none) (layer "F.CrtYd"))
 (fp_circle (center 0 0) (end .9 0) (stroke (width .05) (type default)) (fill none) (layer "B.CrtYd"))
 (pad "1" thru_hole circle (at 0 0) (size 1.3 1.3) (drill .6) (layers "*.Cu" "*.Mask"))
 (model "${{KIPRJMOD}}/../models/{M.name}" (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0))))'''
(R/'footprints/YuEEG.pretty'/(name+'.kicad_mod')).write_text(fp)
data={'reference_part':'0906-1-15-20-75-14-11-0','manufacturer':'Mill-Max','source':'https://www.mill-max.com/sites/default/files/external/catalog/2019-04/023M-028M.pdf','source_pdf_sha256':hashlib.sha256(Path('logs/model_sources/millmax-complete.pdf').read_bytes()).hexdigest(),'source_page_index':3,'source_printed_page':'25 metric','free_height_mm':4.5,'height_tolerance_mm':.15,'midstroke_mm':.7,'maxstroke_mm':1.4,'midstroke_height_mm':3.8,'tip_diameter_mm':1.07,'flange_diameter_mm':1.83,'tail_length_mm':1.75,'tail_diameter_mm':.43,'diameter_tolerance_mm':.051,'manufacturer_minimum_mounting_hole_mm':.51,'project_finished_hole_mm':.6,'continuous_current_A':2,'peak_current_A':3,'max_contact_resistance_ohm':.020,'spring_force_at_midstroke_g':60,'recommended_power_pcb_thickness_mm':1.0,'pcb_thickness_reason':'At 1.6mm board plus tolerance the minimum 1.60mm solder tail may not protrude. A 1.0mm board leaves a practical solder-tail allowance. Enclosure must support the thinner strip.','assembly_orientation_proposal':'Probes on battery-facing B side, other components mainly outward F side. Through-hole solder lands must be clear on F side.','battery_geometry_reference':{'source':'https://gist.github.com/ednisley/c842ec39d6ac5a2e6945ea03435c56c3','contact_pitch_mm':10,'contact_height_from_battery_bottom_mm':6.2,'contact_recess_mm':.75,'status':'Author sample measurements, NOT Sony tolerance drawing. Polarity orientation and 1.07mm tip fit unresolved.'},'not_yet_installed_on_power_pcb':True,'procurement_status':'Manufacturer dimensional reference verified; exact Taobao seller or interchangeable part not verified','scope':'Real manufacturer footprint reference, NOT a released NP-BX1 holder or completed power board contact interface.'}
(R/'mechanical/current/pogo_reference.json').write_text(json.dumps(data,indent=2));print('Created exact manufacturer pogo reference; battery-side mounting/layout remains to be implemented')
