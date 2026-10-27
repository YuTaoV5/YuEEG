"""Independent two-board pin, assembly and isolation invariants for Rev F."""
from pathlib import Path
import sys,json,csv,hashlib,xml.etree.ElementTree as ET,pcbnew as p
BASE=Path(__file__).resolve().parents[1]
ROOT=BASE.parents[1]/'logs/RevF_layout70d' if '--layout70d' in sys.argv else BASE
checked=[]
def inspect(folder,stem,count,pairs,host_name):
 tree=ET.parse(folder/'review/netlist.xml')
 nets={q.get('ref')+'.'+q.get('pin'):n.get('name') for n in tree.findall('./nets/net') for q in n.findall('node')}
 b=p.LoadBoard(str(folder/(stem+'.kicad_pcb')));fps={f.GetReference():f for f in b.GetFootprints()};actual={}
 for r,f in fps.items():
  assert f.GetLayer()==p.F_Cu,('bottom component',r)
  for q in f.Pads():
   if q.GetNumber():actual.setdefault(r+'.'+q.GetNumber(),set()).add(q.GetNetname())
 assert len(fps)==count and len(nets)==pairs
 assert all(actual.get(k)=={v} for k,v in nets.items())
 with (folder/'BOM.csv').open(encoding='utf-8-sig') as f:rows={r['Reference']:r for r in csv.DictReader(f)}
 assert len(rows)==count
 for r,f in fps.items():assert rows[r]['Value']==f.GetValue() and rows[r]['Footprint']==f.GetFPIDAsString(),r
 host=set(json.loads((folder/'review/host_domain_nets.json').read_text()));assert host_name in host and 'GND' not in host
 objects={ly:[] for ly in [p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]}
 for item in [q for f in fps.values() for q in f.Pads()]+list(b.GetTracks()):
  for ly in objects:
   if item.IsOnLayer(ly) and not (isinstance(item,p.PAD) and item.GetAttribute()==p.PAD_ATTRIB_NPTH):
    sh=item.GetEffectiveShape(ly);objects[ly].append((item.GetNetname() in host,sh,sh.BBox()))
 near_pairs=0
 for ly,items in objects.items():
  for ishost,sh,box in items:
   if not ishost:continue
   box.Inflate(p.FromMM(8))
   for other,shape,bb in items:
    if not other and box.Intersects(bb):
     assert not sh.Collide(shape,p.FromMM(7.999)),('isolation copper gap',stem,ly)
     near_pairs+=1
 assert not any(not isinstance(t,p.PCB_VIA) and t.GetLayer()==p.In1_Cu for t in b.GetTracks())
 def part(r,m):
  for n,w in m.items():
   got=nets[r+'.'+str(n)].rsplit('/',1)[-1];assert got==w,(stem,r,n,w,got);checked.append([stem,r,str(n),w])
 return b,fps,nets,part,near_pairs
b,fps,nets,part,nnear=inspect(ROOT,'YuEEG_8CH_RevF',305,876,'HOST_GND')
part('U701',{1:'DATA_5V',2:'HOST_GND',3:'USB_VDD1',4:'USB_VDD1',5:'USB_VDD1',6:'USB_UP_DM',7:'USB_UP_DP',8:'HOST_GND',9:'GND',10:'USB_DOWN_DP',11:'USB_DOWN_DM',12:'+3V3',13:'+3V3',14:'+3V3',15:'GND',16:'+3V3'})
part('U2',{2:'+3V3',4:'ADS_DRDY',5:'MCU_RESET',6:'MCU_PWDN',7:'MCU_START',12:'AM_CLK_A',13:'USB_MCU_DM',14:'USB_MCU_DP',17:'AM_D0_A',18:'MCU_CS',19:'MCU_MOSI',20:'MCU_SCLK',21:'ADS_MISO',31:'LED_RUN_K',32:'LED_WIFI_K',33:'LED_FAULT_K'})
for n in [28,29,30]:assert nets[f'U2.{n}'].startswith('unconnected-')
part('J1202',{1:'PACK_POS',2:'GND',3:'CHG_TS',4:'CHG_CE',5:'USB5',6:'CHG_PG'})
part('J1301',{1:'REF_RAW',2:'BIAS_ELECTRODE',**{11-ch:f'E{ch}P' for ch in range(1,9)}})
assert len({q.GetPosition().x for q in fps['J1301'].Pads()})==1
for ch in range(1,9):
 base=100+10*ch;part(f'R{base+3}',{1:'REF_RAW',2:f'CLAMP{ch}N'});assert f'R{base+5}' not in fps
