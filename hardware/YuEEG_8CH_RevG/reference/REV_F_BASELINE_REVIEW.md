# Rev F 设计与复核

## 紧凑布局与单面贴装

主板 70 × 80 mm，副板 44 × 48 mm；4 层，所有器件位于正面。保持单面贴装、8 mm USB 隔离区域、ESP 天线净空和屏幕支撑后，本版未压到最初 56 × 35 mm 目标。更小的尺寸需要重新选择显示模块、连接器或改变装配方式，不能把零间距摆放视为完成设计。

主板 305 个封装比 Rev E 的 378 个少 73 个；充电电源及充电芯片移到 50 封装的副板，总计 355 个。主板面积减少约 51.2%，两板总面积减少约 32.7%。电池与外壳尚未选型，未定义整机体积。主板天线边缘略伸出板框，microSD 示意模型包含退卡空间，不能直接按 PCB 外框制作外壳。

输入排针为 1×10 P2.54：1 REF、2 BIAS、3 CH8 至 10 CH1。整个线束一并拔出；需有 pin1 标记和可靠的防误插装配。输入电极到首级电阻保持短路径，ADS1299 位于输入区旁。每腿两只 4.99k 0.1%，47p C0G 1% 共模支路及 1n C0G 2% 差模电容保持离散元件；共享 REF 不再通过八个冗余零欧电阻。

湿电极的匹配关注接触阻抗、输入漏电与两腿传递函数一致性，不是 50Ω 传输线匹配。参考通道共享回路的噪声和阻抗不能靠统一电阻值消除。首板需用电极等效 RC 源、共模注入和阻抗不平衡测试测量实际 CMRR、噪声及饱和恢复。

## 电源与充电

ADS1299 模拟电源为 ±2.5 V；前级稳压约 4.4319 V，数字约 3.3 V。ADS 内部参考与这些供电轨是不同概念。VCAP1 使用 Panasonic EEEFT1E101AP 100µF 电解，名义时间常数约 0.98 s；固件上电等待 10 s。各去耦和降压电感靠近对应 IC，开关节点优先布线。In1 为地平面，无信号走线。

主板不从电脑 USB 或充电副板给采集电路供电。主板数据 USB 使用 ADuM4160；副板使用 THM6-0511 标准引脚隔离电源，BQ25886 进行 2S 升压充电。THM6 移至副板而非删除隔离，以免把充电器原边带入采集域。USB 原边地分别为 HOST_GND / CHARGE_HOST_GND。

GH6 主板 J1202 ↔ 副板 J1204：1 PACK_POS、2 GND、3 CHG_TS、4 CHG_CE、5 USB5、6 CHG_PG，全部为隔离次级信号。主板 USB5 只用于均衡资格光耦，不接采集电源。保护、均衡、欠压资格判断保留在主板，充电电源与 BQ25886 在副板。

电池按两节匹配的 4.2 V 锂离子/聚合物、至少 1000 mAh、10k NTC 设计。VSET 接地的充电标称电压为 **8.2 V**，最大 8.241 V；R604 1.14k 对应约 299 mA，低电流误差按手册 ±25% 评估。R605 9.31k / R606 365k 属于 NTC 网络，不是充电电压反馈。外接 NTC 应使用与温度窗计算匹配的 Semitec 103AT-2 或经复算验证的等效件，不能仅凭 25°C 为 10k 直接替换；实际电芯允许温度窗仍须核对。

充电 CE 默认通过副板 1M 上拉禁止充电。手册 2.5µA 最大输入电流已包含内部下拉，不重复计算：4.75 V 输入时 CE=1.8 V 可提供 2.95µA。主板 OFF 时，含电阻误差且忽略内部下拉的 CE 上界约 0.324 V，低于 0.4 V。47k VBAT_SW 泄放与约 66µF 标称输入电容使关机后充电存在延时，约 10–15 s 需实测确认。

**充电前拔下整个电极线束并关闭采集。** 固件无法确认电极已经拔除。主板 J301 裸露 pogo 调试是非隔离接口，仅供电极拔除后的台架调试。BIAS 是限流驱动的共模电极，不是保护地；BAV199T 输入钳位不构成除颤或医疗级浪涌防护。

## 屏幕与装配

