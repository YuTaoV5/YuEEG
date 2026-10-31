"""Conservative segmented swept FPC vs selected neighbor envelope boxes.

Nominal geometric screening only: excludes tolerances, solder, screen, cables,
connector latch/removal paths, dielectric adequacy and surface creepage.
"""
from pathlib import Path
import json,math,hashlib
H=Path('hardware/YuEEG_8CH_RevH_Stack');D=H/'display_link';q=json.loads((D/'review/design_contract.json').read_text());neighbors=json.loads((D/'review/neighbor_native.json').read_text());center=next(v['xy'] for v in neighbors if v['ref']=='J2002')
def bounds(local,xy,angle):
 a=math.radians(angle);pts=[(xy[0]+x*math.cos(a)+y*math.sin(a),xy[1]-x*math.sin(a)+y*math.cos(a)) for x in [local[0],local[2]] for y in [local[1],local[3]]]
 return [min(x for x,y in pts),min(y for x,y in pts),0,max(x for x,y in pts),max(y for x,y in pts),1.45]
obstacles=[]
for ref in ['U1001','U1003']:
 f=next(v for v in neighbors if v['ref']==ref)
 # Package footnotes allow .25 mm mold flash per body side. Use separate
 # body/lead boxes rather than incorrectly extending the leads by body flash.
 boxes=[bounds([-1.125,-1.775,1.125,1.775],f['xy'],f['angle']),bounds([-1.5,-1.2,1.5,1.2],f['xy'],f['angle'])]
 for bb in boxes:bb[5]=1.55
 union=[min(bb[i] for bb in boxes) for i in range(3)]+[max(bb[i+3] for bb in boxes) for i in range(3)]
 obstacles.append(dict(ref=ref,box=union,boxes=boxes,scope='Body 1.75 x 3.05 mm plus .25 mm mold flash on each side; lead span 3.0 mm with end-pin .95 mm center plus .25 mm half-width. Both boxes raised to 1.45 mm max package height plus assumed .10 mm solder lift; conservative lead height.',source='https://www.ti.com/lit/ds/symlink/'+('tps22918' if ref=='U1001' else 'tps7a20')+'.pdf',drawing='DBV0006A p27 note3' if ref=='U1001' else 'DBV0005A p60 note4'))
for ref in ['U402','R1101']:
 f=next(v for v in neighbors if v['ref']==ref);x0,y0,x1,y1=f['courtyard'];obstacles.append(dict(ref=ref,box=[x0,y0,0,x1,y1,2.0],scope='Native courtyard extruded to an assumed 2.0 mm screening height. Not a sourced body height.'))
