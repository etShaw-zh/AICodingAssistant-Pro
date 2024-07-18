import pandas as pd
import sqlite3
from src.module.config import localDBFilePath

class localDB():
    def __init__(self) -> None:
        self.db_path = localDBFilePath()
        self.conn = sqlite3.connect(self.db_path)

    def readPromptFromLocalDB(self, has_coding = False):
        if has_coding:
            data = pd.read_sql('select * from prompt where prompt_code != "None"', self.conn)
        else:
            data = pd.read_sql('select * from prompt where prompt_code == "None"', self.conn)
        return data