import sys
import os
import re
import time
import queue
from collections import deque
from datetime import datetime, timedelta

import numpy as np
from PyQt5 import QtWidgets, QtCore, QtGui
import pyqtgraph as pg
import serial
import serial.tools.list_ports
from PyQt5.QtWidgets import QFrame

from qfluentwidgets import CheckBox, ComboBox, PushButton, LineEdit, SpinBox, InfoBar, InfoBarPosition
from qfluentwidgets import FluentIcon as FIF

from scipy.signal import butter, filtfilt, lfilter, lfilter_zi, iirnotch, firwin, get_window
from scipy.signal import medfilt
# ================== 配置参数（可按需修改） ==================
SAMPLE_RATE = 500  # 采样率（与固件保持一致）
UPDATE_INTERVAL = 60  # UI刷新间隔 ms
DATA_LENGTH = 20000  # 环形缓存长度（每通道，增大以适应分时数据）
PLOT_LENGTH = 1000  # 时域显示长度
FFT_LENGTH = 500  # FFT长度（点数）

# 滤波参数
NOTCH_FREQ      = 50.0          # 保持50Hz陷波（工频干扰）
QUALITY_FACTOR  = 30            # 提高品质因数，更精准去除50Hz
LOW_CUTOFF      = 0.5           # 降低低频截止，保留更慢的变化
HIGH_CUTOFF     = 80.0          # 提高高频截止，保留方波边沿
FIR_ORDER       = 61            # 适当降低FIR阶数，减少延迟

# 中值滤波窗口（针对方波信号优化）
MEDIAN_WINDOW_SIZE = 5          # 5-7点（方波信号专用）

# 显示参数
DEFAULT_Y_LIM_UV = 100.0  # 固定Y轴半幅（±μV）

# ================== 日志配置 ==================
LOG_DIR = "logs"  # 日志保存目录
LOG_MAX_SIZE_MB = 100  # 单个日志文件最大大小（MB）
LOG_MAX_AGE_HOURS = 24  # 日志最大时长（小时）
LOG_FLUSH_SEC = 1.0  # 日志刷新间隔（秒）
LOG_BATCH_LINES = 1000  # 每批写入的行数
LOG_QUEUE_MAX = 10000  # 日志队列最大长度（防内存溢出）

class ChannelBuffer:
    """
    修复满缓冲后波形消失问题
    核心思路：
    1. x_axis 从每个通道实际最晚时间戳减去 n，保证不会超出 buffer
    2. np.interp 时限制插值范围在已有数据区间
    """
    def __init__(self, capacity=20000):
        self.capacity = capacity
        self.data = [np.zeros(capacity, dtype=np.float32) for _ in range(8)]
        self.timestamps = [np.zeros(capacity, dtype=np.int64) for _ in range(8)]
        self.indices = [0]*8
        self.is_full = [False]*8

    def append(self, channel_id, values: list, start_index=None):
        if channel_id < 0 or channel_id >= 8 or len(values) == 0:
            return

        n = len(values)
        idx = self.indices[channel_id]
        ts = np.arange(start_index, start_index + n) if start_index is not None else np.arange(idx, idx + n)

        if n > self.capacity:
            values = values[-self.capacity:]
            ts = ts[-self.capacity:]
            n = self.capacity

        for i in range(n):
            self.data[channel_id][idx] = values[i]
            self.timestamps[channel_id][idx] = ts[i]
            idx = (idx + 1) % self.capacity
            if idx == 0:
                self.is_full[channel_id] = True
        self.indices[channel_id] = idx

    def get_recent(self, n=PLOT_LENGTH):
        """
        获取最近 n 个点的数据
        修复20000点满后波形消失问题：
        1. 不依赖全局索引计算x轴
        2. 始终返回连续数组
        """
        y_data = np.full((8, n), np.nan, dtype=np.float32)
        x_axis = np.arange(n)  # 绘图直接用 0~n-1

        for ch in range(8):
            idx = self.indices[ch]
            if self.is_full[ch]:
                # 已满，取环形缓冲最后n个点
                data = np.concatenate((self.data[ch][idx:], self.data[ch][:idx]))
            else:
                # 未满，直接取已有数据
                data = self.data[ch][:idx]
            # 截取最后n个点
            y_data[ch, -len(data):] = data[-n:]
        return x_axis, y_data


