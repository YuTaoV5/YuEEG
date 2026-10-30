"""Adapt the reviewed local router to Rev H, validating off-grid endpoint escapes."""
from pathlib import Path
import sys
def load(board='digital',board_path=None):
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
