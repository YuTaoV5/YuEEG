# Rev D 设计与复核记录

2026-10-26。此版满足 Type-C 烧录/串口/充电、串口与 Wi-Fi 双路输出、湿电极公共参考、可旁路前端扩展及状态指示的设计需求。当前为工程评审文件，未执行人体试验或物理样机验证。

## USB 数据、电源和工作模式

ESP32-S3 GPIO19=D−、GPIO20=D+，由原生 USB Serial/JTAG 支持下载与 CDC。数据通过 ADuM4160BRIZ 双向全速隔离，12 Mbps 足以承载当前 500 SPS × 50 字节≈25 kB/s 的数据帧。该器件不是 480 Mbps USB 高速隔离器。SPU/SPD 高电平，PDEN 到 VDD1，PIN 到系统 3V3；上下游四条数据线各按 ADI 手册串联 24 Ω、1% 终端电阻。

ADuM4160 上游由 USB_HOST 侧 5 V 供电，内部 VDD1 仅用于去耦和配置；下游 VBUS2/VDD2 均接系统 3V3。上游地与 USB 外壳为 HOST_GND，下游为系统 GND。BQ25886 的 D+/D− 不连接真实 USB 数据线，仅在充电器侧局部短接用于内部源识别；实际输入上限仍由 ILIM 与主机侧限流约束。

USB 数据口 D602/D603 改为 PESD5V0U1BAF（SOD323、双向、典型 2.9 pF），降低数据线保护的容性负载。它与 EEG 输入的低漏电轨导向保护用途不同；USB 波形仍须实测。

| USB 来源/开关 | 系统供电与功能 |
|---|---|
| 无 USB，POWER ON | 2S 电池供电；Wi-Fi 输出，USB 未连接不阻塞采样 |
| 普通 USB-A 或 Type-C 默认电流，POWER ON | 电池必须存在；隔离 USB 数据与 Wi-Fi 可同时工作；隔离功率转换器关闭，不充电 |
| Type-C 声明 1.5 A/3 A，POWER ON | 隔离电源经 BQ25886 SYS 和延时双 MOS 供电；支持无电池烧录/台架运行；CE 禁止电池充电 |
| Type-C 声明 1.5 A/3 A，POWER OFF | 主采集负载关闭，约 299 mA、8.2 V 充电；原 NTC、逐节保护与均衡有效 |

用户要求的是串口与 Wi-Fi 同时实时输出，因此本版保证这两条数据通路共存的架构；**没有把边充电边采集作为默认工作模式**。电池充电与记录分时，有助于限制噪声和 USB 功率需求。主机 Type-C 有数据接口并不代表它一定声明 1.5 A；只充电适配器即使声明 3 A，也没有电脑数据连接。

TUSB320LAIRWBR 配置为 UFP、GPIO 模式，ADDR 悬空、PORT 与 EN_N 接 HOST_GND；内部 CC 下拉取代旧两颗 5.1 kΩ。OUT1 默认电流/未连接时为高，经上拉和反相器仅在声明 1.5 A 或 3 A 时使能 TPS2553。RILIM=23.7 kΩ 对应约 1.0–1.17 A 阈值范围，另计电阻公差；低于 1.5 A 广告上限。没有 USB-PD 控制器，不请求 9/12/20 V。

THM 6-0511 是 5 V 输入、5 V/1.2 A 输出的隔离模块，使用 **standard 1/12/13/23/24 引脚版本**，不能代换 -B1 或 WI 版本后沿用封装。电源模块标称 6 W，但 USB 限流、效率、线缆压降及启动冲击会降低可用功率。USB 主机和线缆须保证模块输入达到其最低启动/运行电压，不能把 6 W 模块铭牌理解为任意 USB 口都能提供 6 W。

## 电源切换、充电与保护

Rev C 的电池通路 Q603/Q604 仍在隔离 USB_RAW 出现时由 Q606 硬件禁止；新增 Q701/Q702 为共源极 PMOS，连接充电器 SYS 至 ACQ_INPUT。它们没有直接绕过电池保护给 BAT 充电。

TPS3808G01 检查隔离 USB_RAW：1.00 MΩ/100 kΩ 分压，名义阈值 4.455 V；CT=47 nF，延时约 0.2 s 后才开启 USB SYS 通路。电池通路的栅源电容 C642 改为 10 nF，先关电池路径再开 USB，避免 SYS 通过采集输入反灌电池。USB 降压时监督器应先撤销 USB 通路，Q606 在更低电压才允许恢复电池；必须实测实际器件公差、软启动和插拔波形，确认没有重叠、掉电振荡或反向电流。

POWER ON 后 VBAT_SW 通过分压保持 CE 禁止充电，SYS 仍可向负载供电。POWER OFF 后 CE 允许充电。无电池、NTC 开路时，SYS 供电行为、充电器电池检测脉冲及 USB 枚举稳定性是首件必测项目，不能仅按网络连接宣称已经验证。

