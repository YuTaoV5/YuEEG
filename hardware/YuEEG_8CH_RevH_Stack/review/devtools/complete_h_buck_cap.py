from pathlib import Path
s=Path('logs/complete_h_endpoint_routes.py').read_text().replace('drc_ground_fill.json','drc_buck_cap.json').replace('endpoint_route_results.json','buck_cap_routes.json')
# Surface pads can now be on either assembly side.
s=s.replace("sl=0 if isinstance(a,(p.PAD,p.PCB_VIA)) else ns['layers'].index(a.GetLayer());el=0 if isinstance(c,(p.PAD,p.PCB_VIA)) else ns['layers'].index(c.GetLayer())","sl=0 if isinstance(a,p.PCB_VIA) else ns['layers'].index(a.GetLayer());el=0 if isinstance(c,p.PCB_VIA) else ns['layers'].index(c.GetLayer())")
exec(s)
