"""Generate independent Rev H board schematics from audited Rev G pin contracts."""
from pathlib import Path
import json,csv,copy,sys,uuid
R=Path('hardware/YuEEG_8CH_RevH_Stack');G=Path('hardware/YuEEG_8CH_RevG')
src=Path('hardware/YuEEG_8CH_RevA/review/build_schematic.py').read_text(encoding='utf8').split('sheets=[]')[0]
src=src.replace("max(float(sub(p,'at')[2]) for p in allp)","max((float(sub(p,'at')[2]) for p in allp),default=0)")
src=src.replace("'open_collector','line'","'open_collector','no_connect','line'")
src=src.replace('2026-10-24','2026-10-30').replace('A0 review','H development')
ns={'__file__':str(Path('hardware/YuEEG_8CH_RevA/review/build_schematic.py').resolve())};exec(src,ns)
parse,sub,children=ns['parse'],ns['sub'],ns['children'];lib=ns['library'];units={};source={}
for base in [G,G/'display_carrier']:
 for path in base.glob('*.kicad_sch'):
  tree=parse(path.read_text(encoding='utf8'));ls=sub(tree,'lib_symbols')
  if ls:
   for s in children(ls,'symbol'):lib[s[1]]=copy.deepcopy(s)
  for s in children(tree,'symbol'):
   ref=next(x[2] for x in children(s,'property') if x[1]=='Reference')
   if ref.startswith('#'):continue
   key=sub(s,'lib_id')[1];unit=int(sub(s,'unit')[1]);units.setdefault(ref,{})[unit]=key
   source[ref]=s
def connector(key,n):
 ns['load']('Connector_Generic',key.split(':')[1]);return key
