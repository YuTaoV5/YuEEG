from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
R=Path('hardware/YuEEG_8CH_RevH_Stack/mechanical/current');d=json.loads((R/'battery_side_envelope.json').read_text());r=next(r for r in d['candidate_layouts'] if r['name']==d['proposed_layout']);fig,ax=plt.subplots(figsize=(10,8))
def box(q,color,label,alpha=.6):
 x,y,x2,y2=q;ax.add_patch(Rectangle((x,y),x2-x,y2-y,facecolor=color,edgecolor='#34495e',alpha=alpha));ax.text((x+x2)/2,(y+y2)/2,label,ha='center',va='center',fontsize=11)
box([0,0,48,60],'#d7e3ee','');box(d['host_copper_xy_bounding_envelope_mm'],'#c9aedf','USB HOST envelope');box(d['screen_projection_xy_mm'],'#a9dad9','SCREEN\n34.14 x 42.74');box(d['afe_electrode_header_courtyard_xy_mm'],'#d6b16e','INPUT\naccess');box(r['battery_body_xy_mm'],'#b3cebb','NP-BX1\n29.9 x 42.7')
ax.annotate('6 mm board-edge gap',xy=(51,28),xytext=(55,49),arrowprops={'arrowstyle':'->'},fontsize=10)
ax.text(52,57,f"Conservative XY separation\n{r['host_xy_envelope_separation_mm']:.2f} mm",fontsize=11)
ax.set_xlim(-13,88);ax.set_ylim(64,-4);ax.set_aspect('equal');ax.set_xlabel('X / mm');ax.set_ylabel('Y / mm');ax.grid(alpha=.15);ax.set_title('USB stays on digital: proposed battery on right',fontsize=15,pad=18)
fig.text(.5,.035,'SCREENING ONLY: approximate battery size; no enclosure, contact holder, cable or complete 3D assembly',ha='center',color='#aa263d',fontsize=10);fig.tight_layout(rect=[0,.06,1,1]);fig.savefig(R/'battery_side_envelope.png',dpi=160);fig.savefig(R/'battery_side_envelope.svg');print('Conditional side envelope plotted')
