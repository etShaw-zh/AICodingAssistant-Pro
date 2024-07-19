import os
import re
import platform
import configparser
import arrow


# 文件夹存在检查
def newFolder(folder_name):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)


# 配置文件路径
def configPath():
    if platform.system() == "Windows":
        sys_path = os.environ["APPDATA"]
    elif platform.system() == "Darwin":
        sys_path = os.path.expanduser("~/Library/Application Support")
    elif platform.system() == "Linux":
        sys_path = os.path.expanduser("~/.config")
    else:
        return "N/A"

    config_path = os.path.join(sys_path, "AICodingOfficer")
    newFolder(config_path)

    return config_path


def configFile():
    config_file = os.path.join(configPath(), "config.ini")

    # 是否存在该配置文件
    if not os.path.exists(config_file):
        initConfig(config_file)

    return config_file

def exportCodingResultPath():
    export_coding_result_path = os.path.join(configPath(), "export")
    newFolder(export_coding_result_path)

    return export_coding_result_path + "/coding_result_{}.csv".format(arrow.now().format('YYYY_MM_DD_HH_mm_ss'))

def localDBFilePath():
    local_db_file_path = os.path.join(configPath(), "coding_framework")
    newFolder(local_db_file_path)

    return local_db_file_path + "/aicoding.db"


def logFolder():
    log_folder = os.path.join(configPath(), "logs")
    newFolder(log_folder)

    return log_folder

def getFilePath():
    return os.path.join(configPath())

# 初始化配置
def initConfig(config_file):
    config = configparser.ConfigParser()

    config.add_section("Language")
    config.set("Language", "language", "Chinese")

    config.add_section("Application")
    config.set("Application", "version", "1.0.0")

    config.add_section("APIkey")
    config.set("APIkey", "api_key", "")

    config.add_section("AICO")
    config.set("AICO", "model", "moonshot-v1-8k")

    config.add_section("Thread")
    config.set("Thread", "thread_count", "1")

    config.add_section("Counter")
    config.set("Counter", "open_times", "0")
    config.set("Counter", "analysis_times", "0")

    # 写入配置内容
    with open(config_file, "w", encoding="utf-8") as content:
        config.write(content)

# 删除旧版配置文件
def oldConfigCheck():
    config = readConfig()
    current_config_version = config.get("Application", "version")

    # 提取旧版配置计数器
    open_times = config.get("Counter", "open_times")
    analysis_times = config.get("Counter", "analysis_times")

    if current_config_version != "1.0.0":
        config_file = configFile()
        os.remove(config_file)
        initConfig(config_file)

        # 写入计数器
        config = readConfig()
        config.set("Counter", "open_times", open_times)
        config.set("Counter", "analysis_times", analysis_times)
        with open(config_file, "w", encoding="utf-8") as content:
            config.write(content)


# 读取配置
def readConfig():
    config = configparser.ConfigParser()
    config_file = configFile()

    config.read(config_file, encoding="utf-8")

    return config
