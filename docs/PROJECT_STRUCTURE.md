# 项目目录与版本

- `Firmware/ads1299_driver/`：当前 Rev G CO5300 固件与说明。
- `Firmware/tools/`：接收、控制、SD 离线解析和协议测试。
- `hardware/YuEEG_8CH_RevG/`：70×80 mm 主板 KiCad、16 页原理图、BOM、模型、静态证据。
- `display_carrier/`：35×67 mm 两层屏幕载板、1 页原理图和独立加工文件。
- `isolated_power/`：原样沿用 Rev F 44×48 mm 隔离充电副板，文件名保留 F。
- 各板 `fabrication_review/`：Gerber、钻孔、SMT 坐标与工艺；G 根目录 `order_gerbers/` 含三块板分别下单的 ZIP。
- G 的 `reference/`：OSPTEK 授权材料、源文件哈希及冻结基线记录；`firmware/`：G 快照和二进制。
- `hardware/YuEEG_8CH_RevD/`、`RevE/`、`RevF/`（完整名称均以 YuEEG_8CH_ 开头）：历史交付保持字节冻结。
- `scripts/verify_review.py`：当前 G 清单、PCB 报告、固件与 ZIP，以及 D/E/F 冻结校验。
- `logs/`、用户提供的完整厂家下载目录：本机工作资料，不整体提交。

当前评审包 `hardware/YuEEG_8CH_RevG_AM178_review.zip`；CHECKSUMS.json 绑定交付文件，修改 PCB 后必须重新执行 KiCad 检查和导出。
