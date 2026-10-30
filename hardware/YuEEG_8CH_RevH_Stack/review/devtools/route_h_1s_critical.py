from h_local_router import load
import json
ns=load('power');p,b,route,pad,loc=[ns[k] for k in ['p','b','route','pad','loc']]
items=[('UP2',5,'LP1',2,.3),('UP2',6,'CP5',1,.25),('UP2',3,'CP4',1,.25),('UP2',4,'CP5',2,.25),('UP2',4,'CP4',2,.25),('UP2',1,'RP5',2,.15),('RP5',2,'RP6',1,.15),('RP5',1,'CP5',1,.2)]
out=[]
for ra,pa,rb,pb,w in items:
 a,c=pad(ra,pa),pad(rb,pb);assert a.GetNetname()==c.GetNetname()
 print(ra,pa,loc(a.GetPosition()),rb,pb,loc(c.GetPosition()),flush=True)
 try:
  route(a.GetNet(),loc(a.GetPosition()),loc(c.GetPosition()),width=w,sl=0,el=0);p.SaveBoard(str(ns['path']),b);out.append({'pins':[ra+'.'+str(pa),rb+'.'+str(pb)],'status':'routed'})
 except RuntimeError as e:print(e,flush=True);out.append({'pins':[ra,rb],'status':str(e)})
ns['path'].parent.joinpath('review/boost_critical_routes.json').write_text(json.dumps(out,indent=2))
