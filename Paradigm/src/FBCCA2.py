from scipy.signal import filtfilt, resample, butter, lfilter, decimate
import os
import sys
sys.path.append("..")  # 添加上级目录到模块搜索路径
from src.filterbank import filterbank
from scipy.fftpack import fft,ifft
from matplotlib.pylab import plt
import numpy as np
import matplotlib.pyplot as plt

from scipy.linalg import svd
import math
from scipy import signal


def check_files_format(path):
    filename = []
    pathname = []

    if len(path) == 0:
        raise TypeError('please select valid file')

    elif len(path) == 1:
        (temppathname, tempfilename) = os.path.split(path[0])
        if 'edf' in tempfilename:
            filename.append(tempfilename)
            pathname.append(temppathname)
            return filename, pathname
        elif 'bdf' in tempfilename:
            raise TypeError('unsupport only one neuracle-bdf file')
        else:
            raise TypeError('not support such file format')

    else:
        temp = []
        temppathname = r''
        evtfile = []
        idx = np.zeros((len(path) - 1,))
        for i, ele in enumerate(path):
            (temppathname, tempfilename) = os.path.split(ele)
            if 'data' in tempfilename:
                temp.append(tempfilename)
                if len(tempfilename.split('.')) > 2:
                    try:
                        idx[i] = (int(tempfilename.split('.')[1]))
                    except:
                        raise TypeError('no such kind file')
                else:
                    idx[i] = 0
            elif 'evt' in tempfilename:
                evtfile.append(tempfilename)

        pathname.append(temppathname)
        datafile = [temp[i] for i in np.argsort(idx)]

        if len(evtfile) == 0:
            raise TypeError('not found evt.bdf file')

        if len(datafile) == 0:
            raise TypeError('not found data.bdf file')
        elif len(datafile) > 1:
            print('current readbdfdata() only support continue one data.bdf ')
            return filename, pathname
        else:
            filename.append(datafile[0])
            filename.append(evtfile[0])
            return filename, pathname


def cca_reference(list_freqs, fs, num_smpls, num_harms=3):
    num_freqs = len(list_freqs)
    tidx = np.arange(0, num_smpls) / fs  # time index

    y_ref = np.zeros((num_freqs, 2 * num_harms, num_smpls))
    for freq_i in range(num_freqs):
        tmp = []
        for harm_i in range(1, num_harms + 1):
            stim_freq = list_freqs[freq_i]  # in HZ
            # Sin and Cos
            tmp.extend([np.sin(2 * np.pi * tidx * harm_i * stim_freq),
                        np.cos(2 * np.pi * tidx * harm_i * stim_freq)])
        y_ref[freq_i] = tmp  # 2*num_harms because include both sin and cos

    return y_ref


'''
Base on fbcca, but adapt to our input format
'''
import numpy as np
from scipy.signal import butter, lfilter, decimate


def butter_lowpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return b, a


def lowpass_filter(data, cutoff, fs, order=5):
    b, a = butter_lowpass(cutoff, fs, order=order)
    if len(data) < max(len(b), len(a)):
        return data  # 如果数据点不足，返回原始数据
    y = lfilter(b, a, data, axis=0)  # 滤波所有通道
    return y


def downsample(data, original_fs, target_fs):
    factor = original_fs // target_fs
    # Lowpass filter
    cutoff = target_fs / 2.0  # Nyquist frequency
    filtered_data = lowpass_filter(data, cutoff, original_fs, order=5)

    # Decimate (downsample) each channel
    downsampled_data = decimate(filtered_data, factor, axis=1, ftype='iir')

    return downsampled_data


def fbcca_realtime(data, list_freqs, org_fs, num_harms=3, num_fbs=3):
    target_fs = 250  # 目标采样率

    # 检查原始采样率是否等于目标采样率
    if org_fs != target_fs:
        # 如果不相等，则执行降采样
        data = downsample(data, original_fs=org_fs, target_fs=target_fs)
    else:
        target_fs = org_fs

    fb_coefs = [math.pow(i, -1.25) + 0.25 for i in range(1, num_fbs + 1)]
    y_ref = cca_reference(list_freqs, target_fs, data.shape[1], num_harms)
    r = np.zeros((num_fbs, len(list_freqs)))

    fbdata = filterbank(data, target_fs, num_fbs)

    for fb_i in range(num_fbs):
        testdata = fbdata[fb_i]
        _, p = my_cca(testdata, y_ref)
        r[fb_i] = p

    rho = np.dot(fb_coefs, r)
    result = np.argmax(rho)
    top_3_indices = np.argsort(rho)[-3:][::-1]  # 找出最大的三个索引，并按降序排列

    # 获取最大的三个索引对应的结果
    result_top_3 = top_3_indices
    for i in range(3):
        print(f"第{i}，{list_freqs[result_top_3[i]]}Hz")
    return result, abs(rho[result])


def my_cca(input_x, input_y):
    p = []
    Q_x, _ = np.linalg.qr(input_x.T)
    for i_target in input_y:
        i_target = i_target.T
        Q_y, _ = np.linalg.qr(i_target)
        data_svd = np.dot(Q_x.T, Q_y)
        try:
            U, S, V = svd(data_svd)
        except np.linalg.LinAlgError:
            print("SVD did not converge for this pair of matrices.")
            continue
        rho = S[0]
        p.append(rho)

    if p:
        result = p.index(max(p)) + 1
    else:
        result = None  # 如果没有成功计算出任何结果

    return result, p

if __name__ == "__main__":

    # 加载npz文件
    channel = [1, 2, 3, 4, 5, 6, 7, 8]
    freqlist = [15.0, 14.0, 13.0, 12.0, 11.0, 10.0, 9.0, 8.0, 15.2, 14.2, 13.2, 12.2, 11.2, 10.2, 9.2, 8.2, 15.4, 14.4,
                13.4, 12.4, 11.4, 10.4, 9.4, 8.4, 15.6, 14.6, 13.6, 12.6, 11.6, 10.6, 9.6, 8.6, 15.8, 14.8, 13.8, 12.8,
                11.8, 10.8, 9.8, 8.8]
    for item in freqlist:
        eeg_data = np.load(f'data_save/{item}Hz.npy')
        eeg_data = np.array([eeg_data[i - 1] for i in channel])
        result, score = fbcca_realtime(eeg_data, freqlist, 250, num_harms=3, num_fbs=5)
        # print(result, score)
        print(f"频率为：{freqlist[result]}Hz, 实际为:{item}Hz, 得分：{score}")