"""Small local maze route for regulator feedback, using exact KiCad copper shapes."""
from pathlib import Path
import pcbnew as p,heapq,math,json
import sys
MAIN=Path(__file__).resolve().parents[1];aux='--power' in sys.argv
if '--layout70d' in sys.argv:ROOT=MAIN.parents[1]/'logs/RevF_layout70d'
elif '--layout70c' in sys.argv:ROOT=MAIN.parents[1]/'logs/RevF_layout70c'
elif '--layout70b' in sys.argv:ROOT=MAIN.parents[1]/'logs/RevF_layout70b'
elif '--layout70' in sys.argv:ROOT=MAIN.parents[1]/'logs/RevF_layout70'
elif '--trial' in sys.argv:ROOT=MAIN.parents[1]/'logs/RevF_route_trial/board_fresh'
else:ROOT=MAIN/'isolated_power' if aux else MAIN
path=ROOT/('YuEEG_8CH_RevF_POWER.kicad_pcb' if aux else 'YuEEG_8CH_RevF.kicad_pcb');b=p.LoadBoard(str(path));mm=p.FromMM

def xy(x,y):return p.VECTOR2I(mm(x),mm(y))
def loc(v):return p.ToMM(v.x),p.ToMM(v.y)
layers=[p.F_Cu,p.In2_Cu,p.B_Cu]
fps={f.GetReference():f for f in b.GetFootprints()}
def pad(ref,num):return next(q for q in fps[ref].Pads() if q.GetNumber()==str(num))
def route(net,start,end,width=.15,sl=0,el=0):
    code=net.GetNetCode();obs={ly:[] for ly in layers};allobs=[];holes=[];pads=[]
    for f in fps.values():
        for q in f.Pads():
            for ly in layers:
                if q.IsOnLayer(ly):
                    sh=q.GetEffectiveShape(ly)
                    if q.GetNetCode()!=code:obs[ly].append((sh,sh.BBox()));allobs.append((sh,sh.BBox()))

                    if q.GetNetCode()!=code:pads.append((sh,sh.BBox()))
            if q.GetDrillSize().x:holes.append((*loc(q.GetPosition()),p.ToMM(q.GetDrillSize().x)/2))
    for t in b.GetTracks():
        for ly in layers:
            if t.IsOnLayer(ly) and t.GetNetCode()!=code:
                sh=t.GetEffectiveShape(ly);obs[ly].append((sh,sh.BBox()));allobs.append((sh,sh.BBox()))
        if isinstance(t,p.PCB_VIA):holes.append((*loc(t.GetPosition()),p.ToMM(t.GetDrillValue())/2))
    nonplated=[(q.GetEffectiveHoleShape(),q.GetEffectiveHoleShape().BBox()) for f in fps.values() for q in f.Pads() if q.GetAttribute()==p.PAD_ATTRIB_NPTH and q.GetDrillSize().x]
    spatial={}
    def index(items):
        key=id(items)
        if key not in spatial:
            bins={}
            for sh,bb in items:
                for ix in range(bb.GetX()//mm(2),(bb.GetX()+bb.GetWidth())//mm(2)+1):
                    for iy in range(bb.GetY()//mm(2),(bb.GetY()+bb.GetHeight())//mm(2)+1):bins.setdefault((ix,iy),[]).append((sh,bb))
            spatial[key]=bins
        return spatial[key]
    def collides(circle,items,clear=.151):
        cb=circle.BBox();cb.Inflate(mm(clear));bins=index(items)
        for ix in range(cb.GetX()//mm(2),(cb.GetX()+cb.GetWidth())//mm(2)+1):
            for iy in range(cb.GetY()//mm(2),(cb.GetY()+cb.GetHeight())//mm(2)+1):
                if any(bb.Intersects(cb) and sh.Collide(circle,mm(clear)) for sh,bb in bins.get((ix,iy),[])):return True
        return False
    scale=20 if '--fine' in sys.argv else 10;cache={};v_cache={}
    margin=4 if '--fine' in sys.argv else 10
    right=123.3 if aux else (149.3 if any(a.startswith('--layout70') for a in sys.argv) else 147.3);bottom=147.3 if aux else 179.3
    bounds=(max(math.ceil(80.7*scale),math.floor((min(start[0],end[0])-margin)*scale)),min(math.floor(right*scale),math.ceil((max(start[0],end[0])+margin)*scale)),max(math.ceil(100.7*scale),math.floor((min(start[1],end[1])-margin)*scale)),min(math.floor(bottom*scale),math.ceil((max(start[1],end[1])+margin)*scale)))
    keepouts=[z for z in b.Zones() if z.GetIsRuleArea()]+[z for f in b.GetFootprints() for z in f.Zones()]
    def free(node):
        if node in cache:return cache[node]
        x,y,l=node
        if not(bounds[0]<=x<=bounds[1] and bounds[2]<=y<=bounds[3]) or (not aux and 120*scale<x<140*scale and y>175*scale):cache[node]=False;return False
        circ=p.SHAPE_CIRCLE(xy(x/scale,y/scale),mm(width/2))
        blocked=any(z.IsOnLayer(layers[l]) and z.GetDoNotAllowTracks() and z.Outline().Collide(circ) for z in keepouts)
        cache[node]=not blocked and not collides(circ,obs[layers[l]]) and not collides(circ,nonplated,.251);return cache[node]
    ownvias=[t for t in b.GetTracks() if isinstance(t,p.PCB_VIA) and t.GetNetCode()==code]
    def reusable(x,y):return next((t for t in ownvias if math.dist((x/scale,y/scale),loc(t.GetPosition()))<.075),None)
    def vfree(x,y):
        if reusable(x,y) is not None:return True
        if (x,y) in v_cache:return v_cache[x,y]
        xx,yy=x/scale,y/scale;circ=p.SHAPE_CIRCLE(xy(xx,yy),mm(.175 if '--small-via' in sys.argv else .2))
        if any(z.GetDoNotAllowVias() and z.Outline().Collide(circ) for z in keepouts):v_cache[x,y]=False;return False
        okay=all(math.hypot(xx-hx,yy-hy)>r+.25+.21 for hx,hy,r in holes)
        if okay:okay=not collides(circ,allobs)
        if okay:okay=not collides(p.SHAPE_CIRCLE(xy(xx,yy),mm(.1)),pads,.26)
        v_cache[x,y]=okay;return okay
    s=(round(start[0]*scale),round(start[1]*scale),sl);goal=(round(end[0]*scale),round(end[1]*scale),el)
    def h(n):return math.hypot(n[0]-goal[0],n[1]-goal[1])+(0 if n[2]==goal[2] else 1.8*scale)
    costs={s:0};parents={};queue=[(h(s),0,s)];visited=0
    while queue:
        _,cost,n=heapq.heappop(queue)
        if cost!=costs.get(n):continue
        if n==goal:break
        visited+=1
        if visited>400000:raise RuntimeError('local route search exceeded bounds')
        x,y,l=n
        for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
            nn=(x+dx,y+dy,l)
            if not free(nn):continue
            if dx and dy and (not free((x+dx,y,l)) or not free((x,y+dy,l))):continue
            cc=cost+math.hypot(dx,dy)*(1.0 if l==0 else 1.12)
            if cc<costs.get(nn,1e99):costs[nn]=cc;parents[nn]=n;heapq.heappush(queue,(cc+h(nn),cc,nn))
        if vfree(x,y):
            for ll in range(len(layers)):
                if ll==l or not free((x,y,ll)):continue
                nn=(x,y,ll);cc=cost+(1 if reusable(x,y) is not None else 2.5*scale)
                if cc<costs.get(nn,1e99):costs[nn]=cc;parents[nn]=n;heapq.heappush(queue,(cc+h(nn),cc,nn))
    else:raise RuntimeError(f'No local route found: {visited} visited, start {free(s)}, goal {free(goal)}')
    nodes=[goal]
    while nodes[-1]!=s:nodes.append(parents[nodes[-1]])
    nodes.reverse()
    # Compress collinear grid edges into normal KiCad segments.
    compressed=[nodes[0]]
    for i in range(1,len(nodes)-1):
        a,c,d=nodes[i-1:i+2]
        if (c[0]-a[0],c[1]-a[1],c[2]-a[2])!=(d[0]-c[0],d[1]-c[1],d[2]-c[2]):compressed.append(c)
    compressed.append(nodes[-1]);vias=set()
    for exact,grid,layer in [(start,s,sl),(end,goal,el)]:
        if exact!=(grid[0]/scale,grid[1]/scale):
            t=p.PCB_TRACK(b);t.SetStart(xy(*exact));t.SetEnd(xy(grid[0]/scale,grid[1]/scale));t.SetWidth(mm(width));t.SetLayer(layers[layer]);t.SetNet(net);b.Add(t)
    for a,c in zip(compressed,compressed[1:]):
        if a[2]!=c[2]:
            point=(a[0]/scale,a[1]/scale)
            existing=reusable(a[0],a[1])
            if existing is not None:
                for li in [a[2],c[2]]:
                    t=p.PCB_TRACK(b);t.SetStart(xy(*point));t.SetEnd(existing.GetPosition());t.SetWidth(mm(width));t.SetLayer(layers[li]);t.SetNet(net);b.Add(t)
                continue
            if point not in vias:
                v=p.PCB_VIA(b);v.SetPosition(xy(*point));v.SetWidth(mm(.35 if '--small-via' in sys.argv else .4));v.SetDrill(mm(.15 if '--small-via' in sys.argv else .2));v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetViaType(p.VIATYPE_THROUGH);v.SetNet(net);b.Add(v);vias.add(point)
        else:
            t=p.PCB_TRACK(b);t.SetStart(xy(a[0]/scale,a[1]/scale));t.SetEnd(xy(c[0]/scale,c[1]/scale));t.SetWidth(mm(width));t.SetLayer(layers[a[2]]);t.SetNet(net);b.Add(t)
    print('Local route:',net.GetNetname(),'nodes',len(nodes),'vias',len(vias),'visited',visited,flush=True)
