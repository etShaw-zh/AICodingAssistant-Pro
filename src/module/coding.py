import os
import arrow
import threading

from PySide6.QtCore import QObject, Signal

from src.module.api import *
from src.module.config import codingFrameworkFolder, readConfig

class AICoding(QObject):
    main_state = Signal(str)
    coding_state = Signal(list)
    added_progress_count = Signal(int)

    # TODO: 批量编码
    def standardCoding(self, texts):
        config = readConfig()
        pass

    # TODO: 单个编码
    def singleCoding(self, text):
        config = readConfig()
        pass


def getFinalName(anime):
    config = readConfig()
    data_format = config.get("Format", "date_format")
    rename_format = config.get("Format", "rename_format")

    final_name = eval(f'f"{rename_format}"')
    anime["final_name"] = final_name
