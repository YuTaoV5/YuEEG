"""Screen a complete nominal PH4-to-PH4 wire route in the product frame.

Source PCBs are read-only. The two exit datums and wire properties remain
explicit assumptions; this report cannot release the physical cable assembly.
"""
from pathlib import Path
import hashlib
import json
import math
import re
import sys
import numpy as np
from scipy.spatial import cKDTree

H = Path('hardware/YuEEG_8CH_RevH_Stack')
M = H / 'mechanical/current'
sys.path.insert(0, str((H / 'review/devtools').resolve()))
from check_h_display_fold_space import sweep, q

sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
ports = json.loads((M / 'power_ports_native.json').read_text())
pogo = json.loads((M / 'pogo_assembly_review.json').read_text())
contract = json.loads((H / 'review/interboard_contract.json').read_text())
assert ports['power']['rotation_deg'] % 360 == 270 and ports['power']['xy_mm'] == [7.5, 11.4]
assert contract['nominal_pcb_clear_gap_mm'] == 8.5
pose = pogo['proposed_product_pose']
assert pose['power_pcb_x_mm'] == [49.95, 83.95] and pose['power_pcb_z_mm'] == [-1.4, 16.6]
assert pose['power_F_y_mm'] == -4.05
# Product frame: AFE F=0; digital B=8.5 and F=10.1. Power PCB F
# maps (u,v,w) to (49.95+u, -4.05-w, 16.6-v).
def thickness(board):
    text = (H / board / ('YuEEG_H_'+board.upper()+'.kicad_pcb')).read_text()
    match = re.search(r'\(general\s+\(thickness\s+([0-9.]+)\)', text)
    assert match
    return float(match[1])
digital_F = contract['nominal_pcb_clear_gap_mm'] + thickness('digital')
assert digital_F == 10.1
od = 1.1
radius = 3.3
ds = .02
exit_axis_height = 2.75  # assumed at both connectors, not catalogued
main_z = digital_F + exit_axis_height
power_exit_y = pose['power_F_y_mm'] - exit_axis_height
# Catalog p4 central body length 6 mm, footprint central rear local Y=-1.6.
# Catalog p2 mated length 9.6 mm from that rear gives local exit Y=+8.0.
# Rotation270 points toward PCB-X; native pad row Y maps to product Z.
power_exit_x = pose['power_pcb_x_mm'][0]+ports['power']['xy_mm'][0]-(-1.6+9.6)
straight_at_power = 2.2  # proposed free straight length; not a JST requirement

def line(a, b):
    return {'type': 'line', 'a': list(a), 'b': list(b)}

def sample(s):
    typ = s['type']
    if typ == 'line':
        a, b = np.array(s['a']), np.array(s['b'])
        n = max(2, math.ceil(np.linalg.norm(b-a)/ds)+1)
        return np.linspace(a, b, n)
    if typ == 'blend_y':
        a, b = np.array(s['a']), np.array(s['b'])
        delta = b-a
        # The only non-Y coordinate follows a cubic smoothstep. This upper
        # bound on speed makes adjacent samples <=ds apart.
        n = math.ceil((abs(delta[1])+1.5*np.linalg.norm(delta[[0,2]]))/ds)+1
        t = np.linspace(0, 1, n)
        v = np.tile(a, (n,1)) + (3*t*t-2*t*t*t)[:,None]*delta
        v[:,1] = a[1]+t*delta[1]
        return v
    n = math.ceil(s['radius_mm']*math.pi/2/ds)+1
    t = np.linspace(0, math.pi/2, n)
    a = np.array(s['a']); r = s['radius_mm'];v = np.tile(a, (n,1))
    if typ == 'xy_right_to_forward':
        v[:,0] += r*np.sin(t); v[:,1] -= r*(1-np.cos(t))
    elif typ == 'xy_forward_to_right':
        v[:,0] += r*(1-np.cos(t)); v[:,1] -= r*np.sin(t)
    elif typ == 'xz_right_to_down':
        v[:,0] += r*np.sin(t); v[:,2] -= r*(1-np.cos(t))
    elif typ == 'yz_forward_to_down':
        v[:,1] -= r*np.sin(t); v[:,2] -= r*(1-np.cos(t))
    elif typ == 'xz_down_to_right':
        v[:,2] -= r*np.sin(t); v[:,0] += r*(1-np.cos(t))
    else:
        raise ValueError(typ)
    return v

def box_gap(points, bb):
    v = np.maximum(np.maximum(np.array(bb[:3])-points, points-np.array(bb[3:])), 0)
    return float(np.linalg.norm(v,axis=1).min()) - od/2 - ds/2

