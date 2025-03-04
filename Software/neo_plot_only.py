import sys
import time
import numpy as np
import re
from PyQt5 import QtWidgets, QtCore, QtGui
import pyqtgraph as pg
import serial
import serial.tools.list_ports
from scipy.signal import butter, lfilter, lfilter_zi

# 配置参数
DATA_LENGTH = 2000  # 数据缓存长度
PLOT_LENGTH = 750  # 显示数据长度
UPDATE_INTERVAL = 30  # 界面刷新间隔(ms)
SAMPLE_RATE = 500  # 采样率
FILTER_CUTOFF = 45  # 低通滤波截止频率


class SerialThread(QtCore.QThread):
    data_received = QtCore.pyqtSignal(str)

    def __init__(self, com_port):
        super().__init__()
        self.com_port = com_port
        self.serial_port = None
        self.running = False

        # 环形缓冲区初始化
        self.data_buffer = np.full((9, DATA_LENGTH), np.nan, dtype=np.float32)
        self.write_index = 0
        self.buffer_filled = False

        # 滤波器初始化
        nyquist = 0.5 * SAMPLE_RATE
        self.filter_b, self.filter_a = butter(5, FILTER_CUTOFF / nyquist, btype='low')
        self.filter_zi = [lfilter_zi(self.filter_b, self.filter_a) for _ in range(9)]

    def run(self):
        self.running = True
        try:
            self.serial_port = serial.Serial(self.com_port, baudrate=115200, timeout=1)
            self.serial_port.write(b'1')  # 启动数据传输

            while self.running:
                if self.serial_port.in_waiting:
                    raw_data = self.serial_port.readline().decode('utf-8', errors='ignore').strip()
                    self.data_received.emit(raw_data)

                    # 改进的正则表达式匹配
                    if match := re.match(r'^Channel:(-?\d+\.?\d*,){8}-?\d+\.?\d*$', raw_data):
                        values = list(map(float, raw_data.split('Channel:')[1].split(',')))
                        self._update_buffer(values)
        finally:
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()

    def _update_buffer(self, values):
        for i in range(9):
            # 单样本滤波处理
            filtered, self.filter_zi[i] = lfilter(
                self.filter_b,
                self.filter_a,
                [values[i]],
                zi=self.filter_zi[i]
            )
            # 确保取出单个元素
            self.data_buffer[i, self.write_index % DATA_LENGTH] = filtered[0]

        self.write_index += 1
        if self.write_index >= DATA_LENGTH:
            self.buffer_filled = True
            self.write_index %= DATA_LENGTH

    def get_plot_data(self):
        if self.write_index < PLOT_LENGTH:
            return self.data_buffer[:, :self.write_index]

        start = (self.write_index - PLOT_LENGTH) % DATA_LENGTH
        end = self.write_index % DATA_LENGTH

        if start < end:
            return self.data_buffer[:, start:end]
        else:
            return np.hstack((self.data_buffer[:, start:], self.data_buffer[:, :end]))

    def stop(self):
        self.running = False
        self.wait(2000)


class ADCPlotter(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("YuEEG Data Viewer")
        self.setWindowIcon(QtGui.QIcon('./school_logo.ico'))

        # 初始化UI
        self._setup_ui()

        # 初始化串口线程
        if not (com_port := self._detect_com_port()):
            QtWidgets.QMessageBox.critical(self, "错误", "未检测到可用串口")
            sys.exit(1)

        self.serial_thread = SerialThread(com_port)
        self.serial_thread.data_received.connect(self._append_serial_data)

        # 启动线程和定时器
        self.serial_thread.start()
        self._start_timers()

    def _setup_ui(self):
        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)
        layout = QtWidgets.QVBoxLayout(self.central_widget)

        # 绘图区域
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setAntialiasing(True)
        self.plot_widget.useOpenGL(True)
        self.plot_widget.setLabel('bottom', 'Samples')
        self.plot_widget.setLabel('left', 'Amplitude')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        layout.addWidget(self.plot_widget)

        # 初始化曲线
        colors = ['#FF0000', '#00FF00', '#0000FF', '#00FFFF',
                  '#FF00FF', '#FFFF00', '#FFFFFF', '#A0A0A0', '#FFA500']
        self.plots = []
        for i, color in enumerate(colors):
            plot = self.plot_widget.plot(pen=pg.mkPen(color, width=1.5))
            self.plots.append(plot)

        # 图例
        self.legend = pg.LegendItem(offset=(70, 20))
        self.legend.setParentItem(self.plot_widget.getPlotItem())
        for i, plot in enumerate(self.plots):
            self.legend.addItem(plot, f'CH{i + 1}')

        # 控制面板
        control_layout = QtWidgets.QHBoxLayout()
        self.checkboxes = [QtWidgets.QCheckBox(f"CH{i + 1}") for i in range(9)]
        for cb in self.checkboxes:
            cb.setChecked(True)
            control_layout.addWidget(cb)
        layout.addLayout(control_layout)
        self.checkboxes[0].setChecked(False)

    def _start_timers(self):
        self.plot_timer = QtCore.QTimer()
        self.plot_timer.timeout.connect(self._update_plot)
        self.plot_timer.start(UPDATE_INTERVAL)

    def _update_plot(self):
        data = self.serial_thread.get_plot_data()
        if data.size == 0:
            return

        # 动态调整Y轴范围
        active_channels = [i for i, cb in enumerate(self.checkboxes) if cb.isChecked()]
        if not active_channels:
            return

        visible_data = data[active_channels]
        y_min = np.nanmin(visible_data)
        y_max = np.nanmax(visible_data)
        if np.isnan(y_min) or np.isnan(y_max):
            return

        margin = (y_max - y_min) * 0.1 or 1.0
        self.plot_widget.setYRange(y_min - margin, y_max + margin, padding=0)

        # 更新曲线数据
        for i in active_channels:
            self.plots[i].setData(data[i])

    def _append_serial_data(self, text):
        self.statusBar().showMessage(text[-200:], 2000)

    def _detect_com_port(self):
        ports = serial.tools.list_ports.comports()
        for p in ports:
            if 'USB' in p.description:
                return p.device
        return None

    def closeEvent(self, event):
        self.serial_thread.stop()
        event.accept()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = ADCPlotter()
    window.show()
    sys.exit(app.exec_())