"""Native FPC copper/edge, gang-coverlay and stiffener geometry screening.

Checks the nominal artwork, not laser/lamination tolerances, approved layer
stack, bending life, connector mating or the unknown factory screen-back Z.
"""
from pathlib import Path
import hashlib
import json
import math
import sys
import pcbnew as p
import wx

wx.DisableAsserts()
H = Path('hardware/YuEEG_8CH_RevH_Stack'); D = H/'display_link'; R = D/'review'
pcb = D/'YuEEG_H_DISPLAY_LINK.kicad_pcb'; pro = pcb.with_suffix('.kicad_pro'); rules = pcb.with_suffix('.kicad_dru')
sha = lambda f: hashlib.sha256(f.read_bytes()).hexdigest()
board = p.LoadBoard(str(pcb)); contract = json.loads((R/'design_contract.json').read_text())
project = json.loads(pro.read_text())
assert project['board']['design_settings']['rules']['min_copper_edge_clearance'] == .3
assert "A.Type == 'Pad' || B.Type == 'Pad'" in rules.read_text() and '(min 0.15mm)' in rules.read_text()
assert abs(p.ToMM(board.GetDesignSettings().GetBoardThickness())-.11) < 1e-8
def xy(v): return (p.ToMM(v.x), p.ToMM(v.y))
def cross(a,b): return a[0]*b[1]-a[1]*b[0]
def subtract(a,b): return (a[0]-b[0],a[1]-b[1])
def point_segment(point,a,b):
    dx,dy=subtract(b,a);length2=dx*dx+dy*dy
    t=max(0,min(1,((point[0]-a[0])*dx+(point[1]-a[1])*dy)/length2)) if length2 else 0
    return math.hypot(point[0]-a[0]-t*dx,point[1]-a[1]-t*dy)
def segment_gap(a,b,c,d):
    ab=subtract(b,a);cd=subtract(d,c);delta=subtract(c,a);den=cross(ab,cd)
    if abs(den)>1e-12 and 0<=cross(delta,cd)/den<=1 and 0<=cross(delta,ab)/den<=1:return 0.
    return min(point_segment(a,c,d),point_segment(b,c,d),point_segment(c,a,b),point_segment(d,a,b))
edges=[(xy(g.GetStart()),xy(g.GetEnd())) for g in board.GetDrawings() if g.GetLayer()==p.Edge_Cuts]
assert len(edges)==12
W,B=contract['outline_mm'];my=contract['connector_centers_flat_mm']['JF1'][1];fy=contract['connector_centers_flat_mm']['JF2'][1]
lo=(W-contract['neck_width_mm'])/2;hi=W-lo
lt0,lt1=contract['end_taper_offsets_by_connector_mm']['JF1'];ut0,ut1=contract['end_taper_offsets_by_connector_mm']['JF2']
outline=[(0,0),(W,0),(W,my+lt0),(hi,my+lt1),(hi,fy-ut1),(W,fy-ut0),(W,B),(0,B),(0,fy-ut0),(lo,fy-ut1),(lo,my+lt1),(0,my+lt0),(0,0)]
normal=lambda a,b:tuple(sorted([tuple(round(v,5) for v in a),tuple(round(v,5) for v in b)]))
assert sorted(normal(a,b) for a,b in edges)==sorted(normal(a,b) for a,b in zip(outline,outline[1:])), 'Native outline differs from folded-space model'
pad_rows=[];coverlay_rows=[]
for fp in board.GetFootprints():
    windows=[g for g in fp.GraphicalItems() if g.GetLayer()==p.B_Mask and g.GetShape()==p.SHAPE_T_RECT]
    assert fp.GetLayer()==p.B_Cu and len(windows)==1
    window=windows[0];s,e=xy(window.GetStart()),xy(window.GetEnd());bb=[min(s[0],e[0]),min(s[1],e[1]),max(s[0],e[0]),max(s[1],e[1])]
    margins=[]
    for pad in fp.Pads():
        assert pad.GetShape()==p.PAD_SHAPE_RECT
        x,y=xy(pad.GetPosition());w,h=xy(pad.GetSize());angle=math.radians(pad.GetOrientationDegrees())
        corners=[(x+a*math.cos(angle)-b*math.sin(angle),y+a*math.sin(angle)+b*math.cos(angle)) for a,b in [(-w/2,-h/2),(w/2,-h/2),(w/2,h/2),(-w/2,h/2)]]
        gap=min(segment_gap(a,b,c,d) for a,b in zip(corners,corners[1:]+corners[:1]) for c,d in edges)
        assert gap>=.29999,(fp.GetReference(),pad.GetNumber(),gap)
        pad_rows.append({'pin':fp.GetReference()+'.'+pad.GetNumber(),'net':pad.GetNetname(),'edge_gap_mm':gap})
        margins.append(min(min(a-bb[0],b-bb[1],bb[2]-a,bb[3]-b) for a,b in corners))
    assert min(margins)>=.09999
    coverlay_rows.append({'connector':fp.GetReference(),'window_flat_xy_mm':bb,'minimum_nominal_pad_expansion_mm':min(margins),'single_gang_rectangle':True})
