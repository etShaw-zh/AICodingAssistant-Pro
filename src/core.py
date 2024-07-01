import os
import time
import threading
import shutil
import arrow
import requests
import pandas as pd

from PySide6.QtWidgets import QMainWindow, QTableWidgetItem, QDialog, QListWidgetItem, QToolBar, QLabel, QWidget, QHBoxLayout, QApplication, QVBoxLayout, QStackedWidget, QMenu
from PySide6.QtCore import Qt, QEvent, QUrl, Signal, QPoint
from PySide6.QtGui import QDesktopServices, QIcon, QFontDatabase, QFont

from qfluentwidgets import InfoBar, InfoBarPosition, Flyout, InfoBarIcon, RoundMenu, Action, FluentIcon, NavigationToolButton, NavigationPanel, NavigationItemPosition, MessageBox, Theme, setTheme, isDarkTheme
from qfluentwidgets import (NavigationInterface, setThemeColor, PushButton, ToolButton, TableWidget, PrimaryPushButton,
                            ProgressRing, ListWidget, NavigationAvatarWidget)
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets.common.style_sheet import styleSheetManager

from qframelesswindow import FramelessWindow, StandardTitleBar


from src.gui.mainwindow import MainWindow
from src.gui.about import AboutWindow
from src.gui.setting import SettingWindow
from src.gui.dialog import NameEditBox

from src.function import log, readCSV, initList, addTimes, openFolder
from src.module.coding import AICoding, getFinalName
from src.module.config import configFile, codingFrameworkFolder, logFolder, readConfig, oldConfigCheck
from src.module.version import newVersion, currentVersion
from src.module.resource import getResource

class Widget(QWidget):

    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.label = QLabel(text, self)
        self.hBoxLayout = QHBoxLayout(self)

        self.label.setAlignment(Qt.AlignCenter)
        self.hBoxLayout.addWidget(self.label, 1, Qt.AlignCenter)

        self.setObjectName(text.replace(' ', '-'))

class NavigationBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.hBoxLayout = QHBoxLayout(self)
        self.menuButton = NavigationToolButton(FIF.MENU, self)
        self.navigationPanel = NavigationPanel(parent, True)
        self.titleLabel = QLabel(self)

        self.navigationPanel.move(0, 31)
        self.hBoxLayout.setContentsMargins(5, 5, 5, 5)
        self.hBoxLayout.addWidget(self.menuButton)
        self.hBoxLayout.addWidget(self.titleLabel)

        self.menuButton.clicked.connect(self.showNavigationPanel)
        self.navigationPanel.setExpandWidth(260)
        self.navigationPanel.setMenuButtonVisible(True)
        self.navigationPanel.hide()

        # enable acrylic effect
        self.navigationPanel.setAcrylicEnabled(True)

        self.window().installEventFilter(self)

    def setTitle(self, title: str):
        self.titleLabel.setText(title)
        self.titleLabel.adjustSize()

    def showNavigationPanel(self):
        self.navigationPanel.show()
        self.navigationPanel.raise_()
        self.navigationPanel.expand()

    def addItem(self, routeKey, icon, text: str, onClick, selectable=True, position= NavigationItemPosition.TOP):
        def wrapper():
            onClick()
            self.setTitle(text)

        self.navigationPanel.addItem(
            routeKey, icon, text, wrapper, selectable, position)

    def addSeparator(self, position=NavigationItemPosition.TOP):
        self.navigationPanel.addSeparator(position)

    def setCurrentItem(self, routeKey: str):
        self.navigationPanel.setCurrentItem(routeKey)
        self.setTitle(self.navigationPanel.widget(routeKey).text())

    def eventFilter(self, obj, e: QEvent):
        if obj is self.window():
            if e.type() == QEvent.Resize:
                self.navigationPanel.setFixedHeight(e.size().height() - 31)

        return super().eventFilter(obj, e)

