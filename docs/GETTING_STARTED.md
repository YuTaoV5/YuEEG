# Rev F 使用指南

用 KiCad 9 分别打开 [主板工程](../hardware/YuEEG_8CH_RevF/YuEEG_8CH_RevF.kicad_pro) 和 [隔离充电副板](../hardware/YuEEG_8CH_RevF/isolated_power/YuEEG_8CH_RevF_POWER.kicad_pro)。主板 70 × 80 mm、305 封装、16 页；副板 44 × 48 mm、50 封装、4 页，均四层且元件全在正面。投板前阅读 [复核记录](../hardware/YuEEG_8CH_RevF/REV_F_REVIEW.md) 和两板 fabrication_review/ASSEMBLY_NOTES.md。

| 接法 | 工作方式 |
|---|---|
| 电池 + 主板 POWER ON | 采集、Wi-Fi、显示及 SD 备份 |
| 电池 + POWER ON + DATA/FLASH | 隔离 USB 烧录/CDC；可与 Wi-Fi 并行 |
| 仅 DATA/FLASH | 不给主板供电，不能替代电池 |
| 副板 CHARGE + GH6 + POWER OFF | 电极线束完全拔除后充电；允许 CE 放行前的放电延时 |

充电口需要满足其 Type-C 输入能力判断，副板不提供 USB 数据。GH6 线束必须逐针核对，不能当作通用串口或 USB 线。外接示波器地、非隔离调试器和金属安装件不得跨接隔离区域。

电池使用匹配 2S、≥1000 mAh 电芯，连接 B+/MID/B−，贴附与设计匹配的 103AT-2 10k NTC。实际电芯未选定，第一次充电前核对电芯规格、极性、温度窗和保护动作。VSET 接地对应标称 8.2 V、约 299 mA；不要把 8.241 V 最大公差当作标称设定。

电极 J1301：1 REF、2 BIAS、3 CH8 至 10 CH1。BIAS 为有源共模电极，不是保护地。充电前拔下整个十路电极线束并关闭主板；软件 stop 不能代替物理断开。J301 pogo 是非隔离台架调试点，使用前也应拔下电极。

AMOLED 在主板上方使用四个名义 8 mm 绝缘支柱。专用显示接口是 FTSH-110 20 针，前 18 个功能接模块 CN1，19/20 为 GND；需验证 20→18 定制线束，不能接 JTAG。模块准确型号、插头方向和局部去耦应按供应商实物确认。

固件烧录、Wi-Fi 配置、采集命令、显示和 SD 操作见 [固件说明](../Firmware/ads1299_driver/README.md)。首次只接模拟信号源/假电极验证电源、寄存器、采样和保护，不以静态规则检查代替样机验收。

```powershell
python Firmware/tools/test_protocol.py
python scripts/verify_review.py
python Firmware/tools/receive_eeg.py --serial COM8 --command start > samples.csv
python Firmware/tools/receive_eeg.py --udp 9000 > samples.csv
python Firmware/tools/receive_eeg.py --file eeg_000001.yee > samples.csv
```
