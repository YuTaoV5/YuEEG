import logging
import sys
import time
import numpy as np
sys.path.append("..")  # 添加上级目录到模块搜索路径
from lib.neuracle_lib.dataServer import DataServerThread
import scipy.fftpack

class REC():
    def __init__(self):
        self.thread_data_server = None

    def init_neuracle(self, time_buffer=3):
        # 创建线程
        ## 配置设备 + ['TRG']
        neuracle = dict(device_name='Neuracle', hostname='127.0.0.1', port=8712,
                        srate=1000, n_chan=65)

        target_device = neuracle
        ## 初始化 DataServerThread 线程
        self.thread_data_server = DataServerThread(device=target_device['device_name'], n_chan=target_device['n_chan'],
                                                   srate=target_device['srate'], t_buffer=time_buffer)
        ### 建立TCP/IP连接
        notconnect = self.thread_data_server.connect(hostname=target_device['hostname'], port=target_device['port'])
        if notconnect:
            raise TypeError("Can't connect recorder, Please open the hostport ")
        else:
            # 启动线程
            print('thread Ready!')

    def start(self):
        if not self.thread_data_server.is_alive():
            # 启动线程
            self.thread_data_server.Daemon = True
            self.thread_data_server.start()
            print('Data server connected')

    def stop(self):
        self.thread_data_server.stop()
        print('Data server STOP')

    def get_data(self):
        data = self.thread_data_server.GetBufferData()
        self.thread_data_server.ResetDataLenCount()
        return data


def calculate_frequency_energy(ndarray, freq_range=(1, 100), sampling_rate=1000):
    """
    检测ndarray数组在指定频率范围内的频域能量。

    参数：
    ndarray: 输入的一维numpy数组，形状为(1, 3000)
    freq_range: 频率范围元组，默认值为(1, 100)
    sampling_rate: 采样率，默认值为1000

    返回：
    频域能量值
    """
    # 确保输入数组是一维的
    if ndarray.ndim != 1:
        raise ValueError("输入数组必须是一维的")

    # 计算FFT
    fft_values = scipy.fftpack.fft(ndarray)

    # 计算对应的频率
    freqs = scipy.fftpack.fftfreq(len(ndarray), d=1 / sampling_rate)

    # 仅取正频率部分
    positive_freqs = freqs[:len(freqs) // 2]
    positive_fft_values = np.abs(fft_values[:len(fft_values) // 2])

    # 找到指定频率范围内的频率索引
    idx = np.where((positive_freqs >= freq_range[0]) & (positive_freqs <= freq_range[1]))[0]

    # 计算指定频率范围内的能量
    energy = np.sum(positive_fft_values[idx] ** 2)

    return energy

if __name__ == '__main__':
    app = REC()
    # 设置需要缓存的时间长度
    app.init_neuracle(3)  # 单位为秒
    app.start()  # 开始线程
    data = None
    tp7_th = -9999
    while True:
        logging.info("-延时3秒-")
        time.sleep(3)
        data = app.get_data()  # 数据大小 size = time * 65 * 1000
        logging.info("接收到的数据大小size = time * 65 * 1000：" + str(data.size))
        result = np.argmin(data[40])
        freq_range = (1, 30)  # 频率范围1~100
        sampling_rate = 1000  # 假设采样率为1000Hz
        energy = calculate_frequency_energy(data[40], freq_range, sampling_rate) // 100000000
        print(f"频率范围 {freq_range[0]}~{freq_range[1]} Hz 内的频域能量: {energy}")
        # print("差值", str(-data[40][result] + tp7_th))
        if tp7_th - data[40][result] > 100:
            # print("咬牙")
            print("咬牙")
            print("开启闪烁")
            tp7_th = data[40][result]
        else:
            tp7_th = data[40][result]
        # print("接收到的数据大小size = time * 65 * 1000：",str(data.size))
    app.thread_data_server.stop()  # 停止线程
