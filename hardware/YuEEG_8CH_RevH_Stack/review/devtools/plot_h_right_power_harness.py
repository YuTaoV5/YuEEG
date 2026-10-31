from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
H=Path('hardware/YuEEG_8CH_RevH_Stack');M=H/'mechanical/current';r=json.loads((M/'power_harness_routing_review.json').read_text());fig=plt.figure(figsize=(13,8));gs=fig.add_gridspec(2,2,width_ratios=[1.5,1]);ax=fig.add_subplot(gs[:,0]);zoom=fig.add_subplot(gs[0,1]);txt=fig.add_subplot(gs[1,1]);txt.axis('off')
def rect(ax,bb,color,label=None,alpha=.3):
 x,y,X,Y=bb;ax.add_patch(Rectangle((x,y),X-x,Y-y,edgecolor=color,facecolor=color,alpha=alpha));
 if label:ax.text((x+X)/2,(y+Y)/2,label,ha='center',va='center',fontsize=9)
rect(ax,[0,0,48,60],'#476c60','AFE / digital\n48 x 60',.12);rect(ax,[0,40.55,48,49.05],'#cc8747','USB barrier',.18);rect(ax,[0,49.05,48,60],'#79649b','USB HOST',.25);rect(ax,[54,0,83.9,42.7],'#7194ba','Sony NP-BX1\nbody envelope',.25);rect(ax,[6,.4,40.14,43.14],'#65a4b3',None,.09);ax.text(8,4,'Screen projection',fontsize=9)
fpc=[26.19,20.58,34.19,25.985];rect(ax,fpc,'#b68a15','FPC',.4);b=r['reference_mated_body_box_mm'];rect(ax,[b[0],b[1],b[3],b[4]],'#2d7a67','PH4 mate',.35);rect(ax,[41.55,29.55,44.45,48.45],'#666666',None,.15);ax.text(45,43,'JH1',fontsize=8)
colors=['#b94b40','#b58c20','#347ca4','#614b94']
for w,color in zip(r['current_right_exit_wires'],colors):
 pts=w['points'];ax.plot([p[0] for p in pts],[p[1] for p in pts],color=color,lw=2,label=w['pin']+': '+w['net'])
ax.text(54,-4,'Power strip / battery contacts pending',fontsize=8);ax.annotate('6 mm cable channel',(51,15),(60,51),arrowprops=dict(arrowstyle='->'),fontsize=9);ax.set(xlim=(-2,87),ylim=(64,-8),xlabel='Main X / mm',ylabel='Main Y / mm',title='Implemented right-facing port; conditional cable path');ax.set_aspect('equal');ax.grid(alpha=.15);ax.legend(loc='lower right',fontsize=8)
rect(zoom,fpc,'#b68a15','FPC',.35)
for w,color in zip(r['former_forward_exit_wires'],colors):
 pts=w['points'];zoom.plot([p[0] for p in pts],[p[1] for p in pts],color=color,lw=2)
zoom.set(xlim=(25,42),ylim=(30,20),xlabel='Main X / mm',ylabel='Main Y / mm',title='Former forward-exit bend assumption');zoom.set_aspect('equal');zoom.grid(alpha=.15)
lines=['Cable reservation / not assembly release','Wire OD <= 1.1 mm; bend radius 3.3 mm','Wire-axis Z = 2.75 mm is assumed','Current modeled FPC gap: '+f"{min(w['minimum_signed_gap_mm'] for w in r['current_right_exit_wires']):.2f}"+' mm','Channel nominal wall margin: 0.50 mm','','JH1 top solder/tail projection <= 1.5 mm','JH2 bottom solder/tails: trim <= 1.2 mm','Bottom tails overlap AFE C220 in XY','Full local gap / delivered cable need inspection','','No case, strain relief or power-strip path qualified']
for i,line in enumerate(lines):txt.text(0,1-i*.073,line,fontsize=9 if i else 11,va='top',weight='bold' if i==0 else 'normal')
fig.tight_layout();fig.savefig(M/'power_harness_routing_review.png',dpi=180);fig.savefig(M/'power_harness_routing_review.svg');print('Power harness review views saved')
