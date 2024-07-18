import os
import time
import threading
import shutil
import arrow
import json
import requests
import pandas as pd
import sqlite3

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
from src.gui.autocodingwindow import AutoCodingWindow

from src.function import log, readCSV, initList, addTimes, openFolder, loadLanguage
from src.module.coding import AICodingWorkerThread, fetch_data_from_database, worker
from src.module.config import configFile, localDBFilePath, logFolder, readConfig, oldConfigCheck, exportCodingResultPath
from src.module.localDB import localDB
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

        self.icon_win_path = getResource("src/image/icon_win.png")
        self.setTitleBar(StandardTitleBar(self))

        self.hBoxLayout = QHBoxLayout(self)
        self.navigationInterface = NavigationInterface(self, showMenuButton=True)
        self.stackWidget = QStackedWidget(self)

        # create sub interface
        self.myAutoCodingWindow = MyAutoCodingWindow()
        self.stackWidget.addWidget(self.myAutoCodingWindow)

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
        self.navigationInterface.setExpandWidth(150)

        self.navigationInterface.addItem('MyAutoCodingWindow', FIF.ROBOT, '自动编码', lambda: self.switchTo(self.myAutoCodingWindow))
        
        # TODO: 优化导航栏，添加手动编码功能
        # self.navigationInterface.addItem('MyMainWindow', FIF.CODE, '手动', lambda: self.switchTo(self.myMainWindow))
        self.navigationInterface.addSeparator()

        self.navigationInterface.addWidget(
            routeKey='avatar',
            widget=NavigationAvatarWidget('作者', self.icon_win_path),
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
        self.setWindowIcon(QIcon(self.icon_win_path))
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
            '您的支持就是作者开发和维护项目的动力🚀',
            self
        )

        w.yesButton.setText('来啦老弟')
        w.cancelButton.setText('下次一定')

        if w.exec():
            QDesktopServices.openUrl(QUrl("https://xiaojianjun.cn"))

class MyMainWindow(QMainWindow, MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUI(self)
        self.initConnect()
        self.initList()
        self.checkVersion()

        self.localDBFunc = localDB()

        oldConfigCheck()
        addTimes("open_times")
        self.config = readConfig()
        self.local_db_file_path = localDBFilePath()

    def initConnect(self):
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)  # 自定义右键菜单
        self.table.customContextMenuRequested.connect(self.showRightClickMenu)
        self.table.itemSelectionChanged.connect(self.selectTable)

        self.searchList.setContextMenuPolicy(Qt.CustomContextMenu)  # 自定义右键菜单 - 编码代码，方便修改
        self.searchList.customContextMenuRequested.connect(self.showRightClickMenu2)

        self.newVersionButton.clicked.connect(self.openRelease)
        self.aboutButton.clicked.connect(self.openAbout)
        self.settingButton.clicked.connect(self.openSetting)

        self.singleCodingButton.clicked.connect(self.singleCoding)
    
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

    def singleCoding(self):
        print("单个编码")
        pass

