"""Check current firmware battery wiring against the actual KiCad export and BOM."""
from pathlib import Path
import re,csv,json,xml.etree.ElementTree as E
R=Path('hardware/YuEEG_8CH_RevH_Stack');F=Path('Firmware/ads1299_driver/YuEEG_Battery.h');text=F.read_text();xml=E.parse(R/'digital/review/netlist.xml')
def constant(name):return int(re.search(r'\b'+name+r'\s*=\s*(\d+)',text).group(1))
pinmap={};gpio=None
for net in xml.findall('./nets/net'):
 for node in net.findall('node'):
  pinmap[node.get('ref')+'.'+node.get('pin')]=net.get('name')
  if node.get('ref')=='U2' and net.get('name')=='BAT_SENSE':gpio=int(re.fullmatch('IO(\d+)',node.get('pinfunction')).group(1))
assert gpio==constant('BATTERY_ADC_GPIO')==1
assert pinmap['R309.1']==pinmap['JH2.2']=='BAT_PROTECTED_SENSE'
assert pinmap['R309.2']==pinmap['R310.1']==pinmap['C305.1']=='BAT_SENSE'
assert pinmap['R310.2']==pinmap['C305.2']=='GND'
assert pinmap['JH2.1']=='SYS_5V' and pinmap['R309.1']!='SYS_5V'
bom={row['Reference']:row for row in csv.DictReader((R/'digital/BOM.csv').open(encoding='utf-8-sig'))}
def ohms(ref):
 val=bom[ref]['Value'].split()[0];return int(float(val[:-1])*1000) if val.endswith('k') else int(val)
assert ohms('R309')==constant('BATTERY_DIVIDER_TOP_OHMS')
assert ohms('R310')==constant('BATTERY_DIVIDER_BOTTOM_OHMS')
assert constant('BATTERY_LOW_ON_MV')<constant('BATTERY_LOW_OFF_MV')
result={'status':'PASS','adc_gpio_from_kicad_pinfunction':gpio,'divider_top_ohms':ohms('R309'),'divider_bottom_ohms':ohms('R310'),'divider_ratio':(ohms('R309')+ohms('R310'))/ohms('R310'),'measurement_source':'BAT_PROTECTED_SENSE, before boost; excludes regulated SYS_5V','scope':'Firmware constants versus exported physical pin function, net wiring and current BOM. No ADC calibration, timing or physical board validation.'}
(R/'review/firmware_battery_contract.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
