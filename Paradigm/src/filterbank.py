import warnings
from scipy import signal
import numpy as np


def filterbank(eeg, samp_rate, num_fbs):
    y = []
    # 设计陷波滤波器
    f0 = 50
    q = 30
    high_pass = 90
    passband = [8, 16, 24, 32, 40, 48, 56, 64, 72, 80]
    # passband = [6, 14, 22, 30, 38, 46, 54, 62, 70, 78]
    notch_b, notch_a = signal.iircomb(f0, q, ftype='notch', fs=samp_rate)
    eeg = signal.filtfilt(notch_b, notch_a, eeg)
    # 设计陷波滤波器
    # center_freq = 50.0  # 中心频率为50Hz
    # Q = 2.0  # 带宽参数
    # b, a = signal.iirnotch(center_freq, Q, samp_rate)
    # # 50Hz工频
    # eeg = signal.lfilter(b, a, eeg)

    for fb_i in range(num_fbs):
        [N, Wn] = signal.cheb1ord([passband[fb_i], high_pass], [passband[fb_i]-2, high_pass + 10], 3, 40, fs=samp_rate)
        [B, A] = signal.cheby1(N, 0.5, Wn, 'bandpass', fs=samp_rate)
        y.append(signal.filtfilt(B, A, eeg))
        # fs = samp_rate/2
        # Wn = [(passband[fb_i]) / fs, high_pass / fs]
        # bandpass_B, bandpass_A = signal.butter(3, Wn, btype='bandpass')
        # y.append(signal.filtfilt(bandpass_B, bandpass_A, eeg))

    y = np.array(y)
    return y

