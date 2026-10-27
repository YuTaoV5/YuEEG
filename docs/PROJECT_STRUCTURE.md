# 项目目录与版本

- `Firmware/ads1299_driver/`：当前 Rev F 固件源文件及烧录说明。
- `Firmware/tools/`：接收、控制、离线 SD 解析和主机协议测试。
- `hardware/YuEEG_8CH_RevF/`：主板 KiCad、16 页原理图、BOM、模型、固件快照及静态检查。
- `hardware/YuEEG_8CH_RevF/isolated_power/`：隔离充电副板独立工程、4 页原理图与加工文件。
- 两板各自 `fabrication_review/`：Gerber、钻孔、正面 SMT 坐标和装配说明；`review/`：静态证据、完整网表与预览。
- `hardware/YuEEG_8CH_RevD/`、`hardware/YuEEG_8CH_RevE/`：冻结的历史交付及其源文件/固件快照，不与当前固件混验。
- `hardware/archive/`、`docs/archive/`：历史入口与早期记录。
- `reference/README.md`：一手资料索引；本机保存的第三方数据手册不随项目许可提交。
- `scripts/verify_review.py`：校验当前交付清单、双板报告、固件快照、ZIP 与历史冻结字节。
- `logs/`、`Firmware/build_revF/`：本机布线和编译工作区，不提交。

当前评审 ZIP 为 `hardware/YuEEG_8CH_RevF_70x80_main_44x48_power_review.zip`。交付中的 `CHECKSUMS.json` 绑定两个 PCB、加工输出、文档与固件快照；ZIP 需与清单逐字节对应。任何硬件修改后都要重新生成相关报告与输出，不能沿用旧版“通过”结论。
