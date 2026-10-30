"""Point the offset MCU legend back to the ESP module, away from display ICs."""
from pathlib import Path
import pcbnew as p,json,subprocess,hashlib
R=Path('hardware/YuEEG_8CH_RevH_Stack/digital');path=R/'YuEEG_H_DIGITAL.kicad_pcb';old=path.read_bytes();b=p.LoadBoard(str(path))
for a,c in [((32.7,5.8),(25.0,5.8)),((25.0,5.8),(26.0,5.3)),((25.0,5.8),(26.0,6.3))]:
 g=p.PCB_SHAPE(b);g.SetShape(p.SHAPE_T_SEGMENT);g.SetStart(p.VECTOR2I(p.FromMM(a[0]),p.FromMM(a[1])));g.SetEnd(p.VECTOR2I(p.FromMM(c[0]),p.FromMM(c[1])));g.SetLayer(p.F_SilkS);g.SetWidth(p.FromMM(.1));b.Add(g)
p.SaveBoard(str(path),b);report=R/'review/drc_legend_arrow.json'
subprocess.run(['X:/SoftWare/Kicad/bin/kicad-cli.exe','pcb','drc','--schematic-parity','--format','json','-o',str(report),str(path)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True)
d=json.loads(report.read_text())
if any(d[k] for k in ['violations','unconnected_items','schematic_parity']):path.write_bytes(old);raise RuntimeError('Arrow DRC failed; restored')
e=R/'review/module_legends.json';d=json.loads(e.read_text());d['mcu_leader_arrow']='Points left from label to ESP module; label is offset to available silk space.';d['source_sha256']=hashlib.sha256(path.read_bytes()).hexdigest();e.write_text(json.dumps(d,indent=2));print('MCU legend arrow checked')
