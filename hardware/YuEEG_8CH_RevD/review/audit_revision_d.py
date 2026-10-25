"""Independent datasheet pin/topology and PCB invariants. No generator intent file used."""
from pathlib import Path
import pcbnew as p,xml.etree.ElementTree as ET,json,re,hashlib,csv,collections
ROOT=Path(__file__).resolve().parents[1];file=ROOT/'YuEEG_8CH_RevD.kicad_pcb';t=ET.parse(ROOT/'review/netlist.xml')
nets={q.get('ref')+'.'+q.get('pin'):n.get('name') for n in t.findall('./nets/net') for q in n.findall('node')};checked=[]
def pin(k,w):assert nets[k].rsplit('/',1)[-1]==w,(k,w,nets[k]);checked.append([k,w])
def part(r,m):
 for k,v in m.items():pin(r+'.'+str(k),v)
part('U701',{1:'HOST_5V',2:'HOST_GND',3:'USB_VDD1',4:'USB_VDD1',5:'USB_VDD1',6:'USB_UP_DM',7:'USB_UP_DP',8:'HOST_GND',9:'GND',10:'USB_DOWN_DP',11:'USB_DOWN_DM',12:'+3V3',13:'+3V3',14:'+3V3',15:'GND',16:'+3V3'})
part('U702',{1:'HOST_5V',2:'HOST_GND',3:'HOST_5V',5:'HOST_3V3'})
part('U703',{1:'USB_CC1',2:'USB_CC2',3:'HOST_GND',4:'CC_VBUS_DET',7:'CC_HIGH_N',8:'CC_MODE2',10:'HOST_GND',11:'HOST_GND',12:'HOST_3V3'})
for k in [5,6,9]:assert nets[f'U703.{k}'].startswith('unconnected-')
part('U704',{2:'CC_HIGH_N',3:'HOST_GND',4:'HOST_POWER_EN',5:'HOST_3V3'})
part('U705',{1:'HOST_5V',2:'HOST_GND',3:'HOST_POWER_EN',5:'HOST_ILIM',6:'HOST_DCDC_IN'})
part('U706',{1:'HOST_DCDC_IN',12:'GND',13:'USB_RAW',23:'HOST_GND',24:'HOST_GND'})
part('U707',{1:'USB_RUN_READY',2:'GND',3:'USB_RAW',4:'USB_RUN_CT',5:'USB_RUN_SENSE',6:'USB_RAW'})
part('U2',{2:'+3V3',4:'ADS_DRDY',5:'MCU_RESET',6:'MCU_PWDN',7:'MCU_START',12:'OLED_SDA',13:'USB_MCU_DM',14:'USB_MCU_DP',17:'OLED_SCL',18:'MCU_CS',19:'MCU_MOSI',20:'MCU_SCLK',21:'ADS_MISO',31:'LED_RUN_K',32:'LED_WIFI_K',33:'LED_FAULT_K'})
for k in [28,29,30]:assert nets[f'U2.{k}'].startswith('unconnected-') # OPI PSRAM pins excluded
part('Q701',{1:'USB_RUN_GATE',2:'USB_RUN_SOURCE',3:'CHG_SYS'});part('Q702',{1:'USB_RUN_GATE',2:'USB_RUN_SOURCE',3:'ACQ_INPUT'});part('Q703',{1:'USB_RUN_BASE',2:'GND',3:'USB_RUN_SINK'})
part('U601',{1:'CHG_DETECT',2:'CHG_STAT',3:'CHG_CE',4:'GND',5:'GND',6:'GND',7:'CHG_TS',8:'CHG_ILIM',9:'CHG_PG',10:'CHG_ISET',11:'CHG_REGN',12:'CHG_BOOT',13:'PACK_POS',14:'PACK_POS',15:'CHG_SYS',16:'CHG_SYS',17:'CHG_SW',18:'CHG_SW',19:'GND',20:'GND',21:'CHG_PMID',22:'CHG_PMID',23:'USB5',24:'CHG_DETECT',25:'GND'})
part('U602',{1:'DSG_GATE',2:'CHARGE_GATE',3:'PROT_VM',4:'PROT_VC',5:'PROT_VDD',6:'RAW_BMINUS'})
part('U603',{1:'BAL_VC2',2:'BAL_VC1',3:'BAL_VC1_CB',4:'BAL_CD',5:'RAW_BMINUS',6:'BAL_ENABLE',7:'BAL_VDD',8:'BAL_OV_ALARM',9:'RAW_BMINUS'})
part('J401',{1:'RAW_BPLUS',2:'RAW_MID',3:'RAW_BMINUS'});part('J602',{1:'CHG_TS',2:'GND'})
for r,source,gate in [('Q601','DSG_SOURCE','DSG_GATE'),('Q602','GND','CHARGE_GATE')]:part(r,{1:source,2:source,3:source,4:gate,5:'BMS_DRAINS'})
part('Q603',{1:'RUN_GATE',2:'RUN_SOURCES',3:'PACK_POS'});part('Q604',{1:'RUN_GATE',2:'RUN_SOURCES',3:'ACQ_INPUT'});part('Q606',{1:'USB_INHIBIT_B',2:'GND',3:'RUN_BASE'})
part('R647',{1:'USB_RAW',2:'USB_INHIBIT_B'});part('R607',{1:'VBAT_SW',2:'CHG_CE'});part('R608',{1:'CHG_CE',2:'GND'});part('F401',{1:'ACQ_INPUT'});part('F602',{1:'USB_RAW',2:'USB5'})
part('J201',{1:'REF_RAW',2:'BIAS_ELECTRODE'});part('D801',{1:'-2V5A',2:'+2V5A',3:nets['R211.2'].rsplit('/',1)[-1]});assert nets['D801.3']==nets['R212.1']
for ch in range(1,9):
 for j,pol in enumerate('PN'):
  base=100+10*ch;part('R'+str(base+(1 if pol=='P' else 3)),{1:f'E{ch}{pol}',2:f'CLAMP{ch}{pol}'})
  part('R'+str(base+(2 if pol=='P' else 4)),{1:f'AFE_RET_{ch}{pol}',2:f'AIN{ch}{pol}'})
  part('R'+str(810+2*(ch-1)+j),{1:f'CLAMP{ch}{pol}',2:f'AFE_RET_{ch}{pol}'})
  header='J801' if ch<=4 else 'J802';offset=((ch-1)%4)*4+j*2+1;part(header,{offset:f'CLAMP{ch}{pol}',offset+1:f'AFE_RET_{ch}{pol}'})