# ================== 异步日志写入线程 ==================
class LogWriterThread(QtCore.QThread):
    """
    异步日志写入线程，解决以下问题：
    1. 避免UI线程因写日志而卡顿
    2. 支持日志自动分片（按大小/时间）
    3. 防止日志队列无限增长导致内存溢出
    4. 高效批量写入，减少I/O操作次数
    """
    log_rotated = QtCore.pyqtSignal(str)  # 发出新日志文件路径

    def __init__(self, base_dir: str, log_queue: queue.Queue):
        super().__init__()
        self.base_dir = base_dir
        self.log_queue = log_queue
        self.running = False
        self._f = None
        self._current_path = None
        self._start_time = None
        self._line_count = 0
        self._file_size = 0  # 当前文件字节数

    def _new_log_file(self):
        """创建新日志文件，添加头信息"""
        now = datetime.now()
        filename = f"EEG_log_{now.strftime('%Y%m%d_%H%M%S')}.csv"
        self._current_path = os.path.join(self.base_dir, filename)
        os.makedirs(self.base_dir, exist_ok=True)
        # 使用大缓冲区减少I/O次数
        self._f = open(self._current_path, "w", encoding="utf-8", buffering=1024 * 1024)
        # 写入头信息
        self._f.write(f"# YuEEG 日志 - {now.strftime('%Y-%m-%d %H:%M:%S')}\n")
        self._f.write("# 时间戳,CH1,CH2,CH3,CH4,CH5,CH6,CH7,CH8\n")
        self._f.flush()
        self._start_time = now
        self._line_count = 0
        self._file_size = 0
        self.log_rotated.emit(self._current_path)  # 通知UI

    def _should_rotate(self):
        """判断是否需要切换到新日志文件"""
        if self._f is None:
            return True
        # 按大小
        if self._file_size > LOG_MAX_SIZE_MB * 1024 * 1024:
            return True
        # 按时间
        if datetime.now() - self._start_time > timedelta(hours=LOG_MAX_AGE_HOURS):
            return True
        return False

    def run(self):
        """主线程：从队列取数据，批量写入磁盘"""
        self.running = True
        self._new_log_file()  # 初始化第一个文件

        batch = []  # 批量缓存
        last_flush = time.monotonic()

        while self.running:
            try:
                item = self.log_queue.get(timeout=0.2)  # 最多等0.2秒
            except queue.Empty:
                item = None

            if item is None:
                # 超时或收到停止信号
                if batch:
                    content = "\n".join(batch) + "\n"
                    self._f.write(content)
                    self._file_size += len(content.encode('utf-8'))
                    batch.clear()
                    self._f.flush()
                if not self.running:
                    break
            else:
                # 检查是否需要切分日志
                if self._should_rotate():
                    if batch:
                        self._f.write("\n".join(batch) + "\n")
                        batch.clear()
                    self._f.flush()
                    self._f.close()
                    self._new_log_file()  # 创建新文件

                batch.append(item)
                self._line_count += 1

                # 批量写入
                if len(batch) >= LOG_BATCH_LINES:
                    content = "\n".join(batch) + "\n"
                    self._f.write(content)
                    self._file_size += len(content.encode('utf-8'))
                    batch.clear()

                # 定期 flush
                now = time.monotonic()
                if now - last_flush >= LOG_FLUSH_SEC:
                    self._f.flush()
                    last_flush = now

        # 结束前最后 flush
        if batch:
            self._f.write("\n".join(batch) + "\n")
        self._f.flush()
        self._f.close()

    def stop(self):
        """安全停止线程"""
        self.running = False
        try:
            self.log_queue.put_nowait(None)  # 唤醒阻塞的 get()
        except Exception:
            pass
        self.wait(2000)


