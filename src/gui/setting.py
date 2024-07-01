from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QHBoxLayout, QFrame
from PySide6.QtGui import QIcon
from qfluentwidgets import LineEdit, PushButton, FluentIcon, PrimaryPushButton, EditableComboBox

from src.module.resource import getResource
from src.module.config import codingFrameworkFolder, logFolder


class SettingWindow(object):
    def setupUI(self, this_window):
        # 加载 QSS
        with open(getResource("src/style/style_light.qss"), "r", encoding="UTF-8") as file:
            style_sheet = file.read()
        this_window.setStyleSheet(style_sheet)

        this_window.setWindowTitle("设置")
        this_window.setWindowIcon(QIcon(getResource("src/image/AICO-logo.png")))
        this_window.resize(850, -1)
        this_window.setFixedSize(self.size())  # 禁止拉伸窗口

        # 选择语言
        self.languageTitle = QLabel("语言")

        self.languageInfo = QLabel("选择你的首选语言，重启后生效。")
        self.languageInfo.setObjectName("cardInfoLabel")

        self.language = EditableComboBox(this_window)
        self.language.setMinimumWidth(200)
        self.language.setMaximumWidth(200)
        self.language.addItems(["简体中文", "English"])
        self.language.setText("简体中文")

        self.languageCard = self.settingCard(self.languageTitle, self.languageInfo, self.language, "full")

        # 选择模型

        self.modelTypeTitle = QLabel("GPT 模型")

        self.modelTypeInfo = QLabel("指定编码的GPT模型，不同模型有不同的编码效果。")
        self.modelTypeInfo.setObjectName("cardInfoLabel")

        self.modelTypeUrl = QLabel("<a href='https://aicodingassistant.readthedocs.io/en/latest/' "
                                  "style='font-size:12px;color:#2E75B6;'>查看在线文档</a>")
        self.modelTypeUrl.setOpenExternalLinks(True)

        self.modelInfoLayout = QHBoxLayout()
        self.modelInfoLayout.setSpacing(0)
        self.modelInfoLayout.setContentsMargins(0, 0, 0, 0)
        self.modelInfoLayout.setAlignment(Qt.AlignLeft)
        self.modelInfoLayout.addWidget(self.modelTypeInfo)
        self.modelInfoLayout.addWidget(self.modelTypeUrl)

        self.dateInfoFrame = QFrame()
        self.dateInfoFrame.setLayout(self.modelInfoLayout)

        self.modelType = EditableComboBox(self)
        self.modelType.setMinimumWidth(200)
        self.modelType.setMaximumWidth(200)
        self.modelType.addItems(["ChatGPT-3.5", "Kimi", "QWen-7B"])
        self.modelType.setText("Kimi")  # 设置默认值为 "Kimi"

        self.modelTypeCard = self.settingCard(self.modelTypeTitle, self.dateInfoFrame, self.modelType, "full")

        # 设置模型API key 
        
        self.modelApiTitle = QLabel("GPT API Key")
        self.modelApiInfo = QLabel("输入你的GPT API Key，用于调用GPT模型。")

        self.modelApiKey = LineEdit(self)
        self.modelApiKey.setFixedWidth(200)
        self.modelApiKey.setClearButtonEnabled(True)

        self.modelApiCard = self.settingCard(self.modelApiTitle, self.modelApiInfo, self.modelApiKey, "full")

        # 编码框架文件夹

        self.posterFolderTitle = QLabel("编码框架文件夹")
        self.posterFolderInfo = QLabel(codingFrameworkFolder())

        self.posterFolderButton = PushButton("打开", self, FluentIcon.FOLDER)
        self.posterFolderButton.setFixedWidth(100)

        self.posterFolderCard = self.settingCard(
            self.posterFolderTitle, self.posterFolderInfo, self.posterFolderButton, "full")

        # 日志

        self.logFolderTitle = QLabel("日志文件夹")
        self.logFolderInfo = QLabel(logFolder())

        self.logFolderButton = PushButton("打开", self, FluentIcon.FOLDER)
        self.logFolderButton.setFixedWidth(100)

        self.logFolderCard = self.settingCard(
            self.logFolderTitle, self.logFolderInfo, self.logFolderButton, "full")

        # 按钮

        self.applyButton = PrimaryPushButton("保存", self)
        self.applyButton.setFixedWidth(120)
        self.cancelButton = PushButton("取消", self)
        self.cancelButton.setFixedWidth(120)

        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.setSpacing(12)
        self.buttonLayout.addStretch(0)
        self.buttonLayout.addWidget(self.applyButton)
        self.buttonLayout.addWidget(self.cancelButton)
        self.buttonLayout.addStretch(0)

        # 叠叠乐

        layout = QVBoxLayout(this_window)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.addWidget(self.languageCard)
        layout.addWidget(self.modelTypeCard)
        layout.addWidget(self.modelApiCard)
        layout.addWidget(self.posterFolderCard)
        layout.addWidget(self.logFolderCard)
        layout.addSpacing(12)
        layout.addLayout(self.buttonLayout)

    def settingCard(self, card_title, card_info, card_func, size):
        card_title.setObjectName("cardTitleLabel")
        card_info.setObjectName("cardInfoLabel")

        self.infoPart = QVBoxLayout()
        self.infoPart.setSpacing(3)
        self.infoPart.setContentsMargins(0, 0, 0, 0)
        self.infoPart.addWidget(card_title)
        self.infoPart.addWidget(card_info)

        self.card = QHBoxLayout()
        self.card.setContentsMargins(20, 16, 20, 16)
        self.card.addLayout(self.infoPart, 0)
        self.card.addStretch(0)
        self.card.addWidget(card_func)

        self.cardFrame = QFrame()
        self.cardFrame.setLayout(self.card)

        if size == "half":
            self.cardFrame.setObjectName("cardFrameHalf")
        elif size == "full":
            self.cardFrame.setObjectName("cardFrameFull")

        return self.cardFrame

    def tutorialCard(self, card_token, card_explain):
        self.tokenLabel = QLabel(card_token)
        self.tokenLabel.setObjectName("lightLabel")
        self.explainLabel = QLabel(card_explain)
        self.explainLabel.setObjectName("lightLabel")

        self.tutorialLayout = QHBoxLayout()
        self.tutorialLayout.setContentsMargins(12, 8, 12, 8)
        self.tutorialLayout.addWidget(self.tokenLabel)
        self.tutorialLayout.addStretch(0)
        self.tutorialLayout.addWidget(self.explainLabel)

        self.card = QFrame()
        self.card.setMinimumWidth(181)
        self.card.setMaximumWidth(181)
        self.card.setObjectName("cardFrameTutorial")
        self.card.setLayout(self.tutorialLayout)

        return self.card
