import sys
import time
from PySide6.QtWidgets import QApplication, QMenu
from PySide6.QtGui import QAction
from PySide6.QtCore import QLocale
from qfluentwidgets import FluentTranslator

from src.core import MyMainWindow, Window
from src.function import log, loadLanguage
from src.module.version import currentVersion
from src.module.config import readConfig

if __name__ == "__main__":
    log("=============================")
    log("AICodingOfficer启动")
    log(f"当前版本：{currentVersion()}")

    app = QApplication(sys.argv)

    # # 默认加载系统语言
    # configLanguage = readConfig().get("Language", "language")
    # if configLanguage == "简体中文":
    #     systemLanguage = "zh_CN"
    # else:
    #     systemLanguage = "en_US"
    # # systemLanguage = QLocale.system().name()
    # loadLanguage(app, systemLanguage)

    # translator = FluentTranslator()
    # app.installTranslator(translator)
    
    # window = MyMainWindow()
    window = Window()
    window.show()

    app.exec()
