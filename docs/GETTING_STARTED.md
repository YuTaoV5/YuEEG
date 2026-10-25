# Rev D 使用指南

本指南对应 ADS1299 + ESP32-S3-WROOM-1-N16R8 的 Rev D 工程评审版。首次只连接假电极/模拟信号，先验证供电、寄存器、采样和隔离。尚未完成样机人体使用验证。

## 硬件文件

使用 KiCad 9 打开 [工程](../hardware/YuEEG_8CH_RevD/YuEEG_8CH_RevD.kicad_pro)。原理图共 13 页；PCB 为 84 × 122 mm、四层。投板前阅读 [设计复核](../hardware/YuEEG_8CH_RevD/REV_D_REVIEW.md) 和 [加工要求](../hardware/YuEEG_8CH_RevD/fabrication_review/ASSEMBLY_NOTES.md)，其中 72 处焊盘内过孔要求填孔、铜封帽。

电极端口为 CH1–8、REF、BIAS，REF 与 BIAS 各有不同功能，BIAS 不是普通电路地。公共 REF 经各通道负输入保护网络接入；SRB1/SRB2 未用。外接电源、示波器地、串口适配器和扩展子板不得跨接 HOST_GND 与系统 GND。电池接口 B+/MID/B− 与独立 NTC 的要求见设计复核。

| 条件 | 支持的工作方式 |
|---|---|
| 电池、POWER ON | Wi-Fi 采集 |
| 普通 USB-A/默认电流 Type-C、POWER ON | 需要电池；USB 数据与 Wi-Fi 可并行，不充电 |
| 广告 1.5 A/3 A 的 Type-C、POWER ON | 启用隔离供电，支持无电池台架烧录；不充电 |
| 广告 1.5 A/3 A 的 Type-C、POWER OFF | 约 300 mA、8.2 V 充电 |

USB 接口有数据能力不等于支持 1.5 A 广告；充电适配器有功率也不等于有电脑数据通路。

## 编译与烧录

源码入口是 `Firmware/ads1299_driver/ads1299_driver.ino`，实现位于相邻 `YuEEG.h`。已验证 Arduino ESP32 core 2.0.11，选用 16 MB QIO Flash、8 MB OPI PSRAM、Hardware CDC and JTAG、CDC On Boot 和 16 MB 分区。

在仓库根目录执行：

```powershell
arduino-cli compile --fqbn esp32:esp32:esp32s3:FlashSize=16M,FlashMode=qio,PSRAM=opi,USBMode=hwcdc,CDCOnBoot=cdc,PartitionScheme=app3M_fat9M_16MB Firmware/ads1299_driver
```

烧录时选择实际设备端口，具体 Arduino IDE 配置、BOOT/RESET 恢复下载及启动等待见 [固件说明](../Firmware/ads1299_driver/README.md)。不要烧录 `ads1299_driver_legacy.txt`。本项目没有执行实物烧录验证。

## USB 接收

```powershell
python -m pip install -r Firmware/tools/requirements.txt
python Firmware/tools/receive_eeg.py --serial COM5 > eeg_usb.csv
```

将 COM5 改为实际端口；接收程序默认发送 `start`。上电初始化约需 10 秒，再打开接收器。默认 500 SPS、增益 12；数据是带 CRC 的二进制帧，不能直接使用旧版 `FIFO_plot.py`。

## Wi-Fi 接收与控制

1. 首次通过 USB 串口命令 `status` 取得本机随机 AP 密码，私下保存。设备默认停采。
2. 电脑连接设备的 `YuEEG-…` 无线网络，在一个终端接收：

   ```powershell
   python Firmware/tools/receive_eeg.py --udp 9000 > eeg_wifi.csv
   ```

3. 在另一终端启动采集，按提示输入本机 AP 密码：

   ```powershell
   python Firmware/tools/send_eeg_command.py start
   python Firmware/tools/send_eeg_command.py status
   ```

结束时发送 `stop`。控制端口为 9001，数据端口为 9000；`queued` 只表示命令排队成功，使用 `status` 确认。UDP 不保证送达，必须检查序号、CRC、missed_drdy 和丢帧计数。USB、Wi-Fi 两端可同时接收。

连接路由器的 STA 配置、定向 UDP、内部测试输入、导联激励及增益命令见固件说明。无线控制尚无应用层加密或重放保护，仅用于受控 WPA 网络。

## 状态显示

POWER：电源指示；RUN：采集慢闪；WIFI：连接状态；FAULT：ADC 初始化失败或采样/队列丢失；另有充电指示。FAULT 不代表覆盖全部电源或电池故障。J803 预留 3.3 V I²C OLED，尚未包含屏幕和显示驱动。