DWO DO0200PFS12 必须为 RM67162 QSPI 版本，IM1 高、模块 R4 装/R3 不装。模块外形 26.4 × 57.52 × 5.38 mm，叠于主板上方，四个 M2 绝缘支柱名义高 8 mm。核对模块本身的局部去耦；主板侧电容不能替代模块端去耦。屏幕金属结构与 ESP 天线保留区分开。

主板采用 Samtec FTSH-110-01-L-DV-K-P-TR 20 针 SMT 专用显示接口，前 18 个电气功能不变，19/20 为 GND。不是 ARM JTAG。需要 FFSD-10 系列配合端与模块 CN1 的定制 20→18 线束，确认键位、pin1、接触侧、绝缘和弯折半径。不能把两端针距相近理解为直接兼容。模块 CN1 的准确连接器系列需要供应商确认。

自制封装按 Samtec Rev H：pad 0.74 × 2.79 mm、pitch 1.27 mm、两排中心 y±2.035 mm；不为 -K 增加 -A 专用定位孔。预留 FFSD 插合包络。推荐 0.152 mm 钢网需与 0402 元件共同做钢网/阶梯钢网审查。普通按键为 C&K PTS645SM43SMTR92 LFS，6×6 mm、4.3 mm 高；不再用超薄金属弹片。

全部封装正面放置不代表一次回流完成所有装配。电极排针、USB 固定脚和 THM6 仍含通孔工序。过孔填孔封帽清单见两板 review/via_in_pad.json；板厂需确认钻孔、阻焊、钢网、回流及插装流程。

## 复核证据与边界

主板 305 封装 / 16 页 / 876 个导出 ref-pin 对，副板 50 封装 / 4 页 / 160 对。网表与焊盘核对、ADS1299 独立引脚约束、主副板线束、显示电平转换、保留 GPIO 与隔离铜箔距离经过静态核查。两板 ERC、DRC、未连接及原理图一致性均为零。全部检查绑定 PCB SHA256，见 review/PCB_validation.json 与 review/REV_F_ELECTRICAL_AUDIT.json。

固件使用同一 GPIO 和 50 字节 YEEG CRC 协议，Rev F 编译程序 769761 字节、静态 RAM 46068 字节，6 项主机测试通过。尚未烧录或实测 USB、Wi-Fi、AMOLED、SD 并发、充电和模拟噪声。DRC 不会证明 USB 阻抗、纹波、CMRR、皮肤接触安全、热性能和隔离认证。首板先接模拟信号源与电极等效网络进行验证。

## 一手资料

- [TI ADS1299](https://www.ti.com/lit/ds/symlink/ads1299.pdf)、[BQ25886](https://www.ti.com/lit/ds/symlink/bq25886.pdf)
- [ADI ADuM4160](https://www.analog.com/media/en/technical-documentation/data-sheets/adum4160.pdf)、[TRACO THM6](https://www.tracopower.com/products/thm6.pdf)
- [C&K PTS645](https://www.ckswitches.com/media/1471/pts645.pdf)、[Panasonic EEEFT1E101AP](https://industrial.panasonic.com/ww/products/pt/aluminum-cap-smd/models/EEEFT1E101AP)、[Diodes BAV199T](https://www.diodes.com/datasheet/download/BAV199T.pdf)
- [Samtec FTSH land pattern](https://suddendocs.samtec.com/prints/ftsh-1xx-xx-xxx-dv-xxx-footprint.pdf)、[FTSH drawing](https://suddendocs.samtec.com/prints/ftsh-1xx-xx-xxx-dv-xxx-mkt.pdf)、[FFSD family](https://suddendocs.samtec.com/catalog_english/ffsd.pdf)
- [DWO DO0200PFS12](https://18746902.s21i.faimallusr.com/61/1/ABUIABA9GAAgxZGgswYo8vqOygc.pdf)、[LilyGO AMOLED](https://github.com/Xinyuan-LilyGO/LilyGo-AMOLED-Series)、[Arduino_GFX RM67162](https://github.com/moononournation/Arduino_GFX/blob/master/src/display/Arduino_RM67162.h)

历史文献和 Rev D/E 调研保留在原版本文件中。本版沿用已审阅的 ADS1299 湿电极体系，未把先前论文结论当作本板实测结果。
