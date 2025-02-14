'''
Author: ProtoDrive000
Date: 2023-04-01 14:06:58
LastEditTime: 2023-04-01 19:10:03
Description: 
FilePath: \BCI_Timer\run.py
Copyright © : 2021年 赛博智能车实验室. All rights reserved. 
'''
import os
from login import LOGIN
from ssvep_paradigm import SSVEPApp
import sys
import pandas as pd
import numpy as np
from PyQt5.QtWidgets import *
import time
from ui.ui import initUI
# def exit(ssvep_win):
#     if ssvep_win.rec_flag:
#         ssvep_win.receiver.stop()
#     ssvep_win.close()
#     login_Win.show()

def get_device_serial_number():
    if os.name == 'nt':  # 如果是 Windows
        import platform
        if platform.system() == 'Windows':
            import wmi
            w = wmi.WMI()
            for physical_disk in w.Win32_DiskDrive():
                return physical_disk.SerialNumber
    elif os.name == 'posix':  # 如果是类 Unix（Linux、macOS 等）
        try:
            with open('/sys/class/dmi/id/product_uuid', 'r') as file:
                return file.read().strip()
        except FileNotFoundError:
            pass
    return None

def sign_confirm():
        tmp = [login_Win.reg_name.text(), login_Win.gender.text(), login_Win.age.text(), login_Win.reg_password.text()]
        flag = True
        for item in tmp:
            if item == '':
                QMessageBox.information(login_Win, "提示", "请填入完整信息", QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                flag = False
        if login_Win.reg_password.text() != login_Win.password_confirm.text():
            QMessageBox.information(login_Win, "提示", "两次密码输入不符", QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            flag = False

        uuid = get_device_serial_number()
        print("uuid:", uuid)
        # if uuid == "0025_38BC_11B7_A3B4." or uuid == "0025_38B3_31B7_51C3.":
        #     flag = True
        #     QMessageBox.information(login_Win, "提示", "欢迎管理员", QMessageBox.Yes | QMessageBox.No,
        #                             QMessageBox.Yes)
        # else:
        #     flag = False
        #     QMessageBox.information(login_Win, "提示", "此设备尚未注册，请联系秦珂", QMessageBox.Yes | QMessageBox.No,
        #                             QMessageBox.Yes)

        if flag:
            # ssvep_win = SSVEPApp()
            now_Time = str(time.strftime('%Y-%m-%d %H:%M:%S'))
            tmp.append(now_Time)
            login_Win.data.append(tmp)
            QMessageBox.information(login_Win, "提示", "注册成功！", QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            login_Win.access = True
            pd.DataFrame(data=login_Win.data).to_csv('./usr/data.csv')
            tmp2 = []
            tmp1 = [login_Win.reg_name.text(), login_Win.reg_password.text(), now_Time, '成功注册']
            tmp2.append(tmp1)
            try:
                df = pd.read_csv('./usr/login.csv')
                tmp_data = np.array(df)  # 先将数据框转换为数组
                tmp_data = np.delete(tmp_data, 0, axis=1).tolist()
                tmp_data.append(tmp1)
                pd.DataFrame(data=tmp_data).to_csv('./usr/login.csv')
            except:
                pd.DataFrame(data=tmp2).to_csv('./usr/login.csv')


            if login_Win.bound_wave.currentText() == "正弦波":
                mywave = 0
                print("正弦波")
            else:
                mywave = 1
                print("方波")

            button_text = login_Win.plainTextEdit_buttons.toPlainText()
            # 去除首尾的单引号并按逗号分隔
            split_strings = button_text.strip("'").split("', '")
            # 将结果放入列表
            button_text = [s.strip("'") for s in split_strings]
            languages = [
                'french', 'german', 'danish', 'dutch', 'english',
                'finnish', 'greek', 'italian', 'portuguese', 'spanish', 'swedish'
            ]
            if login_Win.comboBox_ssvep_mode.currentText() in languages:
                pymod = login_Win.comboBox_ssvep_mode.currentText()
            else:
                pymod = 'chinese'
            if login_Win.checkBox_tri.isChecked():
                login_Win.checkBox_onlinedata.setChecked(True)
                login_Win.checkBox_analysis.setChecked(True)
            else:
                login_Win.checkBox_onlinedata.setChecked(False)
                login_Win.checkBox_analysis.setChecked(False)
            channel_text = login_Win.plainTextEdit_channel.toPlainText()
            channel_text = [int(x.strip()) for x in channel_text.split(',')]
            ssvep_win.initPara(Fs=int(login_Win.lineEdit_Fs.text()), tri_flag=login_Win.checkBox_tri.isChecked(),
                               fsc_flag=login_Win.checkBox_fullscreen.isChecked(),
                               rec_flag=login_Win.checkBox_onlinedata.isChecked(),
                               cal_flag=login_Win.checkBox_analysis.isChecked(), my_wave=mywave,
                               fre=int(login_Win.lineEdit_screenflash.text()),
                               rows=int(login_Win.lineEdit_rows.text()), cols=int(login_Win.lineEdit_cols.text()),
                               sta_fre=int(login_Win.lineEdit_sta_fre.text()),
                               end_fre=int(login_Win.lineEdit_end_fre.text()),
                               v_space=float(login_Win.lineEdit_v_space.text()),
                               tlen=int(login_Win.lineEdit_tlen.text()), teeth=int(login_Win.lineEdit_tooth.text()),
                               channel=channel_text, buttonNames=button_text,
                               pinyin_mod=pymod)
            QApplication.processEvents()
            initUI(ssvep_win)
            ssvep_win.initEvent()
            # ssvep_win.buttonBelow.clicked.connect(lambda: exit(ssvep_win))
            ssvep_win.show()
            login_Win.close()
def my_login():
    
        sum_data = sum(login_Win.data, [])
        try:
            location = sum_data.index(login_Win.name.text())
            print("找到账号")
            login_Win.access = True
        except:
            print("不存在此帐号")
            QMessageBox.information(login_Win, "提示", "不存在此帐号", QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            login_Win.access = False
        uuid = get_device_serial_number()
        print("uuid:", uuid)
        # if uuid == "0025_38BC_11B7_A3B4." or uuid == "0025_38B3_31B7_51C3.":
        #     flag = True
        #     QMessageBox.information(login_Win, "提示", "欢迎管理员", QMessageBox.Yes | QMessageBox.No,
        #                             QMessageBox.Yes)
        # else:
        #     flag = False
        #     QMessageBox.information(login_Win, "提示", "此设备尚未注册，请联系秦珂", QMessageBox.Yes | QMessageBox.No,
        #                             QMessageBox.Yes)
        if login_Win.access:

            if sum_data[location+3] == login_Win.password.text():
                print("成功登录")
                QMessageBox.information(login_Win, "提示", "成功登录", QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                now_Time = time.strftime('%Y-%m-%d %H:%M:%S')

                tmp = []
                tmp1 = [login_Win.name.text(), login_Win.password.text(), now_Time, '成功登录']
                tmp.append(tmp1)
                try:
                    df = pd.read_csv('./usr/login.csv')
                    tmp_data = np.array(df)  # 先将数据框转换为数组
                    tmp_data = np.delete(tmp_data, 0, axis=1).tolist()
                    tmp_data.append(tmp1)
                    pd.DataFrame(data=tmp_data).to_csv('./usr/login.csv')
                except:
                    pd.DataFrame(data=tmp).to_csv('./usr/login.csv')

                if login_Win.bound_wave.currentText() == "正弦波":
                    mywave = 0
                    print("正弦波")
                else:
                    mywave = 1
                    print("方波")
                button_text = login_Win.plainTextEdit_buttons.toPlainText()
                # 去除首尾的单引号并按逗号分隔
                split_strings = button_text.strip("'").split("', '")
                # 将结果放入列表
                button_text = [s.strip("'") for s in split_strings]
                languages = [
                    'french', 'german', 'danish', 'dutch', 'english',
                    'finnish', 'greek', 'italian', 'portuguese', 'spanish', 'swedish'
                ]
                if login_Win.comboBox_ssvep_mode.currentText() in languages:
                    pymod = login_Win.comboBox_ssvep_mode.currentText()
                else:
                    pymod = 'chinese'
                if login_Win.checkBox_tri.isChecked():
                    login_Win.checkBox_onlinedata.setChecked(True)
                    login_Win.checkBox_analysis.setChecked(True)
                else:
                    login_Win.checkBox_onlinedata.setChecked(False)
                    login_Win.checkBox_analysis.setChecked(False)
                channel_text = login_Win.plainTextEdit_channel.toPlainText()
                channel_text = [int(x.strip()) for x in channel_text.split(',')]
                ssvep_win.initPara(Fs=int(login_Win.lineEdit_Fs.text()), tri_flag=login_Win.checkBox_tri.isChecked(),
                                   fsc_flag=login_Win.checkBox_fullscreen.isChecked(),
                                   rec_flag=login_Win.checkBox_onlinedata.isChecked(),
                                   cal_flag=login_Win.checkBox_analysis.isChecked(), pinyin_mod=pymod,
                                   my_wave=mywave, fre=int(login_Win.lineEdit_screenflash.text()),
                                   rows=int(login_Win.lineEdit_rows.text()), cols=int(login_Win.lineEdit_cols.text()),
                                   sta_fre=int(login_Win.lineEdit_sta_fre.text()),
                                   end_fre=int(login_Win.lineEdit_end_fre.text()),
                                   v_space=float(login_Win.lineEdit_v_space.text()),
                                   tlen=int(login_Win.lineEdit_tlen.text()), teeth=int(login_Win.lineEdit_tooth.text()),
                                   channel=channel_text, buttonNames=button_text)

                QApplication.processEvents()
                initUI(ssvep_win)
                ssvep_win.initEvent()
                # ssvep_win.buttonBelow.clicked.connect(lambda: exit(ssvep_win))
                ssvep_win.show()
                login_Win.close()
            else:
                print("密码错误")
                QMessageBox.information(login_Win, "提示", "密码错误", QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                login_Win.access = False




app = QApplication(sys.argv)
login_Win = LOGIN()
ssvep_win = SSVEPApp()
login_Win.Login.clicked.connect(my_login)
login_Win.confirm.clicked.connect(sign_confirm)

login_Win.show()
sys.exit(app.exec_())