class Window(FramelessWindow):

    def __init__(self):
        super().__init__()
        self.setTitleBar(StandardTitleBar(self))

        self.hBoxLayout = QHBoxLayout(self)
        self.navigationInterface = NavigationInterface(self, showMenuButton=True)
        self.stackWidget = QStackedWidget(self)

        # create sub interface
        self.myMainWindow = MyMainWindow()
        self.stackWidget.addWidget(self.myMainWindow)

        # initialize layout
        self.initLayout()

        # add items to navigation interface
        self.initNavigation()

        self.initWindow()

    def initLayout(self):
        self.hBoxLayout.setSpacing(0)
        self.hBoxLayout.setContentsMargins(0, self.titleBar.height(), 0, 0)
        self.hBoxLayout.addWidget(self.navigationInterface)
        self.hBoxLayout.addWidget(self.stackWidget)
        self.hBoxLayout.setStretchFactor(self.stackWidget, 1)

    def initNavigation(self):
        self.navigationInterface.setExpandWidth(100)

        self.navigationInterface.addItem('MyMainWindow', FIF.HOME, '主页', lambda: self.switchTo(self.myMainWindow))
        self.navigationInterface.addSeparator()

        self.navigationInterface.addWidget(
            routeKey='avatar',
            widget=NavigationAvatarWidget('Shaw', 'src/image/icon_win.png'),
            onClick=self.showMessageBox,
            position=NavigationItemPosition.BOTTOM,
        )
        self.navigationInterface.addItem(
            'About Interface',
            FIF.INFO,
            '关于',
            onClick=self.openAbout,
            position=NavigationItemPosition.BOTTOM
        )
        self.navigationInterface.addItem(
            'Setting Interface', 
            FIF.SETTING, 
            '设置', 
            onClick=self.openSetting,
            position=NavigationItemPosition.BOTTOM
        )

        self.stackWidget.currentChanged.connect(self.onCurrentInterfaceChanged)
        self.stackWidget.setCurrentIndex(0)

    def initWindow(self):
        self.resize(1280, 720)
        self.setWindowTitle(f"AI Coding Officer Pro {currentVersion()}")
        self.setWindowIcon(QIcon(getResource("src/image/icon_win.png")))
        setThemeColor("#2E75B6")
        
        # 加载 QSS
        with open(getResource("src/style/style_light.qss"), "r", encoding="UTF-8") as file:
            style_sheet = file.read()
        self.setStyleSheet(style_sheet)

        desktop = QApplication.screens()[0].availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)

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

    def switchTo(self, widget):
        self.stackWidget.setCurrentWidget(widget)
    
    def openAbout(self):
        about = MyAboutWindow()
        about.exec()

    def openSetting(self):
        setting = MySettingWindow()
        setting.save_notice.connect(self.closeSetting)
        setting.exec()

    def closeSetting(self, title):
        self.showInfo("success", title, "配置修改成功")
    
    def showInfo(self, state, title, content):
        info_state = {
            "info": InfoBar.info,
            "success": InfoBar.success,
            "warning": InfoBar.warning,
            "error": InfoBar.error
        }

        if state in info_state:
            info_state[state](
                title=title, content=content,
                orient=Qt.Horizontal, isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000, parent=self
            )

    def onCurrentInterfaceChanged(self, index):
        widget = self.stackWidget.widget(index)
        self.navigationInterface.setCurrentItem(widget.objectName())

    def showMessageBox(self):
        w = MessageBox(
            '支持作者🥰',
            '个人开发不易，如果这个项目帮助到了您，可以考虑请作者喝一瓶快乐水🥤。您的支持就是作者开发和维护项目的动力🚀',
            self
        )
        w.yesButton.setText('来啦老弟')
        w.cancelButton.setText('下次一定')

        if w.exec():
            QDesktopServices.openUrl(QUrl("https://xiaojianjun.cn"))

# class Window(FramelessWindow):

#     def __init__(self):
#         super().__init__()
#         self.setTitleBar(StandardTitleBar(self))

#         self.vBoxLayout = QVBoxLayout(self)
#         # self.navigationInterface = NavigationBar(self)
#         self.navigationInterface = NavigationInterface(self, showMenuButton=True, collapsible=True)
#         self.stackWidget = QStackedWidget(self)

#         # create sub interface
#         self.myMainWindow = MyMainWindow()
#         self.musicInterface = Widget('Music Interface', self)
#         self.videoInterface = Widget('Video Interface', self)
#         self.folderInterface = Widget('Folder Interface', self)
#         self.settingInterface = Widget('Setting Interface', self)

