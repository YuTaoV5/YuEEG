# YuEEG Rev E 工程评审版

94 × 122 mm、四层、378 个元件、15 页原理图。以 `YuEEG_8CH_RevE.kicad_pro` 打开 KiCad 9 工程。

- 双 Type-C 同边：DATA/FLASH 为隔离原生 USB，CHARGE/POWER 为独立充电/供电；VBUS 不并联。
- ESP32-S3-WROOM-1-N16R8；USB CDC 与 Wi-Fi UDP 并行；SDMMC microSD 备份。
- DWO DO0200PFS12 RM67162 1.91 英寸 AMOLED，专用 2.8/1.8 V 电源及电平转换；需要确认供应商版本和配套排线。
- 0.53 mm Panasonic EVPBB2A9B000 超薄贴片 RESET/BOOT/REC；电解电容和按钮均在正面。
- CH1–8、REF、BIAS 同列；移除外置模拟前端扩展接口，恢复直接对称 P/N 输入路径。
- 圆角板框、圆角丝印分区、分组状态灯；黑色阻焊/白字/ENIG 外观。

## 文件入口

- [原理图 PDF](YuEEG_8CH_RevE.pdf)
- [设计分析与一手资料](REV_E_REVIEW.md)
- [静态检查结果](review/PCB_validation.json)
- [加工/装配要求](fabrication_review/ASSEMBLY_NOTES.md)
- [模块、排线和支撑件清单](ASSEMBLY_EXTRAS.csv)
- [固件操作说明](firmware/ads1299_driver/README.md)
- [正面预览](review/PCB_3D_top.png) · [背面预览](review/PCB_3D_bottom.png)

原理图、PCB、加工文件、引脚复核及固件快照由 CHECKSUMS.json 绑定。过孔填孔/铜封帽、模块与外壳的实际配合、屏幕初始化、SD 卡延迟、并行传输及模拟噪声需要首板验证。3D 中屏幕图案仅为布局示意，模型不替代供应商机械图。工程评审通过不等于人体使用放行或医疗认证。
