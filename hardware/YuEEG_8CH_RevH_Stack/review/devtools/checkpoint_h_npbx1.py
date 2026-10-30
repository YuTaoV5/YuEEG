from pathlib import Path
import json,subprocess,hashlib,datetime,shutil
R=Path('hardware/YuEEG_8CH_RevH_Stack');summary={'timestamp':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),'battery':'Sony NP-BX1, 1S; supersedes NP-FW50 goal wording','release_status':'DEVELOPMENT; contact mechanics, display FPC and system verification unresolved','boards':{}}
cli='X:/SoftWare/Kicad/bin/kicad-cli.exe'
for board in ['afe','digital','power']:
 base=R/board;stem='YuEEG_H_'+board.upper();path=base/(stem+'.kicad_pcb')
 for args,report in [(['pcb','drc','--schematic-parity'],'drc_current.json'),(['sch','erc'],'erc_current.json')]:
  source=path if args[0]=='pcb' else base/(stem+'.kicad_sch')
  subprocess.run([cli,*args,'--format','json','--output',str(base/'review'/report),str(source)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True)
 d=json.loads((base/'review/drc_current.json').read_text());e=json.loads((base/'review/erc_current.json').read_text())
 counts={'drc':len(d['violations']),'unconnected':len(d['unconnected_items']),'parity':len(d['schematic_parity']),'erc':sum(len(q['violations']) for q in e['sheets'])}
 sources=list(base.glob('*.kicad_sch'))+list(base.glob('*.kicad_pro'))+list(base.glob('*.kicad_dru'))+[base/'BOM.csv',base/'fp-lib-table',base/'sym-lib-table',base/'review/netlist.xml',base/'review/expected_connections.json']
 summary['boards'][board]={**counts,'pcb_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'source_files_sha256':{p.relative_to(base).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}};print(board,counts)
 assert all(n==0 for n in counts.values()),(board,counts)
(R/'review/current_check_summary.json').write_text(json.dumps(summary,indent=2))
note='> **最新要求与状态（2026-10-30）**：用户已改用 Sony NP-BX1 单节电池。电源条板已重做为反接／欠压／限流保护＋5V 升压；三板共 269 个器件，最新 ERC／DRC／未连接／原理图一致性检查均为零。旧文中的 NP-FW50、2S、TPS26600 和并联双电源针定义已失效。电池触点与屏幕 FPC 仍未定型，尚不可下单。以 [NP-BX1 改版说明](REVH_NPBX1_POWER.md) 为准。\n\n'
for name in ['REVH_CIRCUIT_PROGRESS.md','REVH_SONY_BATTERY_LAYOUT.md','REVH_SIDE_BY_SIDE_ANALYSIS.md']:
 f=Path('docs')/name;s=f.read_text(encoding='utf8')
 if not s.startswith('> **最新要求与状态（2026-10-30）**'):f.write_text(note+s,encoding='utf8')
(R/'README.md').write_text('''# YuEEG Rev H 三板叠装 — 开发中

最新电池为 **Sony NP-BX1（单节）**，覆盖 NP-FW50／2S 版本。电池与最上层屏幕／数字板／模拟板叠层体并排；拆下电池使用专用充电器。详情见 [NP-BX1 电源改版](../../docs/REVH_NPBX1_POWER.md)。

模拟／数字板均为 48×60 mm，电源条板 34×18 mm。三板共 269 个实物器件（135／113／21），最新 ERC、DRC、未连接、原理图一致性问题均为零，文件哈希及检查时间见 `review/current_check_summary.json`。侧键已转向左侧板边，加入 ALPS 安装面禁铜区；数字板保留 9 个背面 SMT，其余主要器件正面装配。

模拟／数字板已有三处上下同轴的 2.4 mm M2 绝缘固定内切口，位于 Edge.Cuts，不能在 CAM 中丢弃。数字板电感已选定 TDK SPM4015T-2R2M-LR。Rev H 开发固件增加 NP-BX1 带载电压遥测，编译与六项协议测试通过；源文件与开发二进制在 `firmware/`，并非实物验证或生产放行。

短线束 JP2→JH2：1=SYS_5V，2=BAT_PROTECTED_SENSE，3/4=GND。针 2 用于升压前电芯电压检测，不再与针 1 并联。板间 JH1 的 1／19 针仍是并联 SYS_5V。

**尚未完成制造放行**：JP1 为临时逻辑端子，弹性电池触点真实封装未定型；屏幕 FPC 插接高度、最终支撑件和整机三维隔离未验证。旧 `mechanical/` 屏下电池方案已失效。静态检查不代表采集性能、装配或人体连接安全已经验证。

`archive/` 保留已失效的 2S 电源板及接口迁移前源文件，只供追溯。`BOM_source.csv`、`expected_source.json` 是旧版来源，不能作为生产依据。当前器件清单与连接表为各板 `BOM.csv`、`review/expected_connections.json`。本目录尚未发布制造包；不要使用旧 Rev G Gerber 代替本版。

`fabrication_engineering/` 是带源 PCB 哈希的 Gerber／钻孔／SMT 坐标工程复核导出，**不可直接下单**；电池探针与屏幕连接定型后必须重新生成。机械复核见 [记录](../../docs/REVH_MECHANICAL_REVIEW.md)。
''',encoding='utf8')
dev=R/'review/devtools';dev.mkdir(exist_ok=True)
for name in ['build_stack_circuits.py','build_h_1s_power.py','layout_h_1s_power.py','h_local_router.py','route_h_1s_critical.py','finish_h_1s_routes.py','adapt_h_1s_bus.py','update_h_1s_sources.py','route_h_cell_sense.py','fix_h_1s_control_escape.py','escape_h_1s_control_vias.py','finish_h_1s_ground.py','add_h_1s_decoupler_vias.py','checkpoint_h_npbx1.py','add_h_switch_keepouts.py','orient_h_side_keys_outward.py','clean_h_switch_control_branches.py','complete_h_switch_escapes.py']:
 shutil.copy2(Path('logs')/name,dev/name)
for name in ['select_h_power_fuse.py','make_h_component_envelopes.py','make_h_pogo_reference.py','check_h_screen_envelope.py','render_h_current.py','refine_h_components.py']:
 shutil.copy2(Path('logs')/name,dev/name)
 if (R/'review'/name).exists():shutil.copy2(Path('logs')/name,R/'review'/name)
shutil.copy2(Path('logs/build_stack_circuits.py'),R/'review/build_stack_circuits.py')
for name in ['select_h_digital_inductor.py','fit_h_l401_capacitor.py','clear_h_l401_neighbors.py','route_h_l401_neighbors.py','widen_h_c407_link.py','add_h_c407_local_via.py','check_h_mount_candidates.py','add_h_mounting_holes.py','route_h_mount_cutouts.py','link_h_pcb_schematic.py','materialize_h_libraries.py','capture_h_current_placement.py','check_h_firmware_contract.py','snapshot_h_firmware.py','export_h_engineering_review.py']:
 shutil.copy2(Path('logs')/name,dev/name)
 if (R/'review'/name).exists():shutil.copy2(Path('logs')/name,R/'review'/name)
print('NP-BX1 checkpoint recorded; production release remains pending')
for name in ['add_h_usb_return_vias.py','add_h_usb_host_return_vias.py','add_h_module_legends.py','clarify_h_mcu_legend.py','audit_h_usb_geometry.py','audit_h_usb_reference.py','audit_h_usb_partition.py','rebind_h_graphic_evidence.py']:
 shutil.copy2(Path('logs')/name,dev/name)
