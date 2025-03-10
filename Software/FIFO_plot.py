import sys
import time
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

# 新增滤波器参数
NOTCH_FREQ = 50.0  # 陷波频率
QUALITY_FACTOR = 10  # 品质因数（决定带宽）
FILTER_CUTOFF = 45  # 低通滤波截止频率
BUTTER_ORDER = 4        # 巴特沃兹滤波器阶数
BUTTER_CUTOFF = 45      # 巴特沃兹截止频率

class SerialThread(QtCore.QThread):
    data_received = QtCore.pyqtSignal(str)

    def __init__(self, com_port):
        super().__init__()
        self.com_port = com_port
        self.filter_flag = True
        self.serial_port = None
        self.running = False
        self.data_buffer = [[] for _ in range(9)]  # 动态数据池
        self.timestamps = []  # 时间戳记录
        self.write_index = 0
        self.max_data_length = 1_000_000  # 最大数据量限制

        # 初始化滤波器参数
        self.b_notch = [1] * 9  # 滤波器分子系数
        self.a_notch = [1] * 9  # 滤波器分母系数
        self.zi_notch = [np.zeros(2) for _ in range(9)]  # 滤波器状态

        # 设计50Hz陷波滤波器
        nyquist = 0.5 * SAMPLE_RATE
        freq = NOTCH_FREQ / nyquist
        self.b_notch, self.a_notch = iirnotch(freq, QUALITY_FACTOR)
        self.zi_notch = [lfilter_zi(self.b_notch, self.a_notch) for _ in range(9)]

        # 巴特沃兹滤波器初始化
        butter_cutoff = BUTTER_CUTOFF / nyquist
        self.b_butter, self.a_butter = butter(BUTTER_ORDER, butter_cutoff, btype='low')
        self.zi_butter = [lfilter_zi(self.b_butter, self.a_butter) for _ in range(9)]

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
        # 应用50Hz陷波滤波
        filtered_values = []
        for i in range(9):
            # 使用lfilter进行实时滤波处理
            filtered_value, self.zi_notch[i] = lfilter(
                self.b_notch,
                self.a_notch,
                [values[i]],
                zi=self.zi_notch[i]
            )
            filtered_values.append(filtered_value[0])
        # 第二级：4阶巴特沃兹低通滤波
        for i in range(9):
            filtered, self.zi_butter[i] = lfilter(
                self.b_butter,
                self.a_butter,
                [filtered_values[i]],
                zi=self.zi_butter[i]
            )
            filtered_values[i] = filtered[0]
        # 将滤波后的数据存入缓冲区（替代原始数据）
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