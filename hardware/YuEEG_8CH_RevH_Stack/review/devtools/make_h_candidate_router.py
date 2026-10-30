from pathlib import Path
s=Path('logs/route_h_digital.py').read_text().replace("Path('hardware/YuEEG_8CH_RevH_Stack/digital')","Path('logs/RevH_DigitalCandidate')").replace("D=R/'review'","D=R").replace("=='In1.Cu'","in ['In1.Cu','In3.Cu']").replace('protected analog paths, In1 reserved for ground','protected local critical paths, In1 and In3 reserved for ground')
Path('logs/route_h_candidate.py').write_text(s)
