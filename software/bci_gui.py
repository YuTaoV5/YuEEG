# coding:utf-8
import sys
from PyQt5.QtCore import Qt, QRect, QUrl
from PyQt5.QtGui import QIcon, QPainter, QImage, QBrush, QColor, QFont, QDesktopServices
from PyQt5.QtWidgets import QApplication, QFrame, QStackedWidget, QHBoxLayout, QLabel

from qfluentwidgets import (NavigationInterface, NavigationItemPosition, NavigationWidget, MessageBox,
                            isDarkTheme, setTheme, Theme, setThemeColor, qrouter, FluentWindow, NavigationAvatarWidget)
from qfluentwidgets import FluentIcon as FIF
from qframelesswindow import FramelessWindow, StandardTitleBar
from plot_card import *

class Widget(QFrame):

    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.label = QLabel(text, self)
        self.label.setAlignment(Qt.AlignCenter)
        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.addWidget(self.label, 1, Qt.AlignCenter)
        self.setObjectName(text.replace(' ', '-'))


class Window(FramelessWindow):

    def __init__(self):
        super().__init__()
        self.setTitleBar(StandardTitleBar(self))

        # use dark theme mode
        setTheme(Theme.DARK)

        # change the theme color
        # setThemeColor('#0078d4')
        self.hBoxLayout = QHBoxLayout(self)
        self.navigationInterface = NavigationInterface(self, showMenuButton=True)
        self.stackWidget = QStackedWidget(self)
        channels_to_display = [0, 1, 2, 3, 4, 5, 6, 7]  # Example control parameter list
        # channels_to_display = [2]
        pen_colors = ['r', 'g', 'b', 'c', 'm', 'y', 'k', 'w', 'orange']
        pen_widths = [2, 2, 2, 2, 2, 2, 2, 2, 2]
        plot_num = 1000
        # create sub interface
        self.tfplot = TFwindow(channels_to_display, pen_colors, pen_widths, plot_num)
        self.time_plot = TimeDomainPlot2(channels_to_display, pen_colors, pen_widths, plot_num)
        self.leadoff = StatusGrid()
        self.ser_frame = SerialCommunication()
        self.vtk_demo = VTKWidget()

        self.folderInterface = Widget('Folder Interface', self)
        self.settingInterface = Widget('Setting Interface', self)
        self.albumInterface = Widget('Album Interface', self)
        self.albumInterface1 = Widget('Album Interface 1', self)
        self.albumInterface2 = Widget('Album Interface 2', self)
        self.albumInterface1_1 = Widget('Album Interface 1-1', self)

        # initialize layout
        self.initLayout()

        # add items to navigation interface
        self.initNavigation()

        self.initWindow()

        self.ser_frame.open_button.clicked.connect(self.open_port)

    def open_port(self):
        if self.ser_frame.serial_port and self.ser_frame.serial_port.is_open:
            self.ser_frame.serial_port.close()
            self.ser_frame.serial_port = None
            self.ser_frame.open_button.setText("Open Port")
            self.ser_frame.send_button.setEnabled(False)
        else:
            port = self.ser_frame.port_combobox.currentText()
            baud_rate = int(self.ser_frame.baud_combobox.currentText())
            try:
                self.ser_frame.serial_port = serial.Serial(port, baud_rate, timeout=1)
                self.ser_frame.open_button.setText("Close Port")
                self.ser_frame.send_button.setEnabled(True)
                self.read_thread = SerialReader(self.ser_frame.serial_port)
                self.read_thread.data_received.connect(self.ser_frame.receive_data)
                self.read_thread.status_received.connect(self.ser_frame.receive_data)
                self.read_thread.data_received.connect(self.tfplot.update_plots)
                self.read_thread.data_received.connect(self.time_plot.update_plot)
                self.read_thread.status_received.connect(self.leadoff.update_status)
                self.read_thread.start()
            except serial.SerialException as e:
                self.ser_frame.receive_text.append(f"Error opening port: {e}")

    def initLayout(self):
        self.hBoxLayout.setSpacing(0)
        self.hBoxLayout.setContentsMargins(0, self.titleBar.height(), 0, 0)
        self.hBoxLayout.addWidget(self.navigationInterface)
        self.hBoxLayout.addWidget(self.stackWidget)
        self.hBoxLayout.setStretchFactor(self.stackWidget, 1)

    def initNavigation(self):
        # enable acrylic effect
        # self.navigationInterface.setAcrylicEnabled(True)

        self.addSubInterface(self.vtk_demo, FIF.PHOTO, 'PCB')
        self.addSubInterface(self.tfplot, FIF.MARKET, 'Data')
        self.addSubInterface(self.leadoff, FIF.TILES, 'Impedance')
        self.addSubInterface(self.ser_frame, FIF.CHAT, 'Chat')
        self.addSubInterface(self.time_plot, FIF.ALIGNMENT, 'Data2')
        self.navigationInterface.addSeparator()

        self.addSubInterface(self.albumInterface, FIF.ALBUM, 'Albums', NavigationItemPosition.SCROLL)
        self.addSubInterface(self.albumInterface1, FIF.ALBUM, 'Album 1', parent=self.albumInterface)
        self.addSubInterface(self.albumInterface1_1, FIF.ALBUM, 'Album 1.1', parent=self.albumInterface1)
        self.addSubInterface(self.albumInterface2, FIF.ALBUM, 'Album 2', parent=self.albumInterface)

        # add navigation items to scroll area
        self.addSubInterface(self.folderInterface, FIF.FOLDER, 'Folder library', NavigationItemPosition.SCROLL)

        # add custom widget to bottom
        self.navigationInterface.addWidget(
            routeKey='avatar',
            widget=NavigationAvatarWidget('YuTaoV5', './resource/my_logo.jpg'),
            onClick=self.showMessageBox,
            position=NavigationItemPosition.BOTTOM,
        )

        self.addSubInterface(self.settingInterface, FIF.SETTING, 'Settings', NavigationItemPosition.BOTTOM)

        # !IMPORTANT: don't forget to set the default route key if you enable the return button
        # qrouter.setDefaultRouteKey(self.stackWidget, self.musicInterface.objectName())

        # set the maximum width
        # self.navigationInterface.setExpandWidth(300)

        self.stackWidget.currentChanged.connect(self.onCurrentInterfaceChanged)
        self.stackWidget.setCurrentIndex(0)

        # always expand
        # self.navigationInterface.setCollapsible(False)


    def initWindow(self):
        self.resize(900, 700)
        self.setWindowIcon(QIcon('./resource/school_logo.ico'))
        self.setWindowTitle('ADS1299上位机')
        self.titleBar.setAttribute(Qt.WA_StyledBackground)

        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)

        # NOTE: set the minimum window width that allows the navigation panel to be expanded
        # self.navigationInterface.setMinimumExpandWidth(900)
        # self.navigationInterface.expand(useAni=False)

        self.setQss()

    def addSubInterface(self, interface, icon, text: str, position=NavigationItemPosition.TOP, parent=None):
        """ add sub interface """
        self.stackWidget.addWidget(interface)
        self.navigationInterface.addItem(
            routeKey=interface.objectName(),
            icon=icon,
            text=text,
            onClick=lambda: self.switchTo(interface),
            position=position,
            tooltip=text,
            parentRouteKey=parent.objectName() if parent else None
        )

    def setQss(self):
        color = 'dark' if isDarkTheme() else 'light'
        with open(f'resource/{color}/demo.qss', encoding='utf-8') as f:
            self.setStyleSheet(f.read())

    def switchTo(self, widget):
        self.stackWidget.setCurrentWidget(widget)

    def onCurrentInterfaceChanged(self, index):
        widget = self.stackWidget.widget(index)
        self.navigationInterface.setCurrentItem(widget.objectName())
        print(widget.objectName())
        if self.ser_frame.serial_port and self.ser_frame.serial_port.is_open:
            if index == 1:
                data = "1"
                self.ser_frame.serial_port.write(data.encode('utf-8'))
            if index == 2:
                data = "2"
                self.ser_frame.serial_port.write(data.encode('utf-8'))

        # !IMPORTANT: This line of code needs to be uncommented if the return button is enabled
        # qrouter.push(self.stackWidget, widget.objectName())

    def showMessageBox(self):
        w = MessageBox(
            'ADS1299上位机',
            '所有硬件资料以及软件即将全部开源🚀',
            self
        )
        w.yesButton.setText('给个Star😘')
        w.cancelButton.setText('残忍拒绝OrZ')

        if w.exec():
            QDesktopServices.openUrl(QUrl("https://github.com/YuTaoV5/ADS1299_EEG"))


if __name__ == '__main__':
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    w = Window()
    w.show()
    app.exec_()
