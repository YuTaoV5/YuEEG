import sys
import serial
import threading
import numpy as np
from PyQt5.QtGui import QPalette, QColor, QFont
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QFrame, QGridLayout, QLabel, QHBoxLayout
from PyQt5.QtCore import pyqtSignal, QThread, QTimer, Qt
from pyqtgraph import PlotWidget, mkPen, ViewBox, TextItem
from qfluentwidgets import TransparentPushButton, ComboBox, LineEdit, TextEdit, PushButton
import serial.tools.list_ports
from scipy.signal import find_peaks
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import vtkmodules.all as vtk
from scipy.signal import iirnotch, lfilter

class SerialReader(QThread):
    data_received = pyqtSignal(list)
    status_received = pyqtSignal(list)

    def __init__(self, serial_port):
        super().__init__()
        self.serial_port = serial_port
        self.running = True

    def run(self):
        while self.running:
            line = self.serial_port.readline().decode('utf-8').strip()
            if line.startswith("Channel:"):
                if self.is_valid_data(line):
                    data = list(map(float, line.split(":")[1].split(",")))
                    self.data_received.emit(data)
            elif line.startswith("Lead-Off Status:"):
                status = line.split(":")[1].split(",")
                self.status_received.emit(status)

    def stop(self):
        self.running = False
        self.serial_port.close()

    def is_valid_data(self, line):
        if not line.startswith("Channel:"):
            return False
        parts = line.split(":")[1].split(",")
        return len(parts) == 9

class SerialCommunication(QFrame):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.serial_port = None

    def initUI(self):
        layout = QVBoxLayout()
        self.setObjectName("Chat")

        port_layout = QHBoxLayout()
        port_label = TransparentPushButton("Port:", self)
        self.port_combobox = ComboBox()
        self.refresh_ports()
        port_layout.addWidget(port_label)
        port_layout.addWidget(self.port_combobox)

        baud_layout = QHBoxLayout()
        baud_label = TransparentPushButton("Baud Rate:", self)
        self.baud_combobox = ComboBox()
        self.baud_combobox.addItems(["115200", "9600", "250000", "500000", "1000000"])
        baud_layout.addWidget(baud_label)
        baud_layout.addWidget(self.baud_combobox)

        self.send_text = LineEdit()
        self.receive_text = TextEdit()
        self.receive_text.setReadOnly(True)

        self.open_button = PushButton("Open Port")
        self.send_button = PushButton("Send")
        self.send_button.clicked.connect(self.send_data)
        self.send_button.setEnabled(False)

        sendV_layout = QVBoxLayout()
        sendV_layout.addWidget(self.send_text)
        sendV_layout.addWidget(self.send_button)
        send_layout = QHBoxLayout()
        send_layout.addWidget(TransparentPushButton("Send:", self))
        send_layout.addLayout(sendV_layout)

        recV_layout = QVBoxLayout()
        recV_layout.addWidget(self.receive_text)
        recV_layout.addWidget(self.open_button)
        rec_layout = QHBoxLayout()
        rec_layout.addWidget(TransparentPushButton("Receive:", self))
        rec_layout.addLayout(recV_layout)

        layout.addLayout(port_layout)
        layout.addLayout(baud_layout)
        layout.addLayout(send_layout)
        layout.addLayout(rec_layout)
        layout.setContentsMargins(30, 50, 20, 20)
        layout.setSpacing(10)
        self.setLayout(layout)

    def refresh_ports(self):
        ports = serial.tools.list_ports.comports()
        self.port_combobox.clear()
        for port in ports:
            self.port_combobox.addItem(port.device)

    def open_port(self):
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            self.serial_port = None
            self.open_button.setText("Open Port")
            self.send_button.setEnabled(False)
        else:
            port = self.port_combobox.currentText()
            baud_rate = int(self.baud_combobox.currentText())
            try:
                self.serial_port = serial.Serial(port, baud_rate, timeout=1)
                self.open_button.setText("Close Port")
                self.send_button.setEnabled(True)
                self.read_thread = SerialReader(self.serial_port)
                self.read_thread.data_received.connect(self.receive_data)
                self.read_thread.status_received.connect(self.receive_data)
                self.read_thread.start()
            except serial.SerialException as e:
                self.receive_text.append(f"Error opening port: {e}")

    def send_data(self):
        if self.serial_port and self.serial_port.is_open:
            data = self.send_text.text()
            self.serial_port.write(data.encode('utf-8'))

    def receive_data(self, data):
        self.receive_text.append(str(data))

