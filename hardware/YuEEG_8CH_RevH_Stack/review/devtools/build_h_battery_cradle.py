"""Build the actual three-part Rev H battery cage; source battery stays local.
python build_h_battery_cradle.py --battery-step <user supplied STEP>
Install CadQuery into the optional --runtime directory, or use its own venv.
"""
from pathlib import Path
import sys,argparse,json,hashlib,math,platform,importlib.metadata
ap=argparse.ArgumentParser();ap.add_argument('--battery-step',required=True,type=Path);ap.add_argument('--runtime',default=Path('logs/mechanical_runtime'),type=Path);ap.add_argument('--output',default=Path('logs/battery_cradle_candidate'),type=Path);args=ap.parse_args()
if args.runtime.exists():sys.path.insert(0,str(args.runtime.resolve()))
import cadquery as cq
H=Path('hardware/YuEEG_8CH_RevH_Stack');M=H/'mechanical/current';contract=M/'battery_cradle_contract.json';data=json.loads(contract.read_text());source=args.battery_step
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
expected=json.loads((M/'npbx1_user_model_comparison.json').read_text())['source_sha256'];assert sha(source)==expected,'Source model changed; inspect it before building'
O=args.output;O.mkdir(parents=True,exist_ok=True)
def box(b):return cq.Solid.makeBox(b[3]-b[0],b[4]-b[1],b[5]-b[2],cq.Vector(*b[:3]))
def vol(q):return abs(q.Volume()) if q.Solids() else 0.
def overlap(a,b):return vol(a.intersect(b))
def bbox(q):
 b=q.BoundingBox();return [b.xmin,b.ymin,b.zmin,b.xmax,b.ymax,b.zmax]
def make_part(spec):
 additions=[box(b) for _,b in spec['add_boxes']];solid=additions[0].fuse(*additions[1:]).clean()
 for _,pnt,direction,length,dia in spec.get('cut_round_holes',[]):solid=solid.cut(cq.Solid.makeCylinder(dia/2,length,cq.Vector(*pnt),cq.Vector(*direction)))
 for _,pnt,length,width,depth in spec.get('cut_slots',[]):
  x,y,z=pnt;separation=length-width;r=width/2
  cutter=cq.Solid.makeCylinder(r,depth,cq.Vector(x,y-separation/2,z)).fuse(cq.Solid.makeCylinder(r,depth,cq.Vector(x,y+separation/2,z)),box([x-r,y-separation/2,z,x+r,y+separation/2,z+depth]))
  solid=solid.cut(cutter)
 solid=solid.clean();assert solid.isValid() and len(solid.Solids())==1 and vol(solid)>0,'Invalid or disconnected holder part'
 return solid
parts={name:make_part(v) for name,v in data['parts'].items()}
raw=cq.importers.importStep(str(source)).val();assert raw.isValid() and len(raw.Solids())==1
battery=raw.rotate((0,0,0),(1,0,0),90).translate((69.95,21.375,13.2));bb=bbox(battery);jaw_delta=bb[4]-42.7
assert -.5<=jaw_delta<=.5
assembled=dict(parts);assembled['rear_jaw']=parts['rear_jaw'].translate((0,jaw_delta,0))
static=[]
for name,part in assembled.items():
 v=overlap(part,battery);static.append({'part':name,'battery_overlap_mm3':v,'minimum_native_distance_mm':part.distance(battery)})
 assert v<1e-5,('Battery intrusion',name,v)
pair=[]
for i,a in enumerate(assembled):
 for b in list(assembled)[i+1:]:
  v=overlap(assembled[a],assembled[b]);pair.append({'parts':[a,b],'overlap_mm3':v});assert v<1e-5,('Part intrusion',a,b,v)
# Actual local body is used only for checks and derived figures, never exported.
key_boxes=[b for name,b in data['parts']['cradle']['add_boxes'] if name in ['key_L','key_R']];keys=box(key_boxes[0]).fuse(box(key_boxes[1]))
assert overlap(keys,battery)<1e-5
axis_y=((69.95,0,13.2),(69.95,1,13.2));axis_z=((69.95,(bb[1]+bb[4])/2,0),(69.95,(bb[1]+bb[4])/2,1))
wrong={'upside_down':battery.rotate(*axis_y,180),'reverse_end':battery.rotate(*axis_z,180),'upside_reverse':battery.rotate(*axis_y,180).rotate(*axis_z,180)};key_results=[]
for name,body in wrong.items():
 at_seat=overlap(keys,body);assert at_seat>.01,('Wrong orientation not blocked',name)
 lo,hi=0.,2.
 assert overlap(keys,body.translate((0,hi,0)))<1e-6
 for _ in range(18):
  mid=(lo+hi)/2
  if overlap(keys,body.translate((0,mid,0)))>1e-6:lo=mid
  else:hi=mid
 compression=max(0.,4.5-3.05-hi);assert compression<1.4
 key_results.append({'orientation':name,'overlap_if_forced_seated_mm3':at_seat,'blocking_front_offset_mm':[lo,hi],'nominal_flat_face_probe_compression_at_block_mm':compression,'scope':'Source-model nominal geometry only; tolerances, key strength and load deflection unqualified.'})
