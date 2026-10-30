"""NP-BX1 power schematic. Deliberately does not regenerate the other boards."""
from pathlib import Path
import json,csv,uuid,shutil
R=Path('hardware/YuEEG_8CH_RevH_Stack')
archive=R/'archive/power_2s_before_npbx1'
if not archive.exists():
 shutil.copytree(R/'power',archive)
 (archive/'SUPERSEDED.txt').write_text('SUPERSEDED: NP-FW50 2S input. NOT compatible with user-selected NP-BX1. Retained for traceability only.\n')
s=Path('logs/build_stack_circuits.py').read_text().split('contracts=json.loads')[0]
bootstrap={};exec(s,bootstrap);ns=bootstrap['ns']
for name in ['R','C','L','Fuse']:ns['load']('Device',name)
ns['load']('Switch','SW_SPDT')
dest=R/'power';project='YuEEG_H_POWER'
ns.update(ROOT=dest,PROJECT=project,rootid=str(uuid.uuid4()),bom=[],expected={},components={})
def custom(key,pins,fp,url):
 half=(len(pins)+1)//2
 ns['custom'](key,[(15.24,27.94,ns['boxpins'](pins[:half],'L',start=22.86)+ns['boxpins'](pins[half:],'R',start=22.86))],fp,url)
 return 'YuEEG:'+key
efp='Package_SON:Texas_DSG0008A_WSON-8-1EP_2x2mm_P0.5mm_EP0.9x1.6mm'
ek=custom('TPS259530DSG',[(1,'dVdt','passive'),(2,'EN_UVLO','input'),(3,'IN','power_in'),(4,'IN','passive'),(5,'OUT','power_out'),(6,'FLT_N','open_collector'),(7,'ILM','passive'),(8,'GND','power_in'),(9,'EP_GND','passive')],efp,'https://www.ti.com/lit/ds/symlink/tps2595.pdf')
bfp='Package_TO_SOT_SMD:SOT-563'
bk=custom('TPS61023DRL',[(1,'FB','input'),(2,'EN','input'),(3,'VIN','power_in'),(4,'GND','power_in'),(5,'SW','passive'),(6,'VOUT','power_out')],bfp,'https://www.ti.com/lit/ds/symlink/tps61023.pdf')
qfp='Package_TO_SOT_SMD:SOT-23'
qk=custom('DMP2035U_GSD',[(1,'G','input'),(2,'S','passive'),(3,'D','passive')],qfp,'https://www.diodes.com/datasheet/download/DMP2035U.pdf')
entries=[]
def add(key,ref,val,fp,mp):entries.append((key,ref,val,1,fp,mp))
add(ek,'UP1','TPS259530DSGR / latch fault',efp,{'1':'P_DVDT','2':'P_UV','3':'PACK_RP','4':'PACK_RP','5':'BAT_PROTECTED_SENSE','6':None,'7':'P_ILM','8':'GND','9':'GND'})
add(bk,'UP2','TPS61023DRLR / 5V boost',bfp,{'1':'P_FB','2':'BAT_PROTECTED_SENSE','3':'BAT_PROTECTED_SENSE','4':'GND','5':'P_SW','6':'SYS_5V'})
# Reverse polarity PMOS: D to cell, S to load, body diode D -> S.
add(qk,'QP1','DMP2035U-7',qfp,{'1':'P_GATE','2':'PACK_RP','3':'PACK_FUSED'})
add('Connector_Generic:Conn_01x02','JP1','NP-BX1 + / - contacts: NOT FINAL MECHANICS','Connector_PinHeader_2.00mm:PinHeader_1x02_P2.00mm_Vertical',{'1':'PACK_POS','2':'GND'})
add('Connector_Generic:Conn_01x04','JP2','1=5V 2=CELL_SENSE 3/4=GND','Connector_JST:JST_PH_S4B-PH-SM4-TB_1x04-1MP_P2.00mm_Horizontal',{'1':'SYS_5V','2':'BAT_PROTECTED_SENSE','3':'GND','4':'GND'})
add('Switch:SW_SPDT','SWP1','OFF:1-2 / RUN:2-3','Button_Switch_SMD:SW_SPDT_PCM12',{'1':'GND','2':'P_UV','3':None})
for kind,ref,val,a,b,fp in [
 ('Fuse','FP1','2A / Littelfuse 0466002.NRHF / 63V fast','PACK_POS','PACK_FUSED','Fuse:Fuse_1206_3216Metric'),
 ('R','RP1','196k 0.1%','PACK_RP','P_UV',''),('R','RP2','100k 0.1%','P_UV','GND',''),
 ('R','RP3','1.37k 1% / 1.50A nominal','P_ILM','GND',''),('R','RP4','100k 1%','P_GATE','GND',''),
 ('R','RP5','732k 0.1%','SYS_5V','P_FB',''),('R','RP6','100k 0.1%','P_FB','GND',''),
 ('C','CP1','1u 10V X7R','PACK_RP','GND',''),('C','CP2','22u 25V X5R / C3216X5R1E226M160AB','BAT_PROTECTED_SENSE','GND','Capacitor_SMD:C_1206_3216Metric'),
 ('C','CP3','10n 16V X7R','P_DVDT','GND',''),('C','CP4','100n 16V X7R','BAT_PROTECTED_SENSE','GND',''),
 ('C','CP5','22u 25V X5R / C3216X5R1E226M160AB','SYS_5V','GND','Capacitor_SMD:C_1206_3216Metric'),
 ('C','CP6','22u 25V X5R / C3216X5R1E226M160AB','SYS_5V','GND','Capacitor_SMD:C_1206_3216Metric'),
 ('C','CP7','100n 16V X7R','SYS_5V','GND',''),
 ('L','LP1','1uH / TDK SPM4015T-1R0M-LR','BAT_PROTECTED_SENSE','P_SW','YuEEG:TDK_SPM4015_LR')]:
  if not fp:fp=('Resistor_SMD:R_0603_1608Metric' if kind=='R' else 'Capacitor_SMD:C_0603_1608Metric')
  add('Device:'+kind,ref,val,fp,{'1':a,'2':b})