for n in [2,4,10,20]:connector('Connector_Generic:Conn_01x'+str(n).zfill(2),n)
ns['load']('Device','FerriteBead')
contracts=json.loads((R/'review/interboard_contract.json').read_text())
contracts['AFE_DIGITAL']['19']='SYS_5V'
(R/'review/interboard_contract.json').write_text(json.dumps(contracts,indent=2))
for board in ['afe','digital']:
 dest=R/board;project='YuEEG_H_'+board.upper();ns.update(ROOT=dest,PROJECT=project,rootid=str(uuid.uuid4()),bom=[],expected={},components={})
 rows=list(csv.DictReader((dest/'BOM_source.csv').open(encoding='utf-8-sig')))
 expect=json.loads((dest/'review/expected_source.json').read_text()); entries=[]
 # Keep main MCU until the external antenna module's memory SKU and footprint are selected.
 for row in rows:
  ref=row['Reference']
  # Obsolete 2.8-V display rail and IM1 strap terminated only at the removed carrier cable.
  if board=='digital' and ref in {'U1002','C1004','C1005','C1011','R1006'}:continue
  if ref=='U2':
   row['Value']='ESP32-S3-WROOM-1U-N16R8';row['Footprint']='RF_Module:ESP32-S3-WROOM-1U'
  if ref in {'SW301','SW302','SW1001'}:
   row['Value']='ALPS SKRTLBE010 / '+{'SW301':'RESET','SW302':'BOOT','SW1001':'REC'}[ref]
   row['Footprint']='YuEEG:ALPS_SKRTLBE010_GroundedShell'
  if ref=='J1101':
   row['Value']='KINGCONN 7TFCN-FA-1010-C / H3.75';row['Footprint']='YuEEG:KINGCONN_7TFCN_FA_1010_C_NotchedShield'
  if ref=='J1301':
   row['Value']='1x10 2.54mm RIGHT ANGLE / ELECTRODES';row['Footprint']='YuEEG:Electrode_1x10_Horizontal_ReverseLogical'
  if board=='digital' and ref=='L401':
   row['Value']='2.2uH / TDK SPM4015T-2R2M-LR';row['Footprint']='YuEEG:TDK_SPM4015_LR'
  if ref=='C406':
   row['Value']='22u 25V X5R / C3216X5R1E226M160AB H1.8max'
  for unit,key in units[ref].items():
   mp={pin.split('.',1)[1]:('SYS_5V' if net=='VBAT_SW' else net) for pin,net in expect.items() if pin.startswith(ref+'.')}
   if board=='digital' and ref=='R309':mp['1']='BAT_PROTECTED_SENSE'
   entries.append((key,ref,row['Value'],unit,row['Footprint'],mp))
 inter={str(k):v for k,v in contracts['AFE_DIGITAL'].items()}
 if board=='afe':
  entries += [('Device:FerriteBead','FBH1','600R@100MHz / verify DCR and current',1,'Inductor_SMD:L_0603_1608Metric',{'1':'+3V3','2':'+3V3_AFE'}),('Device:C','CH1','1u 10V',1,'Capacitor_SMD:C_0603_1608Metric',{'1':'+3V3_AFE','2':'GND'}),('Device:C','CH2','100n 10V',1,'Capacitor_SMD:C_0402_1005Metric',{'1':'+3V3_AFE','2':'GND'})]
 entries.append(('Connector_Generic:Conn_01x20','JH1','TMM-110-03-L-D / 4mm POST / bottom logical' if board=='digital' else 'SQT-110-01-L-D / SOCKET / logical pins',1,'YuEEG:Samtec_TMM_110_03_BottomLogical' if board=='digital' else 'YuEEG:Samtec_SQT_110_01_Logical',inter))
 if board=='digital':
  entries.append(('Connector_Generic:Conn_01x04','JH2','POWER INPUT: 1=5V 2=CELL_SENSE 3/4=GND',1,'Connector_JST:JST_PH_S4B-PH-SM4-TB_1x04-1MP_P2.00mm_Horizontal',{'1':'SYS_5V','2':'BAT_PROTECTED_SENSE','3':'GND','4':'GND'}))
 for i,net in enumerate(['+3V3_AFE','GND','SYS_5V'] if board=='afe' else ['SYS_5V','GND','+3V3','DATA_5V','HOST_GND','USB_VDD1','SD_3V3'],1):
  # External power ports are the sources; passive connector/ferrite pins need ERC source declarations.
  if net not in {v for *_,mp in entries for v in mp.values()}:continue
  entries.append(('power:PWR_FLAG','#PFH'+str(i),net,1,'',{'1':net}))
 ns['globals_']={net for *_,mp in entries for net in mp.values() if net is not None}
 sheets=[]
 for start in range(0,len(entries),6):
  sh=ns['Sheet']('circuit_'+str(len(sheets)+1).zfill(2),project+' / circuit '+str(len(sheets)+1),len(sheets)+2)
  sh.text(project+' DEVELOPMENT / acquisition priority / NOT RELEASED',15,12,2)
  for i,(key,ref,value,unit,fp,mp) in enumerate(entries[start:start+6]):
   # Two columns and three rows; large multiunit pin blocks get ample room.
   x=101.6+(i%2)*195.58;y=58.42+(i//2)*80.01
   sh.named(key,ref,value,x,y,mp,unit=unit,footprint=fp)
  sh.write();sheets.append(sh)
 q=ns['q'];root=ns['rootid'];uid=ns['uid'];eff=ns['eff']
 text=f'(kicad_sch (version 20250114) (generator "eeschema") (uuid "{root}") (paper "A3") (lib_symbols) (sheet_instances (path "/" (page "1")))'
 for i,s in enumerate(sheets):
  x=15+(i%3)*125;y=20+(i//3)*32
  text+=f'(sheet (at {x} {y}) (size 110 25) (stroke (width 0.15) (type default)) (fill (color 0 0 0 0)) (uuid "{s.id}") (property "Sheetname" "{s.name}" (at {x} {y-1} 0) {eff()}) (property "Sheetfile" "{s.name}.kicad_sch" (at {x} {y+26} 0) {eff()}) (instances (project "{project}" (path "/{root}" (page "{i+2}")))))'
 (dest/(project+'.kicad_sch')).write_text(text+'(embedded_fonts no))',encoding='utf8')
 with (dest/'BOM.csv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=ns['bom'][0]);w.writeheader();w.writerows(r for r in ns['bom'] if not r['Reference'].startswith('#'))
 (dest/'review/expected_connections.json').write_text(json.dumps(ns['expected'],indent=2))
 print(board,len(ns['bom']),len(sheets))

# Single-cell battery power is maintained independently.
exec(Path('logs/build_h_1s_power.py').read_text())
