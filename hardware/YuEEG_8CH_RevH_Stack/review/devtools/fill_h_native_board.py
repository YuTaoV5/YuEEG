from pathlib import Path
import sys,pcbnew as p,wx
wx.DisableAsserts();name=sys.argv[1];path=Path('hardware/YuEEG_8CH_RevH_Stack')/name/('YuEEG_H_'+name.upper()+'.kicad_pcb');pro=path.with_suffix('.kicad_pro').read_bytes();b=p.LoadBoard(str(path));p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(path),b);path.with_suffix('.kicad_pro').write_bytes(pro);print('Refilled',name)