for i,net in enumerate(['PACK_POS','PACK_RP','GND'],1):add('power:PWR_FLAG','#PFP'+str(i),net,'',{'1':net})
ns['globals_']={v for *_,mp in entries for v in mp.values() if v is not None}
sheets=[]
for start in range(0,len(entries),6):
 sh=ns['Sheet']('power_'+str(len(sheets)+1),project,len(sheets)+2)
 sh.text('NP-BX1 1S / external charger only / DEVELOPMENT NOT RELEASED',15,12,2)
 for i,(key,ref,val,u,fp,mp) in enumerate(entries[start:start+6]):sh.named(key,ref,val,101.6+i%2*195.58,58.42+i//2*80.01,mp,footprint=fp)
 sh.write();sheets.append(sh)
root=ns['rootid'];text=f'(kicad_sch (version 20250114) (generator "eeschema") (uuid "{root}") (paper "A3") (lib_symbols) (sheet_instances (path "/" (page "1")))'
for i,sh in enumerate(sheets):
 x=15+i%3*125;y=30+i//3*50
 text+=f'(sheet (at {x} {y}) (size 110 25) (stroke (width 0.15) (type default)) (fill (color 0 0 0 0)) (uuid "{sh.id}") (property "Sheetname" "{sh.name}" (at {x} {y-1} 0) {ns["eff"]()}) (property "Sheetfile" "{sh.name}.kicad_sch" (at {x} {y+26} 0) {ns["eff"]()}) (instances (project "{project}" (path "/{root}" (page "{i+2}")))))'
(dest/(project+'.kicad_sch')).write_text(text+'(embedded_fonts no))',encoding='utf8')
with (dest/'BOM.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=ns['bom'][0]);w.writeheader();w.writerows(r for r in ns['bom'] if not r['Reference'].startswith('#'))
(dest/'review/expected_connections.json').write_text(json.dumps(ns['expected'],indent=2))
print('NP-BX1 power schematic:',len([e for e in entries if not e[1].startswith('#')]),'parts')
