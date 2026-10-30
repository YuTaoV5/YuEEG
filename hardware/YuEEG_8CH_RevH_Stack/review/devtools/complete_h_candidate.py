from pathlib import Path
s=Path('logs/complete_h_endpoint_routes.py').read_text().replace("R=Path('hardware/YuEEG_8CH_RevH_Stack/digital');ns=load()","R=Path('logs/RevH_DigitalCandidate');ns=load(board_path=str(R/'YuEEG_H_DIGITAL.kicad_pcb'))").replace("R/'review/drc_ground_fill.json'","R/'drc_filled.json'").replace("R/'review/endpoint_route_results.json'","R/'endpoint_route_results.json'")
exec(s)
