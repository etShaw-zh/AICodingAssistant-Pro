import os
import platform
import subprocess
import logging

import pandas as pd
from datetime import datetime

from PySide6.QtCore import QTranslator

from src.module.config import configFile, readConfig, logFolder
from src.module.resource import getResource


def log(content):
    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%Y-%m-%d %H:%M:%S")

    log_folder = logFolder()
    log_file = os.path.join(log_folder, f"{date}.log")

    logging.basicConfig(filename=log_file, level=logging.INFO, format="%(message)s")
    logging.info(f"[{time}] {content}")

    print(f"[{time}] {content}")

def readCSV(df, file_list, raw_list):
    """
    读取CSV文件
    :param df: DataFrame, 已有的数据
    :param file_list: list 已有的文件列表
    :param raw_list: list 从拖入文件中获取的文件列表
    :return: DataFrame, list 读取后的数据
    """
    for raw_path in raw_list:
        # 转换为文件路径
        file_path = raw_path.toLocalFile()

        # Windows 下调整路径分隔符
        if platform.system() == 'Windows':
            file_path = file_path.replace('/', '\\')

        # 解决 macOS 下路径无法识别
        if file_path.endswith('/'):
            file_path = file_path[:-1]

        # 过滤非CSV文件
        if not file_path.endswith('.csv'):
            log(f"文件不是CSV格式：{file_path}")
            continue

        # 去重已存在的文件夹
        path_exist = any(item == file_path for item in file_list)
        if path_exist:
            continue

        try:
            df = pd.concat([df, pd.read_csv(file_path, encoding='utf-8')], ignore_index=True)
            file_list.append(file_path)
        except Exception as e:
            log(f"读取CSV文件失败：{e}")
    return df, file_list

def initList(list_id, anime_list, raw_list):

    for raw_path in raw_list:
        # 转换为文件路径
        file_path = raw_path.toLocalFile()

        # Windows 下调整路径分隔符
        if platform.system() == 'Windows':
            file_path = file_path.replace('/', '\\')

        # 解决 macOS 下路径无法识别
        if file_path.endswith('/'):
            file_path = file_path[:-1]

        # 过滤非文件夹
        if not os.path.isdir(file_path):
            continue

        # 去重已存在的文件夹
        path_exist = any(item['file_path'] == file_path for item in anime_list)
        if path_exist:
            continue

        # TODO: 从拖入文件中获取数据
        this_anime_dict = dict()
        this_anime_dict['list_id'] = list_id
        this_anime_dict['file_name'] = os.path.basename(file_path)
        this_anime_dict['file_path'] = file_path

        anime_list.append(this_anime_dict)
        list_id += 1

    return list_id, anime_list


def addTimes(counter_name):
    config = readConfig()
    config_file = configFile()

    counter = int(config.get("Counter", counter_name)) + 1
    config.set("Counter", counter_name, str(counter))

    with open(config_file, "w") as content:
        config.write(content)


def openFolder(path):
    if platform.system() == "Windows":
        subprocess.call(["explorer", path])
    elif platform.system() == "Darwin":
        subprocess.call(["open", path])
    elif platform.system() == "Linux":
        subprocess.call(["xdg-open", path])

def loadLanguage(app, language):
    translator = QTranslator(app)
    _language_path = getResource(f"i18n/{language}.qm")
    print(_language_path)
    if translator.load(_language_path):
        log(f"加载语言文件：{language}")
        app.installTranslator(translator)
    else:
        log(f"加载语言文件失败：{language}")