f=next(v for v in neighbors if v['ref']=='U402');bb=bounds([-2.525,-1.7,2.525,1.7],f['xy'],f['angle']);bb[5]=1.2;obstacles.append(dict(ref='U402_max_package_plus_solder',box=bb,source='https://www.ti.com/lit/ds/symlink/tps62160.pdf',drawing='DGK0008A p35',scope='5.05 mm maximum lead span, 3.1 mm body length plus .15 mm mold flash each side, 1.1 mm maximum height plus assumed .10 mm solder lift. Full lead/body box.'))
selected=json.loads((H/'digital/review/r1101_height_selection.json').read_text());assert selected['mpn']=='RC0402FR-0722RL'
f=next(v for v in neighbors if v['ref']=='R1101');assert selected['mpn'] in f['value'];x0,y0,x1,y1=f['courtyard'];obstacles.append(dict(ref='R1101_selected_low_profile',box=[x0,y0,0,x1,y1,selected['maximum_mounted_height_for_fold_screen_mm']],source=selected['source'],scope='Selected BOM MPN RC0402FR-0722RL: .40 mm maximum body plus .10 mm assumed solder lift, native courtyard XY. Substitutions require maximum height/envelope review. Solder lift remains an assembly assumption.'))
# PH4 body uses existing nominal manufacturer-derived envelope.
screen=json.loads((H/'mechanical/current/screen_envelope_review.json').read_text())
f=next(v for v in screen['known_component_bodies'] if v['reference']=='JH2');x0,y0,x1,y1=f['body_xy_bounds_mm'];obstacles.append(dict(ref='JH2',box=[x0,y0,0,x1,y1,f['height_mm']],scope='Existing nominal PH4 body envelope; plug/wires excluded.'))
def sweep(q):
 W,B=q['outline_mm'];my=q['connector_centers_flat_mm']['JF1'][1];fy=q['connector_centers_flat_mm']['JF2'][1];a,c=q['bend_interval_flat_y_mm'];r=q['U_fold_neutral_radius_mm'];v=q['vertical_centerline_section_mm'];half=q['finished_fpc_thickness_mm']/2;neck=q['neck_width_mm'];cx,cy=center;z0=.8+half;straight=q['straight_center_to_bend_mm']
 def point(t):
  if t<a:y=t-my;z=z0;theta=0
  elif t<a+math.pi*r/2:theta=(t-a)/r;y=straight+r*math.sin(theta);z=z0+r*(1-math.cos(theta))
  elif t<a+math.pi*r/2+v:theta=math.pi/2;y=straight+r;z=z0+r+t-a-math.pi*r/2
  elif t<c:theta=math.pi/2+(t-a-math.pi*r/2-v)/r;y=straight+r*math.sin(theta);z=z0+r+v-r*math.cos(theta)
  else:theta=math.pi;y=fy-t;z=z0+2*r+v
  # Beveled transition from the same offsets used in native Edge.Cuts.
  t0,t1=q.get('end_taper_offsets_from_connector_mm',[1.8,2.3]);e=min(t-my,fy-t);mix=min(1,max(0,(e-t0)/(t1-t0)));w=W*(1-mix)+neck*mix
  stiff=.2 if abs(t-my)<=1.5 or abs(t-fy)<=1.5 else 0
  pts=[(cx+sgn*w/2,cy+y-off*math.sin(theta),z+off*math.cos(theta)) for sgn in [-1,1] for off in [-half,half+stiff]]
  return pts
 def bbox(pts):return [min(v[i] for v in pts) for i in range(3)]+[max(v[i] for v in pts) for i in range(3)]
 n=math.ceil(B/.002);out=[];prev=point(0)
 for i in range(1,n+1):
  nxt=point(B*i/n);bb=bbox(prev+nxt);out.append(bb);prev=nxt
 # Nominal connector body boxes, excluding the intentional J2002 mating pair.
 # Both parts are B-mounted, which points down at the lower end and up after fold.
 cx,cy=center;gap=q['connector_mounting_plane_separation_target_mm']
 out.extend([[cx-3.3,cy-1,.8-.65,cx+3.3,cy+1,.8],[cx-3.65,cy-1.25,gap-.8,cx+3.65,cy+1.25,gap-.8+.77]])
 return out
def dist(a,b):return math.sqrt(sum(max(b[i]-a[i+3],a[i]-b[i+3],0)**2 for i in range(3)))
def check(q):
 cells=sweep(q);rows=[]
 for ob in obstacles:
  pairs=[(cell,bb) for cell in cells for bb in ob.get('boxes',[ob['box']])];cell,bb=min(pairs,key=lambda pair:dist(*pair));rows.append(dict(**ob,minimum_nominal_box_distance_mm=dist(cell,bb),nearest_fpc_cell=cell,nearest_obstacle_box=bb))
 # HOST begins at y49.05; minimum Y-only separation is a conservative lower bound
 return dict(neighbors=rows,fpc_swept_bounds=[min(c[i] for c in cells) for i in range(3)]+[max(c[i+3] for c in cells) for i in range(3)],host_y_only_separation_lower_bound_mm=49.05-max(c[4] for c in cells))
result=check(q);report=dict(status='CONDITIONAL_NOMINAL_SPACE_SCREEN_NOT_ASSEMBLY_RELEASE',design_contract_sha256=hashlib.sha256((D/'review/design_contract.json').read_bytes()).hexdigest(),digital_pcb_sha256=hashlib.sha256((H/'digital/YuEEG_H_DIGITAL.kicad_pcb').read_bytes()).hexdigest(),fpc_pcb_sha256=hashlib.sha256((D/'YuEEG_H_DISPLAY_LINK.kicad_pcb').read_bytes()).hexdigest(),neighbor_native_sha256=hashlib.sha256((D/'review/neighbor_native.json').read_bytes()).hexdigest(),sampling_step_max_mm=.002,model='Swept substrate, proposed .20 mm F-side end stiffeners and nominal connector body boxes; intentional mate excluded. Segment AABBs conservative for each interval, with curve chord approximation below .000001 mm; no overall manufacturing/assembly tolerance approval.',**result,scope='Only listed obstacles. A small distance to a conservative full lead-height box is a design risk, not proof of actual package collision. Screen back, factory FPC, solder and all other obstacles remain unverified.')
out=D/'review/fold_space.json';out.write_text(json.dumps(report,indent=2));print([(v['ref'],round(v['minimum_nominal_box_distance_mm'],4)) for v in result['neighbors']]);print('HOST Y-only separation',result['host_y_only_separation_lower_bound_mm'])
