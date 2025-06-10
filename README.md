<div align="right">
    <img src="https://imgpool.protodrive.xyz/img/yank-note-picgo-img-20241105215145.png" alt="Image Description" width="150" />
</div>
<h1 align = "center">🌟YuEEG 8通道脑机接口设备🌟</h1>

<p align = "center">    
<img  src="https://img.shields.io/badge/Arduino-passing-green" />
<img  src="https://img.shields.io/badge/PlatformIO-passing-green" />
<img  src="https://img.shields.io/badge/ESP32S3%20-项目-blue" />
<img  src="https://img.shields.io/badge/ADS1299%20-项目-red" />
<img  src="https://img.shields.io/badge/YuEEG-V1.6-grey" />
</p>

<p align = "center">    
<img  src="https://imgpool.protodrive.xyz/img/yank-note-picgo-img-20241110230401.jpg" width="300" />
<img  src="https://imgpool.protodrive.xyz/img/yank-note-picgo-img-20241112220356.jpg" width="300" />
</p>

## 概述 🧠🔌

本项目旨在利用 TI 的 ADS1299 芯片构建一个 8 通道的脑机接口（BCI）设备。项目涵盖硬件电路设计、芯片驱动开发以及数据接收和显示的上位机程序。

## 项目亮点

- **8 通道高分辨率 EEG 采集**，适合科研和创客项目。
- **定制 3D 打印脑电帽外壳**，设计舒适，便于精确放置电极。
- **兼容 Arduino 的驱动代码**，便于集成和控制，支持多种 EEG 应用和项目开发。

> [!CAUTION]
> 项目基于自定义的 MIT 协议，除本项目拥有者以外该项目不允许用来参加任何商业比赛。

> [!CAUTION]
> 【注意】请勿焊接TPS模块，直接使用USB供电，原因如下：
> ESP的Vbus引脚直连USB电源，并没有引脚二极管处理供电冲突所以请不要同时使用两种供电

> [!NOTE] 更新日志 2025/6/10
> 更新波形显示界面`FIFO_Plot.py`,添加去基线等滤波功能。修改部分驱动寄存器配置。

> [!NOTE] 更新日志 2024/12/7
> 项目已更新【SSVEP 范式】，后续还会添加APP以及网页波形显示，建议 Star 或者Fork后，作者会添加更多内容。



## 目录 📁

