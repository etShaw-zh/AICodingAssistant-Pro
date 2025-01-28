import re
import time
import arrow
import json
import sqlite3
import threading
from PySide6.QtCore import QObject, Signal, QThread
from queue import Queue, Empty
from src.module.config import localDBFilePath, readConfig
from src.module.aihubmix import AiHubMixAPI

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
        self._stop_event.clear()
        self.running_signal.emit(True)
        main_coding(self._stop_event, self.output_signal, self.thread_results, self.THREAD_COUNT, self.DATABASE_PATH, 
                   self.TABLE_NAME, self.LABEL_COLUMN_NAME, self.LIMIT, self.DEFAULT_NODE_RECOGNITION_PROMPT)
        self.running_signal.emit(False)

    def stop(self):
        self._stop_event.set()
        self.wait()

    def __del__(self):
        self.stop()

def get_code_from_gpt(output_signal, prompt_content):
    """调用AI模型进行代码生成"""
    api = AiHubMixAPI()
    model = readConfig().get("AICO", "model")
    
    if not model:
        error_msg = "未选择AI模型" if language == "Chinese" else "No AI model selected"
        output_signal.emit(f"[Error] [{arrow.now().format('YYYY-MM-DD HH:mm:ss')}] {error_msg}")
        return None

    messages = [
        {
            "role": "system",
            "content": "您将看到一组论坛中的话题和回帖，您的任务是优先根据下面的编码表中的含义解释对每个回帖提取一组标签，并在一组 JSON 对象中输出。",
        },
        {
            "role": "user", 
            "content": prompt_content
        }
    ]

    response = api.chat_completion(model, messages)
    
    if 'error' in response:
        timestamp = arrow.now().format('YYYY-MM-DD HH:mm:ss')
        if language == "Chinese":
            output_signal.emit(f"[错误] [{timestamp}] {response['error']}")
        else:
            output_signal.emit(f"[Error] [{timestamp}] {response['error']}")
        return None
        
    return response

def parse_gpt_response(response):
    """解析AI模型的响应"""
    try:
        if not response or 'choices' not in response:
            return None
        content = response['choices'][0]['message']['content']
        # 去除content中的换行、空格等字符
        content = re.sub(r'[\n\r\s]+', ' ', str(content)).strip()
        return content if content else None
    except Exception as e:
        print(f"解析响应失败: {str(e)}")
        return None

def encode_data(output_signal, record, default_node_recognition_prompt, label):
    """编码数据"""
    try:
        prompt_content = record[0]  # 获取 prompt_content 列的值
        response = get_code_from_gpt(output_signal, prompt_content)
        if response:
            prompt_code = parse_gpt_response(response)
            if prompt_code:
                return prompt_code, json.dumps(response)  # 使用 json.dumps 确保 response 被正确序列化
    except Exception as e:
        print(f"编码失败: {str(e)}")
    return None, None

def worker(stop_event, output_signal, input_queue, output_dict, db_path, table_name, label, default_node_recognition_prompt):
    """工作线程处理函数"""
    while not stop_event.is_set():
        try:
            # 使用timeout参数，这样可以更频繁地检查stop_event
            try:
                record = input_queue.get(timeout=0.1)
            except Empty:
                continue
                
            # 再次检查stop_event，如果设置了就立即退出
            if stop_event.is_set():
                break
                
            # 输出当前处理进度
            timestamp = arrow.now().format('YYYY-MM-DD HH:mm:ss')
            if language == "Chinese":
                output_signal.emit(f"[提示] [{timestamp}] [当前线程]：{threading.current_thread().name}，剩余 {input_queue.qsize()} 项待处理")
            else:
                output_signal.emit(f"[Notice] [{timestamp}] [Current thread]: {threading.current_thread().name}, {input_queue.qsize()} items remaining")
        except Empty:
            break

        # 如果设置了stop_event，跳过处理直接退出
        if stop_event.is_set():
            break
            
        prompt_code, prompt_code_orign = encode_data(output_signal, record, default_node_recognition_prompt, label)
        
        # 再次检查stop_event
        if stop_event.is_set():
            break
            
        if prompt_code and prompt_code_orign:
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE prompt SET prompt_code = ?, prompt_code_orign = ? WHERE prompt_content = ?", 
                    (prompt_code, prompt_code_orign, record[0])
                )
                conn.commit()
                conn.close()
            except Exception as e:
                timestamp = arrow.now().format('YYYY-MM-DD HH:mm:ss')
                if language == "Chinese":
                    output_signal.emit(f"[错误] [{timestamp}] 数据库更新失败: {str(e)}")
                else:
                    output_signal.emit(f"[Error] [{timestamp}] Database update failed: {str(e)}")
        else:
            timestamp = arrow.now().format('YYYY-MM-DD HH:mm:ss')
            if language == "Chinese":
                output_signal.emit(f"[警告] [{timestamp}] 编码失败")
            else:
                output_signal.emit(f"[Warning] [{timestamp}] Encoding failed")

def fetch_data_from_database(db_path, table_name, label, limit=-1):
    """从数据库获取数据"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        if limit == -1:
            cursor.execute("SELECT prompt_content FROM prompt WHERE prompt_code IS NULL OR prompt_code = 'None'")
        else:
            cursor.execute("SELECT prompt_content FROM prompt WHERE prompt_code IS NULL OR prompt_code = 'None' LIMIT ?", 
                         (limit,))
        records = cursor.fetchall()
        return records
    finally:
        conn.close()

def main_coding(stop_event, output_signal, thread_results, THREAD_COUNT, DATABASE_PATH, TABLE_NAME, LABEL_COLUMN_NAME, LIMIT, DEFAULT_NODE_RECOGNITION_PROMPT):
    """主编码处理函数"""
    records = fetch_data_from_database(DATABASE_PATH, TABLE_NAME, LABEL_COLUMN_NAME, LIMIT)
    if not records:
        if language == "Chinese":
            output_signal.emit(f"[提示] [{arrow.now().format('YYYY-MM-DD HH:mm:ss')}] 没有需要处理的数据")
        else:
            output_signal.emit(f"[Notice] [{arrow.now().format('YYYY-MM-DD HH:mm:ss')}] No data to process")
        return

    input_queue = Queue()
    for record in records:
        input_queue.put(record)

    threads = []
    for _ in range(min(THREAD_COUNT, len(records))):
        t = threading.Thread(
            target=worker,
            args=(stop_event, output_signal, input_queue, thread_results, DATABASE_PATH, 
                  TABLE_NAME, LABEL_COLUMN_NAME, DEFAULT_NODE_RECOGNITION_PROMPT)
        )
        t.daemon = True  # 设置为守护线程，这样主程序退出时线程会自动结束
        t.start()
        threads.append(t)

    # 使用超时等待，这样可以响应停止信号
    while threads:
        for t in threads[:]:
            t.join(timeout=0.1)  # 等待0.1秒
            if not t.is_alive():
                threads.remove(t)
        
        # 如果设置了stop_event，就不再等待其他线程
        if stop_event.is_set():
            break

    # 只有在正常完成时才显示统计信息
    if not stop_event.is_set():
        remaining = len(fetch_data_from_database(DATABASE_PATH, TABLE_NAME, LABEL_COLUMN_NAME))
        if language == "Chinese":
            output_signal.emit(f"[提示] [{arrow.now().format('YYYY-MM-DD HH:mm:ss')}] [编码统计]：剩余 {remaining} 项待处理")
        else:
            output_signal.emit(f"[Notice] [{arrow.now().format('YYYY-MM-DD HH:mm:ss')}] [Coding statistics]：Total {remaining} items remaining to be processed")