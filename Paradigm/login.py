'''
Author: ProtoDrive000
Date: 2023-04-01 14:06:58
LastEditTime: 2023-04-01 18:23:57
Description: 
FilePath: \BCI_Timer\login.py
Copyright © : 2021年 赛博智能车实验室. All rights reserved. 
'''



from ui.login_ui import Ui_MainWindow

import sys
import pandas as pd
import numpy as np
import serial
import serial.tools.list_ports
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt, QPropertyAnimation, QRect, QEasingCurve
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QDesktopWidget
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import time
import os

class LOGIN(QMainWindow, Ui_MainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.access = False
        self.setupUi(self)
        self.start_x = None
        self.start_y = None
        self.anim=None
        self.Com_Dict = None
        self.setWindowTitle("BCI登录")
        self.setWindowIcon(QIcon("ui/mylogo.jpg"))
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint)  # 设置窗口标志：隐藏窗口边框
        self.name.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)
        self.password.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)
        #self.resize(QDesktopWidget().screenGeometry().width(),
        #            QDesktopWidget().screenGeometry().height())  # 主窗大小
        self.Login.setCursor(QCursor(Qt.PointingHandCursor))
        self.create_Account.setCursor(QCursor(Qt.PointingHandCursor))
        self.confirm.setCursor(QCursor(Qt.PointingHandCursor))

        try:
            df = pd.read_csv('./usr/data.csv')
            tmp_data = np.array(df)  # 先将数据框转换为数组
            self.data = np.delete(tmp_data, 0, axis=1).tolist()
            self.data = [[str(i) for i in self.data[j]] for j in range(len(self.data))]#字符化
        except:
            self.data = []
        self.label_pix.setPixmap(QPixmap("ui/logo.png"))
        self.label_pix.setScaledContents(True)
        self.e = 1
        self.init()
        
    def init(self):
        #self.Login.clicked.connect(self.my_login)
        self.create_Account.clicked.connect(self.my_sign)
        #self.confirm.clicked.connect(self.sign_confirm)
        self.check.clicked.connect(self.port_check)

    
    def my_sign(self):
        self.tabWidget.setCurrentIndex(1)

    

    def port_check(self):
        # 检测所有存在的串口,将信息存储在字典中
        self.Com_Dict = {}
        port_list = list(serial.tools.list_ports.comports())

        for port in port_list:
            self.Com_Dict["%s" % port[0]] = "%s" % port[1]

        if len(self.Com_Dict) == 0:
            self.check.setText(" 无串口")

    def keyPressEvent(self, QKeyEvent):
        """快捷键"""
        if QKeyEvent.key() == Qt.Key_Escape:  # esc
            if self.e == 1:
                self.animation_exit()
                self.close()
            elif self.e == 0:
                self.animation_start()

    def animation_start(self):
        self.e = 1
        self.show()
        self.anim = QPropertyAnimation(self, b'geometry')  # 动画类型
        self.anim.setStartValue(QRect(QDesktopWidget().screenGeometry().width() / 2 - 230, QDesktopWidget().screenGeometry().height() / 2 - 338, 461, 676))
        self.anim.setEndValue(QRect(0, 0, QDesktopWidget().screenGeometry().width(), QDesktopWidget().screenGeometry().height()))
        self.anim.setDuration(400)
        self.anim.setEasingCurve(QEasingCurve.OutBounce)
        main_opacity = QPropertyAnimation(self, b"windowOpacity", self)
        main_opacity.setStartValue(0)
        main_opacity.setEndValue(1)
        main_opacity.setDuration(400)
        main_opacity.start()

        # self.anim.setLoopCount(-1)  # 设置循环旋转
        self.anim.start()

    def animation_exit(self):
        self.e = 0
        self.anim = QPropertyAnimation(self, b'geometry')  # 动画类型
        self.anim.setStartValue(QRect(0, 0, self.width(), self.height()))
        self.anim.setEndValue(QRect(QDesktopWidget().screenGeometry().width() / 2 - 230, QDesktopWidget().screenGeometry().height() / 2 - 338, 461,676))
        self.anim.setDuration(400)
        self.anim.setEasingCurve(QEasingCurve.OutBounce)
        main_opacity = QPropertyAnimation(self, b"windowOpacity", self)
        main_opacity.setStartValue(1)
        main_opacity.setEndValue(0)
        main_opacity.setDuration(400)
        main_opacity.start()

        # self.anim.setLoopCount(-1)  # 设置循环旋转
        self.anim.start()

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            super(LOGIN, self).mousePressEvent(event)
            self.start_x = event.x()
            self.start_y = event.y()

    def mouseReleaseEvent(self, event):
        self.start_x = None
        self.start_y = None

    def mouseMoveEvent(self, event):
        try:
            super(LOGIN, self).mouseMoveEvent(event)
            dis_x = event.x() - self.start_x
            dis_y = event.y() - self.start_y
            self.move(self.x() + dis_x, self.y() + dis_y)
        except:
            pass

    def effect_shadow_style(self, widget):
        effect_shadow = QtWidgets.QGraphicsDropShadowEffect(self)
        effect_shadow.setOffset(12, 12)  # 偏移
        effect_shadow.setBlurRadius(128)  # 阴影半径
        effect_shadow.setColor(QColor(155, 230, 237, 150))  # 阴影颜色
        widget.setGraphicsEffect(effect_shadow)



if __name__ == "__main__":

    app = QApplication(sys.argv)
    myWin = LOGIN()
    myWin.show()
    sys.exit(app.exec_())
