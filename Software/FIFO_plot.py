import sys
import time
from collections import deque

import numpy as np
import re
from PyQt5 import QtWidgets, QtCore, QtGui
import pyqtgraph as pg
import serial
import serial.tools.list_ports
from qfluentwidgets import *
from qfluentwidgets import FluentIcon as FIF
from scipy.signal import butter, lfilter, lfilter_zi, iirnotch

# 配置参数
DATA_LENGTH = 2000  # 数据缓存长度
PLOT_LENGTH = 1000  # 显示数据长度
FFT_LENGTH = 500  # FFT分析长度
UPDATE_INTERVAL = 60  # 界面刷新间隔(ms)
SAMPLE_RATE = 500  # 采样率

# 修改滤波器参数
NOTCH_FREQ = 50.0  # 陷波频率
QUALITY_FACTOR = 10  # 品质因数
LOW_CUTOFF = 2.0    # 带通滤波低频截止
HIGH_CUTOFF = 40.0  # 带通滤波高频截止
FIR_ORDER = 101     # FIR滤波器阶数
MEDIAN_WINDOW = 800 # 中值滤波窗口大小

class SerialThread(QtCore.QThread):
    data_received = QtCore.pyqtSignal(str)

    def __init__(self, com_port):
        super().__init__()
        self.com_port = com_port
        self.filter_flag = True
        self.serial_port = None
        self.running = False
        self.data_buffer = [[] for _ in range(9)]
        self.timestamps = []
        self.write_index = 0
        self.max_data_length = 1_000_000

        # 初始化滤波器
        self._init_filters()

    def _init_filters(self):
        # 设计50Hz陷波滤波器
        nyquist = 0.5 * SAMPLE_RATE
        freq = NOTCH_FREQ / nyquist
        self.b_notch, self.a_notch = iirnotch(freq, QUALITY_FACTOR)
        self.zi_notch = [lfilter_zi(self.b_notch, self.a_notch) for _ in range(9)]

        # 设计FIR带通滤波器
        from scipy.signal import firwin
        self.fir_coeff = firwin(FIR_ORDER, 
                               [LOW_CUTOFF/nyquist, HIGH_CUTOFF/nyquist],
                               pass_zero=False)
        self.zi_fir = [np.zeros(FIR_ORDER - 1) for _ in range(9)]
        # 中值滤波缓冲区
        self.median_buffers = [deque(maxlen=MEDIAN_WINDOW) for _ in range(9)]

    def run(self):
        self.running = True
        try:
            self.serial_port = serial.Serial(self.com_port, baudrate=115200, timeout=1)
            self.serial_port.write(b'1')  # 启动数据传输
            while self.running:
                if self.serial_port.in_waiting:
                    try:
                        raw_data = self.serial_port.readline().decode('utf-8', errors='ignore').strip()
                        self.data_received.emit(raw_data)
                        # 使用正则表达式验证数据格式
                        if re.match(r'^Channel:(-?\d+\.?\d*,){8}-?\d+\.?\d*$', raw_data):
                            values = list(map(float, raw_data.split('Channel:')[1].split(',')))
                            self._update_buffer(values)
                    except Exception as e:
                        print(f"Error processing data: {e}")
        finally:
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()

    def _update_buffer(self, values):
        filtered_values = []
        for i in range(9):
            # 1. 50Hz陷波滤波
            notch_filtered, self.zi_notch[i] = lfilter(
                self.b_notch,
                self.a_notch,
                [values[i]],
                zi=self.zi_notch[i]
            )

            # 2. FIR带通滤波
            fir_filtered, self.zi_fir[i] = lfilter(
                self.fir_coeff,
                [1.0],
                notch_filtered,
                zi=self.zi_fir[i]
            )

            # 3. 中值滤波去基线
            self.median_buffers[i].append(fir_filtered[0])
            # 当缓冲区满时计算中值
            if len(self.median_buffers[i]) >= MEDIAN_WINDOW:
                median = np.median(self.median_buffers[i])
                filtered_values.append(fir_filtered[0] - median)
            else:
                filtered_values.append(fir_filtered[0])

        # 更新数据缓冲区
        while len(self.timestamps) >= self.max_data_length:
            for ch in self.data_buffer:
                ch.pop(0)
            self.timestamps.pop(0)

        for i in range(9):
            if self.filter_flag:
                self.data_buffer[i].append(filtered_values[i])
            else:
                self.data_buffer[i].append(values[i])
        self.timestamps.append(self.write_index)
        self.write_index += 1

    def get_plot_data(self, length=PLOT_LENGTH):
        valid_length = min(len(self.timestamps), length)
        start = max(0, len(self.timestamps) - valid_length)
        x_axis = np.arange(start, start + valid_length)
        data = [np.array(ch[start:start + valid_length]) for ch in self.data_buffer]
        return x_axis, np.array(data)

    def get_fft_data(self):
        return self.get_plot_data(FFT_LENGTH)

    def get_last_data(self, num):
        """获取最新的num个点数据，返回形状为(9, num)的ndarray"""
        data = []
        for ch in self.data_buffer:
            if len(ch) >= num:
                data.append(np.array(ch[-num:]))
            else:
                padding = np.full(num - len(ch), np.nan)
                data.append(np.concatenate([padding, ch]))
        return np.array(data)

    def stop(self):
        self.running = False
        self.wait(2000)


