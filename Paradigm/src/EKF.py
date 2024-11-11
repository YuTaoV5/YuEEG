import numpy as np
import matplotlib.pyplot as plt


def EKF(measurement_data):
    # Define state transition matrix A, observation matrix H, and initial values
    A = np.array([[1.0]])
    H = np.array([[1.0]])
    x_hat = np.array([0.0])  # Initial state estimate
    P = np.array([[1.0]])  # Initial state covariance
    Q = np.array([[0.01]])  # Process noise covariance
    R = np.array([[0.1]])  # Measurement noise covariance

    # EKF algorithm
    estimated_states = []

    for z in measurement_data:
        # Prediction step
        x_hat_predicted = np.dot(A, x_hat)
        P_predicted = np.dot(np.dot(A, P), A.T) + Q

        # Measurement update step
        K = np.dot(np.dot(P_predicted, H.T), np.linalg.inv(np.dot(np.dot(H, P_predicted), H.T) + R))
        x_hat = x_hat_predicted + np.dot(K, z - np.dot(H, x_hat_predicted))
        P = P_predicted - np.dot(np.dot(K, H), P_predicted)

        estimated_states.append(x_hat[0])
    return estimated_states

if __name__ == '__main__':
    # estimated_states now contains the EKF estimates for your data
    # Simulated measurements (replace with your actual data)
    measurement_data = np.random.randint(0, 100, size=750).tolist()
    estimated_states = EKF(measurement_data)


    # 创建一个新的图形
    plt.figure(figsize=(10, 6))

    # 绘制第一个列表
    plt.plot(measurement_data, label='measurement', color='blue')

    # 绘制第二个列表
    plt.plot(estimated_states, label='estimated', color='red')

    # 添加图例
    plt.legend()

    # 添加标题和标签
    plt.title('Comparison of Two Lists')
    plt.xlabel('Index')
    plt.ylabel('Value')

    # 显示图形
    plt.show()