class MyAutoCodingWindow(QMainWindow, AutoCodingWindow):
    def __init__(self):
        super().__init__()
        self.setupUI(self)
        self.initConnect()
        oldConfigCheck()
        addTimes("open_times")
        self.config = readConfig()

        self.localDBFunc = localDB()

        # 检查本地数据
        self.has_coding_count, self.no_coding_count = len(self.localDBFunc.readPromptFromLocalDB(True)), len(self.localDBFunc.readPromptFromLocalDB(False))
        self.updateLogContent('[Notice] [' + arrow.now().format("YYYY-MM-DD HH:mm:ss") + "] [检查本地数据]：加载本地数据{}条".format(self.has_coding_count + self.no_coding_count))
        self.updateLogContent('[Notice] [' + arrow.now().format("YYYY-MM-DD HH:mm:ss") + "] [检查本地数据]：已编码{}条，未编码{}条".format(self.has_coding_count, self.no_coding_count))

        self.local_db_file_path = localDBFilePath()
        self.topicFilePath = self.topicInfo.text()
        self.replyFilePath = self.replyInfo.text()
        self.codingSchemePath = self.schemaInfo.text()

        self.doingCoding = False

        # 数据
        self.topics = pd.DataFrame()
        self.replys = pd.DataFrame()
        self.codingScheme = pd.DataFrame()

        self.db_path = self.local_db_file_path
        self.conn = sqlite3.connect(self.db_path)

        self.texts = [
            '随着科技的飞速发展，人工智能（AI）已经成为我们日常生活中不可或缺的一部分。...',
            '最开始在使用Chatgpt的时候，如果你像用百度或者google一样提问，会发现它并不会给你带来特别惊艳的地方...',
            'Chatgpt类型的Ai工具不是搜索引擎，而是生产工具，目前对教师的备课可以起到重要的作用。',
            '@张建鑫：它不会替代你思考，可以帮助你思考的更多面向。'
        ]
        self.limit = 10 # 默认编码10条测试数据

    def initConnect(self):
        self.newVersionButton.clicked.connect(self.openRelease)
        self.aboutButton.clicked.connect(self.openAbout)
        self.settingButton.clicked.connect(self.openSetting)

        self.loadDataButton.clicked.connect(self.loadData)
        self.standardCodingButton.clicked.connect(self.standardCoding)
        self.stopCodingButton.clicked.connect(self.stopCoding)
        self.exportCodingResultButton.clicked.connect(self.exportCodingResult)
        self.testCodingButton.clicked.connect(self.testCoding)

        self.updateLogContent('[Notice] [' + arrow.now().format("YYYY-MM-DD HH:mm:ss") + "] [初始化]：初始化成功")
        self.updateLogContent('[Notice] [' + arrow.now().format("YYYY-MM-DD HH:mm:ss") + "] [初始化]：当前版本{}".format(currentVersion()))
        self.updateLogContent('[Notice] [' + arrow.now().format("YYYY-MM-DD HH:mm:ss") + "] [初始化]：示例数据下载及教程地址：{}".format('https://xiaojianjun.cn/aicodingofficer/'))

    def loadData(self):
        if self.doingCoding:
            self.showInfo("warning", "警告", "编码正在进行中，请勿重复加载数据")
            return
        if self.topicFilePath == '':
            self.showInfo("error", "错误", "请先选择话题文件")
            return
        if self.replyFilePath == '':
            self.showInfo("error", "错误", "请先选择回复文件")
            return
        if self.codingSchemePath == '':
            self.showInfo("error", "错误", "请先选择编码方案文件")
            return
        
        self.topics = pd.read_csv(self.topicFilePath, encoding='utf-8', index_col=0)
        self.replys = pd.read_csv(self.replyFilePath, encoding='utf-8', index_col=0)
        self.codingScheme = pd.read_csv(self.codingSchemePath, encoding='utf-8')
        _keys = self.codingScheme['code'].to_list()
        for key in _keys:
            self.replys[key] = ''
        self.prepare_prompt()
        self.showInfo("success", "成功", "数据加载成功")
        self.standardCodingButton.setEnabled(True)

        self.topics.to_sql('topics', self.conn, if_exists='replace', index=True)
        self.replys.to_sql('replys', self.conn, if_exists='replace', index=True)
        self.codingScheme.to_sql('coding_scheme', self.conn, if_exists='replace')

    def prepare_prompt(self):
        # self.topic_df = pd.read_sql('select * from topics', self.conn, index_col=0)
        # self.reply_df = pd.read_sql('select * from replys', self.conn, index_col=0)
        # self.coding_scheme_df = pd.read_sql('select * from coding_scheme', self.conn)
        self.topic_df = self.topics
        self.reply_df = self.replys
        self.coding_scheme_df = self.codingScheme
        
        code_keys = self.coding_scheme_df['code'].to_list()
        code_temp_df = pd.DataFrame(0, index=self.reply_df.index.to_list(), columns=code_keys)
        self.coding_result_df = pd.merge(self.reply_df, code_temp_df, left_index=True, right_index=True)

        topic_reply_tree_dict = {}
        has_process_reply_id_lst = []
        check_reply_count = 0
        for index, row in self.topic_df.iterrows():
            topic_id = row['topic_id']
            topic_desc = row['topic_title'] + row['topic_content']
            topic_reply_tree_dict[topic_id] = {'topic_desc': topic_desc,'reply_tree': []}
            for index, row in self.reply_df[self.reply_df['topic_id'] == topic_id].iterrows():
                reply_id = row['reply_id']
                if reply_id in has_process_reply_id_lst:
                    continue
                reply_desc = '- ' + row['user_name'] + '(reply_id:' + str(reply_id) + ')：' + row['reply_content']
                topic_reply_tree_dict[topic_id]['reply_tree'].append({'reply_id': reply_id, 'reply_desc': reply_desc, 'reply_tree': []})
                check_reply_count += 1
                has_process_reply_id_lst.append(reply_id)
                for index, row in self.reply_df[self.reply_df['to_reply_id'] == reply_id].iterrows():
                    reply_id = row['reply_id']
                    if reply_id in has_process_reply_id_lst:
                        continue
                    reply_desc = '- ' + row['user_name'] + '(reply_id:' + str(reply_id) + ')：' + row['reply_content']
                    topic_reply_tree_dict[topic_id]['reply_tree'][-1]['reply_tree'].append({'reply_id': reply_id, 'reply_desc': reply_desc})
                    check_reply_count += 1
                    has_process_reply_id_lst.append(reply_id)

        prompt_dict = {
            'prompt_content': [],
        }

        for topic_id in topic_reply_tree_dict:
            for reply_tree in topic_reply_tree_dict[topic_id]['reply_tree']:
                prompt_content = r"""您将看到一组论坛中的话题和回帖，您的任务是优先根据下面的编码表中的含义解释对每个回帖提取一组标签“codes”（只有当编码表中没有合适的标签时才输出“NULL”），并以中文举例说明提取标签的理由，注意将理由翻译为中文列出。结果以JSON格式的数组输出：[{"reply_id":"1234","tags":[],"reason":[]},{"reply_id":"2345","tags":[],"reason":[]}]，注意只输出JSON，不要包括其他内容!tags和reason中的内容一一对应，请根据实际情况填写，不要直接复制粘贴。
                编码表：\n
                """
                prompt_content += r"""
                {encode_table_latex}
                \n\n话题：\n
                """.format(encode_table_latex=self.coding_scheme_df.to_latex(index=False))
                topic_desc = topic_reply_tree_dict[topic_id]['topic_desc']
                prompt_content += topic_desc + '\n\n回帖：\n'
                if len(reply_tree['reply_tree']) == 0:
                    prompt_content += reply_tree['reply_desc'] + '\n\n'
                else:
                    prompt_content += reply_tree['reply_desc'] + '\n'
                    for reply_tree_2 in reply_tree['reply_tree']:
                        prompt_content += reply_tree_2['reply_desc'] + '\n'
                    prompt_content += '\n'
                prompt_dict['prompt_content'].append(prompt_content)

        self.prompt_df = pd.DataFrame(prompt_dict)
        self.prompt_df['prompt_code'] = 'None'
        self.prompt_df['prompt_code_orign'] = 'None'
        self.prompt_df.to_sql('prompt', self.conn, if_exists='replace', index=True)

    def testCoding(self):
        if not self.doingCoding:
            self.limit = 10 # 批量编码测试数据
            self.worker = AICodingWorkerThread(self.limit)
            self.worker.output_signal.connect(self.updateLogContent)
            self.worker.running_signal.connect(self.lisenToWorker)
            t = '[Notice] [' + arrow.now().format("YYYY-MM-DD HH:mm:ss") + "] [开始测试编码]：10条"
            self.updateLogContent(t)
            self.doingCoding = True
            self.stopCodingButton.setEnabled(True)
            self.testCodingButton.setEnabled(False)
            self.worker.start()
        else:
            self.showInfo("warning", "警告", "编码正在进行中，请勿重复点击")

    def standardCoding(self):
        if not self.doingCoding:
            self.limit = -1 # 批量编码所有数据
            self.worker = AICodingWorkerThread(self.limit)
            self.worker.output_signal.connect(self.updateLogContent)
            self.worker.running_signal.connect(self.lisenToWorker)
            t = '[Notice] [' + arrow.now().format("YYYY-MM-DD HH:mm:ss") + "] [开始编码]"
            self.updateLogContent(t)
            self.doingCoding = True
            self.stopCodingButton.setEnabled(True)
            self.standardCodingButton.setEnabled(False)
            self.worker.start()
        else:
            self.showInfo("warning", "警告", "编码正在进行中，请勿重复点击")

    def lisenToWorker(self, state):
        self.doingCoding = state
        self.stopCodingButton.setEnabled(state)
        self.standardCodingButton.setEnabled(not state)
        self.testCodingButton.setEnabled(not state)
        if not state:
            self.updateLogContent('[Notice] [' + arrow.now().format("YYYY-MM-DD HH:mm:ss") + "] [编码已停止]")
            has_coding_count = len(self.localDBFunc.readPromptFromLocalDB(True))
            no_coding_count = len(self.localDBFunc.readPromptFromLocalDB(False))
            self.updateLogContent('[Notice] [' + arrow.now().format("YYYY-MM-DD HH:mm:ss") + "] [编码统计]：当前编码{}条，剩余{}条".format(has_coding_count, no_coding_count))

    def stopCoding(self):
        if self.doingCoding:
            self.worker.stop()
            self.lisenToWorker(False)

    def exportCodingResult(self):
        if self.doingCoding:
            self.showInfo("warning", "警告", "编码正在进行中，请等待编码完成后再导出")
            return
        coding_result_df = pd.read_sql('select * from prompt', self.conn)
        coding_result_df.index = coding_result_df['index']
        reply_df = pd.read_sql('select * from replys', self.conn)
        reply_df.index = reply_df['reply_id']
        # 解析编码结果
        success_count = 0
        fail_count = 0
        for index, row in coding_result_df.iterrows():
            if row['prompt_code'] != 'None':
                try:
                    code_response_lst = json.loads(row['prompt_code'])
                    for code_response in code_response_lst:
                        code_res = code_response
                        reply_id = int(code_res['reply_id'])
                        tags_lst = code_res['tags']
                        reasons_lst = code_res['reason']
                        reason_str = " | ".join(reasons_lst)
                        for i in range(len(tags_lst)):
                            tag = tags_lst[i]
                            reply_df.loc[reply_id, tag] = 1
                            reply_df.loc[reply_id, 'reason'] = reason_str
                            success_count += 1
                except Exception as e:
                    print(f"编码结果解析失败: {e}")
                    fail_count += 1
        log(f"编码结果解析成功: {success_count} 条, 失败: {fail_count} 条")
        self.updateLogContent("[Notice] [{}] [编码结果解析成功: {success_count} 条, 失败: {fail_count} 条]".format(arrow.now().format('YYYY-MM-DD HH:mm:ss'), success_count=success_count, fail_count=fail_count))
        self.updateLogContent("[Notice] [{}] [编码结果导出中...]".format(arrow.now().format('YYYY-MM-DD HH:mm:ss')))
        save_path = exportCodingResultPath()
        self.updateLogContent("[Notice] [{}] [编码结果导出路径]: {}".format(arrow.now().format('YYYY-MM-DD HH:mm:ss'), save_path))
        reply_df.to_csv(save_path, encoding='utf-8-sig')
        if os.path.exists(save_path):
            self.showInfo("success", "成功", "编码结果导出成功，正在打开文件，请稍后...")
            openFolder(save_path)
        else:
            self.showInfo("error", "错误", "编码结果导出失败")
        self.testCodingButton.setEnabled(True)
        self.standardCodingButton.setEnabled(True)

    def updateLogContent(self, message):
        self.logContent.append(message)
        self.logContent.verticalScrollBar().setValue(self.logContent.verticalScrollBar().maximum())

    def showProgressBar(self):
        self.progress.setVisible(True)
        self.progress.setMaximum(len(self.texts) * 3)

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
        self.showInfo("success", title, "配置修改成功")
    
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

