import sys
import time
from PyQt5 import QtWidgets, QtCore
from collections import deque
import pyqtgraph as pg
import serial
import serial.tools.list_ports
import re
import numpy as np
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout
from pyqtgraph import LegendItem
from qfluentwidgets import LineEdit, PushButton, TextEdit, CheckBox
from scipy.signal import welch, butter, filtfilt

# Set the length of the data pool to handle 750 samples (3 seconds of data at 250Hz)
data_len = 2000


class SerialThread(QtCore.QThread):
    data_received = QtCore.pyqtSignal(str)  # Signal to send data back to the main thread

    def __init__(self, com_port):
        super().__init__()
        self.com_port = com_port
        self.serial_port = serial.Serial(self.com_port, baudrate=115200, timeout=1)
        self.data_pool = [deque(maxlen=data_len) for _ in range(9)]  # Data pool for each channel
        self.running = True

    def run(self):
        self.serial_port.write(b'1')  # Send '1' to start data transmission
        while self.running:
            if self.serial_port.in_waiting:
                try:
                    raw_data = self.serial_port.readline().decode('utf-8').strip()
                    if raw_data:
                        # Emit the raw data to the main thread for display
                        self.data_received.emit(raw_data)
                        # print(f"{raw_data}")
                        # Integrity check (matches 'Channel:' followed by 9 float values)
                        match = re.match(r'Channel:([\d\.\-]+,){8}[\d\.\-]+', raw_data)
                        if match:
                            values = [float(x) for x in raw_data.split('Channel:')[1].split(',')]
                            # Add data to the pool for each channel
                            for i in range(9):
                                self.data_pool[i].append(values[i])
                except:
                    pass

    def stop(self):
        self.running = False
        self.serial_port.close()

    def send_data(self, data):
        self.serial_port.write(data.encode('utf-8') + b'\r\n')  # 发送数据到串口

    def get_latest_data(self, size):
        """Return the latest 'size' data from the data pool for all channels."""
        if size > len(self.data_pool[0]):
            raise ValueError("Requested size is larger than the current data pool size.")

        # Convert the latest 'size' elements from deque to numpy array for each channel
        return np.array([list(self.data_pool[i])[-size:] for i in range(9)])


