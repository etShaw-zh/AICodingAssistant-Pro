import time
import arrow
import json
import sqlite3
import requests
import threading
from PySide6.QtCore import QObject, Signal, QThread
from queue import Queue
from src.module.config import localDBFilePath, readConfig

class AICodingWorkerThread(QThread):
    output_signal = Signal(str)
    running_signal = Signal(bool)

    def __init__(self, texts):
        super().__init__()
        self.texts = texts
        self.THREAD_COUNT = readConfig().getint("Thread", "thread_count")
        self.thread_results = {}
        self.local_db_file_path = localDBFilePath()
        self.DATABASE_PATH = self.local_db_file_path
        self.TABLE_NAME = "prompt"
        self.LABEL_COLUMN_NAME = "prompt_code"
        self.LIMIT = -1
        self.DEFAULT_NODE_RECOGNITION_PROMPT = ""
        self._stop_event = threading.Event()

    def run(self):
        self._stop_event.clear() # 重置停止事件
        self.running_signal.emit(True)
        self.output_signal.emit('[Notice] [' + arrow.now().format("YYYY-MM-DD HH:mm:ss") + "]  [开始编码]")

        main_coding(self._stop_event, self.output_signal, self.thread_results, self.THREAD_COUNT, self.DATABASE_PATH, self.TABLE_NAME, self.LABEL_COLUMN_NAME, self.LIMIT, self.DEFAULT_NODE_RECOGNITION_PROMPT)

        self.output_signal.emit('[Notice] [' + arrow.now().format("YYYY-MM-DD HH:mm:ss") + ']  [编码完成]')

    def stop(self):
        self._stop_event.set()

def send_request(url, headers, data):
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # 将触发异常的HTTP错误
        return response.json()
    except requests.exceptions.HTTPError as e:
        error_code = e.response.status_code
        error_message = e.response.json().get("error", {}).get("message", "未知错误")
        return {"error": f"HTTP {error_code}", "message": error_message}
    except requests.exceptions.RequestException as e:
        return {"error": "网络错误", "message": str(e)}
    except Exception as e:
        return {"error": "未知错误", "message": str(e)}

def get_code_from_gpt(output_signal, prompt_content):
    MOONSHOT_API_KEY = readConfig().get("APIkey", "api_key")
    url = 'https://api.moonshot.cn/v1/chat/completions' 

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {MOONSHOT_API_KEY}'
    }

    data = {
        "model": "moonshot-v1-8k",
        "messages": [{"role": "user", "content": prompt_content}],
        "temperature": 0.3,
        "max_tokens": 1000,
    }

    response = send_request(url, headers, data)
    if 'error' in response:
        output_signal.emit("[Notice] [GPT返回]：" + str(response))
        time.sleep(10)
        return None
    return response

def parse_gpt_response(output_signal, response):
    try:
        res = response['choices'][0]['message']['content'].replace('```json', '').replace('```', '').replace(' ', '').replace('\n', '')
        return str(res)
    except Exception as e:
        print(e)
        return 'None'

def encode_data(output_signal, record, default_node_recognition_prompt, label):
    prompt_content = default_node_recognition_prompt + record['prompt_content']
    res = get_code_from_gpt(output_signal, prompt_content)
    return {
        'index': record['index'],
        label: parse_gpt_response(output_signal, res),
        'orign_response': str(res)
    }

def worker(stop_event, output_signal, input_queue, output_dict, db_path, table_name, label, default_node_recognition_prompt):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    while not input_queue.empty():
        if stop_event.is_set():
            break
        record = input_queue.get()
        output_signal.emit("[Notice] [当前线程]：{}，当前还有{}条数据未处理".format(threading.current_thread().name, input_queue.qsize()))
        try:
            encoded_record = encode_data(output_signal, record, default_node_recognition_prompt, label)
            if encoded_record[label] != 'None':
                cursor.execute("UPDATE {} SET `{}` = ?, `prompt_code_orign` = ? WHERE `index` = ?".format(table_name, label),
                               (encoded_record[label], encoded_record['orign_response'], encoded_record['index']))
                conn.commit()
                output_dict[encoded_record['index']] = encoded_record
            else:
                output_signal.emit("[Notice] [编码失败]：无法从GPT获取代码")
        except sqlite3.Error as e:
            print("An error occurred:", e.args[0])
    conn.close()

def fetch_data_from_database(db_path, table_name, label, limit=-1):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        if limit == -1:
            cursor.execute('SELECT * FROM {} WHERE prompt_content > 0 AND `{}` = "None"'.format(table_name, label))
        else:
            cursor.execute('SELECT * FROM {} WHERE prompt_content > 0 AND `{}` = "None" LIMIT {}'.format(table_name, label, limit))
        columns = [column[0] for column in cursor.description]
        records = cursor.fetchall()
        data_list = [dict(zip(columns, record)) for record in records]
    finally:
        conn.close()
    return data_list

def main_coding(stop_event, output_signal, thread_results, THREAD_COUNT, DATABASE_PATH, TABLE_NAME, LABEL_COLUMN_NAME, LIMIT, DEFAULT_NODE_RECOGNITION_PROMPT):
    input_queue = Queue()
    data_list = fetch_data_from_database(DATABASE_PATH, TABLE_NAME, LABEL_COLUMN_NAME, LIMIT)

    for record in data_list:
        input_queue.put(record)
    threads = []

    for _ in range(THREAD_COUNT):
        t = threading.Thread(target=worker, args=(stop_event, output_signal, input_queue, thread_results, DATABASE_PATH, TABLE_NAME, LABEL_COLUMN_NAME, DEFAULT_NODE_RECOGNITION_PROMPT))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    output_signal.emit("[Notice] 总共还有{}条数据未处理".format(len(fetch_data_from_database(DATABASE_PATH, TABLE_NAME, LABEL_COLUMN_NAME))))