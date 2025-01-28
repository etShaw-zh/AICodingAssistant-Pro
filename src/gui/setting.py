from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QHBoxLayout, QFrame, QMessageBox
from PySide6.QtGui import QIcon
from qfluentwidgets import LineEdit, PushButton, FluentIcon, PrimaryPushButton, EditableComboBox

from src.module.resource import getResource
from src.module.config import localDBFilePath, logFolder, readConfig, configFile
from src.module.aihubmix import AiHubMixAPI

class SettingWindow(object):
    def setupUI(self, this_window):
        # 加载 QSS
        with open(getResource("src/style/style_light.qss"), "r", encoding="UTF-8") as file:
            style_sheet = file.read()
        this_window.setStyleSheet(style_sheet)

        this_window.setWindowTitle("Settings")
        this_window.setWindowIcon(QIcon(getResource("src/image/AICO-logo.png")))
        this_window.resize(850, -1)
        this_window.setFixedSize(self.size())  # 禁止拉伸窗口

        # 选择语言
        self.languageTitle = QLabel("Language")

        self.languageInfo = QLabel("Select the language of the interface, restart the application to take effect.")
        self.languageInfo.setObjectName("cardInfoLabel")

        self.language = EditableComboBox(this_window)
        self.language.setMinimumWidth(200)
        self.language.setMaximumWidth(200)
        self.language.addItems(["Chinese", "English"])
        self.language.setText("Chinese")

        self.languageCard = self.settingCard(self.languageTitle, self.languageInfo, self.language, "full")

        # 设置模型API key 
        self.modelApiTitle = QLabel("API Key")
        self.modelApiInfo = QLabel("Please enter your AiHubMix API key.")

        self.modelApiKey = LineEdit(self)
        self.modelApiKey.setFixedWidth(200)
        self.modelApiKey.setClearButtonEnabled(True)
        self.modelApiKey.setText(readConfig().get("APIkey", "api_key"))
        
        # 添加验证按钮
        self.validateApiButton = PushButton("Validate", self)
        self.validateApiButton.setFixedWidth(80)
        self.validateApiButton.clicked.connect(self.validateApiKey)

        # 创建水平布局来放置API Key输入框和验证按钮
        self.apiKeyLayout = QHBoxLayout()
        self.apiKeyLayout.addWidget(self.modelApiKey)
        self.apiKeyLayout.addWidget(self.validateApiButton)
        self.apiKeyLayout.addStretch()

        self.apiKeyFrame = QFrame()
        self.apiKeyFrame.setLayout(self.apiKeyLayout)

        self.modelApiCard = self.settingCard(self.modelApiTitle, self.modelApiInfo, self.apiKeyFrame, "full")

        # 选择模型
        self.modelTypeTitle = QLabel("AI Model")
        self.modelTypeInfo = QLabel("Select the AI model to use. The list shows models available with your API key.")
        self.modelTypeInfo.setObjectName("cardInfoLabel")

        self.modelTypeUrl = QLabel("<a href='https://doc.aihubmix.com/en'"
                                  "style='font-size:12px;color:#2E75B6;'>View documentation</a>")
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
        
        # 初始化时加载已保存的模型
        current_model = readConfig().get("AICO", "model")
        self.modelType.setText(current_model)
        
        # 添加刷新按钮
        self.refreshModelsButton = PushButton("Refresh", self)
        self.refreshModelsButton.setFixedWidth(80)
        self.refreshModelsButton.clicked.connect(self.refreshAvailableModels)

        self.modelTypeLayout = QHBoxLayout()
        self.modelTypeLayout.addWidget(self.modelType)
        self.modelTypeLayout.addWidget(self.refreshModelsButton)
        self.modelTypeLayout.addStretch()

        self.modelTypeFrame = QFrame()
        self.modelTypeFrame.setLayout(self.modelTypeLayout)

        self.modelTypeCard = self.settingCard(self.modelTypeTitle, self.dateInfoFrame, self.modelTypeFrame, "full")

        # 选择线程数
        self.threadTitle = QLabel("Thread count")

        self.threadInfo = QLabel("Select the number of threads to use, the default is 1.")
        self.threadInfo.setObjectName("cardInfoLabel")

        self.threadCount = EditableComboBox(this_window)
        self.threadCount.setMinimumWidth(200)
        self.threadCount.setMaximumWidth(200)
        self.threadCount.addItems(["1", "2", "4", "8"])
        self.threadCount.setText("1")

        self.threadCard = self.settingCard(self.threadTitle, self.threadInfo, self.threadCount, "full")

        # 本地数据库文件夹

        self.localDBTitle = QLabel("Local database")
        self.localDBInfo = QLabel(localDBFilePath())

        self.localDBButton = PushButton("Open", self, FluentIcon.FOLDER)
        self.localDBButton.setFixedWidth(100)

        self.localDBCard = self.settingCard(
            self.localDBTitle, self.localDBInfo, self.localDBButton, "full")

        # 日志

        self.logFolderTitle = QLabel("Log folder")
        self.logFolderInfo = QLabel(logFolder())

        self.logFolderButton = PushButton("Open", self, FluentIcon.FOLDER)
        self.logFolderButton.setFixedWidth(100)

        self.logFolderCard = self.settingCard(
            self.logFolderTitle, self.logFolderInfo, self.logFolderButton, "full")

        # 按钮

        self.applyButton = PrimaryPushButton("Save", self)
        self.applyButton.setFixedWidth(120)
        self.cancelButton = PushButton("Cancel", self)
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
        layout.addWidget(self.threadCard)
        # layout.addWidget(self.localDBCard)
        # layout.addWidget(self.logFolderCard)
        layout.addSpacing(12)
        layout.addLayout(self.buttonLayout)

        self.applyButton.clicked.connect(self.saveSettings)

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

    def validateApiKey(self):
        """验证API密钥"""
        api_key = self.modelApiKey.text().strip()
        if not api_key:
            QMessageBox.warning(self, "Error", "Please enter your API key first!")
            return

        api = AiHubMixAPI()
        if api.validate_api_key():
            QMessageBox.information(self, "Success", "API Key is valid!")
            self.refreshAvailableModels()
        else:
            QMessageBox.warning(self, "Error", "Invalid API key. Please check and try again.")

    def refreshAvailableModels(self):
        """刷新可用模型列表"""
        api = AiHubMixAPI()
        models = api.get_available_models()
        
        if not models:
            QMessageBox.warning(self, "Error", "Failed to fetch available models. Please check your API key and try again.")
            return
            
        current_model = self.modelType.text()
        self.modelType.clear()
        self.modelType.addItems(models)
        
        # 保持当前选择的模型（如果它仍然可用）
        if current_model in models:
            self.modelType.setText(current_model)
        else:
            self.modelType.setText(models[0])

    def saveSettings(self):
        """保存设置"""
        config = readConfig()
        
        # 保存API密钥
        api_key = self.modelApiKey.text().strip()
        if api_key:
            config.set("APIkey", "api_key", api_key)
        
        # 保存选择的模型
        selected_model = self.modelType.text()
        if selected_model:
            config.set("AICO", "model", selected_model)
        
        # 保存语言设置
        config.set("Language", "language", self.language.text())
        
        # 保存线程数
        thread_count = self.threadCount.text()
        if thread_count.isdigit() and 1 <= int(thread_count) <= 8:
            config.set("Thread", "thread_count", thread_count)
        
        # 写入配置文件
        with open(configFile(), "w", encoding="utf-8") as f:
            config.write(f)
            
        QMessageBox.information(self, "Success", "Settings saved successfully!")
