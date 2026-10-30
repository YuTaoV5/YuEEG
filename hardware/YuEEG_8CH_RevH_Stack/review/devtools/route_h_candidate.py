from pathlib import Path
import pcbnew as p,wx,sys,subprocess
sys.path.insert(0,'hardware/YuEEG_8CH_RevG/review')
from sexpr_io import loads,dumps,sub
R=Path('logs/RevH_DigitalCandidate');b=p.LoadBoard(str(R/'YuEEG_H_DIGITAL.kicad_pcb'));D=R
wx.DisableAsserts();assert p.ExportSpecctraDSN(b,str(D/'digital.dsn'))
d=loads((D/'digital.dsn').read_text());st=sub(d,'structure')
for layer in st:
 if isinstance(layer,list) and layer[0]=='layer' and layer[1].strip('"')in ['In1.Cu','In3.Cu']:sub(layer,'type')[1]='power'
def rules(rule):
 if not rule:return
 for n in rule[1:]:
  if isinstance(n,list) and n[0] in ['width','clearance']:n[1]='150'
rules(sub(st,'rule'))
for cl in sub(d,'network'):
 if isinstance(cl,list) and cl[0]=='class':rules(sub(cl,'rule'))
for copper in (sub(d,'wiring') or [])[1:]:
 if isinstance(copper,list) and copper[0] in ['wire','via']:
  ty=sub(copper,'type')
  if ty:ty[1]='protect'
  else:copper.append(['type','protect'])
def compact(n):return '('+' '.join(compact(v) if isinstance(v,list) else str(v) for v in n)+')'
(D/'digital.dsn').write_text(compact(d))
java='hardware/YuEEG_8CH_RevA/review/tools/java17/jdk-17.0.20.1+1-jre/bin/java.exe'
startup=subprocess.STARTUPINFO();startup.dwFlags|=subprocess.STARTF_USESHOWWINDOW;startup.wShowWindow=0
print('Digital routing started: protected local critical paths, In1 and In3 reserved for ground',flush=True)
with (D/'routing.log').open('w') as log:
 subprocess.run([java,'-jar','hardware/YuEEG_8CH_RevA/review/tools/freerouting-1.6.5.jar','-de',str(D/'digital.dsn'),'-do',str(D/'digital.ses'),'-mp','12'],stdout=log,stderr=log,check=True,startupinfo=startup)
print('Digital routing process complete',flush=True)

