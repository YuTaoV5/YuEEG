from pathlib import Path
R=Path('hardware/YuEEG_8CH_RevH_Stack')
for f in list((R/'digital').glob('*.kicad_sch'))+[R/'digital/BOM.csv',R/'digital/YuEEG_H_DIGITAL.kicad_pcb']:
 s=f.read_text(encoding='utf-8-sig').replace('POWER INPUT: +,+,GND,GND','POWER INPUT: 1=5V 2=CELL_SENSE 3/4=GND')
 f.write_text(s,encoding='utf8')
f=Path('logs/build_stack_circuits.py');s=f.read_text()
marker='# Independent camera-pack protection.'
assert marker in s
s=s.split(marker)[0]+"# Single-cell battery power is maintained independently.\nexec(Path('logs/build_h_1s_power.py').read_text())\n"
s=s.replace("contracts['AFE_DIGITAL']['19']='VBAT_SW'","contracts['AFE_DIGITAL']['19']='SYS_5V'")
s=s.replace("mp={pin.split('.',1)[1]:net for pin,net in expect.items() if pin.startswith(ref+'.')}","mp={pin.split('.',1)[1]:('SYS_5V' if net=='VBAT_SW' else net) for pin,net in expect.items() if pin.startswith(ref+'.')}\n   if board=='digital' and ref=='R309':mp['1']='BAT_PROTECTED_SENSE'")
s=s.replace("'POWER INPUT: +,+,GND,GND'","'POWER INPUT: 1=5V 2=CELL_SENSE 3/4=GND'")
s=s.replace("{'1':'VBAT_SW','2':'VBAT_SW','3':'GND','4':'GND'}","{'1':'SYS_5V','2':'BAT_PROTECTED_SENSE','3':'GND','4':'GND'}")
s=s.replace("['+3V3_AFE','GND','VBAT_SW']","['+3V3_AFE','GND','SYS_5V']").replace("['VBAT_SW','GND','+3V3'","['SYS_5V','GND','+3V3'")
f.write_text(s)
print('Source generator and PH4 labels adapted; do not regenerate routed boards unnecessarily')