电池部分仍为两节匹配 4.2 V 电芯、至少 1000 mAh、独立绝缘 103AT-2 NTC；RICHGSET=1.14 kΩ、标称 299 mA，VSET 接地选择 8.2 V CV。保护仍使用 S-8252AAY-M6T1U、CSD17308Q3 共漏极双管及 10 mΩ 电阻；需验证正常充电不误触发过流。F601 仍须选 1 A 快熔及合适直流分断能力。均衡仅在有效隔离 USB、原始电池接近充满时启用。

J401 仍为 B+／MID／B− 三线，系统 GND 与 RAW_BMINUS 不可短接。NTC 是独立绝缘两线，不能内部共用原始电芯 B−。

USB SYS 最低电压约 6.2–6.4 V，经过原二极管/PTC 后，模拟前级虽然可能仍稳压，其 PSRR 条件可能比电池供电更差。因此 USB 供电模式必须单独测纹波、Wi-Fi 瞬态及短接输入噪声；若前级压差不足，应调整保护压降或提高中间供电电压，而不是沿用电池模式的噪声结论。

## 隔离边界与封装核对

PCB 分成系统侧和左下 USB HOST 侧；四层均有 L 形禁布区。HOST 与系统铜的跨域最小净距规则为 8 mm，没有用 DRC 排除项掩盖隔离错误。USB 屏蔽外壳仅接 HOST_GND，没有跨域 RC/Y 电容或地线。

ADuM4160 必须使用 BRIZ 的增强爬电 RI-16-2 版本，不能把 BRWZ 当作同等隔离结构替代。通用 SOIC-16W 长焊盘会侵占器件引脚间铜净距，因此本版自建较短焊盘、铜间距 8.5 mm 的封装，板厂/贴片厂还须按实际封装机械图审核焊接覆盖。THM6 封装依据厂商底视图转换为 PCB 顶视图，1 脚位于输入侧下方；首次装配前对照实物确认针号。

器件的隔离耐压/2 MOPP 等级是组件规格。板面污染、连接器、外壳、爬电距离、海拔、总隔离电容、患者漏电流和单故障路径仍须整机评估，不能以“装了隔离芯片”认定适合人体使用。普通 UART 调试器、示波器地、USB 转串口、屏幕或前端子板外部电源接入系统侧，可能直接绕过此屏障。调试接口只用于合适的隔离仪器。

## 湿电极、REF/BIAS 与前端扩展

REF、BIAS 两针移至与 CH8…CH1 相同的 X 坐标；具体针号仍为 J201.1=REF、J201.2=BIAS，不能将 BIAS 当作板上 GND。

REF 已经通过八条各自的两级 4.99 kΩ 和 BAV199 保护网络进入负输入；没有在公共 REF 前串入一个大电阻去人为“匹配”电极。BIAS 原两颗 499 kΩ 之间新增 D801 BAV199 低漏电轨导向钳位，外部瞬态先经过外侧限流再到钳位节点。原型串阻的脉冲耐压、钳位电流及供电掉电吸收能力必须测试；它不是除颤保护，也没有宣称满足任意浪涌等级。

这里需要的是低漏电、低电容、双极性兼容的输入保护。电源用防反接/理想二极管芯片不适合直接串入微伏 EEG 输入；普通 TVS 的漏电和电容可能恶化偏置、噪声与匹配，不能无条件增加。此次采用限流＋轨导向的分层结构，仍需系统 ESD/EFT 验证。

J801（CH1–4）和 J802（CH5–8）每路提供 P_SEND/P_RETURN/N_SEND/N_RETURN。位置在第一颗串阻/低漏电钳位之后、第二颗串阻/匹配 RC 之前。R810…R825 共 16 颗 0 Ω 默认直通，现有滤波值不变。接外部放大器时必须拆除本通道 P/N 两颗旁路，不能让输出与发送端短接；负输入来自公共 REF，也不能把多个子板放大器输出直接并联。

两个扩展连接器均为 2.54 mm 间距、2×10 引脚。扩展接口会增加高阻节点的走线长度、寄生电容和耦合面积，首件需分别测试旁路和子板两种状态的共模抑制与噪声；静态连通检查不能替代这些测量。

扩展放大并不自动修正滤波失配。子板要保证 P/N 传递函数匹配，评估输入偏置与电流噪声、直流电极偏置、共模范围、输出摆幅、带宽/稳定性及 ADC 增益后的满量程。缓冲会引入新的输入电容、噪声、保护和故障路径。

17/18 脚为 ±2.5 V，19/20 为系统 GND。初次扩展建议两个连接器合计额外负载每轨不超过 10 mA，再测前级温升、负轨压差和噪声；这是工程约束，不是已验证输出能力。较大负载应由系统侧独立浮地低噪声电源供电，不可把外部接地电源接入人体侧。连接器及默认旁路的寄生电容也要纳入湿电极模型，而非认为预留接口没有影响。

## 控制器、状态灯与固件

U2 改为 ESP32-S3-WROOM-1-N16R8：双核最高 240 MHz、16 MB QSPI Flash、8 MB OPI PSRAM；GPIO35/36/37 保持未用。封装与原模块兼容，PSRAM 与大 Flash 需配套构建选项。硬实时采样队列放内部 RAM，不通过 PSRAM 扩容掩盖丢帧。

