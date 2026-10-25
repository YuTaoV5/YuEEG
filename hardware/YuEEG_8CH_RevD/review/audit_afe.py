"""Independent datasheet-based electrical invariants against exported KiCad nets and PCB.
This is a connectivity / design-budget audit, not SPICE, EMC or patient-safety validation.
"""
from pathlib import Path
import xml.etree.ElementTree as ET,json,math,pcbnew as p,hashlib,collections
ROOT=Path(__file__).resolve().parents[1];t=ET.parse(ROOT/'review/netlist.xml')
nets={q.get('ref')+'.'+q.get('pin'):n.get('name') for n in t.findall('./nets/net') for q in n.findall('node')}
checks=[]
def pin(k,w):
    got=nets[k];assert got.rsplit('/',1)[-1]==w,(k,w,got);checks.append([k,w])
# ADS1299 Rev C pin-function table and Figure 78, independent of generator expectation file.
for num in [19,21,22,54,56,59]:pin(f'U1.{num}','+2V5A')
for num in [20,23,32,53,57,58,25,60,62]:pin(f'U1.{num}','-2V5A')
for num in [31,33,41,49,51]:pin(f'U1.{num}','GND')
for num in [48,50]:pin(f'U1.{num}','+3V3')
for num in [17,18,27,29,37,64]:assert nets[f'U1.{num}'].startswith('unconnected-')
for i in [202,203,*range(220,225)]:pin(f'C{i}.2','-2V5A')
pin('C220.1','VCAP1')
for i in range(210,216):pin(f'C{i}.1','+2V5A');pin(f'C{i}.2','-2V5A')
for ch in range(1,9):
    n=100+10*ch
    pin(f'U1.{18-2*ch}',f'AIN{ch}P');pin(f'U1.{17-2*ch}',f'AIN{ch}N')
    pin(f'J{100+ch}.1',f'E{ch}P');pin(f'R{n+5}.1','REF_RAW');pin(f'R{n+5}.2',f'E{ch}N')
    for k in [1,2]:pin(f'D{n+k}.1','-2V5A');pin(f'D{n+k}.2','+2V5A');pin(f'D{n+k}.3',f'CLAMP{ch}{"P" if k==1 else "N"}')
pin('D403.1','VBAT_SW');pin('D403.2','+4V4_PRE');pin('J201.1','REF_RAW');pin('J201.2','BIAS_ELECTRODE');pin('R211.1','BIAS_OUT');pin('R212.2','BIAS_ELECTRODE')
pin('R202.1','GND');pin('R202.2','ADS_RESET');pin('R203.1','GND');pin('R203.2','ADS_PWDN')
for k,w in {'U403.1':'+4V4_PRE','U403.2':'GND','U403.3':'+4V4_PRE','U403.4':'POS_NR','U403.5':'+2V5A',
 'U404.1':'NEG_RAW','U404.2':'+4V4_PRE','U404.3':'CFLY_MINUS','U404.4':'GND','U404.5':'CFLY_PLUS',
 'U405.1':'GND','U405.2':'NEG_RAW','U405.3':'+3V3','U405.4':'NEG_NR','U405.5':'-2V5A',
 'D402.1':'-2V5A','D402.2':'NEG_RAW','C418.1':'GND','C418.2':'NEG_RAW'}.items():pin(k,w)
assert '+5VA' not in nets.values()
b=p.LoadBoard(str(ROOT/'YuEEG_8CH_RevD.kicad_pcb'));fps={f.GetReference():f for f in b.GetFootprints()};actual={}
for r,f in fps.items():
    for pad in f.Pads():
        if pad.GetNumber():actual.setdefault(r+'.'+pad.GetNumber(),set()).add(pad.GetNetname())
assert all(actual.get(k)=={v} for k,v in nets.items()),[(k,v,actual.get(k)) for k,v in nets.items() if actual.get(k)!={v}]
for r in ['C220','SW301','SW302','U401','C402','C405']:assert fps[r].GetLayer()==p.F_Cu
assert all(len([q for q in fps[f'J{100+i}'].Pads() if q.GetNumber()])==1 for i in range(1,9))
assert not any(not isinstance(tr,p.PCB_VIA) and tr.GetLayer()==p.In1_Cu for tr in b.GetTracks())
for r in ['U403','U404','U405']:assert fps[r].GetFPIDAsString()=='Package_TO_SOT_SMD:SOT-23-5'
pre=1.185*(1+27.4/10)
pre_lo=1.185*.975*(1+27.4*.999/(10*1.001))-.00316
pre_hi=1.185*1.025*(1+27.4*1.001/(10*.999))+.00316
digital_lo=.8*.965*(1+31.2*.999/(10*1.001))-.4e-6*31.2e3
digital_hi=.8*1.04*(1+31.2*1.001/(10*.999))+.4e-6*31.2e3
# Worst-case FB leakage of 400nA is specified at VFB=1.2V, not 0.8V.
# Applying it unchanged is intentionally conservative and reveals a qualification concern.
assert 4.75<2.5*.99+2.5*.97 and 2.5*1.01+2.5*1.03<5.25
assert pre_hi<5.25
project=json.loads((ROOT/'YuEEG_8CH_RevD.kicad_pro').read_text());assert project['board']['design_settings']['drc_exclusions']==[]
report={'revision':'D','components':len(fps),'schematic_sheets':13,'exported_ref_pin_pairs':len(nets),'independent_pin_invariants':len(checks),
 'pcb_pad_net_mismatches':0,'rail_budget_V':{'analog_span':[4.9,5.1],'bias_midpoint':[-.05,.05],'pre_regulator_nominal':pre,'pre_regulator_conservative':[pre_lo,pre_hi],
 'digital_with_full_400nA_FB_leakage':[digital_lo,digital_hi]},
 'startup':{'tPOR_s':2**18/2048000,'VCAP1_tau_nominal_s':9800*100e-6,'VCAP1_nominal_1p1V_time_s':-9800*100e-6*math.log(1-1.1/1.2),'initial_bench_wait_after_PWDN_high_s':10,'automatic_rail_monitor':False},
 'differential_full_scale_V_at_gain24':4.5/24,'rf_filter_nominal_Hz':1/(2*math.pi*19960*1e-9),'bias_feedback_pole_Hz':1/(2*math.pi*1e6*1.5e-9),
 'scope':'Static connectivity and conservative component budgets only. Actual power-up/noise/BIAS/ESD/safety require bench evidence.',
 'sha256_pcb':hashlib.sha256((ROOT/'YuEEG_8CH_RevD.kicad_pcb').read_bytes()).hexdigest()}
(ROOT/'review/ELECTRICAL_AUDIT.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

