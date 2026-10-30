"""Conditional geometric screen. Bounds do not substitute for an actual flex sample."""
from pathlib import Path
import json,math,hashlib,html,pcbnew as p,wx
wx.DisableAsserts();R=Path('hardware/YuEEG_8CH_RevH_Stack');D=R/'mechanical/current';D.mkdir(parents=True,exist_ok=True)
path=R/'digital/YuEEG_H_DIGITAL.kicad_pcb';b=p.LoadBoard(str(path));fs={f.GetReference():f for f in b.GetFootprints()}
data=json.loads((R/'review/component_envelopes.json').read_text());models={q['model']:q for q in data['models']};screen=[6,.4,40.14,43.14];backgap=6.;hits=[]
for bind in data['bindings']:
 if bind['board']!='digital':continue
 if bind['model'] not in models:continue
 f=fs[bind['reference']];angle=math.radians(f.GetOrientationDegrees());x,y=[p.ToMM(q) for q in [f.GetPosition().x,f.GetPosition().y]]
 for box in models[bind['model']]['boxes_footprint_mm']:
  lo,hi=box['min'],box['max'];pts=[(x+xx*math.cos(angle)+yy*math.sin(angle),y-xx*math.sin(angle)+yy*math.cos(angle)) for xx in [lo[0],hi[0]] for yy in [lo[1],hi[1]]]
  bb=[min(q[0] for q in pts),min(q[1] for q in pts),max(q[0] for q in pts),max(q[1] for q in pts)]
  overlap=bb[0]<screen[2] and bb[2]>screen[0] and bb[1]<screen[3] and bb[3]>screen[1]
  hits.append({'reference':bind['reference'],'body_xy_bounds_mm':bb,'height_mm':hi[2],'under_screen_projection':overlap,'nominal_vertical_margin_to_flat_back_at_6mm':backgap-hi[2] if overlap else None})
host=49.05;dy=host-screen[3];flat=math.hypot(dy,backgap)
# Conservative scenario, not assertion that conductor occupies this corner:
# folded drawing .80 max beyond lower edge; component stack allowance 1.20.
tail_extra=.8;tail_down=1.2;dyflex=dy-tail_extra;flex=math.hypot(dyflex,backgap-tail_down);needed=math.sqrt(8**2-dyflex**2)+tail_down
report={'pcb_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'screen_projection_mm':screen,'candidate_screen_back_gap_mm':backgap,'known_component_bodies':hits,'isolated_host_y_min_mm':host,'flat_back_to_host_envelope_distance_mm':flat,'conservative_flex_scenario':{'extension_beyond_bottom_mm':tail_extra,'downward_component_allowance_mm':tail_down,'nearest_corner_distance_at_6mm':flex,'screen_back_gap_needed_for_8mm_corner_distance_mm':needed,'interpretation':'Bounding scenario only; does not prove an actual conductor violates clearance. Actual folded FPC copper/component positions and height require verification.'},'fpc_reach_status':'UNPROVEN: factory folded/taped FPC cannot be assumed to bridge 6mm support gap to .8mm mating connector. Extension or a verified refold/raised socket solution is required.','complete_assembly_status':'NOT VERIFIED; this report covers selected sourced component envelopes, not all parts/tolerances/cables/creepage.'}
(D/'screen_envelope_review.json').write_text(json.dumps(report,indent=2))
S=8;ox,oy=70,65
def rect(bb,fill,stroke,extra=''):
 x0,y0,x1,y1=bb;return f'<rect x="{ox+x0*S}" y="{oy+y0*S}" width="{(x1-x0)*S}" height="{(y1-y0)*S}" fill="{fill}" stroke="{stroke}" {extra}/>'
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="650" viewBox="0 0 1100 650"><rect width="1100" height="650" fill="#f4f5f7"/><g font-family="Arial, sans-serif" fill="#17212e">','<text x="40" y="30" font-size="20">Rev H screen / digital board envelope review</text>','<text x="40" y="50" font-size="12">DEVELOPMENT — conditional dimensions; FPC reach and assembly remain unverified</text>',rect([0,0,48,60],'#d8e9e0','#254e3b','rx="16"'),rect([0,40.55,48,49.05],'#f4dbc4','#be803e'),rect([0,49.05,48,60],'#dcd5e9','#7e65a6'),rect(screen,'#8cc5e0','#187fb1','fill-opacity=".24" stroke-width="2"')]
for q in hits:
 col='#aa503d' if q['reference']=='JH2' else '#586e83';svg.append(rect(q['body_xy_bounds_mm'],'none',col))
for ref in ['H1','H2','H3']:
 if ref not in fs:continue
 f=fs[ref];x,y=p.ToMM(f.GetPosition().x),p.ToMM(f.GetPosition().y)
 svg.append(f'<circle cx="{ox+x*S}" cy="{oy+y*S}" r="{1.2*S}" fill="#f4f5f7" stroke="#52616a"/><text x="{ox+x*S+12}" y="{oy+y*S+4}" font-size="10">{ref}</text>')
for ref in ['JH2','J2002','J1101','SW301','SW302','SW1001','U2','JH1','J601']:
 f=fs[ref];x,y=p.ToMM(f.GetPosition().x),p.ToMM(f.GetPosition().y);svg.append(f'<circle cx="{ox+x*S}" cy="{oy+y*S}" r="3" fill="#263e55"/><text x="{ox+x*S+5}" y="{oy+y*S-5}" font-size="11">{html.escape(ref)}</text>')
lines=['Digital / AFE common outline: 48 x 60 mm','Screen outer: 34.14 x 42.74 mm','JH2 PH4 body height: 5.5 mm','At 6 mm flat-back gap: only 0.5 mm above JH2','','Flat screen back to HOST envelope: '+f'{flat:.2f} mm','Conservative folded-flex corner scenario: '+f'{flex:.2f} mm','For an 8 mm corner target: back gap >= '+f'{needed:.2f} mm','','The flex corner is an assumed bounding scenario,','not a measured conductor or a clearance failure.','','Factory FPC is folded/taped to screen back.','Direct mating across the support gap is unproven.','Do not release enclosure or screen standoffs yet.','','Blue: screen projection','Orange: isolation corridor','Purple: USB host region','Red outline: PH4 connector under the screen']
for i,t in enumerate(lines):svg.append(f'<text x="510" y="{90+i*23}" font-size="15">{html.escape(t)}</text>')
svg.append('</g></svg>');(D/'screen_envelope_review.svg').write_text('\n'.join(svg),encoding='utf8')
print('Flat back distance',flat,'mm; conservative flex corner',flex,'mm; conditional required back gap',needed,'mm')
