from pathlib import Path
import pcbnew as p,wx
wx.DisableAsserts();path=Path('logs/RevH_DigitalCandidate/YuEEG_H_DIGITAL.kicad_pcb');b=p.LoadBoard(str(path))
for f in b.GetFootprints():
 layer=p.B_Fab if f.GetLayer()==p.B_Cu else p.F_Fab
 f.Reference().SetLayer(layer);f.Reference().SetVisible(True);f.Value().SetLayer(layer);f.Value().SetVisible(True)
 if f.GetReference()=='J601':
  for g in f.GraphicalItems():
   if g.GetLayer()==p.F_SilkS:g.SetLayer(p.F_Fab)
p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(path),b)
print('Assembly references separated; USB shell outline moved to fabrication layer')
