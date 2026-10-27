# YuEEG Rev F 工程评审版

主板 **70 × 80 mm、四层、305 个封装、16 页原理图**；隔离充电副板 **44 × 48 mm、四层、50 个封装、4 页原理图**。两板所有封装均放正面，背面没有贴片器件。用 KiCad 9 打开主板 `YuEEG_8CH_RevF.kicad_pro`，副板位于 `isolated_power/`。

主板面积比 Rev E 的 94 × 122 mm 减少约 51%；两块 PCB 面积合计减少约 33%。这些是 PCB 面积，整机厚度和外形仍取决于未选定的电池、线束及外壳。

- AMOLED 在主板上方叠装，四个名义 8 mm 绝缘支柱；电极排针留在左侧，ADS1299 与输入 RC 紧邻排针。
- 普通 C&K PTS645 贴片按键；电解电容也在正面。主板背面保留说明丝印和分区。
- ESP32-S3-WROOM-1-N16R8；隔离 USB CDC 与 Wi-Fi UDP 并行，microSD 备份，状态灯与 RM67162 AMOLED。
- 主板仅由受保护的 2S 电池供电采集；DATA/FLASH Type-C 保留数据隔离。副板提供独立 CHARGE Type-C 和隔离充电电源。
- 充电前必须拔下整个 CH1–8 / REF / BIAS 电极线束。软件停止采集不能代替物理断开。
- 取消外部模拟前端扩展；共享 REF 直接分配，去掉八个冗余零欧选择电阻，精密 RC 数值保持。

## 文件入口

- [主板原理图](YuEEG_8CH_RevF.pdf) · [副板原理图](isolated_power/YuEEG_8CH_RevF_POWER.pdf)
- [设计与复核说明](REV_F_REVIEW.md) · [模块/线束清单](ASSEMBLY_EXTRAS.csv)
- [主板装配要求](fabrication_review/ASSEMBLY_NOTES.md) · [副板装配要求](isolated_power/fabrication_review/ASSEMBLY_NOTES.md)
- [主板静态检查](review/PCB_validation.json) · [副板静态检查](isolated_power/review/PCB_validation.json)
- [正面叠装预览](review/PCB_3D_top.png) · [背面预览](review/PCB_3D_bottom.png)
- [固件操作说明](firmware/ads1299_driver/README.md)

两板 ERC、DRC、未连接与原理图一致性检查均为零；完整网表、封装焊盘及独立引脚约束经过静态复核。CHECKSUMS.json 将交付文件绑定到同一版本。

单面贴装仍包含通孔焊接、屏幕线束和绝缘装配；部分过孔需要填孔封帽，详见装配要求。3D 模型为包络示意，屏幕图案不是实测显示。板厂工艺审查与首板的电源、充电、噪声、USB/Wi-Fi/SD 并发和隔离验证仍待完成，静态检查通过不等于人体使用放行。
