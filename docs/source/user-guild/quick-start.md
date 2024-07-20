# 快速上手

AICodingOfficer (AICO) 是一款基于人工智能的文本编码助手，可以帮助研究者提高文本编码效率，减少重复劳动。AICO 支持 Windows、macOS 和 Linux 系统。

## 安装
### Windows

1. 下载安装包：[AICodingOfficer_windows.zip](https://github.com/etShaw-zh/AICodingAssistant-Pro/releases)
2. 解压安装包
3. 运行 `AICodingOfficer.exe`

### macOS

1. 下载安装包：[AICodingOfficer_macOS.zip](https://github.com/etShaw-zh/AICodingAssistant-Pro/releases)
2. 解压安装包
3. 运行 `AICodingOfficer.app`

    ⚠️  解决Mac 上「应用程序 “xxx” 不能打开」的问题

    - 首先在应用上点击右键，选择「显示包内容」
    - 之后依次展开「Contents」-「MacOS」，找到对应文件夹下的文件 AICodingOfficer
    - 接下来打开终端，直接输入以下代码（注意 +x 前后都有空格）：
        
        ```shell
        chmod +x
        ```
        
    - 之后再将文件 AICodingOfficer 拖入终端（为了输入完整的执行路径）。完整的命令如下：
        
        ```shell
        chmod +x /Users/xiaojianjun/Downloads/AICodingOfficer.app/Contents/MacOS/AICodingOfficer
        ```

    - 最后点击回车，这时候在访达中原本不明类型的文件现在变成了 Unix 可执行文件，图标也变成正常的了。
    - 重新打开下载的软件，你会发现下载的程序可以正常使用并执行了！
    - 仍然无法打开的话，进入设置，安全性与隐私，找到提示信息，点击运行打开即可。

    📖  图文教程：[macOS 上「应用程序 “xxx” 不能打开」的解决方法](https://sspai.com/post/52828#!)


## 基本使用

1 **在开始编码之前，你需要准备以下数据**: 

1.1 **API_key**: 

- 申请API_key，用于调用编码接口。

- 申请地址：[Kimi Open Platform](https://platform.moonshot.cn/docs)

- API_key查看地址：[Kimi API key console](https://platform.moonshot.cn/console/api-keys)

- API_key示例：sk-DA...xf13S

1.2 **文本数据**:

- Topic和Reply数据，以及Coding_scheme。

- Topic是待编码文本的话题，Reply是话题下的回帖。

- Coding_scheme是编码规则，用于指导AICO进行编码。

- 示例数据下载地址：[示例数据](https://github.com/etShaw-zh/AICodingAssistant-Pro/blob/main/docs/source/_static/example/)

1.2.1 **待编码文本数据，topic和reply**:

| 字段          | 类型 | 描述                             |
|---------------|------|----------------------------------|
| index         | int  | 待编码文本的唯一标识符，是回帖ID |
| user_id       | int  | 回帖的用户ID                     |
| user_name     | str  | 回帖的用户昵称                   |
| reply_content | str  | 回帖内容                         |
| topic_id      | int  | 回帖的话题ID                     |
| reply_id      | int  | 回帖ID                           |
| to_reply_id   | int  | 回帖的父级回帖ID                 |
| reason        | str  | 编码理由，这一列可以空着         |


| 字段          | 类型 | 描述                                       |
|---------------|------|--------------------------------------------|
| topic_id      | int  | 话题ID                                     |
| topic_title   | str  | 话题标题                                   |
| topic_content | str  | 话题内容，一半是话题的详细描述，这里可以空着 |


1.2.2 **编码规则**:

| 字段        | 类型 | 描述                               |
|-------------|------|------------------------------------|
| category    | str  | 编码分类                           |
| code        | str  | 编码指标代码                       |
| indicators  | str  | 编码指标                           |
| example     | str  | 指标的示例（这一列可以不要）       |


2 **将数据准备好后，打开AICO**:

2.1 **填写API_key**:

- 打开设置，填写API_key。 

2.2 **导入数据**:

- 分别将topic, reply, coding_scheme的csv文件导入AICO。

- 点击加载数据。



3 **测试或批量编码**:

- 点击测试编码，AICO会对前10条数据自动调用API进行编码。

- 点击批量编码，AICO会对所有数据自动调用API进行编码。



4 **查看编码结果**:

- 点击导出数据，AICO会将编码结果导出为csv文件，并将导出文件地址输出在log中。

- Macbook上会自动打开导出的csv文件，Windows上需要手动打开。

| 字段              | 类型 | 描述                                       |
|-------------------|------|--------------------------------------------|
| user_id           | int  | 回帖的用户ID                               |
| user_name         | str  | 回帖的用户昵称                             |
| reply_content     | str  | 回帖内容                                   |
| topic_id          | int  | 回帖的话题ID                               |
| reply_id          | int  | 回帖ID                                     |
| to_reply_id       | int  | 回帖的父级回帖ID                           |
| reason            | str  | 编码理由                                   |
| code_indicator 1  | int  | 0或1，1表示这一条回帖中包含了编码指标1     |
| code_indicator 2  | int  | 0或1，1表示这一条回帖中包含了编码指标2     |
| ...               | int  | 0或1，1表示这一条回帖中包含了编码指标...   |
| code_indicator n  | int  | 0或1，1表示这一条回帖中包含了编码指标n     |