#         self.stackWidget.addWidget(self.myMainWindow)
#         self.stackWidget.addWidget(self.musicInterface)
#         self.stackWidget.addWidget(self.videoInterface)
#         self.stackWidget.addWidget(self.folderInterface)
#         self.stackWidget.addWidget(self.settingInterface)

#         # initialize layout
#         self.initLayout()

#         # add items to navigation interface
#         self.initNavigation()

#         self.initWindow()
    
#     def initLayout(self):
#         self.vBoxLayout.setSpacing(0)
#         self.vBoxLayout.setContentsMargins(0, self.titleBar.height(), 0, 0)
#         self.vBoxLayout.addWidget(self.navigationInterface)
#         self.vBoxLayout.addWidget(self.stackWidget)
#         self.vBoxLayout.setStretchFactor(self.stackWidget, 1)

#     def initNavigation(self):
#         self.navigationInterface.addItem('MyMainWindow', FIF.HOME, 'Home', lambda: self.switchTo(self.myMainWindow))
#         self.addSubInterface(self.musicInterface, FIF.MUSIC, 'Music library')
#         self.addSubInterface(self.videoInterface, FIF.VIDEO, 'Video library')

#         self.navigationInterface.addSeparator()

#         # add navigation items to scroll area
#         self.addSubInterface(self.folderInterface, FIF.FOLDER, 'Folder library', NavigationItemPosition.SCROLL)

#         self.navigationInterface.addWidget(
#             routeKey='avatar',
#             widget=NavigationAvatarWidget('Shaw', 'src/image/icon_win.png'),
#             onClick=self.showMessageBox,
#             position=NavigationItemPosition.BOTTOM,
#         )
#         # add item to bottom
#         self.addSubInterface(self.settingInterface, FIF.SETTING, 'Settings', NavigationItemPosition.BOTTOM)

#         self.stackWidget.currentChanged.connect(self.onCurrentInterfaceChanged)
#         self.stackWidget.setCurrentIndex(1)

#     def addSubInterface(self, interface, icon, text: str, position=NavigationItemPosition.TOP, parent=None):
#         self.stackWidget.addWidget(interface)
#         self.navigationInterface.addItem(
#             routeKey=interface.objectName(),
#             icon=icon,
#             text=text,
#             onClick=lambda: self.switchTo(interface),
#             position=position,
#             tooltip=text,
#             parentRouteKey=parent.objectName() if parent else None
#         )

#     def initWindow(self):

#         self.resize(1280, 720)
#         self.setWindowTitle(f"AI Coding Officer Pro {currentVersion()}")
#         self.setWindowIcon(QIcon(getResource("src/image/icon_win.png")))
#         setThemeColor("#2E75B6")
        
#         # 加载 QSS
#         with open(getResource("src/style/style_light.qss"), "r", encoding="UTF-8") as file:
#             style_sheet = file.read()
#         self.setStyleSheet(style_sheet)

#         desktop = QApplication.screens()[0].availableGeometry()
#         w, h = desktop.width(), desktop.height()
#         self.move(w//2 - self.width()//2, h//2 - self.height()//2)

#     def switchTo(self, widget):
#         self.stackWidget.setCurrentWidget(widget)

#     def onCurrentInterfaceChanged(self, index):
#         widget = self.stackWidget.widget(index)
#         self.navigationInterface.setCurrentItem(widget.objectName())

#     def showMessageBox(self):
#         w = MessageBox(
#             'This is a help message',
#             'You clicked a customized navigation widget. You can add more custom widgets by calling `NavigationInterface.addWidget()` 😉',
#             self
#         )
#         w.exec()

