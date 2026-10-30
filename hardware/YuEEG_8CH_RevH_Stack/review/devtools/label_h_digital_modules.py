from pathlib import Path
ns={};exec(Path('logs/clean_h_silkscreen.py').read_text().split("for board in ['afe'")[0],ns)
p,text,frame=[ns[k] for k in ['p','text','frame']];path=Path('hardware/YuEEG_8CH_RevH_Stack/digital/YuEEG_H_DIGITAL.kicad_pcb');b=p.LoadBoard(str(path))
text(b,'YuEEG / DIGITAL',34,2,1);text(b,'REV H / 6L',34,4,.8);text(b,'ISOLATED USB',33,44.3,1.05);text(b,'NO CHARGING',33,46.3,.8)
for bounds in [(.6,2.2,25.5,22.8),(26,6.5,38.5,24.8),(.6,23.5,14,35.3),(18.5,26,39.5,40.1)]:frame(b,*bounds)
text(b,'ESP32-S3',15,3.5,.9,p.B_SilkS);text(b,'DISPLAY LOGIC',32,7.6,.8,p.B_SilkS);text(b,'microSD',7.2,24.8,.85,p.B_SilkS);text(b,'3V3 / POWER',28,39,.8,p.B_SilkS);text(b,'AFE LINK',46.5,21,.8,p.B_SilkS,90);text(b,'USB HOST',38,58,.85,p.B_SilkS)
p.SaveBoard(str(path),b);print('Digital functional labels and module boundaries added')
