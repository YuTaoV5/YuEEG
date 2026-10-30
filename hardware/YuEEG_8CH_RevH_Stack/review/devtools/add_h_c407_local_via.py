from pathlib import Path
import pcbnew as p,wx,json,subprocess
wx.DisableAsserts();path=Path('hardware/YuEEG_8CH_RevH_Stack/digital/YuEEG_H_DIGITAL.kicad_pcb');original=path.read_bytes();b=p.LoadBoard(str(path));f=next(f for f in b.GetFootprints() if f.GetReference()=='C407');q=next(q for q in f.Pads() if q.GetNetname()=='GND');end=p.VECTOR2I(p.FromMM(26.475),p.FromMM(39.75))
assert not any(isinstance(t,p.PCB_VIA) and t.GetPosition()==end for t in b.GetTracks())
t=p.PCB_TRACK(b);t.SetStart(q.GetPosition());t.SetEnd(end);t.SetLayer(p.F_Cu);t.SetWidth(p.FromMM(.4));t.SetNet(q.GetNet());b.Add(t)
v=p.PCB_VIA(b);v.SetPosition(end);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetViaType(p.VIATYPE_THROUGH);v.SetWidth(p.FromMM(.45));v.SetDrill(p.FromMM(.2));v.SetNet(q.GetNet());b.Add(v)
p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(path),b);report=path.parent/'review/drc_c407_ground.json';subprocess.run(['X:/SoftWare/Kicad/bin/kicad-cli.exe','pcb','drc','--schematic-parity','--format','json','-o',str(report),str(path)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True);d=json.loads(report.read_text())
if d['violations'] or d['unconnected_items'] or d['schematic_parity']:path.write_bytes(original);print(json.dumps(d['violations'],ensure_ascii=False));raise RuntimeError('Local ground via failed; restored PCB')
(path.parent/'review/c407_local_ground_via.json').write_text(json.dumps({'via_xy_mm':[26.475,39.75],'diameter_mm':.45,'drill_mm':.2,'stub_width_mm':.4,'stub_length_mm':p.ToMM(t.GetLength()),'native_drc':'zero violations, unconnected and parity issues','scope':'Local ground return to digital ground planes; physical ripple and transient measurements remain pending'},indent=2));print('C407 local ground return reduced to',p.ToMM(t.GetLength()),'mm')
