"""Bind the two public JME drawing revisions to native footprints, without adopting a SKU.

2021 PCB LAYOUT labels the locator span C; its 20-contact table gives C=8.2.
This is an interpretation requiring supplier confirmation, not a qualified alternate.
"""
from pathlib import Path
import json, hashlib, math, pcbnew as p, wx
wx.DisableAsserts()
H=Path('hardware/YuEEG_8CH_RevH_Stack');R=H/'review'
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
current=[]
for name in ['JME_BTB0840_20MR_Logical','JME_BTB0845_20FR_Logical']:
 path=H/'footprints/YuEEG.pretty'/(name+'.kicad_mod');f=p.FootprintLoad(str(path.parent),name)
 pads=[q for q in f.Pads() if q.GetNumber()];holes=[q for q in f.Pads() if not q.GetNumber()]
 assert len(pads)==20 and len(holes)==2
 assert all(q.GetAttribute()==p.PAD_ATTRIB_SMD for q in pads)
 xy=sorted([[p.ToMM(q.GetPosition().x),p.ToMM(q.GetPosition().y)] for q in holes])
 sizes=sorted({(p.ToMM(q.GetSize().x),p.ToMM(q.GetSize().y)) for q in pads})
 assert sizes==[(.35,1.8)] and abs(xy[1][0]-xy[0][0]-9)<.00001
 current.append({'footprint':name,'sha256':sha(path),'pad_size_mm':sizes[0],'locator_xy_mm':xy,'locator_drill_mm':p.ToMM(holes[0].GetDrillSize().x)})
def hole_to_rect(hole,pad,drill,size):
 return math.hypot(max(abs(hole[0]-pad[0])-size[0]/2,0),max(abs(hole[1]-pad[1])-size[1]/2,0))-drill/2
cases=[]
for revision,span,size in [('2017_REV_B',9.,[.35,1.8]),('2021_REV_1P0_PCB_LAYOUT_C_INTERPRETATION',8.2,[.30,2.0])]:
 pad_centers=[(-3.6+.8*i,y) for i in range(10) for y in [-2,2]]
 holes=[(-span/2,1.25),(span/2,1.25)]
 gap=min(hole_to_rect(h,q,.65,size) for h in holes for q in pad_centers)
 cases.append({'drawing':revision,'locator_span_mm':span,'pad_size_mm':size,'pad_row_center_spacing_mm':4.,'nominal_hole_diameter_mm':.65,'minimum_nominal_locator_hole_to_pad_copper_mm':round(gap,6),'meets_current_0p25mm_hole_clearance':gap>=.25-1e-6})
out={'status':'PROCUREMENT_VERSION_CONFLICT_NOT_CLOSED','native_footprints':current,'cases':cases,'mated_height_both_drawings_mm':8.5,'2021_locator_shift_per_side_relative_to_current_mm':.4,'interpretation':'2021 PCB LAYOUT dimension C and table C=8.2 at20contacts; supplier must resolve intended locator/land pattern and confirm delivered variant. Current PCB follows the2017 drawing, not a qualified fit for these later catalog listings.','catalog_candidates':[{'mpn':'5001-BTB0840-20MR-00','catalog':'https://www.lcsc.com/product-detail/C48688647.html','datasheet':'https://datasheet.lcsc.com/datasheet/pdf/94afc7f6e0bd0ea03f46e9c7facf6f62.pdf?productCode=C48688647','pdf_sha256':'fd2a40523e53600771e5d597379b0e4a82d2a8c5ae6d9810d96853594f2ceb5e','pages':2,'drawing_date':'2021-07-08','qualified_drop_in':False},{'mpn':'5001-BTB0845-20FR-00-B','catalog':'https://jlcpcb.com/partdetail/JMEconn-5001_BTB0845_20FR_00B/C53277662','datasheet':'https://datasheet.lcsc.com/datasheet/pdf/c221b29b3e69466c70c42f83db0b10dd.pdf?productCode=C53277662','pdf_sha256':'8e92c3027caa1e2379a264a09367613ea36d3d541ed35253baebf3c6e02538f7','pages':2,'drawing_date':'2021-07-08','qualified_drop_in':False}],'taobao_qualified_sku':None,'scope':'Drawing revision comparison and a nominal circle/rectangle clearance calculation only. No statement of stock, exact delivery version, fit, manufacturing approval or acquisition validation.'}
(R/'smt_btb_procurement_revision_review.json').write_text(json.dumps(out,indent=2),encoding='utf8')
# Original diagram of factual dimensions; supplier drawings are linked, not copied.
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="470" viewBox="0 0 1000 470"><rect width="1000" height="470" fill="#f3f5f7"/><g font-family="Arial,sans-serif" fill="#17252e"><text x="30" y="32" font-size="20">Rev H SMT BTB: drawing revision comparison</text><text x="30" y="58" font-size="13">Procurement remains open. The 2021 C-dimension interpretation requires supplier confirmation.</text>']
for j,case in enumerate(cases):
 ox=260+480*j;oy=225;scale=32;span=case['locator_span_mm'];w,h=case['pad_size_mm']
 svg.append(f'<text x="{ox-205}" y="95" font-size="16">'+('2017 drawing / current footprint' if j==0 else '2021 PCB LAYOUT interpretation')+'</text>')
 for i in range(10):
  for y in [-2,2]:
   x=-3.6+.8*i;svg.append(f'<rect x="{ox+(x-w/2)*scale}" y="{oy+(y-h/2)*scale}" width="{w*scale}" height="{h*scale}" fill="#a36b38"/>')
 for x in [-span/2,span/2]:svg.append(f'<circle cx="{ox+x*scale}" cy="{oy+1.25*scale}" r="{.325*scale}" fill="#f3f5f7" stroke="#15759c" stroke-width="2"/>')
 y=350;svg.append(f'<path d="M{ox-span/2*scale} 310 V{y} H{ox+span/2*scale} V310" fill="none" stroke="#15759c"/><text x="{ox}" y="{y+22}" text-anchor="middle" font-size="15">Locator span {span:.1f} mm</text>')
 svg.append(f'<text x="{ox}" y="400" text-anchor="middle" font-size="14">Pads {w:.2f} x {h:.2f} mm; nominal hole/copper gap {case["minimum_nominal_locator_hole_to_pad_copper_mm"]:.3f} mm</text>')
svg.append('<text x="30" y="449" font-size="13">Current process constraint: hole to copper >=0.25mm. Mated height alone does not establish footprint compatibility.</text></g></svg>')
(R/'smt_btb_drawing_revision_comparison.svg').write_text(''.join(svg),encoding='utf8')
print('Native footprints match2017;2021 C interpretation gives',cases[1]['minimum_nominal_locator_hole_to_pad_copper_mm'],'mm nominal hole/copper gap. No alternate adopted.')
