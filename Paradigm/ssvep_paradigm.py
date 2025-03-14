# -*- coding: utf-8 -*-

'''库文件'''
import math
import random
import sys
import time
import datetime
import logging
from loguru import logger
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import numpy as np
from pyqtgraph import PlotWidget, mkPen
from qfluentwidgets import *
from qfluentwidgets import FluentIcon as FIF
from collections import deque
from scipy.signal import iirnotch, lfilter, welch

logging.basicConfig(level=logging.INFO)  # logging.INFO
import re

'''辅助功能'''
from ui.ui import initUI
# from chat_ui import *
from src.FBCCA2 import fbcca_realtime
from src.tts import TTS
from Multi_Language import MultiLangAutoComplete, word_tokenize

import numpy as np
from collections import deque
from PyQt5 import QtWidgets, QtCore
import serial
import serial.tools.list_ports
from scipy.signal import butter, lfilter, lfilter_zi

# 配置参数
DATA_LENGTH = 20000  # 数据缓存长度
PLOT_LENGTH = 750  # 显示数据长度
FFT_LENGTH = 1000  # FFT分析长度
UPDATE_INTERVAL = 30  # 界面刷新间隔(ms)
SAMPLE_RATE = 500  # 采样率
FILTER_CUTOFF = 45  # 低通滤波截止频率
# 新增滤波器参数
NOTCH_FREQ = 50.0  # 陷波频率
QUALITY_FACTOR = 30  # 品质因数（决定带宽）

class SerialThread(QtCore.QThread):
    data_received = QtCore.pyqtSignal(str)

    def __init__(self, com_port):
        super().__init__()
        self.com_port = com_port
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

        # 为每个通道初始化滤波器状态
        for i in range(9):
            self.zi_notch[i] = lfilter_zi(self.b_notch, self.a_notch)


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

        # 将滤波后的数据存入缓冲区（替代原始数据）
        while len(self.timestamps) >= self.max_data_length:
            for ch in self.data_buffer:
                ch.pop(0)
            self.timestamps.pop(0)

        for i in range(9):
            self.data_buffer[i].append(filtered_values[i])
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

# Example usage:
# self.serial_thread = SerialThread(com_port)
# self.serial_thread.start()

