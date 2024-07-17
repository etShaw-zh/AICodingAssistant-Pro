from PySide6.QtCore import QMetaObject
from PySide6.QtGui import QFontDatabase, QFont, QIcon
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame, QAbstractItemView, QTextEdit
from qfluentwidgets import (setThemeColor, PushButton, ToolButton, TableWidget, PrimaryPushButton, FluentIcon,
                            ProgressRing, ListWidget)
from qfluentwidgets.common.style_sheet import styleSheetManager

from src.module.version import currentVersion
from src.module.resource import getResource
from src.module.image import RoundedLabel


class MainWindow(object):
    def setupUI(self, this_window):
        # 配置主题色与字体
        setThemeColor("#2E75B6")
        font_id = QFontDatabase.addApplicationFont(getResource("src/font/Study-Bold.otf"))
        font_family = QFontDatabase.applicationFontFamilies(font_id)

        # 加载 QSS
        with open(getResource("src/style/style_light.qss"), "r", encoding="UTF-8") as file:
            style_sheet = file.read()
        this_window.setStyleSheet(style_sheet)

        this_window.setWindowTitle(f"AI Coding Officer Pro {currentVersion()}")
        this_window.setWindowIcon(QIcon(getResource("src/image/icon_win.png")))
        this_window.resize(1280, 720)
        this_window.setAcceptDrops(True)

        # 标题区域

        self.titleLabel = QLabel("AI Coding Officer Pro by Shaw")
        self.titleLabel.setObjectName("titleLabel")
        self.titleLabel.setFont(QFont(font_family))

        self.subtitleLabel = QLabel("一款前沿的人工智能编码助手，专为提升文本编码的效率而设计。仅需拖动数据文件至软件界面，即可自动对数据进行编码，无需人工干预。")
        self.subtitleLabel.setObjectName('subtitleLabel')

        self.titleLayout = QVBoxLayout()
        self.titleLayout.setContentsMargins(0, 0, 0, 0)
        self.titleLayout.addWidget(self.titleLabel)
        self.titleLayout.addSpacing(4)
        self.titleLayout.addWidget(self.subtitleLabel)

        self.newVersionButton = PrimaryPushButton("有新版本", self, FluentIcon.LINK)
        self.newVersionButton.setVisible(False)

        self.aboutButton = ToolButton(FluentIcon.INFO, self)
        self.settingButton = PushButton("设置", self, FluentIcon.SETTING)

        self.headerLayout = QHBoxLayout()
        self.headerLayout.setContentsMargins(0, 0, 0, 0)
        self.headerLayout.addLayout(self.titleLayout)
        self.headerLayout.addStretch(0)
        self.headerLayout.addWidget(self.newVersionButton, 0)
        self.headerLayout.addSpacing(12)
        self.headerLayout.addWidget(self.aboutButton, 0)
        self.headerLayout.addSpacing(12)
        self.headerLayout.addWidget(self.settingButton, 0)

        # 表格区域

        self.table = TableWidget(self)
        self.table.verticalHeader().hide()  # 隐藏左侧表头
        self.table.horizontalHeader().setHighlightSections(False)  # 选中时表头不加粗
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)  # 单选模式
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)  # 禁止双击编辑
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "原始文本", "编码"])
        self.table.setColumnWidth(0, 46)  # 1206
        self.table.setColumnWidth(1, 860)
        self.table.setColumnWidth(3, 300)
        styleSheetManager.deregister(self.table)  # 禁用皮肤，启用自定义 QSS
        with open(getResource("src/style/table.qss"), encoding="utf-8") as file:
            self.table.setStyleSheet(file.read())

        self.tableLayout = QHBoxLayout()
        self.tableLayout.setContentsMargins(0, 0, 0, 0)
        self.tableLayout.addWidget(self.table)

        self.tableFrame = QFrame()
        self.tableFrame.setObjectName("tableFrame")
        self.tableFrame.setLayout(self.tableLayout)

        # 1 => 图片
        self.image = RoundedLabel(getResource("src/image/empty.png"))

        # 2 => 详情
        self.separator = QFrame()
        self.separator.setObjectName("separator")
        self.separator.setMinimumHeight(1)
        self.separator.setMaximumHeight(1)

        self.typeLabel = QLabel("当前选中的文本：")
        self.typeLabel.setObjectName("detailLabel")
        self.typeLabel.setWordWrap(True)  # 启用文本换行
        # self.typeLabel.setFixedWidth(200)  # 设置固定宽度为200像素

        self.detailLayout = QVBoxLayout()
        self.detailLayout.setSpacing(10)
        self.detailLayout.addWidget(self.separator)
        self.detailLayout.addSpacing(4)
        self.detailLayout.addWidget(self.typeLabel)
        self.detailLayout.addStretch(0)

        # 3 => 列表

        self.separator2 = QFrame()
        self.separator2.setObjectName("separator")
        self.separator2.setFixedSize(1, 210)

        self.searchList = ListWidget(self)
        self.searchList.setFixedWidth(300)
        styleSheetManager.deregister(self.searchList)  # 禁用皮肤，启用自定义 QSS
        with open(getResource("src/style/list.qss"), encoding="utf-8") as file:
            self.searchList.setStyleSheet(file.read())

        self.infoLayout = QHBoxLayout()
        self.infoLayout.setSpacing(20)
        self.infoLayout.setContentsMargins(16, 16, 16, 16)
        self.infoLayout.addWidget(self.image)
        self.infoLayout.addLayout(self.detailLayout)
        self.infoLayout.addWidget(self.separator2)
        self.infoLayout.addSpacing(-8)
        self.infoLayout.addWidget(self.searchList)

        self.infoFrame = QFrame()
        self.infoFrame.setObjectName("infoFrame")
        self.infoFrame.setLayout(self.infoLayout)
        self.infoFrame.setFixedHeight(self.infoFrame.sizeHint().height())  # 高度自适应

        # 操作区域

        self.progress = ProgressRing(self)
        self.progress.setFixedSize(24, 24)
        self.progress.setStrokeWidth(4)
        self.progress.setTextVisible(False)
        self.progress.setVisible(False)

        self.stateLabel = QLabel("")
        self.stateLabel.setObjectName("stateLabel")

        # self.clearButton = PushButton("清空列表", self)
        # self.clearButton.setFixedWidth(120)

        self.buttonSeparator = QFrame()
        self.buttonSeparator.setObjectName("buttonSeparator")
        self.buttonSeparator.setFixedSize(1, 30)

        # self.standardCodingButton = PushButton("开始批量编码", self)
        # self.standardCodingButton.setFixedWidth(120)
        self.singleCodingButton = PrimaryPushButton("单个编码", self)
        self.singleCodingButton.setFixedWidth(120)

        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.setSpacing(12)
        self.buttonLayout.addWidget(self.progress)
        self.buttonLayout.addWidget(self.stateLabel)
        self.buttonLayout.addStretch(0)
        # self.buttonLayout.addWidget(self.clearButton)
        # self.buttonLayout.addSpacing(8)
        self.buttonLayout.addWidget(self.buttonSeparator)
        self.buttonLayout.addSpacing(8)
        # self.buttonLayout.addWidget(self.standardCodingButton)
        self.buttonLayout.addWidget(self.singleCodingButton)

        # 框架叠叠乐

        self.centralWidget = QWidget(this_window)

        self.layout = QVBoxLayout(self.centralWidget)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(36, 20, 36, 24)
        self.layout.addLayout(self.headerLayout)
        self.layout.addSpacing(24)
        # self.layout.addLayout(self.logLayout)
        # self.layout.addSpacing(24)
        self.layout.addWidget(self.tableFrame)
        self.layout.addSpacing(24)
        self.layout.addWidget(self.infoFrame)
        self.layout.addSpacing(24)
        self.layout.addLayout(self.buttonLayout)

        this_window.setCentralWidget(self.centralWidget)

        QMetaObject.connectSlotsByName(this_window)