wires = []
all_points = []
for n in range(1,5):
    pin = str(n); main = ports['digital']['pads'][pin]; end = ports['power']['pads'][pin]
    assert main['net'] == end['net']
    py = main['xy_mm'][1]; x0 = ports['digital']['xy_mm'][0]-1.35+9.6
    channel_x = 53.95-(n-1)*1.6
    end_x = power_exit_x
    power_exit_z = pose['power_pcb_z_mm'][1]-end['xy_mm'][1]
    # Concentric XZ arcs remain separated by the 2mm contact pitch.
    r_xz = radius+(n-1)*2.
    high_z = power_exit_z+r_xz+radius
    front_x = end_x-straight_at_power-r_xz
    arc_y = power_exit_y+radius
    seg = [line([x0,py,main_z],[channel_x-radius,py,main_z]),
           {'type':'xy_right_to_forward','a':[channel_x-radius,py,main_z],'radius_mm':radius},
           line([channel_x,py-radius,main_z],[channel_x,28.5,main_z]),
           {'type':'blend_y','a':[channel_x,28.5,main_z],'b':[front_x,8.5,high_z]},
           line([front_x,8.5,high_z],[front_x,arc_y,high_z]),
           {'type':'yz_forward_to_down','a':[front_x,arc_y,high_z],'radius_mm':radius},
           {'type':'xz_down_to_right','a':[front_x,power_exit_y,high_z-radius],'radius_mm':r_xz},
           line([end_x-straight_at_power,power_exit_y,power_exit_z],[end_x,power_exit_y,power_exit_z])]
    chunks = [sample(s) for s in seg]
    assert all(np.linalg.norm(a[-1]-b[0]) < 1e-9 for a,b in zip(chunks,chunks[1:]))
    pts = np.concatenate([chunks[0]]+[v[1:] for v in chunks[1:]])
    assert np.linalg.norm(pts[-1]-[end_x,power_exit_y,power_exit_z]) < 1e-8
    assert np.linalg.norm(pts[0]-[x0,py,main_z]) < 1e-8
    assert np.max(np.linalg.norm(np.diff(pts,axis=0),axis=1)) <= ds*1.00001
    # Cubic blend curvature <=6*transverse displacement/longitudinal length^2.
    blend_R = [abs(s['b'][1]-s['a'][1])**2/(6*np.linalg.norm((np.array(s['b'])-s['a'])[[0,2]])) for s in seg if s['type']=='blend_y']
    assert min(blend_R) >= radius
    all_points.append(pts)
    wires.append({'pin':pin,'net':main['net'],'segments':seg,'start_product_xyz_mm':pts[0].tolist(),
                  'end_product_xyz_mm':pts[-1].tolist(),'centerline_length_mm':float(np.linalg.norm(np.diff(pts,axis=0),axis=1).sum()),
                  'minimum_centerline_bend_radius_lower_bound_mm':min(radius,r_xz,*blend_R),
                  'wire_tube_bounds_product_mm':np.r_[pts.min(axis=0)-od/2,pts.max(axis=0)+od/2].tolist()})

pair_clearances = []
for i in range(4):
    for j in range(i):
        d = float(cKDTree(all_points[i]).query(all_points[j],k=1)[0].min())
        # Each actual curve point is within <=ds/2 of a sampled point.
        # Two curves therefore require subtracting ds in addition to OD.
        pair_clearances.append({'pins':[str(j+1),str(i+1)],'sampled_axis_distance_mm':d,'tube_gap_lower_bound_mm':d-od-ds})

flat = np.concatenate(all_points)
board_boxes = {'AFE_substrate':[0,0,-thickness('afe'),48,60,0],
               'digital_substrate':[0,0,8.5,48,60,digital_F],
               'power_substrate':[49.95,-4.05,-1.4,83.95,-3.05,16.6],
               'battery_nominal':[55,0,8.7,84.9,42.7,17.9],
               'conditional_flat_screen_6mm':[6,.4,16.1,40.14,43.14,18.88]}
obstacles = {k:{'box_product_mm':bb,'wire_tube_gap_lower_bound_mm':box_gap(flat,bb)} for k,bb in board_boxes.items()}
fixing = []
for xy in [[44,4],[44,51],[4,55]]:
    radial=np.maximum(np.linalg.norm(flat[:,:2]-xy,axis=1)-2.1,0)
    vertical=np.maximum(np.maximum(-1.6-flat[:,2],flat[:,2]-(digital_F+2.0)),0)
    d=float(np.hypot(radial,vertical).min())
    fixing.append({'xy_mm':xy,'cylinder_diameter_budget_mm':4.2,'z_bounds_product_mm':[-1.6,digital_F+2.0],'finite_cylinder_wire_gap_lower_bound_mm':d-od/2-ds/2})