# Insert/remove with rear jaw removed; explicitly sampled rather than a sweep proof.
move=[]
for dy,dz in [(v*.25,0.) for v in range(19)]+[(4.5,v*.5) for v in range(1,25)]:
 body=battery.translate((0,dy,dz));v=max(overlap(assembled[n],body) for n in ['cradle','power_clip']);move.append({'rear_shift_mm':dy,'lift_mm':dz,'maximum_overlap_mm3':v});assert v<1e-5,('Removal collision',dy,dz,v)
# Rounded hardware space budgets include longest screw, head and nut limits.
# The unthreaded shank/circular nut are envelopes, not supplier part CAD.
hardware_facts=M/'battery_cradle_hardware.json'
hardware_input=json.loads(hardware_facts.read_text());f=data['fastener_requirements']
assert hardware_input['nut']['derived_sharp_regular_hex_corner_diameter_max_mm'] <= f['nut_max_corner_diameter_mm']
def cylinder(pnt,axis,height,radius):return cq.Solid.makeCylinder(radius,height,cq.Vector(*pnt),cq.Vector(*axis))
hardware={};tools={};thread_engagement=[]
for group,positions in data['assembly_targets']['fastener_fixture_positions_product_mm'].items():
 for i,pnt in enumerate(positions):
  x,y,z=pnt;name=group+'_'+str(i+1)
  if group=='power_clip_axisY':
   axis=(0,1,0);outward=(0,-1,0);nut_origin=(x,-.25,z);tool_origin=(x,y-1.61,z)
   grip=4.75
  else:
   axis=(0,0,-1);outward=(0,0,1);nut_origin=(x,y,6.7);tool_origin=(x,y,z+1.61)
   grip=4.
  r=f['screw_shank_max_diameter_budget_mm']/2
  hardware[name+'/shaft']=cylinder(pnt,axis,f['screw_underhead_length_range_mm'][1],r)
  hardware[name+'/head']=cylinder(pnt,outward,f['screw_head_max_height_mm'],f['screw_head_max_diameter_mm']/2)
  hardware[name+'/nut']=cylinder(nut_origin,axis,f['nut_max_thickness_mm'],f['nut_max_corner_diameter_mm']/2).cut(cylinder(nut_origin,axis,f['nut_max_thickness_mm'],r))
  tools[name]=cylinder(tool_origin,outward,15.,f['screw_head_max_diameter_mm']/2)
  projection=f['screw_underhead_length_range_mm'][0]-grip-f['nut_max_thickness_mm']
  assert projection>.4
  thread_engagement.append({'fixture':name,'nominal_grip_mm':grip,'shortest_screw_projection_beyond_maximum_budget_nut_mm':projection,'scope':'Nominal rigid grip and dimensioned hardware envelopes only; no thread-strength, clamp, crush or process tolerance proof.'})
hardware_checks=[];tool_checks=[]
for adjustment in [-.5,0.,jaw_delta,.5]:
 fixture_parts=dict(parts);fixture_parts['rear_jaw']=parts['rear_jaw'].translate((0,adjustment,0))
 for name,shape in {**hardware,**{'tool/'+n:s for n,s in tools.items()}}.items():
  values={part:overlap(shape,solid) for part,solid in fixture_parts.items()}
  assert max(values.values())<1e-5,('Hardware/tool to holder collision',adjustment,name,values)
  assert overlap(shape,battery)<1e-5,('Hardware/tool to source battery collision',name)
  assert overlap(shape,box([55,0,8.7,84.9,42.7,17.9]))<1e-5,('Hardware/tool to Sony nominal battery box collision',name)
  row={'feature':name,'jaw_adjustment_Y_mm':adjustment,'part_overlap_mm3':values,'source_battery_overlap_mm3':overlap(shape,battery),'bounds_product_mm':bbox(shape)}
  (tool_checks if name.startswith('tool/') else hardware_checks).append(row)
# Export only authored holder geometry. No raw/transformed user STEP in STEP/STL.
exports={}
for name,part in parts.items():
 cq.exporters.export(part,str(O/(name+'.step')));cq.exporters.export(part,str(O/(name+'.stl')),tolerance=.03,angularTolerance=.12)
 exports[name]={'solid_count':len(part.Solids()),'valid':part.isValid(),'volume_mm3':vol(part),'bounds_product_mm':bbox(part),'files_sha256':{suffix:sha(O/(name+suffix)) for suffix in ['.step','.stl']}}
