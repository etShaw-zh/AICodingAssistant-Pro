from PySide6.QtCore import QMetaObject
from PySide6.QtGui import QFontDatabase, QFont, QIcon
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame, QTextEdit, QFileDialog
from qfluentwidgets import (setThemeColor, PushButton, ToolButton, PrimaryPushButton, FluentIcon, ProgressRing, LineEdit)
from src.module.version import currentVersion
from src.module.resource import getResource
from src.module.image import RoundedLabel

class AutoCodingWindow:
    def __init__(self):
        self.topicFilePath = 'None'
        self.replyFilePath = 'None'
        self.codingSchemePath = 'None'

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

        self.titleLabel = QLabel("AI Coding Officer Pro")
        self.titleLabel.setObjectName("titleLabel")
        self.titleLabel.setFont(QFont(font_family))

        self.subtitleLabel = QLabel("A cutting-edge AI coding assistant designed to improve the efficiency of text coding.")
        self.subtitleLabel.setObjectName('subtitleLabel')

        self.titleLayout = QVBoxLayout()
        self.titleLayout.setContentsMargins(0, 0, 0, 0)
        self.titleLayout.addWidget(self.titleLabel)
        self.titleLayout.addSpacing(4)
        self.titleLayout.addWidget(self.subtitleLabel)

        self.newVersionButton = PrimaryPushButton("New version", self, FluentIcon.LINK)
        self.newVersionButton.setVisible(False)

        self.aboutButton = ToolButton(FluentIcon.INFO, self)
        self.settingButton = PushButton("Setting", self, FluentIcon.SETTING)

        self.headerLayout = QHBoxLayout()
        self.headerLayout.setContentsMargins(0, 0, 0, 0)
        self.headerLayout.addLayout(self.titleLayout)
        self.headerLayout.addStretch(0)
        self.headerLayout.addWidget(self.newVersionButton, 0)
        self.headerLayout.addSpacing(12)
        self.headerLayout.addWidget(self.aboutButton, 0)
        self.headerLayout.addSpacing(12)
        self.headerLayout.addWidget(self.settingButton, 0)

        # 文件选择区域
        
        # 1 => 图片
        self.image = RoundedLabel(getResource("src/image/empty.png"))

        # 2 => 文件
        self.separator2 = QFrame()
        self.separator2.setObjectName("separator")
        self.separator2.setFixedSize(1, 210)

        # 点击按钮选择topic csv文件区域
        self.topicLabel = QLabel("Topic File:")
        self.topicLabel.setObjectName("topicLabel")
        self.topicInfo = LineEdit(this_window)
        self.topicInfo.setObjectName("topicInfo")
        self.topicInfo.setReadOnly(True)

        self.topicButton = PushButton("Open", this_window)
        self.topicButton.setObjectName("topicButton")
        self.topicButton.setFixedWidth(120)
        self.topicButton.setContentsMargins(8, 0, 0, 0)
        self.topicButton.setIcon(FluentIcon.FOLDER)
        self.topicButton.clicked.connect(self.selectTopicFile)

        # 点击按钮选择reply csv文件区域
        self.replyLabel = QLabel("Reply File:")
        self.replyLabel.setObjectName("replyLabel")
        self.replyInfo = LineEdit(this_window)
        self.replyInfo.setObjectName("replyInfo")
        self.replyInfo.setReadOnly(True)

        self.replyButton = PushButton("Open", this_window)
        self.replyButton.setObjectName("replyButton")
        self.replyButton.setFixedWidth(120)
        self.replyButton.setContentsMargins(8, 0, 0, 0)
        self.replyButton.setIcon(FluentIcon.FOLDER)
        self.replyButton.clicked.connect(self.selectReplyFile)

        # 点击按钮选择coding schema文件区域
        self.schemaLabel = QLabel("Schema File:")
        self.schemaLabel.setObjectName("schemaLabel")
        self.schemaInfo = LineEdit(this_window)
        self.schemaInfo.setObjectName("schemaInfo")
        self.schemaInfo.setReadOnly(True)

        self.schemaButton = PushButton("Open", this_window)
        self.schemaButton.setObjectName("schemaButton")
        self.schemaButton.setFixedWidth(120)
        self.schemaButton.setContentsMargins(8, 0, 0, 0)
        self.schemaButton.setIcon(FluentIcon.FOLDER)
        self.schemaButton.clicked.connect(self.selectSchemaFile)

        # 日志区域
        self.logLabel = QLabel("Log:")
        self.logLabel.setObjectName("logLabel")
        self.logFrame = QFrame()
        self.logFrame.setObjectName("logFrame")
        self.logFrame.setFrameShape(QFrame.StyledPanel)
        self.logFrame.setFrameShadow(QFrame.Raised)
        self.logFrameLayout = QVBoxLayout(self.logFrame)
        self.logFrameLayout.setContentsMargins(0, 0, 0, 0)
        self.logContent = QTextEdit("Welcome to AI Coding Officer Pro!")
        self.logContent.setObjectName("logContent")
        self.logContent.setFontFamily("Courier")
        self.logContent.setFontPointSize(14) 
        self.logContent.setStyleSheet("""
            QTextEdit {
                background-color: #000000;
                color: #00FF00;
                border: 1px solid #555;
            }
        """)
        self.logContent.setReadOnly(True)  
        self.logFrameLayout.addWidget(self.logContent)
        
        self.logLayout = QVBoxLayout()
        self.logLayout.setContentsMargins(0, 0, 0, 0)
        self.logLayout.addWidget(self.logLabel)
        self.logLayout.addWidget(self.logFrame)  

        # 操作区域

        self.progress = ProgressRing(self)
        self.progress.setFixedSize(24, 24)
        self.progress.setStrokeWidth(4)
        self.progress.setTextVisible(False)
        self.progress.setVisible(False)

        self.stateLabel = QLabel("")
        self.stateLabel.setObjectName("stateLabel")

        self.buttonSeparator = QFrame()
        self.buttonSeparator.setObjectName("buttonSeparator")
        self.buttonSeparator.setFixedSize(1, 30)

        self.exportCodingResultButton = PushButton("Export Data", self)
        self.exportCodingResultButton.setFixedWidth(120)
        # self.exprotButton.setEnabled(False)
        self.stopCodingButton = PushButton("Stop Coding", self)
        self.stopCodingButton.setFixedWidth(120)
        self.stopCodingButton.setEnabled(False)
        self.testCodingButton = PushButton("Test Coding", self)
        self.testCodingButton.setFixedWidth(120)
        # self.testCodingButton.setEnabled(False)
        self.standardCodingButton = PushButton("Batch Coding", self)
        self.standardCodingButton.setFixedWidth(120)
        # self.standardCodingButton.setEnabled(False)
        self.loadDataButton = PushButton("Load Data", self)
        self.loadDataButton.setFixedWidth(120)

        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.setSpacing(12)
        self.buttonLayout.addWidget(self.progress)
        self.buttonLayout.addWidget(self.stateLabel)
        self.buttonLayout.addStretch(0)
        self.buttonLayout.addWidget(self.loadDataButton)
        self.buttonLayout.addWidget(self.buttonSeparator)
        self.buttonLayout.addSpacing(4)
        self.buttonLayout.addWidget(self.testCodingButton)
        self.buttonLayout.addSpacing(8)
        self.buttonLayout.addWidget(self.standardCodingButton)
        self.buttonLayout.addSpacing(8)
        self.buttonLayout.addWidget(self.stopCodingButton)
        self.buttonLayout.addWidget(self.buttonSeparator)
        self.buttonLayout.addSpacing(8)
        self.buttonLayout.addWidget(self.exportCodingResultButton)


        # 框架叠叠乐

        self.centralWidget = QWidget(this_window)

        self.layout = QVBoxLayout(self.centralWidget)
        # self.layout.setSpacing(0)
        self.layout.setContentsMargins(36, 20, 36, 24)
        self.layout.addLayout(self.headerLayout)
        self.layout.addSpacing(12)

        self.topicLayout = QHBoxLayout()
        self.topicLayout.addWidget(self.topicLabel)
        self.topicLayout.addWidget(self.topicInfo)
        self.topicLayout.addWidget(self.topicButton)
        self.replyLayout = QHBoxLayout()
        self.replyLayout.addWidget(self.replyLabel)
        self.replyLayout.addWidget(self.replyInfo)
        self.replyLayout.addWidget(self.replyButton)
        self.schemaLayout = QHBoxLayout()
        self.schemaLayout.addWidget(self.schemaLabel)
        self.schemaLayout.addWidget(self.schemaInfo)
        self.schemaLayout.addWidget(self.schemaButton)

        self.layout.addLayout(self.topicLayout)
        self.layout.addLayout(self.replyLayout)
        self.layout.addLayout(self.schemaLayout)

        self.displayLayout = QHBoxLayout()
        self.displayLayout.addLayout(self.logLayout)
        self.layout.addLayout(self.displayLayout)
        self.layout.addLayout(self.buttonLayout)

        this_window.setCentralWidget(self.centralWidget)

        QMetaObject.connectSlotsByName(this_window)

    def selectFile(self, line_edit, file_type, file_filter):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(
            self.centralWidget,  # 使用 centralWidget 作为父组件
            f"Choose {file_type} file", "",
            file_filter,
            options=options
        )
        if fileName:
            line_edit.setText(fileName)
            return fileName

    def selectTopicFile(self):
        self.topicFilePath = self.selectFile(self.topicInfo, "Topic CSV", "CSV 文件 (*.csv);;所有文件 (*)")

    def selectReplyFile(self):
        self.replyFilePath = self.selectFile(self.replyInfo, "Reply CSV", "CSV 文件 (*.csv);;所有文件 (*)")

    def selectSchemaFile(self):
        self.codingSchemePath = self.selectFile(self.schemaInfo, "Schema CSV", "CSV 文件 (*.csv);;所有文件 (*)")