class MyMainWindow(QMainWindow, MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUI(self)
        self.initConnect()
        self.initList()
        self.checkVersion()

        oldConfigCheck()
        addTimes("open_times")
        self.config = readConfig()
        self.coding_framework_folder = codingFrameworkFolder()

        self.worker = AICoding()
        self.worker.main_state.connect(self.showState)
        self.worker.coding_state.connect(self.editTableState)
        self.worker.added_progress_count.connect(self.addProgressBar)

    def initConnect(self):
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)  # 自定义右键菜单
        self.table.customContextMenuRequested.connect(self.showRightClickMenu)
        self.table.itemSelectionChanged.connect(self.selectTable)

        self.searchList.setContextMenuPolicy(Qt.CustomContextMenu)  # 自定义右键菜单 - 编码代码，方便修改
        self.searchList.customContextMenuRequested.connect(self.showRightClickMenu2)

        self.newVersionButton.clicked.connect(self.openRelease)
        self.aboutButton.clicked.connect(self.openAbout)
        self.settingButton.clicked.connect(self.openSetting)

        self.standardCodingButton.clicked.connect(self.standardCoding)
        # self.singleCodingButton.clicked.connect(self.singleCoding)
    
    def initList(self, clean_all=True):
        if clean_all:
            self.list_id = 0
            self.anime_list = [] # 存储所有文本的列表
            self.file_list = [] # 存储所有拖入文件夹的路径
            self.df = pd.DataFrame() # 存储所有文本的DataFrame
            self.table.setRowCount(0)

        self.table.clearContents()
        self.progress.setValue(0)
        self.searchList.clear()
        for text in ['编码1', '编码2', '编码3']:
            self.searchList.addItem(QListWidgetItem(text))

        self.typeLabel.setText("当前选中的文本：")
        self.image.updateImage(getResource("src/image/empty.png"))

    def showState(self, state):
        self.stateLabel.setText(state)

    def editTableState(self, state):
        list_id, coding_state = state
        self.table.setItem(list_id, 2, QTableWidgetItem(coding_state))

    def showProgressBar(self):
        self.progress.setVisible(True)
        step = 6 if len(self.anime_list) < 6 else 7 # TODO: 优化进度条
        self.progress.setMaximum(len(self.anime_list) * step)

    def addProgressBar(self, count):
        now_count = self.progress.value()
        self.progress.setValue(now_count + count)

    def checkVersion(self):
        thread = threading.Thread(target=self.ThreadCheckVersion)
        thread.start()
        thread.join()

    def ThreadCheckVersion(self):
        if newVersion():
            self.newVersionButton.setVisible(True)
            log("发现有新版本")

    def openRelease(self):
        url = QUrl("https://github.com/etShaw-zh/AICodingAssistant-Pro/releases/latest")
        QDesktopServices.openUrl(url)

    def openAbout(self):
        about = MyAboutWindow()
        about.exec()

    def openSetting(self):
        setting = MySettingWindow()
        setting.save_notice.connect(self.closeSetting)
        setting.exec()

    def closeSetting(self, title):
        for anime in self.anime_list:
            getFinalName(anime)
        self.selectTable()
        self.showInfo("success", title, "配置修改成功")

    def RowInTable(self):
        for selected in self.table.selectedRanges():
            row = selected.topRow()
            return row

    def dragEnterEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event):
        # 获取并格式化本地路径，可以多个
        raw_list = event.mimeData().urls() 
        self.df, self.file_list = readCSV(self.df, self.file_list, raw_list)
        print(self.df)

        log("————")
        log(f"拖入了{len(raw_list)}个文本：")
        for file_path in raw_list:
            log(file_path)

        self.showInTableFromDf()

    def showInTableFromDf(self):
        self.table.setRowCount(len(self.df))

        _keys = self.df.keys()
        for index, row in self.df.iterrows():
            for i, key in enumerate(_keys):
                self.table.setItem(index, i, QTableWidgetItem(str(row[key])))

    def selectTable(self):
        row = self.RowInTable()
        if row is None:
            self.typeLabel.setText("请选择一个文本！")
            return
        print(self.df.loc[row, '原始文本'])
        self.typeLabel.setText(f"当前选中的文本：\n {self.df.loc[row, '原始文本']}")

    def showRightClickMenu(self, pos):
        edit_init_name = Action(FluentIcon.EDIT, "修改编码结果")
        open_this_folder = Action(FluentIcon.FOLDER, "打开此文件夹")

        menu = RoundMenu(parent=self)
        menu.addAction(edit_init_name)
        menu.addSeparator()
        menu.addAction(open_this_folder)

        # 必须选中单元格才会显示
        if self.table.itemAt(pos) is not None:
            menu.exec(self.table.mapToGlobal(pos) + QPoint(0, 30), ani=True)  # 在微调菜单位置

            # 不使用RowInTable函数，使用当前pos点位计算行数
            # 目的是避免点击右键时，当前行若未选中，会报错
            # row = self.RowInTable()
            clicked_item = self.table.itemAt(pos)  # 计算坐标
            row = self.table.row(clicked_item)  # 计算行数

            edit_init_name.triggered.connect(lambda: self.editInitName(row))
            open_this_folder.triggered.connect(lambda: self.openThisFolder(row))

    # 显示右键菜单 - 编码代码 - 方便修改
    def showRightClickMenu2(self, pos):
        instead_this_anime = Action(FluentIcon.LABEL, "手动编码此文本")

        menu = RoundMenu(parent=self)
        menu.addAction(instead_this_anime)

        # 必须选中才会显示
        if self.searchList.itemAt(pos) is not None:
            # 计算子表格行
            clicked_item = self.searchList.itemAt(pos)  # 计算坐标
            list_row = self.searchList.row(clicked_item)  # 计算行数

            # 计算主表格行，不需要考虑选中问题，可直接使用RowInTable函数
            table_row = self.RowInTable()
            
            menu.exec(self.searchList.mapToGlobal(pos), ani=True)
            instead_this_anime.triggered.connect(lambda: self.correctThisAnime(table_row))
                
    def correctThisAnime(self, table_row):
        label = self.searchList.currentRow()
        self.df.loc[table_row, '编码结果'] = self.searchList.currentItem().text()
        self.showInTableFromDf()

    # 显示提示信息
    def showInfo(self, state, title, content):
        info_state = {
            "info": InfoBar.info,
            "success": InfoBar.success,
            "warning": InfoBar.warning,
            "error": InfoBar.error
        }

        if state in info_state:
            info_state[state](
                title=title, content=content,
                orient=Qt.Horizontal, isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000, parent=self
            )

    # TODO: 补充编码函数
    def standardCoding():
        pass

    def singleCoding():
        pass