class CustomViewBox(ViewBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setMouseMode(self.RectMode)

    def wheelEvent(self, ev, axis=None):
        if axis is None:
            axis = [0, 1]
        ev.accept()
        if ev.delta() > 0:
            scale_factor = 0.9
        else:
            scale_factor = 1.1
        self.scaleBy((scale_factor, 1), center=(0, 0))

class StatusGrid(QFrame):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.layout = QGridLayout()
        self.squares = []
        self.setObjectName("Impedance")
        for i in range(2):
            row = []
            for j in range(4):
                label = QLabel(self)
                label.setText(f"通道{i * 4 + j + 1}")
                label.setAutoFillBackground(True)
                palette = label.palette()
                palette.setColor(QPalette.Window, QColor('red'))
                label.setPalette(palette)
                # Using QFont to set bold and font size
                font = QFont()
                font.setBold(True)
                font.setPointSize(16)  # Set the font size to 16
                label.setFont(font)
                label.setAlignment(Qt.AlignCenter)
                self.layout.addWidget(label, i, j)
                row.append(label)
            self.squares.append(row)
        self.layout.setContentsMargins(30, 50, 20, 20)
        self.layout.setSpacing(50)
        self.setLayout(self.layout)

    def update_status(self, status_list):
        for i in range(2):
            for j in range(4):
                palette = self.squares[i][j].palette()
                color = QColor('blue') if status_list[i * 4 + j] == 'On' else QColor('red')
                palette.setColor(QPalette.Window, color)
                self.squares[i][j].setPalette(palette)


class TimeDomainPlot(QFrame):
    def __init__(self, channels_to_display, pen_colors, pen_widths, num_plots):
        super().__init__()
        self.channels_to_display = channels_to_display
        self.pen_colors = pen_colors
        self.pen_widths = pen_widths
        self.initUI()
        self.data_buffer = np.zeros((9, num_plots))  # Buffer for data points for 9 channels

        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.refresh_plot)
        self.update_timer.start(20)  # 50Hz refresh rate

        # Design notch filters for 49.5Hz, 50Hz, and 50.5Hz
        fs = 250  # Sampling frequency
        f0_1 = 49.5  # First frequency to be removed from signal
        f0_2 = 50.0  # Second frequency to be removed from signal
        f0_3 = 50.5  # Third frequency to be removed from signal
        Q = 30  # Quality factor
        w0_1 = f0_1 / (fs / 2)  # Normalized Frequency for 49.5Hz
        w0_2 = f0_2 / (fs / 2)  # Normalized Frequency for 50Hz
        w0_3 = f0_3 / (fs / 2)  # Normalized Frequency for 50.5Hz
        self.b1, self.a1 = iirnotch(w0_1, Q)
        self.b2, self.a2 = iirnotch(w0_2, Q)
        self.b3, self.a3 = iirnotch(w0_3, Q)

    def initUI(self):
        self.layout = QVBoxLayout()
        self.plot_widget = PlotWidget()
        self.layout.addWidget(self.plot_widget)
        self.setLayout(self.layout)
        self.setObjectName("TimeDomainPlot")
        self.plots = [self.plot_widget.plot(pen=mkPen(color=self.pen_colors[i], width=self.pen_widths[i])) for i in range(9)]
        self.plot_widget.setYRange(-10, 10)  # Initial Y range

    def update_plot(self, data):
        for i in self.channels_to_display:
            self.data_buffer[i] = np.roll(self.data_buffer[i], -1)
            self.data_buffer[i][-1] = data[i]

        # Apply notch filters to the entire data_buffer for each channel
        for i in self.channels_to_display:
            filtered_data = lfilter(self.b1, self.a1, self.data_buffer[i])
            filtered_data = lfilter(self.b2, self.a2, filtered_data)
            filtered_data = lfilter(self.b3, self.a3, filtered_data)
            self.data_buffer[i] = filtered_data

    def refresh_plot(self):
        half_buffer_length = self.data_buffer.shape[1] // 2
        for i in self.channels_to_display:
            self.plots[i].setData(self.data_buffer[i, -half_buffer_length:])

        max_y = np.max(self.data_buffer[self.channels_to_display, -half_buffer_length:])
        min_y = np.min(self.data_buffer[self.channels_to_display, -half_buffer_length:])
        self.plot_widget.setYRange(min_y, max_y)