class ADCPlotter(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("YuEEG Data Viewer")
        self.setWindowIcon(QIcon('./school_logo.ico'))
        self.setGeometry(100, 100, 800, 750)
        # Detect available COM ports and connect to the first available one
        com_port = self.detect_com_port()
        print(f"Connected to: {com_port}")
        if not com_port:
            raise Exception("No available COM ports detected.")

        # Main layout
        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QtWidgets.QVBoxLayout(self.central_widget)

        # Set up PyQtGraph plot
        self.plot_widget = pg.PlotWidget()
        self.layout.addWidget(self.plot_widget)
        # Create a legend
        self.legend = LegendItem(offset=(30, -30))  # Position the legend in the plot area
        self.legend.setParentItem(self.plot_widget.graphicsItem())
        # Create colored plots with thicker lines for each channel
        self.colors = ['r', 'g', 'b', 'c', 'm', 'y', 'w', 'grey', 'orange']
        self.plot_data = []
        for i in range(9):
            plot_item = self.plot_widget.plot(pen=pg.mkPen(color=self.colors[i], width=2))
            self.plot_data.append(plot_item)
            self.legend.addItem(plot_item, f"Channel {i + 1}")  # Add each plot to the legend with a label

        # Add a QTextEdit widget to display the raw data received
        self.text_box = TextEdit(self)
        self.text_box.setReadOnly(True)

        self.send_text = LineEdit()
        self.send_button = PushButton("Send")
        self.adc_button = PushButton("Normal")
        self.adc_button.clicked.connect(self.mod_switch)
        self.send_button.clicked.connect(self.send_data)
        sendV_layout = QHBoxLayout()
        sendV_layout.addWidget(self.adc_button)
        sendV_layout.addWidget(self.send_text)
        sendV_layout.addWidget(self.send_button)

        self.layout.addWidget(self.text_box)
        self.layout.addLayout(sendV_layout)

        # Add checkboxes for selecting channels to display
        self.checkboxes = []
        self.checkbox_layout = QHBoxLayout()
        for i in range(9):
            checkbox = CheckBox(f"通道{i + 1}")
            checkbox.setChecked(True)  # All channels checked by default
            self.checkboxes.append(checkbox)
            self.checkbox_layout.addWidget(checkbox)

        self.layout.addLayout(self.checkbox_layout)

        # Create a thread to handle serial data reception
        self.serial_thread = SerialThread(com_port)
        self.serial_thread.data_received.connect(self.handle_serial_data)
        self.serial_thread.start()

        # Timer to refresh plot every 20ms
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(100)
        self.beg = time.time()
        self.previous_psd = None

    def send_data(self):
        data = self.send_text.text()
        self.serial_thread.send_data(data)

    def mod_switch(self):
        if self.adc_button.text() == "Normal":
            self.serial_thread.send_data("3")
            self.adc_button.setText("Test")
        elif self.adc_button.text() == "Test":
            self.serial_thread.send_data("1")
            self.adc_button.setText("Normal")
    def detect_com_port(self):
        """Automatically detect available COM ports, excluding virtual ports."""
        ports = list(serial.tools.list_ports.comports())
        for port in ports:
            if 'Bluetooth' not in port.description and 'Virtual' not in port.description:
                return port.device
        return None

    def append_text_box(self, text):
        """Append text to the text box, keeping only the last 10 lines."""
        current_text = self.text_box.toPlainText()
        lines = current_text.split('\n')

        # Append new text
        lines.append(text)

        # Keep only the last 10 lines
        if len(lines) > 10:
            lines = lines[-10:]

        # Update the text box
        self.text_box.setPlainText('\n'.join(lines))
        # Move the cursor to the end
        # self.text_box.moveCursor(QtCore.QTextCursor.End)
    def check_psd(self, data, fs):
        threshold = 50
        if data is not None:
            psd_values = self.compute_psd(data, fs)
            current_psd_sum = np.sum(psd_values)
            if self.previous_psd is not None:
                # 比较当前PSD总和与上次总和的变化是否超过阈值
                if threshold < current_psd_sum - self.previous_psd < 500:
                    print(f"发现向上突变,目前差值为：{(current_psd_sum - self.previous_psd)}")
                    return True
                else:
                    print(f"差值为：{current_psd_sum - self.previous_psd}")
            self.previous_psd = current_psd_sum
    def compute_psd(self, data, fs):
        # 定义感兴趣的频率范围
        low_freq = 3
        high_freq = 40

        # 存储每个通道在3-40Hz的PSD值
        psd_values = []

        for i in range(data.shape[0]):
            # 计算功率谱密度
            f, psd = welch(data[i, :], fs, nperseg=500)

            # 只保留3到40Hz的频段
            freq_mask = (f >= low_freq) & (f <= high_freq)
            psd_in_band = psd[freq_mask]

            # 计算3到40Hz频段内的PSD值（通过对频段内的PSD进行积分）
            psd_band_value = np.trapz(psd_in_band, f[freq_mask])

            # 将结果存储起来
            psd_values.append(psd_band_value)
        return psd_values
    def handle_serial_data(self, raw_data):
        """Handle data received from the serial thread."""
        self.append_text_box(raw_data)

    # 定义 Buterworth 滤波器函数
    def apply_lowpass_filter(self, signal, cutoff_freq=50, sample_rate=500, order=5):
        nyquist_freq = 0.5 * sample_rate
        normalized_cutoff_freq = cutoff_freq / nyquist_freq
        b, a = butter(order, normalized_cutoff_freq, btype='low', analog=False)
        filtered_signal = filtfilt(b, a, signal)
        return filtered_signal

    def update_plot(self):
        """Update the plot based on the current data in the data pool."""
        try:
            # Fetch the latest 750 samples from the serial thread data pool
            latest_data = self.serial_thread.get_latest_data(data_len)


            # Update the plot for each channel
            for i in range(9):
                if self.checkboxes[i].isChecked():  # Only update if the channel is checked
                    waveform = latest_data[i]
                    filtered_waveform = self.apply_lowpass_filter(waveform)
                    self.plot_data[i].setData(filtered_waveform)
                else:
                    self.plot_data[i].setData([])  # Hide the waveform by clearing the data
            # self.plot_data[7].setData(latest_data[7])
            # Collect data from only the selected channels
            selected_data = [latest_data[i] for i in range(9) if self.checkboxes[i].isChecked()]

            # If there is any selected data, calculate global min and max
            if selected_data:
                global_min = np.min([np.min(data) for data in selected_data])
                global_max = np.max([np.max(data) for data in selected_data])
                # Set Y-axis range based on global min/max values
                self.plot_widget.setYRange(global_min, global_max)
            else:
                global_min = -4.5
                global_max = 4.5
            # Set Y-axis range based on global min/max values
            self.plot_widget.setYRange(global_min, global_max)
            eeg_data = latest_data
            self.channel = [1, 2, 3, 4, 5, 6, 7, 8]
            eeg_data = np.array([eeg_data[i - 1] for i in self.channel])
            if time.time() - self.beg > 1:
                # psd_values = self.compute_psd(eeg_data, 500)
                # current_psd_sum = np.sum(psd_values)
                # print(f"psd:{current_psd_sum}")
                self.beg = time.time()
        except ValueError:
            pass  # Skip plotting if not enough data is available

    def closeEvent(self, event):
        """Ensure the thread is stopped when the application is closed."""
        self.serial_thread.stop()
        self.serial_thread.wait()
        event.accept()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    main = ADCPlotter()
    main.show()
    sys.exit(app.exec_())
