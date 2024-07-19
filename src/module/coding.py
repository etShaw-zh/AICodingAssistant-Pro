import time
import arrow
import json
import sqlite3
import requests
import threading
from PySide6.QtCore import QObject, Signal, QThread
from queue import Queue
from src.module.config import localDBFilePath, readConfig

language = readConfig().get("Language", "language")

class AICodingWorkerThread(QThread):
    output_signal = Signal(str)
    running_signal = Signal(bool)

    def __init__(self, limit):
        super().__init__()
        self.THREAD_COUNT = readConfig().getint("Thread", "thread_count")
        self.LIMIT = limit
        self.thread_results = {}
        self.local_db_file_path = localDBFilePath()
        self.DATABASE_PATH = self.local_db_file_path
        self.TABLE_NAME = "prompt"
        self.LABEL_COLUMN_NAME = "prompt_code"
        self.DEFAULT_NODE_RECOGNITION_PROMPT = ""
        self._stop_event = threading.Event()

    def run(self):
        self._stop_event.clear() # 重置停止事件
        self.running_signal.emit(True)
        main_coding(self._stop_event, self.output_signal, self.thread_results, self.THREAD_COUNT, self.DATABASE_PATH, self.TABLE_NAME, self.LABEL_COLUMN_NAME, self.LIMIT, self.DEFAULT_NODE_RECOGNITION_PROMPT)
        self.running_signal.emit(False)

    def stop(self):
        self._stop_event.set()
        self.wait()

    def __del__(self):
        self.stop()

def send_request(url, headers, data):
    error_type_description = {
        "content_filter": "内容审查拒绝，您的输入或生成内容可能包含不安全或敏感内容，请您避免输入易产生敏感内容的提示语，谢谢",
        "invalid_request_error": "请求无效，通常是您请求格式错误或者缺少必要参数，请检查后重试",
        "invalid_authentication_error": "鉴权失败，请检查 apikey 是否正确，请修改后重试",
        "exceeded_current_quota_error": "账户异常，请检查您的账户余额",
        "permission_denied_error": "访问其他用户信息的行为不被允许，请检查",
        "resource_not_found_error": "不存在此模型或者没有授权访问此模型，请检查后重试",
        "engine_overloaded_error": "当前并发请求过多，节点限流中，请稍后重试；建议充值升级 tier，享受更丝滑的体验",
        "exceeded_current_quota_error": "账户额度不足，请检查账户余额，保证账户余额可匹配您 tokens 的消耗费用后重试",
        "rate_limit_reached_error": "请求触发了账户并发个数的限制，请等待指定时间后重试",
        "server_error": "解析文件失败，请重试",
        "unexpected_output": "内部错误，请联系管理员",
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # 将触发异常的HTTP错误
        return response.json()
    except requests.exceptions.HTTPError as e:
        error_code = e.response.status_code
        if language == "Chinese":
            error_type = e.response.json().get("error", {}).get("type", "未知错误")
            error_message = e.response.json().get("error", {}).get("message", "未知错误")
            response_message = {"error": f"HTTP {error_code}", "message": error_message, "description": error_type_description.get(error_type, "未知错误")}
        else:
            error_type = e.response.json().get("error", {}).get("type", "unknown error")
            error_message = e.response.json().get("error", {}).get("message", "unknown error")
            response_message = {"error": f"HTTP {error_code}", "message": error_message, "description": error_type_description.get(error_type, "unknown error")}
        return response_message
    except requests.exceptions.RequestException as e:
        if language == "Chinese":
            return {"error": "网络错误", "message": str(e)}
        else:
            return {"error": "Network error", "message": str(e)}
    except Exception as e:
        if language == "Chinese":
            return {"error": "未知错误", "message": str(e)}
        else:
            return {"error": "unknown error", "message": str(e)}

def get_code_from_gpt(output_signal, prompt_content):
    MOONSHOT_API_KEY = readConfig().get("APIkey", "api_key")
    MODEL_TYPE = readConfig().get("AICO", "model")
    url = 'https://api.moonshot.cn/v1/chat/completions' 

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {MOONSHOT_API_KEY}'
    }

    data = {
        "model": MODEL_TYPE,
        "messages": [
            {
                "role": "system",
                "content": "您将看到一组论坛中的话题和回帖，您的任务是优先根据下面的编码表中的含义解释对每个回帖提取一组标签，并在一组 JSON 对象中输出。",
            },
            {
                "role": "user", 
                "content": prompt_content,
                "partial": True
            },
            # {
            #     "role": "assistant",
            #     "content": "",
            #     "partial": True
            # },
            ],
        "temperature": 0.3,
        "max_tokens": 1000,
    }

    response = send_request(url, headers, data)
    if 'error' in response:
        if language == "Chinese":
            output_signal.emit("[提示] [" + arrow.now().format('YYYY-MM-DD HH:mm:ss') + "] [GPT 返回]：" + str(response))
        else:
            output_signal.emit("[Notice] [" + arrow.now().format('YYYY-MM-DD HH:mm:ss') + "] [GPT returned]：" + str(response))
        time.sleep(1)
        return None
    return response

