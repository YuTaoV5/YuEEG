from pathlib import Path
import re,json,argparse
args=argparse.ArgumentParser(description='Inspect a user-supplied STEP; original is not distributed');args.add_argument('source',type=Path);source=args.parse_args().source
s=source.read_text(encoding='utf8');entities={int(n):v for n,v in re.findall(r'#(\d+)\s*=\s*(.*?);',s,re.S)}
def refs(v):return [int(x) for x in re.findall(r'#(\d+)',v)]
points={n:[float(x) for x in re.search(r',\s*\(([^()]+)\)\s*\)',v).group(1).split(',')] for n,v in entities.items() if v.lstrip().startswith('CARTESIAN_POINT')}
vertices={n:points[refs(v)[0]] for n,v in entities.items() if v.lstrip().startswith('VERTEX_POINT')};vs=list(vertices.values());lo=[min(p[i] for p in vs) for i in range(3)];hi=[max(p[i] for p in vs) for i in range(3)];print('Topological vertex bounds only',lo,hi,'span',[hi[i]-lo[i] for i in range(3)])
rows=[]
for n,v in entities.items():
 if not v.lstrip().startswith('ADVANCED_FACE'):continue
 rr=refs(v);surface=entities[rr[-1]]
 if not surface.lstrip().startswith('PLANE'):continue
 axis=entities[refs(surface)[0]];ar=refs(axis);origin=points[ar[0]];normal=[float(x) for x in re.search(r',\s*\(([^()]+)\)\s*\)',entities[ar[1]]).group(1).split(',')]
 seen=set();todo=rr[:-1];fv=[]
 while todo:
  x=todo.pop()
  if x in seen:continue
  seen.add(x)
  if x in vertices:fv.append(vertices[x]);continue
  if entities[x].lstrip().startswith(('FACE_OUTER_BOUND','FACE_BOUND','EDGE_LOOP','ORIENTED_EDGE','EDGE_CURVE')):todo.extend(refs(entities[x])[:2] if entities[x].lstrip().startswith('EDGE_CURVE') else refs(entities[x]))
 if fv:rows.append(dict(step_face=n,origin=origin,normal=normal,vertex_bounds=[min(p[i] for p in fv) for i in range(3)]+[max(p[i] for p in fv) for i in range(3)]))
Path('logs/npbx1_step_vertex_faces.json').write_text(json.dumps(rows,indent=2));ax=max(range(3),key=lambda i:hi[i]-lo[i]);print('Length axis',ax)
for row in rows:
 if abs(row['normal'][ax])>.999 and min(abs(row['origin'][ax]-lo[ax]),abs(row['origin'][ax]-hi[ax]))<2:print(row)
