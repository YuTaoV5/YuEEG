"""Complete the isolated right-facing PH4 candidate; never writes the main PCB."""
from pathlib import Path
import json,sys,subprocess,math
from h_local_router import load
sys.path.insert(0,'hardware/YuEEG_8CH_RevG/review');from sexpr_io import loads,dumps,sub
D=Path('logs/afe_shadow_candidate');path=D/'YuEEG_H_AFE.kicad_pcb';pro=path.with_suffix('.kicad_pro').read_bytes();cli='X:/SoftWare/Kicad/bin/kicad-cli.exe'
def drc():
 subprocess.run([cli,'pcb','drc','--format','json','-o',str(D/'drc.json'),str(path)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);return json.loads((D/'drc.json').read_text())
def clean():
 for i in range(250):
  d=drc();ids={v['uuid'] for e in d['violations'] if e['type'] in ['track_dangling','via_dangling'] for v in e['items']}
  if not ids:return d
  if i%10==0:print('Stub pass',i,'leaves',len(ids),flush=True)
  t=loads(path.read_text(encoding='utf8'));t[:]=[v for v in t if not(isinstance(v,list) and v[0] in ['segment','via','arc'] and sub(v,'uuid') and json.loads(sub(v,'uuid')[1]) in ids)];path.write_text(dumps(t),encoding='utf8')
 raise RuntimeError('Stub cleanup did not converge')
clean()
for step in range(30):
 d=drc()
 if not d['unconnected_items']:break
 ns=load('afe',str(path));p,b,route,loc=[ns[n] for n in ['p','b','route','loc']];objects={v.m_Uuid.AsString():v for v in b.GetTracks()}
 for f in b.GetFootprints():objects.update({v.m_Uuid.AsString():v for v in f.Pads()})
 def ends(item):
  if isinstance(item,p.PAD) or isinstance(item,p.PCB_VIA):return [(*loc(item.GetPosition()),i) for i,ly in enumerate(ns['layers']) if item.IsOnLayer(ly)]
  return [(*loc(v),ns['layers'].index(item.GetLayer())) for v in [item.GetStart(),item.GetEnd()]] if item.GetLayer() in ns['layers'] else []
 success=False
 for air in d['unconnected_items']:
  aa,bb=[objects[v['uuid']] for v in air['items']];net=aa.GetNet();name=aa.GetNetname();pairs=sorted([(s,t) for s in ends(aa) for t in ends(bb)],key=lambda st:math.dist(st[0][:2],st[1][:2]))
  for s,t in pairs[:8]:
   try:
    print(step,name,s,t,flush=True);route(net,s[:2],t[:2],width=.5 if name in ['SYS_5V','+4V4_PRE'] else .4 if name=='GND' else .15,sl=s[2],el=t[2]);success=True;break
   except RuntimeError as e:print('retry:',e,flush=True)
  if success:break
 if not success:raise RuntimeError('No valid connection found')
 p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(path),b);path.with_suffix('.kicad_pro').write_bytes(pro)
d=clean();print('AFE SHADOW CANDIDATE: DRC',len(d['violations']),'unconnected',len(d['unconnected_items']),flush=True);assert not d['violations'] and not d['unconnected_items']
