import pandas as pd
import sqlite3
from src.module.config import localDBFilePath

class localDB():
    def __init__(self) -> None:
        self.db_path = localDBFilePath()
        self.conn = sqlite3.connect(self.db_path)

    # 检查数据库是否存在，不存在则创建数据库
    def checkDB(self):
        try:
            self.conn.execute("select * from prompt")
            self.conn.commit()
        except:
            self.conn.execute("""
            CREATE TABLE 'prompt' (
                'index' INTEGER,
                'prompt_content' TEXT,
                'prompt_code' TEXT,
                'prompt_code_orign' TEXT
            )
            """)
            self.conn.execute("""
            CREATE TABLE 'reply' (
                'index' INTEGER,
                'user_id' INTEGER,
                'user_name' TEXT,
                'reply_content' TEXT,
                'topic_id' INTEGER,
                'reply_id' INTEGER,
                'to_reply_id' INTEGER,
                'reason' TEXT
            )
            """)
            self.conn.commit()

    def readPromptFromLocalDB(self, has_coding = False):
        if has_coding:
            data = pd.read_sql('select * from prompt where prompt_code != "None"', self.conn)
        else:
            data = pd.read_sql('select * from prompt where prompt_code = "None"', self.conn)
        return data