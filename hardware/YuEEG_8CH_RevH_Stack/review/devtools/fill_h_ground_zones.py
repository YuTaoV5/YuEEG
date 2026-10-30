from pathlib import Path
import pcbnew as p
R=Path('hardware/YuEEG_8CH_RevH_Stack')
for board in ['afe','digital','power']:
 path=R/board/('YuEEG_H_'+board.upper()+'.kicad_pcb');b=p.LoadBoard(str(path));p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(path),b);print(board,'zones filled')
