
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from qfluentwidgets import *
class ColorButton(QPushButton):
    def __init__(self, initial_color, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {initial_color};")

    def changeColor(self, new_color):
        if type(new_color) in [int, float]:
            self.setStyleSheet(f"background-color: rgb({new_color}, {new_color}, {new_color});")
        else:
            self.setStyleSheet(f"background-color: {new_color};")

def initUI(self, side_space = 20, grid_space = 80, layout_space = 50, input_space = 10, fontnum = 40):
    '''
    #########################
        UI界面配置
    #########################
    '''
    # side_space = 20  # 两侧空白宽度
    # grid_space = 80  # 键盘间隔
    # layout_space = 50  # 布局间隔
    # input_space = 10  # 输入间隔
    # fontnum = 40  # 字体大小

    # 主窗口设置
    self.setWindowTitle("5x8 Button Matrix with SSVEP")
    if self.fsc_flag:
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.resize(QDesktopWidget().screenGeometry().width(), QDesktopWidget().screenGeometry().height())
        # self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        self.setFixedSize(self.width(), self.height())

    # 添加布局
    self.layout = QVBoxLayout(self)
    self.gridLayout = QGridLayout()
    self.inputLayout = QVBoxLayout()
    self.topLayout = QHBoxLayout()
    # 添加控件
    self.inputField = LineEdit()
    self.choseField = LineEdit()
    self.buttonAbove = PushButton("开始")
    self.buttonAbove.setCursor(QCursor(Qt.PointingHandCursor))

    # 调整间隙
    self.layout.setSpacing(layout_space)
    self.gridLayout.setSpacing(grid_space)
    self.inputLayout.setSpacing(input_space)

    # 添加侧边的间距
    leftSpacer = QSpacerItem(side_space, 20, QSizePolicy.Fixed, QSizePolicy.Expanding)
    rightSpacer = QSpacerItem(side_space, 20, QSizePolicy.Fixed, QSizePolicy.Expanding)
    downSpacer = QSpacerItem(20, 20, QSizePolicy.Fixed, QSizePolicy.Fixed)
    self.gridLayout.addItem(leftSpacer, 0, 0)
    self.gridLayout.addItem(rightSpacer, 0, 6)
    self.inputField.setMaximumHeight(60)
    self.choseField.setMaximumHeight(40)

    # 设置控件大小
    # self.setStyleSheet(f"background-color: rgb(10, 10, 10);")
    self.inputField.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    self.choseField.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    self.buttonAbove.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
    # self.buttonBelow.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    # 设置样式
    self.buttonAbove.setStyleSheet("background-color: grey;color: white;")
    # self.buttonBelow.setStyleSheet("background-color: grey;color: white;")
    self.inputField.setStyleSheet("background-color: grey")
    self.choseField.setStyleSheet("background-color: grey")
    self.setStyleSheet(
        f"border-radius: 10px;font-family: 微软雅黑;font-size: {fontnum}px;background-color: rgb(10, 10, 10);")

    # 生成按钮
    for col in range(self.cols):
        for row in range(self.rows):
            try:
                button = ColorButton("white", self.buttonNames[col * self.rows + row])
            except:
                button = ColorButton("white", " ")
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            button.clicked.connect(self.buttonClickHandler)
            self.buttons.append(button)
            self.gridLayout.addWidget(button, col, row + 1)

    # 添加layout
    self.inputLayout.addWidget(self.inputField)
    self.inputLayout.addWidget(self.choseField)
    self.topLayout.addLayout(self.inputLayout)
    self.topLayout.addWidget(self.buttonAbove)
    self.layout.addLayout(self.topLayout)
    self.layout.addLayout(self.gridLayout)
    self.layout.addItem(downSpacer)
    # self.layout.addWidget(self.buttonBelow, alignment=Qt.AlignCenter)
