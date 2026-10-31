from pathlib import Path
import pcbnew as p,wx
wx.DisableAsserts();path=Path('logs/afe_shadow_candidate/YuEEG_H_AFE.kicad_pcb');pro=path.with_suffix('.kicad_pro').read_bytes();b=p.LoadBoard(str(path));print('Loaded',type(b).__name__,flush=True);p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(path),b);path.with_suffix('.kicad_pro').write_bytes(pro);print('AFE candidate zones filled')
