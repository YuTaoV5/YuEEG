from pathlib import Path
s=Path('logs/complete_h_buck_cap.py').read_text().replace('drc_buck_cap.json','drc_current.json').replace('buck_cap_routes.json','status_relocation_routes.json')
exec(s)