class MyAboutWindow(QDialog, AboutWindow):
    def __init__(self):
        super().__init__()
        self.setupUI(self)
        self.checkPing()
        self.config = readConfig()
        self.loadConfig()

    def loadConfig(self):
        owner = "etShaw-zh"
        repo = "AICodingAssistant-Pro"
        try:
            repo_data = self.get_repo_info(owner, repo)
            releases = self.get_releases_info(owner, repo)
            download_times = self.count_downloads(releases)
            self.downloadTimes.setText(str(download_times))  
            self.starCount.setText(str(repo_data["star_count"]))  
        except Exception as e:
            print(f"加载配置失败: {e}")
            self.downloadTimes.setText("Error")
            self.starCount.setText("Error")
        # self.openTimes.setText(self.config.get("Counter", "open_times"))
        # self.analysisTimes.setText(self.config.get("Counter", "analysis_times"))

    def get_repo_info(self, username, repo_name):
        url = f"https://api.github.com/repos/{username}/{repo_name}"
        response = requests.get(url)
        if response.status_code == 200:
            repo_data = response.json()
            return {
                "star_count": repo_data["stargazers_count"],
                "fork_count": repo_data["forks_count"],
                "watch_count": repo_data["watchers_count"]
            }
        else:
            return f"Error: {response.status_code} - {response.reason}"
        
    def get_releases_info(self, username, repo_name):
        url = f"https://api.github.com/repos/{username}/{repo_name}/releases"
        response = requests.get(url)
        if response.status_code == 200:
            releases_data = response.json()
            return releases_data
        else:
            return f"Error: {response.status_code} - {response.reason}"

    def count_downloads(self, releases):
        total_downloads = 0
        for release in releases:
            for asset in release.get('assets', []):
                total_downloads += asset['download_count']
        return total_downloads

    def checkPing(self):
        thread1 = threading.Thread(target=self.checkPingThread, args=("www.moonshot.cn", self.anilistPing)) # TODO: 替换API
        thread2 = threading.Thread(target=self.checkPingThread, args=("aicodingassistant.cn", self.bangumiPing)) # TODO: 替换API
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
        self.localDBButton.clicked.connect(self.openLocalDBFilePath)
        self.logFolderButton.clicked.connect(self.openLogFolder)
        self.applyButton.clicked.connect(self.saveConfig)  # 保存配置
        self.cancelButton.clicked.connect(lambda: self.close())  # 关闭窗口

    def loadConfig(self):
        self.modelType.setText(self.config.get("AICO", "model"))
        self.modelApiKey.setText(self.config.get("APIkey", "api_key"))
        self.language.setText(self.config.get("Language", "language"))
        self.threadCount.setText(self.config.get("Thread", "thread_count"))

    def saveConfig(self):
        self.config.set("AICO", "model", self.modelType.currentText())
        self.config.set("APIkey", "api_key", self.modelApiKey.text())
        self.config.set("Language", "language", self.language.currentText())
        self.config.set("Thread", "thread_count", self.threadCount.text())

        with open(configFile(), "w", encoding="utf-8") as content:
            self.config.write(content)

        self.save_notice.emit("配置已保存")
        self.close()

    def openLocalDBFilePath(self):
        openFolder(localDBFilePath())

    def openLogFolder(self):
        openFolder(logFolder())