assembly=cq.Compound.makeCompound(list(assembled.values()));cq.exporters.export(assembly,str(O/'cradle_assembly.step'))
roundtrips=[]
for name,original in {**parts,'cradle_assembly':assembly}.items():
 imported=cq.importers.importStep(str(O/(name+'.step'))).val()
 error=abs(vol(imported)-vol(original));expected_solids=3 if name=='cradle_assembly' else 1
 assert imported.isValid() and len(imported.Solids())==expected_solids and error<1e-4,('STEP export roundtrip failed',name,error)
 roundtrips.append({'file':name+'.step','valid':imported.isValid(),'solid_count':len(imported.Solids()),'volume_mm3':vol(imported),'volume_error_mm3':error})
record={'status':'NATIVE_SOLIDS_PASS_SOURCE_MODEL_NOT_PRODUCTION_QUALIFICATION','cadquery_version':cq.__version__,'OCP_distribution_version':importlib.metadata.version('cadquery-ocp'),'python_version':platform.python_version(),'contract_sha256':sha(contract),'source_model_sha256':expected,'source_model_native_solids':len(raw.Solids()),'source_model_native_bbox_xyz_mm':bbox(raw),'source_model_native_volume_mm3':vol(raw),'product_model_bbox_mm':bb,'rear_jaw_adjustment_for_source_model_mm':jaw_delta,'parts':exports,'static_battery_checks':static,'interpart_checks':pair,'front_key_checks':key_results,'removal_checks':move,'assembly_step_sha256':sha(O/'cradle_assembly.step'),'source_geometry_redistributed':False,'open_items':['Delivered Sony pack must meet dimensional and key/contact receiving requirements','Print/CNC material, process, strength, creep, wear, force and insulating-fastener exact MPNs/torques','Full screen-back/FPC/support mechanical datum and whole-system insulation','Native power component envelopes, cable and external HOST clearances reviewed separately'],'scope':f'Real authored STEP/STL parts with checked OCCT solids, local source-battery nominal interference, three wrong-orientation key tests and {len(move)} sampled removal positions. Not force/deflection/continuous-sweep/production, electrical or patient-isolation qualification.'}
record.update({'builder_sha256':sha(Path(__file__)), 'hardware_fact_sha256':sha(hardware_facts), 'key_notch_basis_sha256':sha(M/'npbx1_key_notch_basis.json'), 'hardware_space_checks':hardware_checks, 'driver_access_space_checks':tool_checks, 'thread_projection_checks':thread_engagement, 'STEP_export_roundtrip_checks':roundtrips, 'assembly_STEP_scope':'Three authored holder parts only; hardware is checked by rounded envelopes and not exported as manufacturer CAD.'})
(O/'native_cad_review.json').write_text(json.dumps(record,indent=2),encoding='utf8')
# Derived image only: body tessellation is permitted, original body CAD is not saved.
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
fig=plt.figure(figsize=(13,8));ax=fig.add_subplot(111,projection='3d');colors={'cradle':'#7298b8','power_clip':'#deae50','rear_jaw':'#6caa89'}
for name,shape in assembled.items():
 v,t=shape.tessellate(.15,.15);tri=[[[v[i].x,v[i].y,v[i].z] for i in face] for face in t];ax.add_collection3d(Poly3DCollection(tri,facecolor=colors[name],edgecolor='none',alpha=.75))
v,t=battery.tessellate(.3,.25);tri=[[[v[i].x,v[i].y,v[i].z] for i in face] for face in t];ax.add_collection3d(Poly3DCollection(tri,facecolor='#65736a',edgecolor='none',alpha=.25))
ax.set(xlim=(42,92),ylim=(-9,52),zlim=(-3,24),xlabel='Product X / mm',ylabel='Product Y / mm',zlabel='Product Z / mm',title='NP-BX1 cage: split guides, front keys, detachable card clip, sliding rear jaw')
ax.set_box_aspect((50,61,27));ax.view_init(28,-125);fig.text(.02,.035,'Authored mechanical prototype; source battery translucent for derived visualization only.\nNative solids/no nominal overlap and sampled extraction pass; source model is a replacement pack, not a Sony tolerance drawing.\nRear jaw shifts +%.3f mm for this source body. Exact material, hardware, load/creep and screen assembly remain unqualified.'%jaw_delta,fontsize=9)
fig.tight_layout(rect=[0,.11,1,1]);fig.savefig(O/'cradle_assembly.png',dpi=160);plt.close(fig)
print('PASS3 valid single solids, nominal body/part interference,3 orientation keys and',len(move),'sampled extraction positions. Jaw delta',jaw_delta,flush=True)
