from pathlib import Path
import pcbnew as p,wx,json,math
wx.DisableAsserts()
R=Path('hardware/YuEEG_8CH_RevH_Stack');F=R/'footprints/YuEEG.pretty'
# TDK land pattern A=1.65, B=1.65, C=2.30; A is pad width, B gap.
(F/'TDK_SPM4015_LR.kicad_mod').write_text('''(footprint "TDK_SPM4015_LR" (version 20241229) (generator "pcbnew") (layer "F.Cu") (attr smd)
 (descr "TDK SPM4015 LR; manufacturer recommended land A/B/C=1.65/1.65/2.30 mm")
 (property "Reference" "REF**" (at 0 -3) (layer "F.SilkS") (effects (font (size .7 .7) (thickness .1))))
 (property "Value" "SPM4015-LR" (at 0 3) (layer "F.Fab") (effects (font (size .7 .7) (thickness .1))))
 (fp_rect (start -2.2 -2.05) (end 2.2 2.05) (stroke (width .1) (type solid)) (fill none) (layer "F.Fab"))
 (fp_rect (start -2.75 -2.4) (end 2.75 2.4) (stroke (width .05) (type solid)) (fill none) (layer "F.CrtYd"))
 (pad "1" smd roundrect (at -1.65 0) (size 1.65 2.3) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio .15))
 (pad "2" smd roundrect (at 1.65 0) (size 1.65 2.3) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio .15)))''')
ns={};exec(Path('logs/place_stack_boards.py').read_text().split('for W,H in [(33.5')[0],ns)
result,bad=ns['build']('power',34,18);assert not bad,bad
b,_=result;xy,bounds,overlap=[ns[k] for k in ['xy','bounds','overlap']];fs={f.GetReference():f for f in b.GetFootprints()};used={};poses={}
hard={'JP2':(7.5,11,180),'JP1':(30,14,90),'SWP1':(19,13,0),'LP1':(25.5,4,270),'UP2':(25,8.5,0),'UP1':(17,7.5,0),'QP1':(13,3,180)}
for ref,(x,y,a) in hard.items():
 f=fs[ref];f.SetOrientationDegrees(a);f.SetPosition(xy(x,y));bb=bounds(f)
 assert not any(overlap(bb,q) for q in used.values()),(ref,bb,used)
 used[ref]=bb;poses[ref]=[x,y,a]
targets={'FP1':(31,3),'RP1':(15,10),'RP2':(18,10),'RP3':(19.5,7.5),'RP4':(10,4),'RP5':(23,10.5),'RP6':(23,12.5),'CP1':(16,4),'CP2':(21,5),'CP3':(14,7),'CP4':(22.5,8.5),'CP5':(29,8),'CP6':(28,12),'CP7':(26,11)}
for ref,target in targets.items():
 f=fs[ref];best=None
 for a in [0,90,180,270]:
  f.SetOrientationDegrees(a);f.SetPosition(xy(0,0));q=bounds(f)
  for ix in range(math.ceil((.7-q[0])*4),math.floor((33.3-q[2])*4)+1):
   x=ix/4
   for iy in range(math.ceil((.7-q[1])*4),math.floor((17.3-q[3])*4)+1):
    y=iy/4;cost=math.hypot(x-target[0],y-target[1]);bb=(x+q[0],y+q[1],x+q[2],y+q[3])
    if best and cost>=best[0]:continue
    if any(overlap(bb,z) for z in used.values()):continue
    best=cost,x,y,a,bb
 assert best,ref
 _,x,y,a,bb=best;f.SetOrientationDegrees(a);f.SetPosition(xy(x,y));used[ref]=bb;poses[ref]=[x,y,a]
for f in fs.values():f.Reference().SetVisible(False);f.Value().SetVisible(False)
# Keep the existing project rules; SaveBoard to a temporary path first.
tmp=Path('logs/power_1s_exchange.kicad_pcb');p.SaveBoard(str(tmp),b)
(R/'power/YuEEG_H_POWER.kicad_pcb').write_bytes(tmp.read_bytes())
(R/'power/review/functional_placement_1s.json').write_text(json.dumps({'board_mm':[34,18],'placements':poses,'status':'1S protection and boost; battery contact footprint still provisional'},indent=2))
print('Placed',len(fs),'NP-BX1 power components')
