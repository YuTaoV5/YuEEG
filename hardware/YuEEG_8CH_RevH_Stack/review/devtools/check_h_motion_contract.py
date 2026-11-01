from pathlib import Path
import json,hashlib,re,xml.etree.ElementTree as E
H=Path('hardware/YuEEG_8CH_RevH_Stack');f=Path('Firmware/ads1299_driver/YuEEG_SPI3.h');text=f.read_text(encoding='utf8');pins={}
for net in E.parse(H/'digital/review/netlist.xml').findall('./nets/net'):
 for node in net.findall('node'):
  if node.get('ref')!='U2':continue
  function=node.get('pinfunction','')
  if re.fullmatch(r'IO\d+',function):pins[int(function[2:])]=net.get('name')
  elif function in ['TXD0','RXD0']:
   assert node.get('pin')==('37' if function=='TXD0' else '36')
   pins[43 if function=='TXD0' else 44]=net.get('name')
contract={'SPI3_PANEL_CS':(2,'AM_CS_A'),'SPI3_IMU_CS':(43,'IMU_CS_MCU'),'IMU_DRDY_GPIO':(44,'IMU_DRDY_MCU'),'SPI3_CLK_GPIO':(8,'AM_CLK_A'),'SPI3_MOSI_GPIO':(9,'AM_D0_A'),'SPI3_MISO_GPIO':(14,'AM_D1_A'),'SPI3_D2_GPIO':(15,'AM_D2_A'),'SPI3_D3_GPIO':(16,'AM_D3_A')}
for name,(gpio,net) in contract.items():
 m=re.search(r'\b'+name+r'\s*=\s*(\d+)',text);assert m and int(m[1])==gpio and pins[gpio]==net,(name,gpio,pins.get(gpio))
report={'status':'PASS','firmware_spi3_source_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'exported_netlist_sha256':hashlib.sha256((H/'digital/review/netlist.xml').read_bytes()).hexdigest(),'uart_alias_source':'https://documentation.espressif.com/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf, module pad37 TXD0=GPIO43; pad36 RXD0=GPIO44','pins':{k:{'gpio':v[0],'native_net':v[1]} for k,v in contract.items()},'scope':'Firmware named GPIO constants versus actual ESP32 pinfunction in native KiCad export. No electrical direction, timing or physical validation.'}
(H/'review/firmware_motion_contract.json').write_text(json.dumps(report,indent=2),encoding='utf8');print('PASS8 motion/display GPIOs vs native KiCad pin functions')
