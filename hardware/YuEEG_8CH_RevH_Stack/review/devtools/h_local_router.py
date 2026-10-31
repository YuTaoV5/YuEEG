"""Adapt the reviewed local router to Rev H, validating off-grid endpoint escapes."""
from pathlib import Path
import sys
def load(board='digital',board_path=None,outline=None,edge=.7,via=None):
 src=Path('hardware/YuEEG_8CH_RevF/review/local_router_f.py').read_text()
 line=next(l for l in src.splitlines() if l.startswith('path=ROOT/'))
 board_path=board_path or f'hardware/YuEEG_8CH_RevH_Stack/{board}/YuEEG_H_{board.upper()}.kicad_pcb'
 src=src.replace(line,f"path=Path({board_path!r});b=p.LoadBoard(str(path));mm=p.FromMM")
 src=src.replace('80.7*scale','.7*scale').replace('100.7*scale','.7*scale')
 src=src.replace('right=123.3 if aux else (149.3 if any(a.startswith(\'--layout70\') for a in sys.argv) else 147.3);bottom=147.3 if aux else 179.3','right=47.3;bottom=59.3')
 src=src.replace('layers=[p.F_Cu,p.In2_Cu,p.B_Cu]','layers=[p.F_Cu,p.In2_Cu,p.In4_Cu,p.B_Cu]')
 if board=='power':
  src=src.replace('layers=[p.F_Cu,p.In2_Cu,p.In4_Cu,p.B_Cu]','layers=[p.F_Cu,p.B_Cu]')
  src=src.replace('right=47.3;bottom=59.3','right=33.3;bottom=17.3')
 if board=='afe':
  src=src.replace('layers=[p.F_Cu,p.In2_Cu,p.In4_Cu,p.B_Cu]','layers=[p.F_Cu,p.In2_Cu,p.B_Cu]')
 if outline is not None:
  old='right=33.3;bottom=17.3' if board=='power' else 'right=47.3;bottom=59.3'
  assert old in src;src=src.replace(old,f'right={outline[0]-edge};bottom={outline[1]-edge}').replace('.7*scale',f'{edge}*scale')
  src=src.replace('    keepouts=[z for z in b.Zones()', '    board_poly=p.SHAPE_POLY_SET();b.GetBoardPolygonOutlines(board_poly);edge_shapes=[g.GetEffectiveShape() for g in b.GetDrawings() if g.GetLayer()==p.Edge_Cuts]\n    keepouts=[z for z in b.Zones()')
  src=src.replace('        blocked=any(',f'        if not board_poly.Contains(xy(x/scale,y/scale)) or any(sh.Collide(circ,mm({edge})) for sh in edge_shapes):cache[node]=False;return False\n        blocked=any(')
  src=src.replace('        blocked=any(',"        clip=globals().get('route_clip_box')\n        if clip and not (clip[0]<=x/scale<=clip[2] and clip[1]<=y/scale<=clip[3]):cache[node]=False;return False\n        blocked=any(")
  src=src.replace('        okay=all(',f'        if not board_poly.Contains(xy(xx,yy)) or any(sh.Collide(circ,mm({edge})) for sh in edge_shapes):v_cache[x,y]=False;return False\n        okay=all(')
 if via is not None:
  diameter,drill=via
  src=src.replace("mm(.35 if '--small-via' in sys.argv else .4)",f'mm({diameter})').replace("mm(.15 if '--small-via' in sys.argv else .2)",f'mm({drill})').replace("mm(.175 if '--small-via' in sys.argv else .2)",f'mm({diameter/2})').replace('r+.25+.21',f'r+.25+{diameter/2+.01}')
  if outline is not None:
   needle='xx,yy=x/scale,y/scale;circ='
   src=src.replace(needle,f'xx,yy=x/scale,y/scale\n        if not ({edge+diameter/2}<=xx<={outline[0]-edge-diameter/2} and {edge+diameter/2}<=yy<={outline[1]-edge-diameter/2}):v_cache[x,y]=False;return False\n        circ=')
 src=src.replace('for z in b.Zones()', 'for z in list(b.Zones())+[fz for footprint in b.GetFootprints() for fz in footprint.Zones()]')
 src=src.replace('margin=4 if','margin=14 if').replace('visited>400000','visited>1200000')
 old='s=(round(start[0]*scale),round(start[1]*scale),sl);goal=(round(end[0]*scale),round(end[1]*scale),el)'
 new='''def choose_endpoint(exact,li):
        cx,cy=round(exact[0]*scale),round(exact[1]*scale);candidates=[]
        for dx in range(-4,5):
            for dy in range(-4,5):
                node=(cx+dx,cy+dy,li)
                if not free(node):continue
                point=(node[0]/scale,node[1]/scale)
                if math.dist(point,exact)>.22:continue
                trial=p.PCB_TRACK(b);trial.SetStart(xy(*exact));trial.SetEnd(xy(*point));trial.SetWidth(mm(width));trial.SetLayer(layers[li]);trial.SetNet(net)
                shape=trial.GetEffectiveShape(layers[li])
                # Native DRC is the final clearance authority; allow only sub-micron numerical tolerance at existing endpoints.
                if collides(shape,obs[layers[li]],.1499) or collides(shape,nonplated,.2499):continue
                if any(z.IsOnLayer(layers[li]) and z.GetDoNotAllowTracks() and z.Outline().Collide(shape) for z in keepouts):continue
                candidates.append((math.dist(point,exact),node))
        if not candidates:raise RuntimeError('No validated grid escape at '+str(exact))
        return min(candidates)[1]
    s=choose_endpoint(start,sl);goal=choose_endpoint(end,el)'''
 assert old in src;src=src.replace(old,new)
 if '--fine' not in sys.argv:sys.argv.append('--fine')
 ns={'__file__':str(Path('hardware/YuEEG_8CH_RevF/review/local_router_f.py').resolve())};exec(src,ns);return ns
