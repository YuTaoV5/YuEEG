# Rev H 高性能低漂 IMU 增补设计

状态（2026-11-01）：**SCH16T-K01 已合入正式开发数字板，129位号、6层、48×60mm；原生 ERC／DRC／未连接／原理图一致性均为零。** 原有113个器件位置保持，新增16个器件在背面，背面SMT共25个。它仍是工程样机设计，尚未完成实物装配与性能验证。室内参考与航向约束见[室内惯导记录](REVH_INDOOR_NAV.md)。

## 低漂方案与候选

以零偏稳定性为优先，首先试排 Murata **SCH16T-K01**。厂家 Rev6 资料给出典型陀螺零偏不稳定性约 0.3°/h；测试采用 13Hz 低通、200Hz 采样，并在采集前热稳定15分钟。厂家同时说明这些表征统计值不构成每颗器件的保证，实际 PCB 需系统验证。该器件3.3V时典型约41mA，SPI数字接口；需为供电、热梯度和软件时序单独设计。[官方资料](https://www.murata.com.cn/-/media/webrenewal/products/sensor/pdf/datasheet/datasheet-sch16t-k01-short.ashx?cvid=20250106010000000000&la=zh-cn)、[系列页](https://www.murata.com/products/sensor/gyro/overview/lineup/sch16t)、[厂家驱动](https://github.com/Murata-MEMS/murata-sensor-driver)

紧凑候选 TDK ICM-45686 为2.5×3mm，低噪声六轴电流0.42mA、陀螺噪声3.8mdps/√Hz，厂家给出陀螺温度系数±0.005°/s/°C。上述噪声和温度系数不能代替小时尺度零偏不稳定性指标。[官方产品页](https://www.invensense.tdk.com/en-us/products/6-axis/icm-45686)

Bosch BMI088 的厂家宣传资料给出陀螺偏置稳定性低于2°/h，但初始偏置、温漂和噪声是另外的指标，不能与前述厂商不同测试条件下的值简单作保证值排名。[厂家资料](https://www.bosch-sensortec.com/media/boschsensortec/downloads/product_flyer/bst-bmi088-fl000.pdf)

用户已明确选择：**不部署基站，先实现姿态与短时相对轨迹**。本版输出任意初始航向的相对姿态，以及静止对准后的3秒速度／位移窗口；不增加UWB电路。六轴IMU不能消除长期航向和位置漂移，3秒是工程窗口而非精度保证，见[使用与限制](REVH_INDOOR_NAV.md)。

## 当前接口约束与拟用架构

- ADS1299 保留专用 SPI2 与现有 DRDY 采集路径，IMU 通信不插入 EEG ISR。
- SPI3 与 AMOLED QSPI 共用，IMU 单独片选，按单线 SPI 事务配置。开发固件已采用 IDF 独立设备句柄及公共主机管理；三态输出、混合方向切换与并发时序仍需硬件验证。
- GPIO43／44已改为IMU片选和DRDY，J301定义同步更新，**不再是UART0 TX/RX调试接口**；Type-C原生USB烧录／CDC保持。外部治具不得继续按旧UART针号驱动这两个脚。
- 显示长事务必须拆分并仲裁，防止持续锁住总线导致 IMU 丢样；EEG SPI2继续独立运行。IMU时间戳与EEG采样计数／主机时钟关联，缓冲和USB／Wi-Fi／SD输出须有序号及丢帧标记。
- IMU 采用独立 TPS7A2033 LDO，由 SYS_5V 供电；VDDIO使用系统3.3V。去耦已锁定具体KEMET型号，见[容量、偏压与ESR复核](REVH_IMU_CAPACITORS.md)。传感器温度、预热、静态零偏校准与热补偿须单独验证。

供电预算需增加约205mW典型的5V输入功率；按47mA作设计估算约235mW，未计LDO静态电流与I/O。5V降至3.3V的LDO损耗约80mW。41／47mA是厂家表征条件下的数值，不能当作未经实测的整机峰值保证；电池侧新增电流还取决于升压效率和电芯电压。应在显示、Wi-Fi、SD和EEG并行时复测5V瞬态、温升和采集噪声，不从该预算直接推算续航。

## 布局、叠层与验证范围

24脚封装依据厂家推荐焊盘建立：间距0.8mm、焊盘1.87×0.50mm、两排中心X=±6.165mm。IMU中心为(30.6,8.5)mm，B面、KiCad原生角度180°。稳压器在(33.5,30.5)mm，输入／输出电容距对应电源脚约1.91／1.61mm。原有过孔位置保留；实际冲突的原有背面走线已重接，最终检查没有未连接或铜箔间距违规。

追加复核发现：厂家Rev6第8.2节不建议在器件下方放接地平面，但允许地线和地过孔。已在实际封装及本地封装库加入**六铜层、仅禁止铺铜**的规则区，随U1801移动／翻面／旋转，当前范围X=25.2…36.0、Y=1.8…15.2mm。取消本体下方平面后，原先依赖平面的三组接地已用明确走线重新接通。新增三颗地过孔另查了对全部SMT焊盘的孔距，包含同网络焊盘；未发现0.25mm检查范围内的焊盘孔距冲突。[厂家Rev6第8.2节](https://sensorsandpower.angst-pfister.com/fileadmin/products/datasheets/191/SCH16T-K01-rev6_1630-21648-0045-E-1125.pdf)

该依据来自公开索引中的厂家正文；完整PDF此前直接获取返回403，未绕过，也未据此声称已取得完整协议。实际庭院同步扩大为14.7×13.4mm，与原先保守机械筛查范围一致，纳入沿排尺寸公差和毛边预留。名义三维模型仍不包含完整公差实体。

修改前后所有非GND走线／过孔保持相同，ADS1299专用SPI的CLK、CS、MOSI、MISO及USB线路的原生地平面中心线采样覆盖未变。**ADS_DRDY、RESET、START及部分显示／IMU线路局部失去平面覆盖**；地线接通不能证明这些线路的高频回流或波形质量。须测DRDY边沿、复位／启动可靠性、10MHz显示和2MHz IMU总线波形，并比较IMU／显示／Wi-Fi／SD启停时的EEG噪声。证据见 `digital/review/imu_underbody_pour_review.json`、`imu_underbody_rule_check.json` 和 `imu_ground_fill_paths.json`，不是完整电磁场或阻抗分析。

传感器最大高度按3.0mm，加假设0.1mm焊接抬高；自建三维模型仅为外观示意。全部16个新增器件已做对下层AFE的庭院投影筛查，记录为 `mechanical/current/imu_interboard_review.json`。LDO及输入电容与AFE C220投影相交：要求该处实测板面净距≥8.3mm、C220含焊接高度≤6.2mm、上层器件含焊接高度≤1.55mm，条件余量≥0.55mm。8.5mm为名义目标，支柱、翘曲和实物高度须验收；这不是完成公差闭合或整机碰撞认证。


开发固件已实现DRDY连续采样、SafeSPI帧／代际／连续性检查、静止对准、相对姿态和3秒相对轨迹；带单调时间、原点ID与EEG关联快照，经USB／UDP9002和独立SD记录输出。ESP32-S3编译、6项EEG测试、10项运动协议测试和36项实际C++核心／门限检查通过；没有实物烧录或性能验证。EEG关联不等于完成群延迟补偿或精密同步。混合SPI方向、供电／采集噪声、安装坐标、温度／Allan和轨迹误差仍需实测。工程Gerber仍为复核导出。
