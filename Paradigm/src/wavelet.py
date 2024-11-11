import numpy as np
import matplotlib.pyplot as plt
import pywt

# 生成示例数据，这里使用正弦波信号作为示例
time = np.linspace(0, 1, 1000)  # 时间从0到1秒
frequency1 = 5  # 频率1 Hz
frequency2 = 20  # 频率2 Hz
signal = np.sin(2 * np.pi * frequency1 * time) + 0.5 * np.sin(2 * np.pi * frequency2 * time)

# 进行小波变换
wavelet = 'db4'  # 使用Daubechies小波函数
coeffs = pywt.wavedec(signal, wavelet)
plt.plot(signal, label="Org")
# 绘制小波系数
for i in range(len(coeffs)):

    plt.plot(coeffs[i], label=f'Detail {i}' if i > 0 else 'Approximation')
plt.xlabel('Sample')
plt.ylabel('Coefficient Value')
plt.legend()
plt.title('Wavelet Coefficients')
plt.show()