assert len(pad_rows)==56
copper_rows=[]
for item in board.GetTracks():
    if isinstance(item,p.PCB_VIA):
        a=xy(item.GetPosition());gap=min(point_segment(a,c,d) for c,d in edges)-p.ToMM(item.GetWidth(p.F_Cu))/2;kind='via'
    else:
        a,b=xy(item.GetStart()),xy(item.GetEnd());gap=min(segment_gap(a,b,c,d) for c,d in edges)-p.ToMM(item.GetWidth())/2;kind='track'
    assert gap>=.29999,(item.m_Uuid.AsString(),kind,gap)
    copper_rows.append({'uuid':item.m_Uuid.AsString(),'net':item.GetNetname(),'kind':kind,'edge_gap_mm':gap})
stiffeners=[];notes=[]
for g in board.GetDrawings():
    if g.GetLayer()==p.F_Adhes:
        assert g.GetShape()==p.SHAPE_T_RECT and g.IsFilled() and p.ToMM(g.GetWidth())==0
        s,e=xy(g.GetStart()),xy(g.GetEnd());stiffeners.append({'flat_xy_bounds_mm':[min(s[0],e[0]),min(s[1],e[1]),max(s[0],e[0]),max(s[1],e[1])],'filled':g.IsFilled(),'stroke_width_mm':p.ToMM(g.GetWidth())})
    if g.GetLayer()==p.Cmts_User and isinstance(g,p.PCB_TEXT):notes.append(g.GetText())
assert len(stiffeners)==2 and any('PI FLEX' in n for n in notes) and any('fab approval pending' in n for n in notes)
for actual,expected in zip(sorted(r['flat_xy_bounds_mm'] for r in stiffeners),sorted([[.2,my-1.5,W-.2,my+1.5],[.2,fy-1.5,W-.2,fy+1.5]])):
    assert all(abs(a-b)<.000002 for a,b in zip(actual,expected)), 'Native stiffener differs from folded-space envelope'
for zone in board.Zones():
    if not zone.GetIsRuleArea():assert abs(p.ToMM(zone.GetLocalClearance())-.15)<1e-8
sys.path.insert(0,str(Path('hardware/YuEEG_8CH_RevG/review').resolve()))
from sexpr_io import loads,sub
tree=loads(pcb.read_text());native_stack=sub(sub(tree,'setup'),'stackup')
assert native_stack is None, 'An actual per-layer stack was added; review its accepted material specification before changing this scope'
record={'status':'PASS_NOMINAL_FPC_FAB_GEOMETRY_NOT_PROCESS_OR_ASSEMBLY_RELEASE',
    'pcb_sha256':sha(pcb),'project_sha256':sha(pro),'rules_sha256':sha(rules),'contract_sha256':sha(R/'design_contract.json'),'checker_sha256':sha(Path(__file__)),
    'reference_capabilities':'https://jlcpcb.com/capabilities/flex-pcb-capabilities',
    'minimum_copper_edge_constraint_mm':.3,'minimum_exposed_pad_other_net_copper_constraint_mm':.15,
    'minimum_pad_edge_gap_mm':min(r['edge_gap_mm'] for r in pad_rows),'minimum_track_via_edge_gap_mm':min(r['edge_gap_mm'] for r in copper_rows),
    'all56_rectangular_SMD_pads':pad_rows,'all_tracks_and_vias':copper_rows,'B_coverlay_gang_windows':coverlay_rows,'F_PI_stiffener_regions':stiffeners,'native_fabrication_notes':notes,
    'native_per_layer_stack_approved':False,'native_numeric_per_layer_stack_present':False,
    'finished_thickness_nominal_mm':.11,'core_PI_target_mm':.025,'base_copper_target_mm_per_side':.012,'F_PI_stiffener_target_mm':.2,
    'scope':'Native12 straight outline segments, all56 rectangular pads and every track/via checked analytically to outline centerlines; minimum planes/pad-other-net copper covered by separate native DRC/custom rule. Two zero-stroke filled F-side stiffener regions and B-side gang windows measured. PI targets are declared in native comments, not invented per-layer laminate values. Actual coverlay/adhesive/plating, laser/stiffener tolerances, advanced vias, assembly and screen-back datum remain unqualified.'}
(R/'fab_geometry.json').write_text(json.dumps(record,indent=2),encoding='utf8')
print('PASS native FPC geometry: min pad/edge',round(record['minimum_pad_edge_gap_mm'],6),'track/via/edge',round(record['minimum_track_via_edge_gap_mm'],6),'mm; gang windows and2 filled PI stiffener regions')
