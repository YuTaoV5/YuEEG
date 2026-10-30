from pathlib import Path
import pcbnew as p,wx,json
wx.DisableAsserts();R=Path('hardware/YuEEG_8CH_RevH_Stack')
for board in ['afe','digital','power']:
 b=p.LoadBoard(str(R/board/('YuEEG_H_'+board.upper()+'.kicad_pcb')));data={'board_mm':[34,18] if board=='power' else [48,60],'copper_layers':b.GetCopperLayerCount(),'back_smd':[],'placements':{},'front_courtyards':{},'back_courtyards':{},'mechanical_features':{}}
 for f in b.GetFootprints():
  ref=f.GetReference()
  if f.GetAttributes()&p.FP_BOARD_ONLY:
   data['mechanical_features'][ref]={'xy_mm':[p.ToMM(f.GetPosition().x),p.ToMM(f.GetPosition().y)],'drills_mm':[p.ToMM(q.GetDrillSize().x) for q in f.Pads()],'edge_cutout_diameters_mm':[2*p.ToMM(q.GetRadius()) for q in f.GraphicalItems() if q.GetLayer()==p.Edge_Cuts and q.GetShape()==p.SHAPE_T_CIRCLE]};continue
  back=f.GetLayer()==p.B_Cu;layer=p.B_CrtYd if back else p.F_CrtYd;r=[q.GetBoundingBox() for q in f.GraphicalItems() if q.GetLayer()==layer]
  data['placements'][ref]=[p.ToMM(f.GetPosition().x),p.ToMM(f.GetPosition().y),f.GetOrientationDegrees(),'B' if back else 'F']
  if r:data['back_courtyards' if back else 'front_courtyards'][ref]=[min(p.ToMM(x.GetX()) for x in r),min(p.ToMM(x.GetY()) for x in r),max(p.ToMM(x.GetRight()) for x in r),max(p.ToMM(x.GetBottom()) for x in r)]
  if back and f.GetAttributes()&p.FP_SMD:data['back_smd'].append(ref)
 data['status']='Native current-board capture; earlier placement packing metadata superseded'
 (R/board/'review/functional_placement.json').write_text(json.dumps(data,indent=2));print(board,len(data['placements']),'parts;',len(data['back_smd']),'back SMD')
