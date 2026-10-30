from pathlib import Path
s=Path('logs/add_h_ground_zones.py').read_text().replace("for board in ['afe','digital','power']:","for board in ['digital']:").replace("path=R/board/('YuEEG_H_'+board.upper()+'.kicad_pcb')","path=Path('logs/RevH_DigitalCandidate/YuEEG_H_DIGITAL.kicad_pcb')")
exec(s)