class SSVEPApp(QWidget):
    def __init__(self):
        super().__init__()
        self.serial_thread = None
        self.timer = QTimer()  # 定时器
        self.timer2 = QTimer()
        self.sta = 0
        self.end = 0
        self.beg = 0
        self.previous_psd = 0
        self.sum = 0  # 计时总误差
        self.key_fre = []  # 按钮频率
        self.key_phr = []  # 按钮相位
        self.buttons = []
        self.count = 0  # 计数器
        self.result = 0
        self.res_list = []  # 输入序列
        self.py2hz_list = []  # 备选按钮文本显示
        self.teeth_cnt = 0
        self.tri_count = 0
        # 设置显示在哪块屏幕
        # desktop = QApplication.desktop()
        # self.setGeometry(desktop.screenGeometry(1))
        self.tp7_th = -99999
        self.pinyin_mod = 'english'
        self.inputText = ""
        self.inputCount = 0
        self.all_pinyin_list = ['min', 'suan', 'deng', 'chui', 'kun', 'me', 'nie', 'zhong', 'bai', 'zha', 'dian', 'pi',
                                'nuan', 'ne', 'hong', 'can', 'yang', 'chun', 'fiao', 'qian', 'lei', 'na', 'lao', 'yi',
                                'zhu', 'weng', 'zun', 'ai', 'zhi', 'san', 'jiang', 'shun', 'cai', 'cun', 'tie', 'yong',
                                'lv', 'zhou', 'chuan', 'mian', 'peng', 'zhuo', 'cou', 'suo', 'dai', 'er', 'mei', 'xin',
                                'xian', 'kua', 'pao', 'ge', 'ru', 'jie', 'gou', 'rang', 'null', 'dou', 'sang', 'su',
                                'mu', 'long', 'gong', 'zuo', 'hai', 'fa', 'lo', 'kuai', 'pian', 'heng', 'jiong', 'guai',
                                'diu', 'shao', 'qun', 'bi', 'chen', 'shuo', 'tun', 'chi', 'bian', 'chai', 'xiao',
                                'duan', 'fou', 'tu', 'gan', 'tiao', 'diao', 'pei', 'shuang', 'cen', 'chou', 'lai', 'an',
                                'te', 'ri', 'fang', 'zeng', 'ti', 'cha', 'bu', 'ying', 'nou', 'wei', 'zai', 'pen',
                                'zong', 'pa', 'liao', 'gao', 'reng', 'xiang', 're', 'ni', 'guo', 'dia', 'hu', 'yin',
                                'kai', 'ruan', 'ming', 'sou', 'lin', 'wai', 'bin', 'zi', 'nian', 'hua', 'nai', 'ang',
                                'qiao', 'geng', 'song', 'mie', 'jun', 'tuan', 'dun', 'fu', 'kang', 'pu', 'zhang',
                                'bang', 'zhuang', 'de', 'shuan', 'cui', 'en', 'qve', 'pai', 'dang', 'shi', 'men', 'liu',
                                'nuo', 'dei', 'zhao', 'ran', 'huang', 'ken', 'nen', 'she', 'ju', 'ren', 'ma', 'qiong',
                                'ruo', 'bao', 'zei', 'pou', 'nu', 'shang', 'fei', 'ke', 'cheng', 'o', 'dan', 'lou',
                                'zui', 'gui', 'cao', 'piao', 'ka', 'qia', 'cong', 'bing', 'zhai', 'bei', 'gun', 'tang',
                                'kui', 'che', 'miao', 'za', 'keng', 'lan', 'xie', 'le', 'pang', 'chuo', 'chan', 'niu',
                                'shan', 'zao', 'tuo', 'ji', 'ca', 'mao', 'shen', 'hen', 'ci', 'zuan', 'ei', 'nong',
                                'tong', 'zen', 'du', 'sa', 'mi', 'ye', 'tan', 'hao', 'tao', 'ya', 'shou', 'jing',
                                'guan', 'miu', 'ga', 'ping', 'a', 'dong', 'cuo', 'sheng', 'zhen', 'beng', 'mo', 'zhuan',
                                'wang', 'mai', 'chong', 'zhuai', 'lun', 'wo', 'run', 'tai', 'qing', 'rong', 'xve',
                                'rou', 'ku', 'kou', 'ha', 'fan', 'hou', 'teng', 'bie', 'sun', 'den', 'kuang', 'lve',
                                'ou', 'ding', 'gen', 'da', 'quan', 'luan', 'nei', 'po', 'duo', 'qie', 'qiang', 'yan',
                                'shu', 'zhan', 'jiao', 'bo', 'li', 'xi', 'he', 'zan', 'nun', 'shai', 'ting', 'chuang',
                                'chua', 'huo', 'hei', 'luo', 'ce', 'yve', 'xiu', 'zhua', 'jin', 'dui', 'cu', 'juan',
                                'xia', 'jve', 'fo', 'shua', 'wu', 'lie', 'ze', 'la', 'kan', 'shuai', 'chang', 'liang',
                                'seng', 'zang', 'kong', 'qin', 'nan', 'gai', 'gu', 'hui', 'zhui', 'sen', 'ta', 'pie',
                                'tou', 'ling', 'neng', 'se', 'hang', 'chu', 'chuai', 'ban', 'man', 'gua', 'mou',
                                'guang', 'chao', 'qiu', 'leng', 'xing', 'gei', 'nao', 'shui', 'dao', 'cuan', 'yu', 'xu',
                                'fen', 'zheng', 'biao', 'niao', 'xun', 'lang', 'nin', 'lia', 'ao', 'die', 'jia', 'rui',
                                'han', 'qi', 'zhun', 'mang', 'feng', 'kao', 'sui', 'si', 'hun', 'sai', 'nve', 'niang',
                                'lu', 'zu', 'tian', 'di', 'jian', 'lian', 'xiong', 'yo', 'shei', 'ning', 'yuan', 'e',
                                'ba', 'yun', 'jiu', 'rao', 'tui', 'zhei', 'sao', 'kuan', 'wa', 'nang', 'pan', 'zou',
                                'wen', 'yao', 'huai', 'gang', 'wan', 'meng', 'ben', 'xuan', 'huan', 'nv', 'pin', 'ceng',
                                'cang', 'kei', 'qu', 'zhe', 'sha', 'you', 'kuo']

        # 加载已有的字词库或创建新的
        self.auto_complete = MultiLangAutoComplete('autocomplete_data.pkl')

    # 参数更新
    def initPara(self, Fs=500, fsc_flag=False, rec_flag=True, cal_flag=True, pinyin_mod='chinese',
                 my_wave=0,
                 fre=100, rows=8, cols=5, sta_fre=15, end_fre=8, v_space=0.2, tlen=4, teeth=41,
                 channel=[1,2,3,4,5,6,7,8],
                 buttonNames=["1", "2", "3", "4", "5", "6", "7", "展开",
                              "Q", "W", "E", "R", "T", "Y", "U", "I",
                              "O", "P", "A", "S", "D", "F", "G", "H",
                              "J", "K", "L", "Z", "X", "C", "V", "B",
                              "N", "M", "，", "。", "_", "确认", "语音", "退格"]):
        """
        #########################
            SSVEP配置
        #########################
        """
        self.orgFs = Fs  # 采样采样率
        self.fsc_flag = fsc_flag  # 是否全屏
        self.rec_flag = rec_flag  # 是否接受在线数据
        self.cal_flag = cal_flag  # 是否使用算法分析
        self.wave = my_wave  # 1为方波，0为sin波形
        self.fre = fre
        self.rows, self.cols = rows, cols
        self.sta_fre = sta_fre
        self.end_fre = end_fre
        self.v_space = v_space
        self.tlen = tlen
        self.teeth = teeth
        self.channel = channel
        self.buttonNames = buttonNames
        self.pinyin_mod = pinyin_mod
        '''
        #########################
            在线接收配置
        #########################
        '''
        if self.rec_flag:
            if not (com_port := self.detect_com_port()):
                QtWidgets.QMessageBox.critical(self, "错误", "未检测到可用串口")
                sys.exit(1)

            self.serial_thread = SerialThread(com_port)
            self.serial_thread.start()

    def initEvent(self):

        self.pre_data(self.sta_fre, self.end_fre, self.v_space, self.rows, self.cols)
        self.timer.setInterval(int(pow(10, 3) / self.fre))  # 设置计时器的间隔，单位是毫秒
        self.timer.timeout.connect(self.onTimerOut)

        self.timer2.setInterval(200)  # 设置计时器的间隔，单位是毫秒
        self.timer2.timeout.connect(self.teeth_judge)

        self.buttonAbove.clicked.connect(self.demo)

    def detect_com_port(self):
        """Automatically detect available COM ports, excluding virtual ports."""
        ports = list(serial.tools.list_ports.comports())
        for port in ports:
            if 'Bluetooth' not in port.description and 'Virtual' not in port.description:
                return port.device
        return None

    # 根据开头找到所有拼音
    def find_starting_with(self, input_list, prefix):
        return [s for s in input_list if s.startswith(prefix)]

    def demo(self):
        self.timer.start()
        logging.info("开始闪烁")

    def pre_data(self, sta_fre, end_fre, v_space, row, cul):
        # 生成频率与间隔序列
        for i in range(cul):
            tmp = np.linspace(sta_fre + i * v_space, end_fre + i * v_space, row).tolist()
            self.key_fre.append(tmp)
            logging.debug(str(tmp) + ',')
            tmp = np.linspace(0 + i * 0.5, (self.rows - 1) * 0.5 + i * 0.5, row).tolist()
            self.key_phr.append(tmp)
        logging.debug("ph:" + str(self.key_phr))

    def set_button_background_colors(self):
        for row in range(self.rows):
            for col in range(self.cols):
                button = self.buttons[row * self.cols + col]
                button.changeColor("white")

    def buttonClickHandler(self):
        sender = self.sender()
        if isinstance(sender, QPushButton):
            button_text = sender.text()
            button_index = next((i for i, button in enumerate(self.buttons) if button.text() == button_text), None)
            if button_index is not None:
                self.set_button_background_colors()
                self.buttons[button_index].changeColor("red")
                QApplication.processEvents()  # 刷新界面
                button_handlers = {
                    "退格": self.handle_backspace_button,
                    "语音": self.handle_voice_button,
                    "确认": self.handle_confirm_button,
                    "展开": self.handle_expand_button,
                    "收缩": self.handle_shrink_button,
                    "发送": self.handle_send_button,
                    "↓": self.handle_down_button,
                    "↑": self.handle_up_button,
                }

                # 如果按钮名称在字典中，就调用对应的处理函数
                if button_text in button_handlers:
                    button_handlers[button_text](button_index)

                # 处理其他情况
                elif button_text.isalpha() and button_text.isupper() and len(button_text) == 1:
                    self.handle_alpha_button(button_text.lower())
                else:
                    self.handle_other_buttons(button_text, button_index)

                logging.info(f"Button '{button_text}' was clicked.")
                QApplication.processEvents()

    # 下面是各个处理函数的定义，需要根据实际情况来实现这些函数
    def handle_backspace_button(self, index):
        # 在这里实现退格按钮的处理逻辑
        if index == self.buttonNames.index("退格"):
            if self.res_list:
                if len(self.res_list[-1]) != 1:
                    self.res_list[-1] = self.res_list[-1][:-1]
                else:
                    self.res_list = self.res_list[:-1]
                self.py2hz_list = [] if not self.res_list else self.py2hz_list
            else:
                self.inputText = self.inputText[:-1]
                self.res_list = []
                self.py2hz_list = []
            self.update_ui_after_backspace()
            QApplication.processEvents()

    def update_ui_after_backspace(self):
        self.inputField.setText((self.inputText + str(self.res_list)) if self.res_list else self.inputText)
        self.choseField.setText("")
        if self.res_list:
            self.update_pinyin_and_ui()

    def handle_voice_button(self, index):
        # 在这里实现语音按钮的处理逻辑
        if index == self.buttonNames.index("语音"):
            TTS(TEXT=self.inputText)

    def handle_send_button(self, index):
        if index == self.buttonNames.index("发送"):
            txt = self.inputText
            # # 使用串口
            # import serial
            # # 创建一个Serial对象，指定串口名称和波特率
            # ser = serial.Serial('COM1', 9600)
            # ser.write(txt)

            # 保存文本
            # 打开文件，如果文件不存在，将会创建一个新文件
            with open("output.txt", "w") as f:
                # 将字符串写入文件
                f.write(txt)
            self.inputText = ""
            self.inputField.setText(self.inputText)

    def handle_confirm_button(self, index):
        confirm_index = self.buttonNames.index("确认")
        if index == confirm_index:
            try:
                pass

            except Exception as e:
                self.py2hz_list = []
                self.res_list = []
                logging.error(f"处理出错，请重新输入。错误详情: {str(e)}")

            logging.debug(f"py2hz_list: {self.py2hz_list}")
            QApplication.processEvents()

    def handle_expand_button(self, index):
        # 在这里实现展开按钮的处理逻辑
        if index == self.buttonNames.index("展开"):
            self.tablecount = 0
            self.buttons[index].changeColor("white")
            for col in range(self.cols):
                for row in range(self.rows):
                    if self.tablecount < len(self.py2hz_list):
                        self.buttons[col * self.rows + row].setText(self.py2hz_list[self.tablecount])
                    else:
                        self.buttons[col * self.rows + row].setText("")
                    self.tablecount = self.tablecount + 1
            self.tablecount = self.tablecount - 3
            self.buttons[self.buttonNames.index("退格")].setText("收缩")
            self.buttons[self.buttonNames.index("确认")].setText("↑")
            self.buttons[self.buttonNames.index("语音")].setText("↓")

    def handle_shrink_button(self, index):
        # 在这里实现收缩按钮的处理逻辑
        if index == self.buttonNames.index("退格"):
            self.update_ui()

    def handle_down_button(self, index):
        # 在这里实现向下按钮的处理逻辑
        for col in range(self.cols):
            for row in range(self.rows):
                if self.tablecount < len(self.py2hz_list):
                    self.buttons[col * self.rows + row].setText(self.py2hz_list[self.tablecount])
                else:
                    self.buttons[col * self.rows + row].setText("")
                self.tablecount = self.tablecount + 1
        self.tablecount = self.tablecount - 3
        self.buttons[self.buttonNames.index("退格")].setText("收缩")
        self.buttons[self.buttonNames.index("确认")].setText("↑")
        self.buttons[self.buttonNames.index("语音")].setText("↓")
        logging.info("tablecount:" + str(self.tablecount))

    def handle_up_button(self, index):
        # 在这里实现向上按钮的处理逻辑
        if self.tablecount >= (5 * 8 - 3):
            self.tablecount = self.tablecount - (5 * 8 - 3) * 2  # 一页只有37个备选
            for col in range(self.cols):
                for row in range(self.rows):
                    if self.tablecount < len(self.py2hz_list) and self.tablecount >= 0:
                        self.buttons[col * self.rows + row].setText(self.py2hz_list[self.tablecount])
                    else:
                        self.buttons[col * self.rows + row].setText("")
                    self.tablecount = self.tablecount + 1
            self.tablecount = self.tablecount - 3
            self.buttons[self.buttonNames.index("退格")].setText("收缩")
            self.buttons[self.buttonNames.index("确认")].setText("↑")
            self.buttons[self.buttonNames.index("语音")].setText("↓")
            logging.info("tablecount:" + str(self.tablecount))
        else:
            pass

    def handle_other_buttons(self, button_text, button_index):
        # 在这里实现其他按钮的处理逻辑
        try:
            if button_index < 8:
                text_to_add = self.py2hz_list[button_index]
            else:
                text_to_add = button_text

            if self.pinyin_mod != 'chinese':
                self.inputText = self.inputText + " " + text_to_add
            else:
                self.inputText = self.inputText + text_to_add
            self.inputField.setText(self.inputText)
            chs_len = len(self.res_list) - len(text_to_add)
            if chs_len > 0:
                self.res_list = self.res_list[-chs_len:]
                self.update_pinyin_and_ui()
                self.inputField.setText(self.inputText + str(self.res_list))
            else:
                self.choseField.setText("")
                self.res_list = []
                self.py2hz_list = []  # 备选按钮文本显示
                self.update_ui()
        except:
            logging.error("备选失败：Error")

    def handle_alpha_button(self, button_text):
        if self.pinyin_mod == 'chinese':
            try:
                judge_last = False
                judge_new = False
                for item in self.all_pinyin_list:
                    if item.startswith(self.res_list[-1]):
                        judge_last = True
                    if item.startswith(self.res_list[-1] + button_text):
                        judge_new = True
                if judge_last and judge_new:
                    self.res_list[-1] = self.res_list[-1] + button_text
                elif judge_last and self.res_list[-1] + button_text not in self.all_pinyin_list:
                    self.res_list.append(button_text)
            except:
                self.res_list.append(button_text)
        else:
            try:
                self.res_list[-1] = self.res_list[-1] + button_text
            except:
                self.res_list.append(button_text)
        # if len(self.res_list) >= 4:
        #     self.res_list = self.res_list[:-1]

        self.update_pinyin_and_ui()
        self.inputField.setText(self.inputText + str(self.res_list))

    def update_pinyin_and_ui(self):
        try:
            self.py2hz_list = self.pinyin_2_hanzi(self.res_list)
            show_list = self.py2hz_list[:7]
            logging.debug(show_list)
            tmp_str = "备选：" + " ".join(f"{i + 1}.{chs}" for i, chs in enumerate(show_list))
            self.choseField.setText(tmp_str)
        except:
            self.py2hz_list = []
            self.res_list = []
            logging.error("请重新输入")
        logging.debug("py2hz_list:" + str(self.py2hz_list))
        QApplication.processEvents()

        self.update_ui()

    def pinyin_2_hanzi(self, pinyin_list):
        all_char = ''.join(pinyin_list)
        # # 添加一些新的文本到英语字词库
        # text = "Hello world, hello Zhangyutao. Zhangyutao is a great programmer."
        # words = word_tokenize(text.lower())
        # self.auto_complete.train_corpus('english', [words])
        res_comb = []
        # 使用联想输入功能
        if self.pinyin_mod != 'chinese':
            res_comb = self.auto_complete.suggest(self.pinyin_mod, all_char)
            print(self.pinyin_mod + ' : ' + str(res_comb))  # English suggestions
        # print('japan:' + str(self.auto_complete.suggest('japanese', 'こ')))  # Japanese suggestions
        # print('korean:' + str(self.auto_complete.suggest('korean', '안'))）  # Korean suggestions
        else:
            # 加载中文
            try:
                res_comb = self.auto_complete.cn.search(all_char)
                print("中文:", res_comb)
            except Exception as e:
                print(f"错误异常反馈: {e}")

        # 欧洲语言
        # for index in self.auto_complete.languages:
        #     print(str(index) + ":" + str(self.auto_complete.suggest(index, 'a')))  # Japanese suggestions

        return res_comb

    def update_ui(self):
        for col in range(self.cols):
            for row in range(self.rows):
                self.buttons[col * self.rows + row].setText(self.buttonNames[col * self.rows + row])

    def delay_ms(self, t):
        start, end = 0, 0
        start = time.perf_counter()
        while ((end - start) * pow(10, 3) < t):
            end = time.perf_counter()
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
            f, psd = welch(data[i, :], fs, nperseg=1000)

            # 只保留3到40Hz的频段
            freq_mask = (f >= low_freq) & (f <= high_freq)
            psd_in_band = psd[freq_mask]

            # 计算3到40Hz频段内的PSD值（通过对频段内的PSD进行积分）
            psd_band_value = np.trapz(psd_in_band, f[freq_mask])

            # 将结果存储起来
            psd_values.append(psd_band_value)
        return psd_values
    # 咬牙检测
    def teeth_judge(self):
        QApplication.processEvents()
        eeg_data = self.serial_thread.get_latest_data(self.orgFs * self.tlen)
        eeg_data = np.array([eeg_data[i] for i in self.channel])
        if self.check_psd(eeg_data, self.orgFs) and time.time() - self.beg > 2:
            logging.info("咬牙")
            logging.info("开启闪烁")
            self.timer2.stop()
            self.timer.start()

    def onTimerOut(self):
        '''
        每次闪烁：更新全部键盘颜色
        '''
        self.count += 1
        if self.count == 1:
            self.sta = time.perf_counter_ns()

        x = float(pow(10, 3) / self.fre) * self.count / pow(10, 3)
        for col in range(self.cols):
            for row in range(self.rows):
                y = self.calculate_color(x, col, row)
                self.buttons[col * self.rows + row].changeColor(y)
                # self.buttons[col * self.rows + row].setStyleSheet(f"background-color: rgb({y}, {0}, {z});")

        '''
        闪烁结束：计算误差
        '''
        if self.count > self.tlen * self.fre:
            self.end_blink()
            # self.timer2.start()

    def calculate_color(self, x, col, row):
        if self.wave == 0:
            return int(255 * (1 + math.sin(
                2 * math.pi * self.key_fre[col][row] * x + self.key_phr[col][row] * math.pi)) * 0.5)
        elif self.wave == 1:
            T_count = int(pow(10, 3) * x / (0.5 * pow(10, 3) / self.key_fre[row][col]))
            return 255 if (T_count & 1) == 0 else 0

    def end_blink(self):
        # 计算误差
        self.end = time.perf_counter_ns()
        self.sum = (self.end - self.sta - self.tlen * pow(10, 9)) / pow(10, 9 - 3)
        logging.warning(f"{self.tlen}s以{self.fre}Hz频率共{self.tlen * self.fre}次闪烁累计误差：{self.sum}毫秒")

        for button in self.buttons:
            button.changeColor(255)
            # button.setStyleSheet(f"background-color: rgb({255}, {0}, {255});")
        QApplication.processEvents()
        eeg_data = None
        # 接收数据
        if self.rec_flag:
            self.delay_ms(140)
            # eeg_data = self.linkme.rec_data[-self.orgFs * self.tlen:].T
            eeg_data = self.serial_thread.get_last_data(self.orgFs * self.tlen)
            freqlist = [item for sublist in self.key_fre for item in sublist]
            np.save(f'data_save/20241013_{freqlist[self.tri_count]}Hz.npy', eeg_data)
            eeg_data = np.array([eeg_data[i] for i in self.channel])
            eeg_data = eeg_data.reshape(len(self.channel), self.orgFs * self.tlen)
            self.tri_count = self.tri_count + 1

        self.timer.stop()
        self.count = 0
        # 保存字词库的状态
        self.auto_complete.save('autocomplete_data.pkl')
        self.beg = time.time()
        # 计算所得数据
        if self.cal_flag:

            freqlist = [item for sublist in self.key_fre for item in sublist]
            self.result, score = fbcca_realtime(eeg_data, freqlist, self.orgFs, num_harms=4,
                                                num_fbs=4)
            logging.info(f"识别结果是： {self.result} {self.buttonNames[self.result]},分数：{score}")
            # 在代码中触发按钮的点击事件
            self.buttons[self.result].click()

    def keyPressEvent(self, QKeyEvent):
        """快捷键"""
        if QKeyEvent.key() == Qt.Key_Escape:  # esc
            self.close()


if __name__ == '__main__':
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    ssvep_win = SSVEPApp()
    ssvep_win.initPara()
    # chat_app = ChatWindow()
    initUI(ssvep_win)
    ssvep_win.initEvent()

    ssvep_win.show()
    sys.exit(app.exec_())