class TimeDomainPlot2(QFrame):
    def __init__(self, channels_to_display, pen_colors, pen_widths, num_plots):
        super().__init__()
        self.channels_to_display = channels_to_display
        self.pen_colors = pen_colors
        self.pen_widths = pen_widths
        self.initUI()
        self.data_buffer = np.zeros((9, num_plots))  # Buffer for data points for 9 channels

        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.refresh_plot)
        self.update_timer.start(20)  # 50Hz refresh rate

        # Design notch filters for 49.5Hz, 50Hz, and 50.5Hz
        fs = 250  # Sampling frequency
        f0_1 = 49.5  # First frequency to be removed from signal
        f0_2 = 50.0  # Second frequency to be removed from signal
        f0_3 = 50.5  # Third frequency to be removed from signal
        Q = 30  # Quality factor
        w0_1 = f0_1 / (fs / 2)  # Normalized Frequency for 49.5Hz
        w0_2 = f0_2 / (fs / 2)  # Normalized Frequency for 50Hz
        w0_3 = f0_3 / (fs / 2)  # Normalized Frequency for 50.5Hz
        self.b1, self.a1 = iirnotch(w0_1, Q)
        self.b2, self.a2 = iirnotch(w0_2, Q)
        self.b3, self.a3 = iirnotch(w0_3, Q)

    def initUI(self):
        self.layout = QVBoxLayout()
        self.plot_widgets = []
        self.plots = []
        for i in range(9):
            plot_widget = PlotWidget()
            plot_widget.setYRange(-10, 10)  # Initial Y range
            self.layout.addWidget(plot_widget)
            self.plot_widgets.append(plot_widget)
            plot = plot_widget.plot(pen=mkPen(color=self.pen_colors[i], width=self.pen_widths[i]))
            self.plots.append(plot)
        self.setLayout(self.layout)
        self.setObjectName("TimeDomainPlot2")

    def update_plot(self, data):
        for i in self.channels_to_display:
            self.data_buffer[i] = np.roll(self.data_buffer[i], -1)
            self.data_buffer[i][-1] = data[i]

        # Apply notch filters to the entire data_buffer for each channel
        for i in self.channels_to_display:
            filtered_data = lfilter(self.b1, self.a1, self.data_buffer[i])
            filtered_data = lfilter(self.b2, self.a2, filtered_data)
            filtered_data = lfilter(self.b3, self.a3, filtered_data)
            self.data_buffer[i] = filtered_data

    def refresh_plot(self):
        half_buffer_length = self.data_buffer.shape[1] // 2
        for i in self.channels_to_display:
            self.plots[i].setData(self.data_buffer[i, -half_buffer_length:])

        for i in range(9):
            max_y = np.max(self.data_buffer[i, -half_buffer_length:])
            min_y = np.min(self.data_buffer[i, -half_buffer_length:])
            self.plot_widgets[i].setYRange(min_y, max_y)

