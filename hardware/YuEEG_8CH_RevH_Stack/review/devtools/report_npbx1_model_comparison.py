from pathlib import Path
import json,hashlib,math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
H=Path('hardware/YuEEG_8CH_RevH_Stack');M=H/'mechanical/current';path=M/'npbx1_user_model_comparison.json'
record=json.loads(path.read_text(encoding='utf8'));confirmed=json.loads((M/'npbx1_user_terminal_order.json').read_text(encoding='utf8'));assert confirmed['cad_mapping_confirmed'];rows=record['recess_base_faces'];mapping=confirmed['confirmed_model_labels'];assert abs(math.dist(rows[1]['center_xy_mm'],rows[3]['center_xy_mm'])-10)<1e-8
record.update(status='USER_MODEL_GEOMETRY_WITH_USER_POLARITY_NOT_SONY_TOLERANCE',source_path='User-supplied NPBX1.STEP (original not distributed)',view_convention='Contact face viewed from +Z toward-Z; model+X right,+Y up; A-D left to right. Electrical labels come from separate user confirmation.',terminal_confirmation_sha256=hashlib.sha256((M/'npbx1_user_terminal_order.json').read_bytes()).hexdigest(),design_action='PowerPCB uses confirmedD+/B- pair; delivered pack / holder tolerances and compression remain unqualified.',remaining=['Whether the replacement-pack model matches the delivered Sony pack','Body curved extrema, supplier tolerances, contact material, stop/retention and compression','Screen-back/FPC Z datum independently unresolved'],redistribution='User explicitly authorized derived dimensions, diagrams, hashes and resulting PCB/docs on2026-11-01. Original STEP/JPG excluded.')
for row in rows:row['polarity']=mapping[row['label']]
path.write_text(json.dumps(record,indent=2),encoding='utf8')
fig,ax=plt.subplots(figsize=(11,4.8));ax.add_patch(Rectangle((-14.65,-4.5),29.29,9,fill=False,edgecolor='#555',lw=2))
short={'BAT+':'+','BAT-':'-','C':'C','T':'T'}
for row in rows:
 b=row['bounds_xyz_mm'];x,y=row['center_xy_mm'];ax.add_patch(Rectangle((b[0],b[1]),row['width_mm'],row['height_mm'],facecolor='#cfac4b',edgecolor='black'));ax.text(x,y,row['label']+' / '+short[row['polarity']],ha='center',va='center',weight='bold');ax.text(x,4.9,f'X={x:.3f}',ha='center',fontsize=9)
ax.annotate('',(rows[1]['center_xy_mm'][0],-.5),(rows[3]['center_xy_mm'][0],-.5),arrowprops=dict(arrowstyle='<->'));ax.text(3.9,-1.25,'B- to D+ =10.000mm',ha='center');ax.text(0,-6.2,'Recess bases Z=20.625; front plane Z=21.375; nominal depth0.750mm\nElectrical labels: user confirmed. Model identifies a RAYPRO replacement pack.\nVertex outline only; delivered Sony fit and holder tolerances remain unverified.',ha='center',fontsize=9)
ax.set(xlim=(-16,16),ylim=(-8,7),xlabel='Model X /mm',ylabel='Model Y /mm',title='NP-BX1 user-model contact face, looking from+Z');ax.set_aspect('equal');ax.grid(alpha=.15);fig.tight_layout();fig.savefig(M/'npbx1_user_model_comparison.png',dpi=180);fig.savefig(M/'npbx1_user_model_comparison.svg');print('Plotted confirmed terminal labels from derived JSON; original STEP/JPG neither read nor copied.')