for r in ['J801','J802']:part(r,{17:'+2V5A',18:'-2V5A',19:'GND',20:'GND'})
part('J803',{1:'+3V3',2:'GND',3:'OLED_SDA',4:'OLED_SCL'})
for pinno in ['A1','A12','B1','B12','S1']:pin('J601.'+pinno,'HOST_GND')
for pinno in ['A4','A9','B4','B9']:pin('J601.'+pinno,'HOST_RAW')
for pinno,want in {'A5':'USB_CC1','B5':'USB_CC2','A6':'USB_HOST_DP','B6':'USB_HOST_DP','A7':'USB_HOST_DM','B7':'USB_HOST_DM'}.items():pin('J601.'+pinno,want)
b=p.LoadBoard(str(file));fps={f.GetReference():f for f in b.GetFootprints()};actual={}
for r,f in fps.items():
 for q in f.Pads():
  if q.GetNumber():actual.setdefault(r+'.'+q.GetNumber(),set()).add(q.GetNetname())
assert all(actual.get(k)=={v} for k,v in nets.items()),[(k,v,actual.get(k)) for k,v in nets.items() if actual.get(k)!={v}]
with (ROOT/'BOM.csv').open(encoding='utf-8-sig') as f:rows={row['Reference']:row for row in csv.DictReader(f)}
assert len(fps)==len(rows)==332
for r,f in fps.items():assert rows[r]['Value']==f.GetValue() and rows[r]['Footprint']==f.GetFPIDAsString(),r
assert fps['U2'].GetValue()=='ESP32-S3-WROOM-1-N16R8'
for r in ['C220','SW301','SW302']:assert fps[r].GetLayer()==p.F_Cu
def pad(r,n):return next(q for q in fps[r].Pads() if q.GetNumber()==str(n))
xs={pad(f'J{100+i}',1).GetPosition().x for i in range(1,9)};xs.update(pad('J201',n).GetPosition().x for n in [1,2]);assert len(xs)==1
host=set(json.loads((ROOT/'review/host_domain_nets.json').read_text()));assert 'GND' not in host and 'HOST_GND' in host
for r in ['J801','J802','J803','J201','J401']:assert not any(q.GetNetname() in host for q in fps[r].Pads())
assert {nets['U701.'+str(n)] for n in range(1,9)}<=host
assert not {nets['U701.'+str(n)] for n in range(9,17)}&host
assert {nets['U706.'+str(n)] for n in [1,23,24]}<=host
assert not {nets['U706.'+str(n)] for n in [12,13]}&host
# Independent physical bridge test for pad/track/via copper across all layers.
object_labels={}
objects={ly:[] for ly in [p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]}
for item in [q for f in fps.values() for q in f.Pads()]+list(b.GetTracks()):
 for ly in objects:
  if item.IsOnLayer(ly) and not (isinstance(item,p.PAD) and item.GetAttribute()==p.PAD_ATTRIB_NPTH):
   sh=item.GetEffectiveShape(ly);object_labels[id(sh)]=(item.GetNetname(),str(item.m_Uuid.AsString()));objects[ly].append((item.GetNetname() in host,sh,sh.BBox()))
count=0
for ly,items in objects.items():
 for ishost,shape,box in items:
  if not ishost:continue
  near=box;near.Inflate(p.FromMM(8))
  for other,sh,bb in items:
   if not other and bb.Intersects(near):assert not shape.Collide(sh,p.FromMM(7.999)),('USB isolation copper bridge',ly,object_labels[id(shape)],object_labels[id(sh)]);count+=1
assert not any(not isinstance(tr,p.PCB_VIA) and tr.GetLayer()==p.In1_Cu for tr in b.GetTracks())
report={'revision':'D','components':len(fps),'ref_pin_pairs_checked':len(nets),'independent_pin_invariants':len(checked),'pcb_pad_net_mismatches':0,'host_system_pad_track_via_gap_mm_min_rule':8,'isolation_near_pairs_checked':count,'electrode_connector_same_column':True,'N16R8_reserved_GPIO35_36_37_unused':True,'charge_and_record_separate_modes':True,'SYS_not_directly_connected_to_BAT':True,'USB_data_not_connected_to_charger_DPDM':True,'scope':'Static pin/topology/copper checks, not USB eye, patient leakage, dielectric testing or hardware qualification','sha256_pcb':hashlib.sha256(file.read_bytes()).hexdigest()}
(ROOT/'review/REV_D_ELECTRICAL_AUDIT.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