POWER 绿色常亮；RUN 采集时慢闪；WIFI 有客户端/STA 连接时常亮、等待时慢闪；FAULT 表示 ADC 初始化失败或采样/队列丢失；CHARGING 沿用充电器 STAT 指示。三颗状态灯 GPIO38/39/40 低有效，2.2 kΩ 限流，无 PWM。FAULT 尚未汇总全部模拟电源或电池故障，不能作为整机安全指示。

J803=3V3/GND/SDA(GPIO8)/SCL(GPIO9)，有 4.7 kΩ 上拉。此次选择状态灯完成信息显示，并预留 OLED 接口，没有装配屏幕或声称已有 OLED UI。未来加入屏幕后应在低优先级任务低频更新，不得在 DRDY ISR 或 SPI 读取路径刷新屏幕。

固件修正外部公共 REF 配置，关闭 SRB1/SRB2；正常记录关闭导联激励。探测模式按正输入逐通道激励，LOFF=0x02（6 nA、31.25 Hz），所有负输入激励关闭。探测输出是回路原始数据，未实现经校准的独立电极阻抗仪。

DRDY ISR 仅计数/时间戳并通知采样任务；SPI Mode1、2 MHz，在采样任务读取 27 字节。统一 50 字节帧含序号、时间、丢 DRDY 计数、模式、增益、状态与 CRC；输出任务向 USB CDC 和 Wi-Fi UDP 同时发送。Wi-Fi 启动不等待 USB；USB 未连接/拥塞不阻塞 UDP。数据率 500 SPS、默认增益 12，需主机 `start` 开始。详情见固件 README 和接收程序。

纯电池无线模式可通过 UDP 9001 发出 `start/stop/status` 等命令，口令使用本机随机 AP 密码；提供 `send_eeg_command.py`。无线输出任务只接收、认证和排队，ADS 寄存器仍由采集任务操作。无线端不开放 Wi-Fi 持久配置，控制口依赖受控 WPA 网络，尚无应用层加密/重放保护。

## 交付检查与实物验收

网络表与 PCB 逐引脚核对、隔离网类检查、RC 插入点检查、芯片引脚和旁路连接检查随工程交付。最终 ERC/DRC/未连接/一致性结果以 `review/` 中报告和 PCB 哈希为准。PCB 的局部 0.13 mm 净距仅用于 NexFET 原厂焊盘，常规净距 0.15 mm；密集模拟区少量 0.5/0.2 mm 过孔需要板厂支持。

自动几何检查识别出 72 处过孔钻孔与同网 SMT 焊盘相交，必须采用填孔、铜封帽工艺，不能按普通开孔或仅盖油工艺装配。位置与相关焊盘见 `review/via_in_pad.json`；板厂工艺、焊膏和贴片审核要求见 `fabrication_review/ASSEMBLY_NOTES.md`。BOM 坐标原点是板框左上角（KiCad 绝对坐标 80、100 mm）。

首件验收必须覆盖：USB 正反插/首次下载/恢复下载；默认电流与 1.5A/3A 端口；无电池 SYS 运行；USB/电池转换不重叠；POWER OFF 充电与 NTC 故障；USB/Wi-Fi 同时持续输出的序号/CRC/吞吐；湿电极假负载下噪声、共模和偏置范围；Wi-Fi 与充电切换杂散；BIAS 稳定性；ESD、隔离耐压、漏电流及所有外部接线单故障路径。软件编译通过不能替代这些实物结果。

## 一手依据

- [Espressif USB Serial/JTAG](https://docs.espressif.com/projects/esp-idf/en/release-v5.3/esp32s3/api-guides/usb-serial-jtag-console.html)、[WROOM-1 模块手册](https://www.espressif.com/sites/default/files/documentation/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf)。
- [ADI ADuM4160 Rev E](https://www.analog.com/media/en/technical-documentation/data-sheets/adum4160.pdf)：供电、24 Ω 终端、BRIZ 封装和隔离等级。
- [TRACO 2025 医疗产品目录](https://tracopower-netzteile.de/app/uploads/2025/05/Traco_Medical_Katalog_EN_2025-web.pdf)：THM6 页的引脚与机械图；[制造商 THM6 数据手册镜像](https://www.mouser.com/pdfdocs/TRACO-THM-6-Datasheet.pdf)。
- [TI TUSB320LAI](https://www.ti.com/lit/ds/symlink/tusb320lai.pdf)、[TPS2553](https://www.ti.com/lit/ds/symlink/tps2553.pdf)、[TPS3808](https://www.ti.com/lit/ds/symlink/tps3808.pdf)、[BQ25886](https://www.ti.com/lit/ds/symlink/bq25886.pdf)、[ADS1299](https://www.ti.com/lit/ds/symlink/ads1299.pdf)。
- [Nexperia PESD5V0U1BA](https://assets.nexperia.com/documents/data-sheet/PESD5V0U1BA.pdf)：USB 数据口低电容双向保护及 SOD323 封装。
