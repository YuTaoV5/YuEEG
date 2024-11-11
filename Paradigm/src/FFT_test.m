clc,clear,close all;
% 读取CSV文件
data = readtable('15Hz_Raw.csv');

% 提取想要的列范围
start_col = 2; % 第二列
end_col = size(data, 2); % 最后一列

start_row = 2; % 第二列
end_row = size(data, 1); % 最后一列

% 提取所需范围内的数据
selected_data = data(start_row:end_row, start_col:end_col);
% 生成示例数据
data = table2array(selected_data);
%%

% 计算FFT
fs = 250; % 采样频率
L = 1000; % 信号长度
f = fs * (0:(L/2)) / L; % 频率范围

% 指定要标记的频率
freq_to_label = [15, 30, 45];

figure;
for i = 1:7
    Y = fft(data(i, :));
    P2 = abs(Y / L);
    P1 = P2(1:L/2 + 1);
    P1(2:end-1) = 2 * P1(2:end-1);

    subplot(3, 3, i);
    plot(f, P1, 'LineWidth', 1.5); % 增加线条粗细
    ylim([-0.00001, 0.00001]); % 设置纵坐标范围
    xlim([-1, 60]); % 设置横坐标范围
    title(['通道 ', num2str(i)]);
    xlabel('Frequency (Hz)');
    ylabel('Magnitude');

    % 添加数据标签
    for freq = freq_to_label
        [~, index] = min(abs(f - freq)); % 找到最接近指定频率的索引
        dip_str = num2str(freq) + "Hz"

        text(f(index), P1(index), dip_str, 'VerticalAlignment', 'bottom', 'HorizontalAlignment', 'center', 'FontSize', 10);
    end
end

sgtitle('FFT of 7 sets of data');