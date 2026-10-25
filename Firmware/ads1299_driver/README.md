# YuEEG ESP32-S3 固件

适配 Rev C/D 的 SPI 与外部公共 REF 接线；Rev C 的 USB-C 没有数据连接，必须等 Rev D 隔离 USB 硬件或使用独立合适接口。软件没有把旧板 USB-C 变成数据口。旧源码存为 `ads1299_driver_legacy.txt`，请勿烧录旧版本。

## 硬件与构建

目标 ESP32-S3-WROOM-1-N16R8，16 MB QSPI Flash、8 MB OPI PSRAM、240 MHz。GPIO35/36/37 不接外设。SPI：SCLK=12、MOSI=11、MISO=13、CS=10；DRDY=4、RESET=5、PWDN=6、START=7。低有效状态 LED：RUN=38、WIFI=39、FAULT=40；OLED 扩展 SDA=8、SCL=9，当前只预留接口，未包含 OLED 驱动。

已使用 Arduino ESP32 core 2.0.11 编译；Arduino IDE 选 ESP32S3 Dev Module、16 MB Flash、QIO 80 MHz、OPI PSRAM、USB Mode=Hardware CDC and JTAG、USB CDC On Boot=Enabled、Partition Scheme=16M Flash (3MB APP/9.9MB FATFS)。内存没有用于掩盖采样阻塞：采样队列保持在内部 RAM，PSRAM 仅作为后续扩展容量。

```powershell
arduino-cli compile --fqbn esp32:esp32:esp32s3:FlashSize=16M,FlashMode=qio,PSRAM=opi,USBMode=hwcdc,CDCOnBoot=cdc,PartitionScheme=app3M_fat9M_16MB ads1299_driver
```

使用原生 USB 烧录；首次/恢复下载可按住 BOOT，再按 RESET，松开 BOOT。没有连接实物执行烧录、枚举或连续采集测试。

## 操作

上电先保持 PWDN/RESET/START 低；释放 PWDN 后等待 10 秒，再释放 RESET，检查八通道器件 ID。首次台架仍必须量测 VCAP1−AVSS>1.1 V，固定等待不能检测电源故障。默认停采。USB 不连接也会启动 Wi-Fi，无阻塞等待串口。

串口命令以换行结束：

- `start`：500 SPS，默认增益 12，公共 REF，关闭激励；同时输出 USB CDC 和 UDP。
- `stop`：停止采集。
- `test`：内部测试输入，验证数字链路。
- `probe 1` 至 `probe 8`：仅对指定正输入施加名义 6 nA、31.25 Hz 激励；所有负输入激励关闭。输出测量回路原始数据，不直接报告独立电极 kΩ。
- `gain 1/2/4/6/8/12/24`：实际命令例如 `gain 12`；参数更改会停采再启动。
- `status`：状态、计数、AP 名称及密码。文本以 `#` 开头，接收器跳过文本。
- `udp 192.168.4.2 9000`：指定 UDP 目标。默认 AP 广播 `192.168.4.255:9000`。
- `wifi SSID<TAB>PASSWORD`：其中 `<TAB>` 为实际制表符；保存在 NVS 并异步连接 STA。AP 仍保留；STA 接收机需重新设置 UDP 目标。

AP 密码首启随机生成并保存在 NVS，通过 USB `status` 查看。UDP 原始数据本身没有应用层加密；使用受控 WPA 网络。不要把密码或受试者数据写入公开日志。

断开 USB 后也可通过 Wi-Fi 启停采集：UDP 控制端口为 9001，认证口令与本机 AP 密码相同。运行 `python Firmware/tools/send_eeg_command.py start`，按提示输入密码；`stop`、`status`、`test`、`"probe 1"`、`"gain 12"`、`"udp 192.168.4.2 9000"` 同样适用。STA 模式加 `--device 设备IP`。先通过 USB 查看并保存本机密码，然后再转为电池无线使用。

控制报文格式为 `YEEG 密码 命令`，最大 192 字节。无线命令只入队，采集任务统一修改 ADS1299 寄存器；回复 `queued` 表示已排队，应再用 `status` 确认 ADC 和采集模式。无线端不支持修改 Wi-Fi 配置。此控制口依赖受控 WPA 网络，尚未实现应用层加密或重放保护，不应暴露到公网。

## 输出协议和接收

USB 和 Wi-Fi 使用完全相同的 **50 字节二进制帧**，USB 921600 波特率设置不限制原生 USB 速率。UDP 每包最多 10 帧、约 20 ms 聚合，500 SPS 时原始载荷约 25 kB/s。原 `FIFO_plot.py` 的文本解析协议不兼容；使用新增 `Firmware/tools/receive_eeg.py` 接收并导出 CSV。

| 字节偏移 | 内容 |
|---|---|
| 0–3 | ASCII `YEEG` |
| 4–7 | 版本 1、模式 1/2/3、PGA 增益、激励通道号（无激励为 0） |
| 8–11 | 序号 uint32，小端 |
| 12–15 | DRDY 时间戳 µs，uint32 小端，约 71.6 分钟回绕 |
| 16–19 | 累积未服务 DRDY 数，小端 |
| 20–46 | ADS1299 原始 STATUS 3 字节＋8 路有符号 24 位数据，芯片大端次序 |
| 47 | bit0：STATUS 上四位非 0xC，表示帧异常 |
| 48–49 | 前 48 字节 CRC16-CCITT，初值 0xFFFF、多项式 0x1021，小端存放 |

序号也会体现漏服务 DRDY；队列丢帧、USB 未接/拥塞、UDP 发送失败分别计数。输出任务运行 core0，采样和 SPI 在 loop；DRDY ISR 只记录事件与时间，不访问 SPI、不做浮点转换。USB 输出不等待主机，避免 USB 停读阻塞 Wi-Fi；UDP 不提供重传，必须检查序号。

阻抗探测模式需要同步解调并校准激励幅度、方波基波、串阻、RC 和 REF/BIAS 回路；不能简单用峰峰值除以 6 nA。不得把八个通道的负端激励同时叠加到共享 REF。正常记录阶段关闭激励，避免测量频率污染 EEG。

## 验证范围

编译通过与协议测试通过，不代表实物时序、500 SPS 无丢帧、Wi-Fi 与 USB 并发吞吐、人体安全或噪声验证通过。首次用假电极/模拟信号验证全部寄存器读回、STATUS、采样率、增益、两路序号和 CRC，再测共模、偏置、阻抗失配和 Wi-Fi 干扰。USB 同时采集依赖 Rev D 的数据与电源隔离，普通串口线、示波器地或外接 OLED 电源不能绕过隔离。