def parse_gpt_response(response):
    try:
        res = response['choices'][0]['message']['content'].replace('```json', '').replace('```', '').replace(' ', '').replace('\n', '')
        return str(res)
    except Exception as e:
        print('parse_gpt_response ', e)
        return 'None'

def encode_data(output_signal, record, default_node_recognition_prompt, label):
    prompt_content = default_node_recognition_prompt + record['prompt_content']
    response = get_code_from_gpt(output_signal, prompt_content)
    return {
        'index': record['index'],
        label: 'None' if response == None else parse_gpt_response(response),
        'orign_response': str(response)
    }

def worker(stop_event, output_signal, input_queue, output_dict, db_path, table_name, label, default_node_recognition_prompt):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    while not input_queue.empty():
        if stop_event.is_set():
            break
        record = input_queue.get()
        if language == "Chinese":
            output_signal.emit("[提示] [{}] [当前线程]：{}，剩余 {} 项待处理".format(arrow.now().format('YYYY-MM-DD HH:mm:ss'), threading.current_thread().name, input_queue.qsize()))
        else:
            output_signal.emit("[Notice] [{}] [Current thread]: {}，remaining {} items to process".format(arrow.now().format('YYYY-MM-DD HH:mm:ss'), threading.current_thread().name, input_queue.qsize()))
        try:
            encoded_record = encode_data(output_signal, record, default_node_recognition_prompt, label)
            if encoded_record[label] != 'None':
                cursor.execute("UPDATE {} SET `{}` = ?, `prompt_code_orign` = ? WHERE `index` = ?".format(table_name, label),
                               (encoded_record[label], encoded_record['orign_response'], encoded_record['index']))
                conn.commit()
                output_dict[encoded_record['index']] = encoded_record
            else:
                if language == "Chinese":
                    output_signal.emit("[提示] [" + arrow.now().format('YYYY-MM-DD HH:mm:ss') + "] [编码失败]：无法从 GPT 获取编码")
                else:
                    output_signal.emit("[Notice] [" + arrow.now().format('YYYY-MM-DD HH:mm:ss') + "] [Encoding failed]: Unable to get code from GPT")
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

    if language == "Chinese":
        output_signal.emit("[提示] [{}] [编码统计]：剩余 {} 项待处理".format(arrow.now().format('YYYY-MM-DD HH:mm:ss'), len(fetch_data_from_database(DATABASE_PATH, TABLE_NAME, LABEL_COLUMN_NAME))))
    else:
        output_signal.emit("[Notice] [{}] [Coding statistics]：Total {} items remaining to be processed".format(arrow.now().format('YYYY-MM-DD HH:mm:ss'), len(fetch_data_from_database(DATABASE_PATH, TABLE_NAME, LABEL_COLUMN_NAME))))