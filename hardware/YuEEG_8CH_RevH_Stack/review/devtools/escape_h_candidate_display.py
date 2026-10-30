from pathlib import Path
ns={};exec(Path('logs/preroute_h_candidate.py').read_text().split("for r in ['R301'")[0],ns)
for k in ['p','b','path','fs','new','pad','pt','tracks','via']:globals()[k]=ns[k]
targets={1:(32.39,20.45),4:(31.39,20.45),5:(30.59,20.45),6:(30.39,22.15),7:(29.79,20.45),22:(31.39,24.3),23:(32.19,24.3),24:(32.39,22.25)}
for n,v in targets.items():
 q=pad('J2002',n);net=q.GetNetname();a=pt(q)
 middle=(a[0],20.65 if a[1]<22 else 24.1) if (a[1]<22 and v[1]<21) or (a[1]>23 and v[1]>24) else a
 tracks(net,[a,middle,v]);via(net,v)
issues=[]
for i,q in enumerate(new):
 for layer in [p.F_Cu,p.In1_Cu,p.In2_Cu,p.In3_Cu,p.In4_Cu,p.B_Cu]:
  if not q.IsOnLayer(layer):continue
  shape=q.GetEffectiveShape(layer)
  for f in b.GetFootprints():
   for a in f.Pads():
    if a.GetNetCode()!=q.GetNetCode() and a.IsOnLayer(layer) and a.GetEffectiveShape(layer).Collide(shape,p.FromMM(.1499)):issues.append([i,q.GetNetname(),f.GetReference(),a.GetNumber()])
  for t in list(b.GetTracks())+new[:i]:
   if t.GetNetCode()!=q.GetNetCode() and t.IsOnLayer(layer) and t.GetEffectiveShape(layer).Collide(shape,p.FromMM(.1499)):issues.append([i,q.GetNetname(),t.GetNetname()])
assert not issues,issues
for q in new:b.Add(q)
p.SaveBoard(str(path),b);print('Display pre-escape routes',len(new))
