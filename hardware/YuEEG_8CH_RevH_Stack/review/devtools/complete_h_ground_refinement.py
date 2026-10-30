from pathlib import Path
s=Path('logs/complete_h_endpoint_routes.py').read_text().replace('drc_ground_fill.json','drc_ground_refinement.json').replace('endpoint_route_results.json','ground_refinement_routes.json')
exec(s)
