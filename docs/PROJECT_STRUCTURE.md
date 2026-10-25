# 目录与版本约定

| 路径 | 用途 |
|---|---|
| `hardware/YuEEG_8CH_RevD/` | 当前 KiCad 原生工程、BOM、加工文件、PDF、预览和静态检查记录 |
| `Firmware/ads1299_driver/` | 当前固件的唯一开发入口 |
| `Firmware/tools/` | 当前二进制帧接收、无线控制和协议测试 |
| `hardware/YuEEG_8CH_RevD/firmware/` | 与工程评审包绑定的固件快照及编译产物，不在此目录开发 |
| `hardware/*review.zip` | 各版冻结的工程评审交付包 |
| `hardware/archive/README.md` | 历史硬件索引及使用范围 |
| `Firmware/Plot/` | 旧文本串口协议绘图程序，未适配 Rev D |
| `Paradigm/` | 历史 SSVEP 范式、UI 和平台依赖，未集成 Rev D 协议 |
| `Model/` | 历史外壳/脑电帽模型，未适配 Rev D 板框 |
| `docs/archive/` | 归档的旧首页与使用方法 |
| `reference/README.md` | 芯片资料的一手来源索引；本机下载文件不上传 |
| `scripts/verify_review.py` | 验证冻结交付与当前源代码、可重新生成评审 ZIP |

历史文件保留原路径，避免破坏旧程序的相对路径。历史 DLL、资源和模型保留，不代表当前可安装或已测试；例如 `Paradigm/src/stream.py` 仍依赖仓库未提供的 `lib.neuracle_lib`。

本机的历史 KiCad 工作目录、布线器/JRE、DSN/SES、中途 DRC 报告、完整编译缓存和日志不进入 Git。旧版原生文件可从对应 ZIP 获取。新增版本应复制为新目录，并单独生成与最终 PCB 哈希绑定的检查报告，不能覆盖已有评审记录。

当前工程目录只提交 `CHECKSUMS.json` 列出的交付文件及该目录的 `.gitignore`，防止重复运行一次性迁移脚本。这些文件包含固件快照；修改规范源代码后，必须重新编译、复核并更新快照与校验清单，验证脚本会拒绝源代码与快照不一致的状态。

## 验证命令

```powershell
python Firmware/tools/test_protocol.py
python scripts/verify_review.py
```

静态报告中的零错误不等于模拟性能或整机安全合格。软件协议测试、固件编译、静态电气检查、实物验收四类证据应分别记录。