# ================== 串口线程（修复分时数据问题） ==================
class SerialThread(QtCore.QThread):
    data_received = QtCore.pyqtSignal(str)  # 原始数据行（用于状态栏）

    def __init__(self, com_port: str, log_queue: queue.Queue):
        super().__init__()
        self.com_port = com_port
        self.serial_port = None
        self.running = False
        self.log_queue = log_queue  # 日志队列

        # 使用通道专用缓冲区（修复核心问题）
        self.buffer = ChannelBuffer(capacity=DATA_LENGTH)
        self.global_index = 0  # 全局时间索引

        # 过滤开关
        self.filter_enabled = True
        self.median_enabled = False  # 中值滤波开关（UI 控制）

        # 滤波器初始化
        self._init_filters()

    # -------- 滤波器设计与状态 --------
    def _init_filters(self):
        nyquist = 0.5 * SAMPLE_RATE

        # 1) 50Hz 陷波（提高Q值）
        w0 = NOTCH_FREQ / nyquist
        self.b_notch, self.a_notch = iirnotch(w0, QUALITY_FACTOR)
        self.zi_notch = [lfilter_zi(self.b_notch, self.a_notch) for _ in range(8)]

        # 2) 方波优化带通（更宽通带）
        self.fir_coeff = firwin(FIR_ORDER, [LOW_CUTOFF / nyquist, HIGH_CUTOFF / nyquist], pass_zero=False)
        self.zi_fir = [np.zeros(FIR_ORDER - 1) for _ in range(8)]

        # 3) 中值滤波缓冲（针对方波优化）
        self.median_buffers = [deque(maxlen=MEDIAN_WINDOW_SIZE) for _ in range(8)]

    # -------- 主循环：读串口，解析，入缓冲 --------
    def run(self):
        self.running = True
        try:
            self.serial_port = serial.Serial("COM4", baudrate=115200, timeout=1)
            # 默认进入连续采样模式
            try:
                self.serial_port.write(b'1')
            except Exception:
                pass

            while self.running:
                chunk = self.serial_port.readline()
                if not chunk:
                    continue
                try:
                    raw = chunk.decode('utf-8', errors='ignore').strip()
                    # print("RAW:", raw)
                except Exception:
                    continue

                if not raw:
                    continue

                # 1. 原始数据送入日志队列（异步写盘）
                try:
                    # 尝试解析为8通道数据，成功则格式化为CSV
                    values = self._parse_line(raw)
                    if values and len(values) == 8:
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                        log_line = f"{timestamp},{','.join(map(str, values))}"
                        self.log_queue.put_nowait(log_line)
                    else:
                        # 无法解析的行，原样记录
                        self.log_queue.put_nowait(f"# {raw}")
                except queue.Full:
                    # 队列满则丢弃，防止阻塞采集
                    pass

                # 2. 限频更新状态栏（避免UI卡顿）
                self.data_received.emit(raw)

                # 3. 尝试解析并处理数据
                self._process_serial_data(raw)

        finally:
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()

    # -------- 处理串口数据（一次发8通道）--------
    def _process_serial_data(self, text: str):
        """处理串口数据：一次性8通道（针对方波信号优化）"""
        values = self._parse_line(text)
        if values is None or len(values) != 8:
            return

        # 遍历8个通道，逐一滤波并写入buffer
        for ch in range(8):
            val = values[ch]

            if self.filter_enabled:
                # ===== 方波信号专用优化滤波 =====
                # 1) 中值滤波优先（去除脉冲噪声，保留方波边沿）
                if self.median_enabled:
                    # 添加当前值到中值缓冲区
                    self.median_buffers[ch].append(val)

                    # 当缓冲区满时计算中值（窗口大小建议5-7点）
                    if len(self.median_buffers[ch]) >= self.median_buffers[ch].maxlen:
                        # 使用中值滤波去除脉冲噪声
                        median_val = float(np.median(self.median_buffers[ch]))
                        val = median_val  # 直接使用中值（去除了脉冲）

                # 2) 带通滤波（针对方波优化）
                # 注意：这里保留IIR滤波用于实时处理，但调整了参数
                y1, self.zi_notch[ch] = lfilter(
                    self.b_notch, self.a_notch, [val], zi=self.zi_notch[ch]
                )

                # 方波信号带通优化：更宽的通带，保留更多谐波成分
                y2, self.zi_fir[ch] = lfilter(
                    self.fir_coeff, [1.0], y1, zi=self.zi_fir[ch]
                )
                val = float(y2[0])

            # 写入对应通道的缓冲区（一次1个点）
            self.buffer.append(ch, [val], self.global_index)

        # 每行数据只增加一次全局时间索引
        self.global_index += 1

    # -------- 行解析：从任意前缀中抽取浮点数 --------
    def _parse_line(self, text: str):
        """
        兼容形如：
        "通道数据(μV): v1,v2,...,v8"
        或任意含冒号/空格后跟 8 个逗号分隔浮点数的行。
        提取前 8 个数并返回（μV）。
        """
        if ":" in text or "：" in text:
            part = re.split(r'[:：]', text, maxsplit=1)[1]
        else:
            part = text
        nums = re.findall(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?', part)
        if len(nums) < 8:
            return None
        # 转换为浮点数
        try:
            return list(map(float, nums))
        except ValueError:
            return None

    # -------- 提供绘图数据 --------
    def get_plot_data(self, length=PLOT_LENGTH):
        """
        获取最近 length 个点的数据
        修复20000点满后波形消失问题：
        1. 使用ChannelBuffer安全x轴
        2. np.interp插值在已有数据范围内
        """
        return self.buffer.get_recent(length)

    def get_fft_data(self, length=FFT_LENGTH):
        """
        获取FFT数据，直接用安全的get_plot_data
        """
        return self.get_plot_data(length)

    # -------- 外部控制 --------
    def set_filter_enabled(self, on: bool):
        self.filter_enabled = on

    def set_median_enabled(self, on: bool):
        self.median_enabled = on

    def send_mode(self, key: str):
        """向固件发送模式：'1'连续、'2'阻抗、'3'自检"""
        try:
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.write(key.encode('ascii'))
        except Exception:
            pass

    def stop(self):
        self.running = False
        self.wait(2000)


# ================== 主窗口（微调） ==================
class ADCPlotter(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("YuEEG Data Viewer")
        self.setWindowIcon(QtGui.QIcon('./school_logo.ico'))

        # 全局绘图配置
        pg.setConfigOptions(antialias=True, useOpenGL=True)

        # ========= 1. 创建日志系统 =========
        self.log_queue = queue.Queue(maxsize=LOG_QUEUE_MAX)
        self.log_thread = LogWriterThread(LOG_DIR, self.log_queue)
        self.log_thread.log_rotated.connect(self._on_log_rotated)
        self.log_thread.start()

        self._setup_ui()

        com_port = self._detect_com_port()
        if not com_port:
            QtWidgets.QMessageBox.critical(self, "错误", "未检测到可用串口")
            # 停止日志线程
            self.log_thread.stop()
            sys.exit(1)

        self.serial_thread = SerialThread(com_port, self.log_queue)
        self.serial_thread.data_received.connect(self._on_serial_line)
        self.serial_thread.start()

        self._start_timers()

        # 显示当前日志文件
        self._on_log_rotated(self.log_thread._current_path)

        # 默认启用自动Y轴，更适合稀疏信号
        self.auto_y_box.setChecked(True)
        self._on_auto_y_changed()

    # -------- UI 构建 --------
    def _setup_ui(self):
        cw = QtWidgets.QWidget()
        self.setCentralWidget(cw)
        main = QtWidgets.QVBoxLayout(cw)
        main.setContentsMargins(8, 8, 8, 8)
        main.setSpacing(8)

        # 绘图区
        self.time_plot = pg.PlotWidget()
        self.fft_plot = pg.PlotWidget()
        for p in (self.time_plot, self.fft_plot):
            p.showGrid(x=True, y=True, alpha=0.3)

        self.time_plot.setLabel('bottom', 'Samples')
        self.time_plot.setLabel('left', 'Amplitude (μV)')
        self.fft_plot.setLabel('bottom', 'Frequency (Hz)')
        self.fft_plot.setLabel('left', 'Amplitude (a.u.)')

        main.addWidget(self.time_plot)
        main.addWidget(self.fft_plot)

        # 曲线（8条）
        palette = ['#FF3B30', '#34C759', '#007AFF', '#5AC8FA',
                   '#AF52DE', '#FFCC00', '#FF9500', '#8E8E93']
        self.time_curves = [self.time_plot.plot(pen=pg.mkPen(color=c, width=1.5)) for c in palette]
        self.fft_curves = [self.fft_plot.plot(pen=pg.mkPen(color=c, width=1.2)) for c in palette]

        # 控制栏
        ctrl = QtWidgets.QHBoxLayout()
        main.addLayout(ctrl)
        # 我想在这里加一条分割线，作为ctrl和串口数据的分割线，但写的好像不对
        # 创建一条水平分割线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)  # 水平线
        line.setFrameShadow(QFrame.Sunken)  # 阴影效果（看起来是“凹下去”的）
        line.setStyleSheet("color: #cccccc;")  # 设置颜色（可选）

        main.addWidget(line)

        # 通道勾选
        self.ch_boxes = [CheckBox(f"CH{i + 1}") for i in range(8)]
        for cb in self.ch_boxes:
            cb.setChecked(True)
            ctrl.addWidget(cb)

        # 显示模式
        self.mode_combo = ComboBox()
        self.mode_combo.addItems(["波形", "频谱", "并列"])
        self.mode_combo.currentIndexChanged.connect(self._update_display_mode)
        ctrl.addWidget(self.mode_combo)

        # 滤波开关
        self.filter_box = CheckBox("滤波开启")
        self.filter_box.setChecked(True)
        self.filter_box.stateChanged.connect(
            lambda s: self.serial_thread.set_filter_enabled(self.filter_box.isChecked()))
        ctrl.addWidget(self.filter_box)

        # 中值滤波开关
        self.median_box = CheckBox("中值滤波(去基线)")
        self.median_box.setChecked(False)
        self.median_box.stateChanged.connect(
            lambda s: self.serial_thread.set_median_enabled(self.median_box.isChecked()))
        ctrl.addWidget(self.median_box)

        # Y轴控制
        self.auto_y_box = CheckBox("自动Y轴")
        self.auto_y_box.setChecked(False)  # 注意：初始化后会在__init__中设为True
        self.auto_y_box.stateChanged.connect(self._on_auto_y_changed)
        ctrl.addWidget(self.auto_y_box)

        self.y_spin = SpinBox()
        self.y_spin.setRange(10, 1000)
        self.y_spin.setValue(int(DEFAULT_Y_LIM_UV))
        self.y_spin.valueChanged.connect(self._apply_y_range)
        ctrl.addWidget(self.y_spin)

        # 模式切换按钮（标准/测试）
        self.fun_btn = PushButton("标准")
        self.fun_btn.clicked.connect(self._toggle_fun_mode)
        ctrl.addWidget(self.fun_btn)

        # 暂停
        self.pause_btn = PushButton("暂停")
        self.pause_btn.clicked.connect(self._toggle_pause)
        ctrl.addWidget(self.pause_btn)

        # 初始显示
        self._update_display_mode()
        self._apply_y_range()

    def _start_timers(self):
        self.plot_timer = QtCore.QTimer(self)
        self.plot_timer.timeout.connect(self._refresh_plots)
        self.plot_timer.start(UPDATE_INTERVAL)

    # -------- 事件处理 --------
    def _toggle_fun_mode(self):
        # 与固件保持一致：'1' 连续、'3' 自检
        if self.fun_btn.text() == "标准":
            self.serial_thread.send_mode('3')  # 切到自检
            self.serial_thread.set_filter_enabled(False)
            self.fun_btn.setText("测试")
            self._info("已切换到自检信号(测试)")
        else:
            self.serial_thread.send_mode('1')  # 回到连续采样
            self.serial_thread.set_filter_enabled(True)
            self.fun_btn.setText("标准")
            self._info("已切换到标准采样")

    def _toggle_pause(self):
        if self.plot_timer.isActive():
            self.plot_timer.stop()
            self.pause_btn.setText("继续")
        else:
            self.plot_timer.start()
            self.pause_btn.setText("暂停")

    def _update_display_mode(self):
        mode = self.mode_combo.currentText()
        if mode == "波形":
            self.time_plot.show()
            self.fft_plot.hide()
        elif mode == "频谱":
            self.time_plot.hide()
            self.fft_plot.show()
        else:
            self.time_plot.show()
            self.fft_plot.show()

    def _on_auto_y_changed(self):
        if self.auto_y_box.isChecked():
            self.time_plot.enableAutoRange(axis='y', enable=True)
        else:
            self.time_plot.enableAutoRange(axis='y', enable=False)
            self._apply_y_range()

    def _apply_y_range(self):
        if not self.auto_y_box.isChecked():
            lim = float(self.y_spin.value())
            self.time_plot.setYRange(-lim, +lim)

    def _refresh_plots(self):
        mode = self.mode_combo.currentText()
        if mode in ("波形", "并列"):
            self._update_time_plot()
        if mode in ("频谱", "并列"):
            self._update_fft_plot()

    def _update_time_plot(self):
        x, data = self.serial_thread.get_plot_data(PLOT_LENGTH)
        if data.size == 0:
            return

        active = [i for i, cb in enumerate(self.ch_boxes) if cb.isChecked()]
        if not active:
            return

        for i in active:
            self.time_curves[i].setData(x, data[i])

        # 自动滚动X轴
        if len(x) > 0:
            self.time_plot.setXRange(x[0], x[-1])

        # 自动Y轴范围（若开启）
        if self.auto_y_box.isChecked():
            # 只考虑有数据的区域
            mask = ~np.isnan(data)
            if np.any(mask):
                valid_data = data[mask]
                y_min, y_max = np.min(valid_data), np.max(valid_data)
                if y_min != y_max:
                    margin = (y_max - y_min) * 0.1 or 1.0
                    self.time_plot.setYRange(y_min - margin, y_max + margin)
                else:
                    # 单一值情况
                    self.time_plot.setYRange(y_min - 1, y_max + 1)

    def _update_fft_plot(self):
        x, data = self.serial_thread.get_fft_data(FFT_LENGTH)
        if data.size == 0:
            return

        fs = SAMPLE_RATE
        win = get_window('hann', data.shape[1])
        freq = np.fft.rfftfreq(len(win), 1.0 / fs)

        max_amp = 0.0
        for i in range(8):
            if not self.ch_boxes[i].isChecked():
                self.fft_curves[i].setData([], [])
                continue

            sig = data[i].astype(float)
            # 跳过全NaN的情况
            if np.all(np.isnan(sig)) or len(sig) < 8:
                self.fft_curves[i].setData([], [])
                continue

            # 处理NaN值
            sig = np.nan_to_num(sig)
            sig = sig - np.mean(sig)
            sig = sig * win

            amp = np.abs(np.fft.rfft(sig))
            # 仅展示 3~50 Hz
            mask = (freq >= 3.0) & (freq <= 50.0)
            self.fft_curves[i].setData(freq[mask], amp[mask])
            if amp[mask].size > 0:
                max_amp = max(max_amp, float(np.max(amp[mask])))

        if max_amp > 0:
            self.fft_plot.setYRange(0, max_amp * 1.1)

    def _on_serial_line(self, text: str):
        # 状态栏里看最后200字符
        try:
            self.statusBar().showMessage(text[-200:], 1500)
        except Exception:
            pass

    def _on_log_rotated(self, path: str):
        """日志切片通知，更新状态栏"""
        filename = os.path.basename(path)
        self.statusBar().showMessage(f"日志: {filename}", 3000)

    # -------- 串口发现 --------
    def _detect_com_port(self):
        ports = serial.tools.list_ports.comports()
        # 优先匹配常见关键字
        for p in ports:
            desc = (p.description or '').lower()
            if 'usb' in desc or 'ch340' in desc or 'cp210' in desc or 'silabs' in desc or 'uart' in desc or 'serial' in desc:
                return p.device
        # 兜底返回第一个
        return ports[0].device if ports else None

    def _info(self, msg: str):
        try:
            InfoBar.success(
                title='提示',
                content=msg,
                orient=QtCore.Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=1500,
                parent=self
            )
        except Exception:
            # 若 qfluentwidgets 不可用则忽略
            pass

    def closeEvent(self, event):
        """窗口关闭时清理资源"""
        # 先停止串口线程
        try:
            self.serial_thread.stop()
        except Exception:
            pass

        # 再停止日志线程（确保数据完整写入）
        try:
            self.log_thread.stop()
        except Exception:
            pass

        event.accept()


# ================== 程序入口 ==================
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = ADCPlotter()
    window.resize(1200, 800)
    window.show()
    sys.exit(app.exec_())