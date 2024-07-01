import sys
from PySide6.QtWidgets import QApplication, QMenu
from PySide6.QtGui import QAction
from PySide6.QtCore import QTranslator, QLocale
from qfluentwidgets import FluentTranslator

from src.core import MyMainWindow, Window
from src.function import log
from src.module.version import currentVersion

def loadLanguage(app, language):
    translator = QTranslator(app)
    if translator.load(f"./i18n/{language}.qm"):
        log(f"加载语言文件：{language}")
        app.installTranslator(translator)
    else:
        log(f"加载语言文件失败：{language}")

if __name__ == "__main__":
    log("=============================")
    log("AICodingOfficer启动")
    log(f"当前版本：{currentVersion()}")

    app = QApplication(sys.argv)

    # 默认加载系统语言
    systemLanguage = QLocale.system().name()
    loadLanguage(app, systemLanguage)

    translator = FluentTranslator()
    app.installTranslator(translator)
    
    # window = MyMainWindow()
    window = Window()

    # 创建语言切换菜单
    languageMenu = QMenu("语言", window)
    actionCN = QAction("简体中文", window)
    actionEN = QAction("English", window)
    languageMenu.addAction(actionCN)
    languageMenu.addAction(actionEN)
    # window.menuBar().addMenu(languageMenu)

    # 连接菜单动作的信号与槽
    actionCN.triggered.connect(lambda: loadLanguage(app, "zh_CN"))
    actionEN.triggered.connect(lambda: loadLanguage(app, "en_US"))

    window.show()
    app.exec()
