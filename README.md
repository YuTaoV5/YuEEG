# YuEEG · 八通道湿电极 EEG 工程

正在开发 **Rev H：NP-BX1 单节电池、独立模拟／数字板叠放**，见 [Rev H 状态](hardware/YuEEG_8CH_RevH_Stack/README.md)。当前 `Firmware/ads1299_driver/` 已切换为 Rev H 开发源码；Rev G 的固件和二进制保存在其[冻结目录](hardware/YuEEG_8CH_RevG/firmware/)。Rev H 的电池触点、屏幕 FPC 与最终装配尚未定型，以下 Rev G 内容仍是此前已发布的工程评审版本。

当前为 **Rev G 工程评审版**：ADS1299 + ESP32-S3-WROOM-1-N16R8，主板 **70 × 80 mm**、隔离充电副板 **44 × 48 mm**，另有 35 × 67 mm 屏幕载板，各板元件均在正面，AMOLED 在主板上方叠装。

支持隔离 USB CDC 与 Wi-Fi UDP 并行、microSD 原始帧备份、状态灯和 CO5300 AMOLED。主板仅由受保护的 2S 电池供电采集，副板提供独立充电 Type-C。**充电前拔下整个电极线束。**

- [使用指南](docs/GETTING_STARTED.md) · [硬件入口](hardware/README.md)
- [Rev G 固件、命令和协议](hardware/YuEEG_8CH_RevG/firmware/ads1299_driver/README.md) · [Rev H 开发固件](Firmware/ads1299_driver/README.md)
- [Rev G 设计与复核](hardware/YuEEG_8CH_RevG/DISPLAY_INTEGRATION.md)
- [完整评审包](hardware/YuEEG_8CH_RevG_AM178_review.zip)
- [目录说明](docs/PROJECT_STRUCTURE.md) · [更新记录](CHANGELOG.md)

| 项目 | 当前设计 |
|---|---|
| 采集 | ADS1299，8 通道湿电极，默认 500 SPS、增益 12，共享 REF、独立 BIAS |
| 控制器 | ESP32-S3-WROOM-1-N16R8，双核 240 MHz、16 MB Flash、8 MB PSRAM |
| 电源 | 模拟 ±2.5 V；2S 电池保护/均衡在主板，隔离充电在副板 |
| Type-C | 主板 DATA/FLASH 隔离数据；副板 CHARGE 无数据，不给采集电路供电 |
| 显示 | OSPTEK AM178Q368448LK CO5300 QSPI，10 mm 绝缘支柱 + 35 × 67 mm 两层载板 |
| 存储 | SDMMC 1-bit microSD，128 KiB 缓冲，50 字节带 CRC 原始帧 |
| 装配 | 普通 PTS645 SMT 按键、电解电容在正面；三块板背面无贴片器件 |
| PCB | 主板 305 封装 / 16 页；副板 50 封装 / 4 页，均为四层；新增屏幕载板 15 封装 / 1 页、两层 |

![Rev G 主板叠装预览](hardware/YuEEG_8CH_RevG/review/PCB_3D_top.png)

屏幕图案为示意。PCB 面积不等于整机体积，电池和外壳尚未选定。20 芯直通有键屏幕线束、通孔装配和焊盘内过孔填孔封帽要求见交付包。主板与载板静态 ERC/DRC/未连接/原理图一致性均为零，隔离副板沿用 Rev F 零错误报告，固件已编译且 6 项主机协议测试通过；实物噪声、并发、充电、温升和隔离验证尚未完成，不能视为已获人体使用放行。

```powershell
python Firmware/tools/test_protocol.py
python scripts/verify_review.py
```

Rev D、Rev E、Rev F 保持冻结，可从 [历史索引](hardware/archive/README.md) 回溯。项目许可为仓库中的 [MIT License with Restrictions](LICENSE)，不是不附加限制的标准 MIT。
