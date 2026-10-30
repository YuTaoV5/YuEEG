from h_local_router import load
ns=load();p,b,route,pad,loc=[ns[k] for k in ['p','b','route','pad','loc']]
a,c=pad('JH2',2),pad('R309',1);assert a.GetNetname()==c.GetNetname()=='BAT_PROTECTED_SENSE'
route(a.GetNet(),loc(a.GetPosition()),loc(c.GetPosition()),width=.15,sl=0,el=0)
p.SaveBoard(str(ns['path']),b)
print('Protected pre-boost cell sense connected')