1. [项目背景](#项目背景)
2. [硬件设计](#硬件设计)
3. [软件开发](#软件开发)
4. [上位机程序](#上位机程序)
5. [使用指南](#使用指南)
6. [项目结构](#项目结构)
7. [贡献](#贡献)
8. [许可](#许可)

## 项目背景 📝

脑机接口（Brain-Computer Interface, BCI）是一种直接连接大脑和外部设备的系统，用于读取大脑活动信号并将其转换为机器指令。本项目使用 ADS1299 芯片，该芯片具有高分辨率和低噪声特性，非常适合 EEG（脑电图）信号的采集。

## 硬件设计 🔧

### 主要组件：

- **ADS1299 芯片**：用于 EEG 信号采集。
- **模拟前端电路**：包括滤波和放大电路。
- **电源管理模块**：提供稳定的电源供应。
- **数据传输接口**：用于与上位机通信。

### 电路设计图：

> 嘉立创链接：[https://oshwhub.com/protodrive000/1299_pro](https://oshwhub.com/protodrive000/1299_pro)
> 访问密码：yutaov5

| 正面                                                                                               | 反面                                                                                               |
| -------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| ![Img](https://imgpool.protodrive.xyz/img/yank-note-picgo-img-20241110221805.png#pic_center%20=400x) | ![Img](https://imgpool.protodrive.xyz/img/yank-note-picgo-img-20241110221809.png#pic_center%20=400x) |

### 外壳模型设计图：

> 3D 外壳文件：https://a360.co/3AnxQdK
> 访问密码：yutaov5

| 单外壳                                                                            | 外壳+脑电帽                                                                       | 仰视图                                                                            |
| --------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| ![Img](https://imgpool.protodrive.xyz/img/yank-note-picgo-img-20241110221759.png) | ![Img](https://imgpool.protodrive.xyz/img/yank-note-picgo-img-20241110221635.PNG) | ![Img](https://imgpool.protodrive.xyz/img/yank-note-picgo-img-20241110221644.png) |

## 上位机程序 📊

> 目前仅提供串口通讯的 plot_only.py 界面程序

### 功能：

- **数据接收**：通过串口接收来自硬件设备的数据。
- **数据展示**：实时显示 EEG 信号。
- **数据存储**：保存数据以便后续分析。

### 使用技术：

- **编程语言**：Python
- **图形库**：pyqt + fluent

### 界面截图：

| 正常采集模式                                                                                         | 测试信号模式                                                                                         |
| ---------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| ![Img](https://imgpool.protodrive.xyz/img/yank-note-picgo-img-20241111123715.png#pic_center%20=400x) | ![Img](https://imgpool.protodrive.xyz/img/yank-note-picgo-img-20241111123732.png#pic_center%20=400x) |

## 范式程序
### 功能：

- **拼音输入**：通过C++编写的动态链接库。
- **联想拼写**：隐马尔可夫链模型。
- **分类算法**：FBCCA算法
- **支持多语言**：NLTK模型。

|配置界面|运行界面|
|-|-|
|![Img](https://imgpool.protodrive.xyz/img/yank-note-picgo-img-20241111135941.png#pic_center%20=400x)|![Img](https://imgpool.protodrive.xyz/img/yank-note-picgo-img-20241111140005.png#pic_center%20=400x)|

>运行 ssvep_paradigm.py


## 使用指南 📚


### 硬件连接：

1. 本项目支持两种供电模式：
   - USB 接入 XiaoESP32S3 直接供电使用，同时串口发送数据
   - 背面焊接 TPS63070 锂电池转 5V 模块，然后电源接口接入 3.7V 锂电池即可
1. 将 EEG 电极正确连接到被测试者。
2. 使用 USB 线连接设备和电脑。
3. 硬件上支持BMM150以及Makerbase的MKS-142健康监测模块

### 引脚连接

```c++
// 定义引脚
#define CS_PIN    A3
#define SCLK_PIN  SCK
#define MOSI_PIN  MOSI
#define MISO_PIN  MISO
#define DRDY_PIN  A0
#define START_PIN A2
#define RESET_PIN A1
```

### 硬件设置

驱动代码是为支持 ESP32 的 Arduino IDE 编写的，代码通过 SPI 与 ADS1299 进行数据采集。

### 先决条件

- **Arduino IDE**：从[Arduino 官方网站](https://www.arduino.cc/en/software)下载最新版本。
- **ESP32 开发板包**：在 Arduino IDE 中通过开发板管理器添加 ESP32 开发板支持。

### 加载代码：

打开 Arduino IDE，选择 `文件` > `打开` 并选择 `ino 文件`。
在 `工具` > `开发板` 下选择你的 ESP32 开发板。
在 `工具` > `端口` 下设置正确的 COM 端口。

### 上传代码：

> 如果是第一次下载，上电前按住 boot 再上电后松开，然后正常下载

编译并将代码上传到 ESP32 开发板。

### 上位机代码使用方法

上传完成后，ESP32 开发板将开始与 ADS1299 芯片进行通信，并将 EEG 数据输出到串口监视器。

- 模式切换：使用以下串口命令或者左下方按钮切换不同模式：
  - 1：连续读取模式
  - 3：自检模式

> 示例用法
> 上传完成后，在 Arduino IDE 中打开串口监视器，波特率设为 115200。你将看到来自每个通道的实时 EEG 数据。

```C
// 数据格式如下
Channel 1: 0.123456, Channel 2: 0.654321, ..., Channel 8: 0.345678
```

### 上位机安装步骤

1. **克隆此仓库**：
   ```bash
   git clone https://github.com/YuTaoV5/YuEEG.git
   cd YuEEG
   ```
1. 安装所需库：
   ```bash
   pip install pyserial pyqt5
   pip install pyqtgraph PyQt-Fluent-Widgets
   pip install scikit-learn
   ```
1. 软件运行：
   ```bash
   python plot_only.py
   ```

## 贡献指南

欢迎社区贡献！请随时提交问题、功能请求或拉取请求。

## 未来改进

- 增加对不同微控制器的支持。
- 扩展脑电帽设计，以便调整电极位置。

## 致谢

特别感谢德州仪器提供 ADS1299 芯片，并感谢开源社区的启发与支持。

## 项目结构 🗂️

```
├── hardware
│   ├── schematics
│   └── pcb
├── firmware
│   └── ads1299_driver.ino
├── software
│   └── bci_gui.py
└── README.md
```

## 软件开发 💻

### 芯片驱动：

- **SPI 通信**：实现与 ADS1299 的 SPI 通信。
- **数据读取**：从芯片读取 EEG 数据。
- **数据处理**：初步处理和滤波。

### 引脚定义

| 引脚名称   | 描述                             |
| ---------- | -------------------------------- |
| CS_PIN     | 片选引脚，低电平有效             |
| SCLK_PIN   | SPI 时钟引脚                     |
| MOSI_PIN   | SPI 主设备输出从设备输入引脚     |
| MISO_PIN   | SPI 主设备输入从设备输出引脚     |
| DRDY_PIN   | 数据就绪引脚，低电平表示数据可读 |
| CLKSEL_PIN | 时钟选择引脚                     |
| START_PIN  | 启动转换引脚                     |
| RESET_PIN  | 重置引脚                         |
| PWDN_PIN   | 省电模式引脚                     |

### 命令定义

| 命令    | 描述             |
| ------- | ---------------- |
| WAKEUP  | 唤醒芯片         |
| STANDBY | 进入待机模式     |
| RESET   | 重置芯片         |
| START   | 开始数据转换     |
| STOP    | 停止数据转换     |
| RDATAC  | 连续读取数据     |
| SDATAC  | 停止连续读取数据 |
| RDATA   | 读取数据         |
| RREG    | 读取寄存器       |
| WREG    | 写寄存器         |

### 定时器中断

代码中使用 ESP32 的定时器来定时读取数据和导联检测状态：

- `onDataTimer`: 检查数据是否就绪，如果就绪则设置标志位`startRead`。
- `onImpedanceTimer`: 读取导联检测状态。

### 初始化

在`setup`函数中：

- 初始化串口通信。
- 初始化引脚模式。
- 初始化 SPI 通信参数。
- 调用`initADS1299`函数初始化 ADS1299。
- 获取并打印设备 ID。
- 配置 ESP32 的定时器用于数据读取和导联检测。

### 主循环

在`loop`函数中：

- 检查串口是否有数据输入，用于切换连续读取模式和导联检测模式。
- 如果`startRead`标志位被设置，调用`readData`函数读取数据。

### 启动连续读取模式

`startContinuousReadMode`函数：

- 设置必要的标志位。
- 重置并初始化 ADS1299 的寄存器。
- 启动连续数据读取模式。
- 启动数据读取定时器，停止导联检测定时器。

### 启动导联检测模式

`startLeadOffDetectionMode`函数：

- 设置必要的标志位。
- 重置并初始化 ADS1299 的寄存器用于导联检测。
- 启动导联检测定时器，停止数据读取定时器。

### ADS1299 初始化

`initADS1299`函数：

- 启动 ADS1299 的时序。
- 重置芯片。
- 停止连续数据读取模式。
- 配置必要的寄存器。

### 读取导联检测状态

`readLeadOffStatus`函数：

- 读取`LOFF_STATP`和`LOFF_STATN`寄存器。
- 打印导联检测状态。

### 读取数据

`readData`函数：

- 从 ADS1299 读取数据。
- 将数据转换为电压并打印。

### 寄存器读写

包含`writeRegister`和`readRegister`函数，用于向 ADS1299 写入和读取寄存器。

### 数据转换

`convertData`函数：

- 将读取的字节数据转换为电压值。

这个代码框架基本涵盖了 ADS1299 的初始化、数据读取、导联检测等主要功能。在实际应用中，可能需要根据具体需求调整寄存器配置和定时器的时间间隔。确保 ADS1299 手册中的寄存器配置正确无误，以实现所需的功能。

### REF 和偏置电压（BIAS）的工作原理及电路连接

#### 1. 参考电极（REF）

参考电极是所有测量电极电位的基准点。它的作用是提供一个稳定的参考电压，以确保各个测量电极的电位能够被正确地采集。ADS1299 提供了灵活的配置选项，可以将任意电极设置为参考电极。

#### 2. 偏置电压（BIAS）

偏置电压用于提供共模电压稳定性和干扰抑制。在 EEG 测量中，人体容易受到共模干扰，如电源线频率的干扰（50/60Hz）。偏置电压通过向病人施加一个控制的电压，帮助将测量电极的共模电压保持在 ADS1299 输入范围内。ADS1299 的偏置放大器（BIAS amplifier）提供了一个内部的反馈回路，用于减少共模干扰。

#### 3. SRB 引脚

SRB（Signal Reference Buffer）引脚在 ADS1299 中用于信号参考电极的配置。

- **SRB1**：当 SRB1 引脚用于参考时，所有通道的负输入可以连接到 SRB1。设置`MISC1`寄存器的 SRB1 位可以实现这种配置。
- **SRB2**：SRB2 引脚可以选择单独的电极作为参考电极，并通过设置`CHnSET`寄存器的 SRB2 位，将该电极的电位作为其他通道的参考。

## 贡献 🤝

欢迎大家对本项目进行贡献！请提交 pull request 或创建 issue 以报告问题。

## 许可 📜

本项目采用基于 MIT 的许可。

```
MIT License with Restrictions

Copyright (c) [2024] [ZhangYutao]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

Additional Restrictions:
The Software may not be used to participate in any commercial competitions or contests without the explicit permission of the copyright holder.
```

