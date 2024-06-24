# 项目名称：ADS1299 8通道脑机接口设备
> [!CAUTION]
> 项目基于自定义的MIT协议，除本项目拥有者以外该项目不允许用来参加任何商业比赛。

## 概述 🧠🔌

本项目旨在利用TI的ADS1299芯片构建一个8通道的脑机接口（BCI）设备。项目涵盖硬件电路设计、芯片驱动开发以及数据接收和显示的上位机程序。

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

脑机接口（Brain-Computer Interface, BCI）是一种直接连接大脑和外部设备的系统，用于读取大脑活动信号并将其转换为机器指令。本项目使用ADS1299芯片，该芯片具有高分辨率和低噪声特性，非常适合EEG（脑电图）信号的采集。

## 硬件设计 🔧

### 主要组件：

- **ADS1299芯片**：用于EEG信号采集。
- **模拟前端电路**：包括滤波和放大电路。
- **电源管理模块**：提供稳定的电源供应。
- **数据传输接口**：用于与上位机通信。

### 电路设计图：

![Img](https://imgpool.protodrive.xyz/img/yank-note-picgo-img-20240623132646.png#pic_center%20=400x)


## 软件开发 💻

### 芯片驱动：

- **SPI通信**：实现与ADS1299的SPI通信。
- **数据读取**：从芯片读取EEG数据。
- **数据处理**：初步处理和滤波。

### 引脚定义

| 引脚名称  | 描述                            |
| --------- | ------------------------------- |
| CS_PIN    | 片选引脚，低电平有效             |
| SCLK_PIN  | SPI时钟引脚                      |
| MOSI_PIN  | SPI主设备输出从设备输入引脚       |
| MISO_PIN  | SPI主设备输入从设备输出引脚       |
| DRDY_PIN  | 数据就绪引脚，低电平表示数据可读 |
| CLKSEL_PIN| 时钟选择引脚                     |
| START_PIN | 启动转换引脚                     |
| RESET_PIN | 重置引脚                         |
| PWDN_PIN  | 省电模式引脚                     |

### 命令定义

| 命令    | 描述                  |
| ------- | --------------------- |
| WAKEUP  | 唤醒芯片              |
| STANDBY | 进入待机模式          |
| RESET   | 重置芯片              |
| START   | 开始数据转换          |
| STOP    | 停止数据转换          |
| RDATAC  | 连续读取数据          |
| SDATAC  | 停止连续读取数据      |
| RDATA   | 读取数据              |
| RREG    | 读取寄存器            |
| WREG    | 写寄存器              |

### 定时器中断

代码中使用ESP32的定时器来定时读取数据和导联检测状态：

- `onDataTimer`: 检查数据是否就绪，如果就绪则设置标志位`startRead`。
- `onImpedanceTimer`: 读取导联检测状态。

### 初始化

在`setup`函数中：

- 初始化串口通信。
- 初始化引脚模式。
- 初始化SPI通信参数。
- 调用`initADS1299`函数初始化ADS1299。
- 获取并打印设备ID。
- 配置ESP32的定时器用于数据读取和导联检测。

### 主循环

在`loop`函数中：

- 检查串口是否有数据输入，用于切换连续读取模式和导联检测模式。
- 如果`startRead`标志位被设置，调用`readData`函数读取数据。

### 启动连续读取模式

`startContinuousReadMode`函数：

- 设置必要的标志位。
- 重置并初始化ADS1299的寄存器。
- 启动连续数据读取模式。
- 启动数据读取定时器，停止导联检测定时器。

### 启动导联检测模式

`startLeadOffDetectionMode`函数：

- 设置必要的标志位。
- 重置并初始化ADS1299的寄存器用于导联检测。
- 启动导联检测定时器，停止数据读取定时器。

### ADS1299初始化

`initADS1299`函数：

- 启动ADS1299的时序。
- 重置芯片。
- 停止连续数据读取模式。
- 配置必要的寄存器。

### 读取导联检测状态

`readLeadOffStatus`函数：

- 读取`LOFF_STATP`和`LOFF_STATN`寄存器。
- 打印导联检测状态。

### 读取数据

`readData`函数：

- 从ADS1299读取数据。
- 将数据转换为电压并打印。

### 寄存器读写

包含`writeRegister`和`readRegister`函数，用于向ADS1299写入和读取寄存器。

### 数据转换

`convertData`函数：

- 将读取的字节数据转换为电压值。

这个代码框架基本涵盖了ADS1299的初始化、数据读取、导联检测等主要功能。在实际应用中，可能需要根据具体需求调整寄存器配置和定时器的时间间隔。确保ADS1299手册中的寄存器配置正确无误，以实现所需的功能。

### REF和偏置电压（BIAS）的工作原理及电路连接

#### 1. 参考电极（REF）

参考电极是所有测量电极电位的基准点。它的作用是提供一个稳定的参考电压，以确保各个测量电极的电位能够被正确地采集。ADS1299提供了灵活的配置选项，可以将任意电极设置为参考电极。

#### 2. 偏置电压（BIAS）

偏置电压用于提供共模电压稳定性和干扰抑制。在EEG测量中，人体容易受到共模干扰，如电源线频率的干扰（50/60Hz）。偏置电压通过向病人施加一个控制的电压，帮助将测量电极的共模电压保持在ADS1299输入范围内。ADS1299的偏置放大器（BIAS amplifier）提供了一个内部的反馈回路，用于减少共模干扰。

#### 3. SRB引脚

SRB（Signal Reference Buffer）引脚在ADS1299中用于信号参考电极的配置。

- **SRB1**：当SRB1引脚用于参考时，所有通道的负输入可以连接到SRB1。设置`MISC1`寄存器的SRB1位可以实现这种配置。
- **SRB2**：SRB2引脚可以选择单独的电极作为参考电极，并通过设置`CHnSET`寄存器的SRB2位，将该电极的电位作为其他通道的参考。

#### 上位机程序 📊

### 功能：

- **数据接收**：通过串口接收来自硬件设备的数据。
- **数据展示**：实时显示EEG信号。
- **数据存储**：保存数据以便后续分析。

### 使用技术：

- **编程语言**：Python
- **图形库**：pyqt + fluent

### 界面截图：

![Img](https://imgpool.protodrive.xyz/img/yank-note-picgo-img-20240623125708.png#pic_center%20=400x)
![Img](https://imgpool.protodrive.xyz/img/yank-note-picgo-img-20240623125839.png#pic_center%20=400x)
![Img](https://imgpool.protodrive.xyz/img/yank-note-picgo-img-20240623125915.png#pic_center%20=400x)
![Img](https://imgpool.protodrive.xyz/img/yank-note-picgo-img-20240623125926.png#pic_center%20=400x)


## 使用指南 📚

### 硬件连接：

1. 连接电源。
2. 将EEG电极正确连接到被测试者。
3. 使用USB线连接设备和电脑。

### 软件运行：

1. 安装所需库：
   ```bash
   pip install pyserial pyqt5
   pip install pyqtgraph PyQt-Fluent-Widgets
   pip install vtk scikit-learn
   ```
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
## 贡献 🤝
欢迎大家对本项目进行贡献！请提交pull request或创建issue以报告问题。

## 许可 📜
本项目采用基于MIT的许可。
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