# 硬件入口

当前版本为 [Rev D](YuEEG_8CH_RevD/README.md)：ESP32-S3-WROOM-1-N16R8、ADS1299、八通道湿电极、公共 REF、BIAS、2S 电池管理、隔离 USB 数据与供电、模拟前端扩展及状态灯。

- [KiCad 9 工程](YuEEG_8CH_RevD/YuEEG_8CH_RevD.kicad_pro)
- [原理图 PDF](YuEEG_8CH_RevD/YuEEG_8CH_RevD.pdf)
- [设计与复核记录](YuEEG_8CH_RevD/REV_D_REVIEW.md)
- [制造工艺要求](YuEEG_8CH_RevD/fabrication_review/ASSEMBLY_NOTES.md)
- [完整评审包](YuEEG_8CH_RevD_84x122_isolated_USB_WiFi_review.zip)
- [历史版本索引](archive/README.md)

Rev D 的工程文件、静态检查、编译产物已生成，尚未完成样机烧录、噪声、USB/Wi-Fi 并发、温升、充电故障、漏电流和耐压验证。请先阅读制造要求，不能仅凭 Gerber 或 DRC 零错误直接将其视为人体使用设备。