class FrequencyDomainPlot(QFrame):
    def __init__(self, channels_to_display, pen_colors, pen_widths, num_plots):
        super().__init__()
        self.channels_to_display = channels_to_display
        self.pen_colors = pen_colors
        self.pen_widths = pen_widths
        self.initUI()
        self.data_buffer = np.zeros((9, num_plots))  # Buffer for 100 data points for 9 channels

        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.refresh_plot)
        self.update_timer.start(20)  # 50Hz refresh rate

        # Design notch filters for 49.5Hz, 50Hz, and 50.5Hz
        fs = 250  # Sampling frequency
        f0_1 = 49.0  # First frequency to be removed from signal
        f0_2 = 50.0  # Second frequency to be removed from signal
        f0_3 = 51.0  # Third frequency to be removed from signal
        Q = 30  # Quality factor
        w0_1 = f0_1 / (fs / 2)  # Normalized Frequency for 48Hz
        w0_2 = f0_2 / (fs / 2)  # Normalized Frequency for 49Hz
        w0_3 = f0_3 / (fs / 2)  # Normalized Frequency for 50Hz
        self.b1, self.a1 = iirnotch(w0_1, Q)
        self.b2, self.a2 = iirnotch(w0_2, Q)
        self.b3, self.a3 = iirnotch(w0_3, Q)

    def initUI(self):
        self.layout = QVBoxLayout()
        self.plot_widget = PlotWidget(viewBox=CustomViewBox())
        self.layout.addWidget(self.plot_widget)
        self.setLayout(self.layout)
        self.setObjectName("FrequencyDomainPlot")
        self.plots = [self.plot_widget.plot(pen=mkPen(color=self.pen_colors[i], width=self.pen_widths[i])) for i in range(9)]
        self.peak_texts = [TextItem("", color=self.pen_colors[i]) for i in range(9)]
        for text in self.peak_texts:
            self.plot_widget.addItem(text)
        self.plot_widget.setYRange(0, 10)  # Initial Y range

    def update_plot(self, data):
        for i in self.channels_to_display:
            self.data_buffer[i] = np.roll(self.data_buffer[i], -1)
            self.data_buffer[i][-1] = data[i]

        # Apply notch filters to the entire data_buffer for each channel
        for i in self.channels_to_display:
            filtered_data = lfilter(self.b1, self.a1, self.data_buffer[i])
            filtered_data = lfilter(self.b2, self.a2, filtered_data)
            filtered_data = lfilter(self.b3, self.a3, filtered_data)
            self.data_buffer[i] = filtered_data

    def refresh_plot(self):
        freq_data = np.abs(np.fft.rfft(self.data_buffer, axis=1))
        freqs = np.fft.rfftfreq(self.data_buffer.shape[1], d=1 / 250.0)  # Assuming 250Hz sampling rate

        # Filter frequency data to only include 3-40Hz
        mask = (freqs >= 3) & (freqs <= 100)
        filtered_freqs = freqs[mask]
        filtered_freq_data = freq_data[:, mask]

        for i in self.channels_to_display:
            self.plots[i].setData(filtered_freqs, filtered_freq_data[i])

            peaks, _ = find_peaks(filtered_freq_data[i])
            if len(peaks) > 0:
                peak_freq = filtered_freqs[peaks]
                peak_value = filtered_freq_data[i][peaks]
                max_peak_index = np.argmax(peak_value)
                self.peak_texts[i].setPos(peak_freq[max_peak_index], peak_value[max_peak_index])
                self.peak_texts[i].setText(f"{peak_freq[max_peak_index]:.1f} Hz")
            else:
                self.peak_texts[i].setText("")

        max_y = np.max(filtered_freq_data[self.channels_to_display])
        self.plot_widget.setYRange(0, max_y)