assert not any(r in fps for r in ['U601','U706','U707','Q701','Q702','Q703','J801','J802','J803'])
assert {k for k,v in nets.items() if v=='USB5'}=={'J1202.5','R663.1'}
part('R607',{1:'VBAT_SW',2:'CHG_CE'});part('R608',{1:'CHG_CE',2:'GND'})
part('U1004',{1:'+3V3',2:'+3V3',10:'GND',11:'+3V3',12:'GND',13:'GND',22:'AM_OE_N',23:'AM_1V8',24:'AM_1V8'})
for i,name in enumerate(['CS','CLK','D0','D1','D2','D3','RST']):
 part('U1004',{3+i:'AM_'+name+'_A',21-i:'AM_'+name+'_B'})
 part('R'+str(1021+i),{1:'AM_'+name+'_B',2:'AM_'+name+'_P'});part('J1001',{5+i:'AM_'+name+'_P'})
part('J1001',{1:'AM_RAW',2:'AM_2V8',3:'AM_1V8',12:'GND',16:'AM_IM1',18:'GND',19:'GND',20:'GND'})
assert fps['U2'].GetValue()=='ESP32-S3-WROOM-1-N16R8'
for r in ['SW301','SW302','SW1001']:assert fps[r].GetFPIDAsString()=='Button_Switch_SMD:SW_SPST_PTS645Sx43SMTR92'
mainhash=hashlib.sha256((ROOT/'YuEEG_8CH_RevF.kicad_pcb').read_bytes()).hexdigest()
aux=BASE/'isolated_power';bb,ff,nn,pp,anear=inspect(aux,'YuEEG_8CH_RevF_POWER',50,160,'CHARGE_HOST_GND')
pp('J1204',{1:'PACK_POS',2:'GND',3:'CHG_TS',4:'CHG_CE',5:'USB5',6:'CHG_PG'})
pp('U706',{1:'CHARGE_HOST_DCDC_IN',12:'GND',13:'USB_RAW',23:'CHARGE_HOST_GND',24:'CHARGE_HOST_GND'})
pp('U601',{1:'CHG_DETECT',2:'CHG_STAT',3:'CHG_CE',4:'GND',5:'GND',6:'GND',7:'CHG_TS',8:'CHG_ILIM',9:'CHG_PG',10:'CHG_ISET',11:'CHG_REGN',12:'CHG_BOOT',13:'PACK_POS',14:'PACK_POS',15:'CHG_SYS',16:'CHG_SYS',17:'CHG_SW',18:'CHG_SW',19:'GND',20:'GND',21:'CHG_PMID',22:'CHG_PMID',23:'USB5',24:'CHG_DETECT',25:'GND'})
pp('R1205',{1:'USB5',2:'CHG_CE'})
assert ff['R1205'].GetValue().startswith('1M')
# CE input leakage specification includes its internal pull-down; do not count twice.
ce_default_available_A=(4.75-1.8)/1e6;assert ce_default_available_A>2.5e-6
rdown=1/(1/105000+1/(105000+49350));ce_off=5.25*rdown/(950000+rdown);assert ce_off<.4
report={'revision':'F','main_components':305,'power_components':50,'main_ref_pin_pairs':876,'power_ref_pin_pairs':160,'top_only_footprints':True,'independent_pin_invariants':len(checked),'isolation_gap_mm':8,'isolation_near_pairs_checked':nnear+anear,'quiet_In1_without_signal_tracks':True,'charging_ce_default_available_A_at_1p8V':ce_default_available_A,'charging_ce_off_upper_bound_V':ce_off,'charge_nominal_V':8.2,'charge_max_V':8.241,'charge_nominal_A':.299,'sha256_pcb':mainhash,'sha256_power_pcb':hashlib.sha256((aux/'YuEEG_8CH_RevF_POWER.kicad_pcb').read_bytes()).hexdigest(),'scope':'Static connectivity, copper and assembly invariants only; hardware qualification pending.'}
(ROOT/'review/REV_F_ELECTRICAL_AUDIT.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
