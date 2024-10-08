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
from src.module.localDB import localDB

if __name__ == "__main__":
    log("=============================")
    log("AICodingOfficer lunched")
    log(f"Current version: {currentVersion()}")

    app = QApplication(sys.argv)

    db = localDB()
    db.checkDB()

    # 默认加载系统语言
    configLanguage = readConfig().get("Language", "language")
    if configLanguage == "Chinese":
        systemLanguage = "zh_CN"
    else:
        systemLanguage = "en_US"
    # systemLanguage = QLocale.system().name()
    loadLanguage(app, systemLanguage)

    translator = FluentTranslator()
    app.installTranslator(translator)

    # window = MyMainWindow()
    window = Window()
    window.show()

    app.exec()