class TFwindow(QWidget):
    def __init__(self, channels_to_display, pen_colors, pen_widths, plot_num):
        super().__init__()
        self.time_domain_plot = TimeDomainPlot(channels_to_display, pen_colors, pen_widths, plot_num)
        self.frequency_domain_plot = FrequencyDomainPlot(channels_to_display, pen_colors, pen_widths, plot_num)
        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.time_domain_plot)
        self.layout.addWidget(self.frequency_domain_plot)
        self.setLayout(self.layout)
        self.setObjectName("TFplot")
        self.setWindowTitle('Real-time Serial Data Plotter')
        self.layout.setContentsMargins(30, 50, 20, 20)

    def update_plots(self, data):
        self.time_domain_plot.update_plot(data)
        self.frequency_domain_plot.update_plot(data)

    def closeEvent(self, event):
        self.time_domain_plot.update_timer.stop()
        self.frequency_domain_plot.update_timer.stop()
        event.accept()


class VTKWidget(QWidget):
    def __init__(self, parent=None):
        super(VTKWidget, self).__init__(parent)
        self.vl = QVBoxLayout()

        # VTK Renderer
        self.vtkWidget = QVTKRenderWindowInteractor(self)
        self.vl.addWidget(self.vtkWidget)

        self.ren = vtk.vtkRenderer()
        self.vtkWidget.GetRenderWindow().AddRenderer(self.ren)
        self.iren = self.vtkWidget.GetRenderWindow().GetInteractor()

        # Load OBJ and MTL files
        self.load_obj_file("resource/PCB.obj", "resource/PCB.mtl")

        # Add a light to the renderer
        self.add_light()

        self.setLayout(self.vl)
        self.iren.Initialize()

    def load_obj_file(self, obj_file_path, mtl_file_path):
        # Create an OBJ importer
        importer = vtk.vtkOBJImporter()
        importer.SetFileName(obj_file_path)
        importer.SetFileNameMTL(mtl_file_path)
        importer.SetTexturePath("resource")
        importer.SetRenderWindow(self.vtkWidget.GetRenderWindow())
        importer.Update()

        self.ren.ResetCamera()

    def add_light(self):
        # Create a light
        light = vtk.vtkLight()
        light.SetFocalPoint(0, 0, 0)
        light.SetPosition(1, 1, 1)
        light.SetIntensity(0.3)  # Adjust intensity to make the scene darker

        self.ren.AddLight(light)
        # Set a darker background color
        colors = vtk.vtkNamedColors()
        self.ren.SetBackground(colors.GetColor3d("DarkSlateGray"))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    channels_to_display = [0]  # Example control parameter list
    pen_colors = ['r', 'g', 'b', 'c', 'm', 'y', 'k', 'w', 'orange']
    pen_widths = [2, 2, 2, 2, 2, 2, 2, 2, 2]
    tfplot = TFwindow(channels_to_display, pen_colors, pen_widths, 100)
    leadoff = StatusGrid()
    ser_frame = SerialCommunication()
    vtk_demo = VTKWidget()
    def open_port():
        if ser_frame.serial_port and ser_frame.serial_port.is_open:
            ser_frame.serial_port.close()
            ser_frame.serial_port = None
            ser_frame.open_button.setText("Open Port")
            ser_frame.send_button.setEnabled(False)
        else:
            port = ser_frame.port_combobox.currentText()
            baud_rate = int(ser_frame.baud_combobox.currentText())
            try:
                ser_frame.serial_port = serial.Serial(port, baud_rate, timeout=1)
                ser_frame.open_button.setText("Close Port")
                ser_frame.send_button.setEnabled(True)
                read_thread = SerialReader(ser_frame.serial_port)
                read_thread.data_received.connect(ser_frame.receive_data)
                read_thread.status_received.connect(leadoff.update_status)
                read_thread.data_received.connect(tfplot.update_plots)
                read_thread.start()
            except serial.SerialException as e:
                ser_frame.receive_text.append(f"Error opening port: {e}")

    ser_frame.open_button.clicked.connect(open_port)
    tfplot.show()
    ser_frame.show()
    leadoff.show()
    vtk_demo.show()
    sys.exit(app.exec_())