class MyAboutWindow(QDialog, AboutWindow):
    def __init__(self):
        super().__init__()
        self.setupUI(self)
        self.checkPing()
        self.config = readConfig()
        self.loadConfig()

    def loadConfig(self):
        self.openTimes.setText(self.config.get("Counter", "open_times"))
        self.analysisTimes.setText(self.config.get("Counter", "analysis_times"))

    def checkPing(self):
        thread1 = threading.Thread(target=self.checkPingThread, args=("aicodingassiatant.cn", self.anilistPing)) # TODO: 替换API
        thread2 = threading.Thread(target=self.checkPingThread, args=("aicodingassiatant.cn", self.bangumiPing)) # TODO: 替换API
        thread1.start()
        thread2.start()

    def checkPingThread(self, url, label):
        for retry in range(3):
            try:
                response = requests.get(f"http://{url}/")
                if response.status_code == 200:
                    label.setText("Online")
                    return
            except requests.ConnectionError:
                pass
            time.sleep(0.1)
        label.setText("Offline")
        label.setStyleSheet("color: #F44336")

class MySettingWindow(QDialog, SettingWindow):
    save_notice = Signal(str)

    def __init__(self):
        super().__init__()
        self.setupUI(self)
        self.initConnect()
        self.config = readConfig()
        self.loadConfig()

    def initConnect(self):
        self.posterFolderButton.clicked.connect(self.openCodingFrameworkFolder)
        self.logFolderButton.clicked.connect(self.openLogFolder)
        self.applyButton.clicked.connect(self.saveConfig)  # 保存配置
        self.cancelButton.clicked.connect(lambda: self.close())  # 关闭窗口

    def loadConfig(self):
        self.modelType.setText(self.config.get("AICO", "model"))
        self.modelApiKey.setText(self.config.get("APIkey", "api_key"))

    def saveConfig(self):
        self.config.set("AICO", "model", self.modelType.currentText())
        self.config.set("APIkey", "api_key", self.modelApiKey.text())

        with open(configFile(), "w", encoding="utf-8") as content:
            self.config.write(content)

        self.save_notice.emit("配置已保存")
        self.close()

    def openCodingFrameworkFolder(self):
        openFolder(codingFrameworkFolder())

    def openLogFolder(self):
        openFolder(logFolder())

