from pathlib import Path
import sys,json,uuid,pcbnew as p,wx
wx.DisableAsserts();sys.path.insert(0,'hardware/YuEEG_8CH_RevG/review');from sexpr_io import loads,dumps,sub
path=Path('hardware/YuEEG_8CH_RevH_Stack/power/YuEEG_H_POWER.kicad_pcb');d=loads(path.read_text())
ids={'90f1c450-9c93-4b16-b7d5-e04a9ba9d6f4','84af6236-cc7c-4273-affd-e8824eb34569','0dca22bb-da8c-41a4-8d51-1bcebe0823b5','445cfbb0-5f0b-416f-8bcf-f053527f9127'}
for t in d:
 if isinstance(t,list) and t[0]=='segment' and json.loads(sub(t,'uuid')[1]) in ids:sub(t,'width')[1]='.15'
n=next(t[1] for t in d if isinstance(t,list) and t[0]=='net' and t[2]=='"GND"')
if not any(isinstance(t,list) and t[0]=='zone' and sub(t,'name') and sub(t,'name')[1]=='"POWER_1S_GND"' for t in d):
 d.append(['zone',['net',n],['net_name','"GND"'],['layer','"B.Cu"'],['uuid',json.dumps(str(uuid.uuid4()))],['name','"POWER_1S_GND"'],['hatch','edge','.5'],['connect_pads','yes',['clearance','.15']],['min_thickness','.15'],['filled_areas_thickness','no'],['fill','yes',['thermal_gap','.2'],['thermal_bridge_width','.3']],['polygon',['pts',['xy','.4','.4'],['xy','33.6','.4'],['xy','33.6','17.6'],['xy','.4','17.6']]]])
path.write_text(dumps(d));b=p.LoadBoard(str(path));p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(path),b)