fpc = np.array(sweep(q)); fpc[:,[2,5]] += digital_F
best = 1e9
for pts in all_points:
    for chunk in np.array_split(pts,24):
        v = np.maximum(np.maximum(fpc[None,:,:3]-chunk[:,None,:],chunk[:,None,:]-fpc[None,:,3:]),0)
        best = min(best,float(np.linalg.norm(v,axis=2).min())-od/2-ds/2)

assert min(r['tube_gap_lower_bound_mm'] for r in pair_clearances) > 0
assert min(v['wire_tube_gap_lower_bound_mm'] for v in obstacles.values()) > 0
assert min(v['finite_cylinder_wire_gap_lower_bound_mm'] for v in fixing) > 0
assert best > 0
report = {
    'status':'COMPLETE_NOMINAL_ENDPOINT_ROUTE_NOT_QUALIFIED_HARNESS',
    'source_sha256':{p.name:sha(p) for p in [M/'power_ports_native.json',M/'pogo_assembly_review.json',H/'review/interboard_contract.json',H/'display_link/review/design_contract.json']},
    'source_code_sha256':{name:sha(H/'review/devtools'/name) for name in ['review_h_complete_power_harness.py','check_h_display_fold_space.py']},
    'catalog':'https://www.jst-mfg.com/product/pdf/eng/ePH.pdf','catalog_reference_pages':[1,2,3,4],
    'product_frame':{'AFE_F_z_mm':0.,'digital_B_z_mm':8.5,'digital_F_z_mm':digital_F,'power_transform':'X=49.95+PCB_X; Y=-4.05-PCB_local_Z; Z=16.6-PCB_Y; local_Z positive away from F'},
    'assumptions':{'wire_AWG':24,'wire_OD_max_mm':od,'wire_axis_height_from_connector_board_F_mm':exit_axis_height,
                   'axis_height_status':'Assumed; not supplied as a dimensional datum by catalog.',
                   'minimum_centerline_radius_target_mm':radius,'allowed_wire_bend_radius_qualified':False,
                   'straight_free_wire_at_power_exit_mm':straight_at_power,'straight_length_status':'Proposed, not a catalog requirement or a qualified strain relief.',
                   'power_mated_exit_local_Y_mm':8.,'power_exit_datum_status':'Nominal derivation from catalog central header rear,6mm body and9.6mm mated length; rotation270 maps local exit to PCB-X. Not a toleranced assembly drawing.',
                   'fixing_head_maximum_projection_above_digital_F_mm':2.0,'fixing_maximum_diameter_budget_mm':4.2,
                   'fixing_head_source':'Essentra drawing10294789,50M020040P008: head diameter3.70..4.00mm,height1.40..1.60mm. Budget adds assembly allowance; screw length/spacer/torque unqualified. No upper screen pillar above this head budget.',
                   'fixing_drawing_sha256':'221c3b9ba8b3b4335441d8e5b2a493f668961dfe1db8912ba1d210596a000bf1',
                   'fixing_drawing_url':'https://storacesswebpraisstibprd.blob.core.windows.net/stiboassets/D365_DOCS_PDF/std.lang.all/D365_DOCS_PDF!10294789_Technical%20Drawing.pdf',
                   'conditional_screen_back_gap_mm':6.,'factory_screen_back_Z_qualified':False,
                   'terminal_insertion_depths_and_cut_lengths_qualified':False},
    'sampling_max_axis_step_mm':ds,'distance_bound_method':'Point-to-box minus OD/2 and ds/2; wire pairs minus OD and ds. Polyline sampling of specified analytic curves only, not tolerance or collision-kernel validation.',
    'wires':wires,'wire_pair_clearances':pair_clearances,'obstacles_checked':obstacles,
    'selected_extension_FPC_tube_gap_lower_bound_mm':best,'finite_fixing_cylinder_screens':fixing,
    'route_tube_union_bounds_product_mm':np.r_[flat.min(axis=0)-od/2,flat.max(axis=0)+od/2].tolist(),
    'power_mated_reference_envelope_product_mm':[49.45,-9.55,-.75,60.65,-4.05,11.15],
    'former_upper_exit_route_reference':{'git_commit':'21618f34c2ccfb7e3641fe9aaab040dd30c9e255','wire_max_product_Z_mm':24.95,'reference_only_not_current':True},
    'power_front_nonconnector_component_height_allowance_at_wire_axis_mm':exit_axis_height-od/2,
    'open_items':['Exact crimped-wire exit axes and tolerances at both headers','Qualified wire OD, allowable static bend radius and stripped/inserted terminal lengths','Tie-downs and strain relief outside each modeled free-wire segment','All actual component, screen-back/FPC, enclosure, RF, metal and dielectric geometries','Delivered battery/model agreement and holder stops/retention','Complete system clearance/creepage, contact heating and concurrent EEG noise validation'],
    'scope':'A full nominal route reaches all four same-number wires after side-port adoption. Substrate/battery boxes,selected flex,wire pairs,bounded fixing cylinders and a conditional6mm flat screen-back scenario only. The latter is not the factory folded-screen datum. Does not establish exact delivered connector geometry,full SMT/holder geometry,RF/noise performance or assembly release. Lengths exclude terminal insertion and are not cut lengths.',
}
(M/'complete_power_harness_review.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print('Full route lengths mm:',[round(v['centerline_length_mm'],2) for v in wires])
print('Minimum wire pair gap lower bound mm:',min(v['tube_gap_lower_bound_mm'] for v in pair_clearances))
print('Wire tube bounds:',report['route_tube_union_bounds_product_mm'])
print('FPC gap lower bound:',best,'mm; all checked nominal obstacle gaps positive.')

if __name__ == '__main__':
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    from matplotlib.patches import Rectangle
    fig=plt.figure(figsize=(15,9));ax=fig.add_subplot(121,projection='3d');top=fig.add_subplot(222);front=fig.add_subplot(224)
    def box(bb,color):
        x,y,z,X,Y,Z=bb;v=[(x,y,z),(X,y,z),(X,Y,z),(x,Y,z),(x,y,Z),(X,y,Z),(X,Y,Z),(x,Y,Z)]
        ids=[[0,1,2,3],[4,5,6,7],[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7]]
        ax.add_collection3d(Poly3DCollection([[v[i] for i in face] for face in ids],facecolor=color,edgecolor=color,alpha=.14,linewidth=.6))
    for (name,bb),col in zip(board_boxes.items(),['#4c8b70','#426e98','#be974e','#73a67d']):box(bb,col)
    box(report['power_mated_reference_envelope_product_mm'],'#ac894b')
    colors=['#bb4840','#bd9028','#347ca4','#7451a1']
    for w,pts,c in zip(wires,all_points,colors):
        z=pts[::10];ax.plot(*z.T,color=c,lw=1.8,label=w['pin']+': '+w['net']);top.plot(z[:,0],z[:,1],color=c,lw=1.4);front.plot(z[:,0],z[:,2],color=c,lw=1.4)
        ax.scatter(*pts[-1],color=c,s=15)
    top.add_patch(Rectangle((49.95,-4.05),34,1,facecolor='#be974e',alpha=.5));top.add_patch(Rectangle((55,0),29.9,42.7,facecolor='#73a67d',alpha=.12));top.add_patch(Rectangle((0,0),48,60,facecolor='#426e98',alpha=.08))
    front.add_patch(Rectangle((49.95,-1.4),34,18,facecolor='#be974e',alpha=.13));front.add_patch(Rectangle((55,8.7),29.9,9.2,facecolor='#73a67d',alpha=.13))
    ax.set(xlim=(-1,85),ylim=(-12,61),zlim=(-2,28),xlabel='Product X / mm',ylabel='Product Y / mm',zlabel='Product Z / mm',title='Full nominal wire route to the vertical power strip')
    ax.set_box_aspect((86,73,30));ax.view_init(25,-65);ax.legend(loc='upper left',fontsize=8)
    top.set(xlim=(33,85),ylim=(42,-12),xlabel='X / mm',ylabel='Y / mm',title='Top: front return reaches strip');top.set_aspect('equal');top.grid(alpha=.15)
    front.set(xlim=(33,85),ylim=(-2,22),xlabel='X / mm',ylabel='Z / mm',title='Front: concentric bends to the side-facing port');front.set_aspect('equal');front.grid(alpha=.15)
    fig.suptitle('Engineering route only: assumed exit axes, wire bend capability and strain relief remain unqualified',fontsize=12)
    fig.text(.02,.02,'Solid curves: four wire centerlines. Translucent boxes: nominal substrates / battery / power mate. Screen and full component geometry omitted.\nCenterline lengths exclude terminal insertion; do not use as cut lengths or an assembly/manufacturing release.',fontsize=10)
    fig.tight_layout(rect=[0,.065,1,.95]);top.set_position([.60,.56,.37,.35]);front.set_position([.54,.13,.43,.30]);fig.savefig(M/'complete_power_harness_review.png',dpi=160);fig.savefig(M/'complete_power_harness_review.svg')