class ADCPlotter(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("YuEEG Data Viewer")
        self.setWindowIcon(QtGui.QIcon('./school_logo.ico'))
        self._setup_ui()
        if not (com_port := self._detect_com_port()):
            QtWidgets.QMessageBox.critical(self, "错误", "未检测到可用串口")
            sys.exit(1)
        self.serial_thread = SerialThread(com_port)
        self.serial_thread.data_received.connect(self._append_serial_data)
        self.serial_thread.start()
        self._start_timers()

    def _setup_ui(self):
        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)
        main_layout = QtWidgets.QVBoxLayout(self.central_widget)

        # 创建绘图区域
        self.plot_container = QtWidgets.QWidget()
        self.plot_layout = QtWidgets.QVBoxLayout(self.plot_container)
        self.plot_layout.setContentsMargins(0, 0, 0, 0)
        self.plot_layout.setSpacing(0)

        # 时域图表配置
        self.time_plot = pg.PlotWidget()
        self.time_plot.setAntialiasing(True)
        self.time_plot.useOpenGL(True)
        self.time_plot.setLabel('bottom', 'Samples')
        self.time_plot.setLabel('left', 'Amplitude')
        self.time_plot.showGrid(x=True, y=True, alpha=0.3)

        # 频域图表配置
        self.fft_plot = pg.PlotWidget()
        self.fft_plot.setAntialiasing(True)
        self.fft_plot.useOpenGL(True)
        self.fft_plot.setLabel('bottom', 'Frequency (Hz)')
        self.fft_plot.setLabel('left', 'Amplitude')
        self.fft_plot.showGrid(x=True, y=True, alpha=0.3)

        self.plot_layout.addWidget(self.time_plot)
        self.plot_layout.addWidget(self.fft_plot)
        main_layout.addWidget(self.plot_container)

        # 初始化曲线
        colors = ['#FF0000', '#00FF00', '#0000FF', '#00FFFF',
                  '#FF00FF', '#FFFF00', '#FFFFFF', '#A0A0A0', '#FFA500']
        self.time_curves = [self.time_plot.plot(pen=color) for color in colors]
        self.fft_curves = [self.fft_plot.plot(pen=color) for color in colors]

        # 控制面板
        control_layout = QtWidgets.QHBoxLayout()
        self.checkboxes = [CheckBox(f"CH{i + 1}") for i in range(9)]
        for cb in self.checkboxes:
            cb.setChecked(True)
            control_layout.addWidget(cb)

        # 显示模式选择
        self.mode_selector = ComboBox()
        self.mode_selector.addItems(["波形", "频谱", "并列"])
        self.mode_selector.currentIndexChanged.connect(self.update_display_mode)
        control_layout.addWidget(self.mode_selector)

        # 功能模式切换按钮
        self.fun_selector = PushButton("标准")
        self.fun_selector.clicked.connect(self.fun_change)
        control_layout.addWidget(self.fun_selector)
        # 暂停按钮
        self.pause_button = PushButton("暂停")
        self.pause_button.clicked.connect(self.toggle_pause)
        control_layout.addWidget(self.pause_button)

        main_layout.addLayout(control_layout)
        self.checkboxes[0].setChecked(False)
        self.update_display_mode()

    def _start_timers(self):
        self.plot_timer = QtCore.QTimer()
        self.plot_timer.timeout.connect(self.update_plots)
        self.plot_timer.start(UPDATE_INTERVAL)

    def fun_change(self):
        if self.fun_selector.text() == "测试":
            self.serial_thread.serial_port.write(b'1')
            self.serial_thread.filter_flag = True
            self.fun_selector.setText("标准")
        elif self.fun_selector.text() == "标准":
            self.serial_thread.serial_port.write(b'3')
            self.serial_thread.filter_flag = False
            self.fun_selector.setText("测试")

    def update_display_mode(self):
        mode = self.mode_selector.currentText()
        if mode == "波形":
            self.time_plot.show()
            self.fft_plot.hide()
        elif mode == "频谱":
            self.time_plot.hide()
            self.fft_plot.show()
        else:
            self.time_plot.show()
            self.fft_plot.show()

    def update_plots(self):
        mode = self.mode_selector.currentText()
        if mode in ["波形", "并列"]:
            self.update_time_plot()
        if mode in ["频谱", "并列"]:
            self.update_fft_plot()

    def update_time_plot(self):
        x_axis, data = self.serial_thread.get_plot_data()
        if data.size == 0:
            return
        active = [i for i, cb in enumerate(self.checkboxes) if cb.isChecked()]
        if not active:
            return

        # 更新时域曲线
        for i in active:
            self.time_curves[i].setData(x_axis, data[i])

        # 自动滚动X轴
        self.time_plot.setXRange(x_axis[-1] - PLOT_LENGTH, x_axis[-1])

        # 自动调整Y轴范围
        valid_data = data[active]
        y_min = np.nanmin(valid_data)
        y_max = np.nanmax(valid_data)
        if not np.isnan(y_min) and not np.isnan(y_max):
            margin = (y_max - y_min) * 0.1 or 1.0
            self.time_plot.setYRange(y_min - margin, y_max + margin)

    def update_fft_plot(self):
        x_axis, data = self.serial_thread.get_fft_data()
        if data.size == 0:
            return
        fs = SAMPLE_RATE
        max_amp = 0
        for i in range(9):
            if not self.checkboxes[i].isChecked():
                continue
            # 计算FFT
            signal = data[i, :]
            fft = np.abs(np.fft.rfft(signal))
            freq = np.fft.rfftfreq(len(signal), 1 / fs)
            # 限制频率范围
            mask = (freq >= 3) & (freq <= 50)
            self.fft_curves[i].setData(freq[mask], fft[mask])
            current_max = np.max(fft[mask])
            if current_max > max_amp:
                max_amp = current_max
        # 调整Y轴范围
        if max_amp > 0:
            self.fft_plot.setYRange(0, max_amp * 1.1)
        else:
            self.fft_plot.enableAutoRange('y')

    def _append_serial_data(self, text):
        try:
            self.statusBar().showMessage(text[-200:], 2000)
        except:
            pass

    def _detect_com_port(self):
        ports = serial.tools.list_ports.comports()
        for p in ports:
            if 'USB' in p.description:
                return p.device
        return None

    def toggle_pause(self):
        if self.plot_timer.isActive():
            self.plot_timer.stop()
            self.pause_button.setText("继续")
        else:
            self.plot_timer.start()
            self.pause_button.setText("暂停")

    def closeEvent(self, event):
        self.serial_thread.stop()
        event.accept()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = ADCPlotter()
    window.show()
    sys.exit(app.exec_())