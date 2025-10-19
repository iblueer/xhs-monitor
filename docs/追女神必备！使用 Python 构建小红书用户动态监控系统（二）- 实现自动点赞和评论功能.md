# 追女神必备！使用 Python 构建小红书用户动态监控系统（二）- 实现自动点赞和评论功能

## **前言**

在上一篇教程中，我们实现了小红书最基础的用户动态监控功能，能够实时监控女神的小红书笔记更新，并第一时间通过企业微信通知我们。

但是，作为一名合格的舔狗，我们不仅要能够实时监控女神的小红书最新笔记，还要能够第一时间向女神送上点赞和评论，让她感受到我们的热情和关注。之前我们是收到企业微信通知后，手动去点赞和评论，但是这样速度太慢了，女神背后的舔狗不知有多少，为了在 PVP 中脱颖而出，我们必须比别人速度更快，更高情商。所以，今天我们就来实现自动点赞和评论功能。

## **需求分析**

在原有功能的基础上，我们需要：

- 自动给女神的新笔记点赞
- 自动评论女神的新笔记
- 使用 LLM (大语言模型) 生成个性化高情商评论
- 通过企业微信通知互动结果
- 首次监控某用户时，不进行互动，以防止短时间内对同一用户的大量历史笔记互动，被系统以及用户发现

## **技术方案**

为了实现这些新功能，我们需要：

- 实现基于 OpenAI API 的评论生成器
- 扩展配置模块,添加 LLM 和互动相关配置
- 扩展监控模块, 添加互动逻辑（点赞和评论）
- 扩展数据库模块, 获取数据库中用户历史笔记数量

## **代码实现**

### **扩展配置模块**

首先我们需要在原来的配置文件中添加 LLM 和互动相关配置，如 OpenAI API 密钥, Prompt 模板, 是否开启自动互动等。

```
# config.py
### ......原配置文件内容

# 监控配置
MONITOR_CONFIG = {
    # ...... 原配置文件内容

    "AUTO_INTERACT": True,  # 是否开启自动互动
    "FALLBACK_COMMENTS": [  # 随机选择一条评论
        "太棒了！",
        "喜欢这篇笔记",
        "我来啦~",
        "路过~",
        "感谢分享",
        "期待更新~",
        "支持支持！"
    ],
    "LIKE_DELAY": 2,  # 点赞延迟(秒)
    "COMMENT_DELAY": 5,  # 评论延迟(秒)
}

# LLM配置
LLM_CONFIG = {
    "API_KEY": "你的OpenAI API Key",
    "API_BASE": "https://api.openai.com/v1", # 或者你的API代理地址
    "MODEL": "gpt-3.5-turbo",  # 或 gpt-4
    "MAX_TOKENS": 150,
    "TEMPERATURE": 0.7,
    "SYSTEM_PROMPT": """你是一个正在追求心仪女生的人，需要对她的小红书笔记进行评论。
请根据笔记内容生成一条甜蜜、真诚但不过分的评论。评论要：
1. 体现你在认真看她的内容
2. 表达适度的赞美和支持
3. 语气要自然、真诚
4. 避免过分讨好或低声下气
5. 根据内容类型（图文/视频）采用合适的表达
6. 字数控制在100字以内
7. 避免过于模板化的表达
8. 评论内容要符合小红书平台规则"""
} 
```

主要添加了:

- LLM 相关配置
  - API_KEY: OpenAI API 密钥
  - API_BASE: OpenAI API 代理地址
  - MODEL: 使用的 LLM 模型
  - MAX_TOKENS: 生成的评论最大字数
  - TEMPERATURE: 生成评论的随机性
  - SYSTEM_PROMPT: 生成评论的提示词
- 自动互动相关配置
  - AUTO_INTERACT: 是否开启自动互动
  - FALLBACK_COMMENTS: 如果 LLM 生成评论失败, 则使用此列表中的随机一条评论
  - LIKE_DELAY: 点赞延迟(秒)，减少点赞频率，避免被系统识别为机器人
  - COMMENT_DELAY: 评论延迟(秒)，减少评论频率，避免被系统识别为机器人

### **实现评论生成器**

创建 comment_generator.py 文件, 实现基于 LLM 的评论生成器。

```
# comment_generator.py
import requests
import random
from config import LLM_CONFIG, MONITOR_CONFIG

class CommentGenerator:
    def __init__(self):
        self.api_key = LLM_CONFIG["API_KEY"]
        self.api_base = LLM_CONFIG["API_BASE"]
        self.model = LLM_CONFIG["MODEL"]
        
    def generate_comment(self, title: str, content: str) -> str:
        """
        根据笔记标题和内容生成评论
        """
        try:
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": LLM_CONFIG["SYSTEM_PROMPT"]
                        },
                        {
                            "role": "user",
                            "content": f"请根据以下笔记生成一条评论:\n标题: {title}\n内容: {content}"
                        }
                    ],
                    "max_tokens": LLM_CONFIG["MAX_TOKENS"],
                    "temperature": LLM_CONFIG["TEMPERATURE"]
                }
            )
            
            if response.status_code == 200:
                comment = response.json()["choices"][0]["message"]["content"].strip()
                return comment
            else:
                print(f"API 请求失败: {response.status_code}")
                print(f"错误信息: {response.text}")
                return self._get_fallback_comment()
                
        except Exception as e:
            print(f"生成评论失败: {e}")
            return self._get_fallback_comment()
            
    def _get_fallback_comment(self) -> str:
        """
        当 API 调用失败时的备用评论
        """
        return random.choice(MONITOR_CONFIG.get('FALLBACK_COMMENTS', [])) 
```

- 我们创建了一个 `CommentGenerator` 类，用于生成评论。
- 通过 `__init__` 方法初始化 OpenAI API 密钥、API 代理地址和要使用的模型。
- 通过 `generate_comment` 方法生成评论。`generate_comment` 方法会接收笔记的标题和内容作为参数，并结合配置模块中定义的系统提示词和用户提示词，构造一个 OpenAI API 的请求体，然后调用 OpenAI API 的 `chat/completions` 接口，并传入请求体。
- 如果 API 调用失败，则使用预先配置的备用评论。
- 通过 `_get_fallback_comment` 方法获取预先配置的备用评论。

### **扩展数据库模块**

我们修改 db.py 文件，添加获取数据库中保存的用户历史笔记数量的方法。

```
# db.py
### ......原数据库模块内容

class Database:
    # ......原数据库模块内容
    def get_user_notes_count(self, user_id: str) -> int:
        """
        获取数据库中某用户的笔记数量
        :param user_id: 用户ID
        :return: 笔记数量
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM notes WHERE user_id = ?", (user_id,))
            count = cursor.fetchone()[0]
            return count or 0
```

### **扩展监控模块**

我们修改 monitor.py 文件中，添加互动逻辑, 并添加首次监控的提醒。

```
# monitor.py
from xhs import XhsClient
import time
from typing import List
from config import XHS_CONFIG, WECOM_CONFIG, MONITOR_CONFIG
from utils import xhs_sign
from db import Database
from wecom import WecomMessage
from comment_generator import CommentGenerator

class XHSMonitor:
    def __init__(self, cookie: str, corpid: str, agentid: int, secret: str):
        """
        初始化监控类
        :param cookie: 小红书cookie
        :param corpid: 企业ID
        :param agentid: 应用ID
        :param secret: 应用的Secret
        """
        self.client = XhsClient(cookie=cookie, sign=xhs_sign)
        self.wecom = WecomMessage(corpid, agentid, secret)
        self.db = Database()
        self.error_count = 0
        self.comment_generator = CommentGenerator()
        
    def send_error_notification(self, error_msg: str):
        """
        发送错误通知
        :param error_msg: 错误信息
        """
        time_str = time.strftime('%Y-%m-%d %H:%M:%S')
        content = (
            "小红书监控异常告警\n"
            f"错误信息：{error_msg}\n"
            f"告警时间：{time_str}"
        )
        self.wecom.send_text(content)
    
    def get_latest_notes(self, user_id: str) -> List[dict]:
        """
        获取用户最新笔记
        :param user_id: 用户ID
        :return: 笔记列表
        """
        try:
            res_data = self.client.get_user_notes(user_id)
            self.error_count = 0
            return res_data.get('notes', [])
            
        except Exception as e:
            error_msg = str(e)

            print(f"获取用户笔记失败: {error_msg}")

            time.sleep(60)

            self.error_count += 1

            if self.error_count >= MONITOR_CONFIG["ERROR_COUNT"]:
                self.send_error_notification(f"API 请求失败\n详细信息：{error_msg}")
                exit(-1)

            return []

    def like_note(self, note_id: str) -> bool:
        """
        点赞笔记
        :param note_id: 笔记ID
        :return: 是否成功
        """
        try:
            time.sleep(MONITOR_CONFIG["LIKE_DELAY"])  # 添加延迟，避免操作过快
            self.client.like_note(note_id)
            print(f"点赞成功: {note_id}")
            returnTrue
        except Exception as e:
            print(f"点赞失败: {e}")
            returnFalse

    def get_note_detail(self, note_id: str, xsec: str) -> dict:
        """
        获取笔记详细信息
        :param note_id: 笔记ID
        :return: 笔记详细信息
        """
        try:
            uri = '/api/sns/web/v1/feed'
            data = {"source_note_id":note_id,"image_formats":["jpg","webp","avif"],"extra":{"need_body_topic":"1"},"xsec_source":"pc_search","xsec_token": xsec}
            res = self.client.post(uri, data=data)
            note_detail = res["items"][0]["note_card"]
            return note_detail
        except Exception as e:
            print(f"获取笔记详情失败: {e}")
            return {}

    def comment_note(self, note_id: str, note_data: dict) -> dict:
        """
        评论笔记
        :param note_id: 笔记ID
        :param note_data: 笔记数据
        :return: 评论结果
        """
        try:
            time.sleep(MONITOR_CONFIG["COMMENT_DELAY"])
            
            note_detail = self.get_note_detail(note_id, note_data.get('xsec_token', ''))
            
            title = note_detail.get('title', '')
            content = note_detail.get('desc', '')
            
            note_type = '视频'if note_detail.get('type') == 'video'else'图文'
            content = f"这是一个{note_type}笔记。{content}"
            
            comment = self.comment_generator.generate_comment(title, content)
            
            self.client.comment_note(note_id, comment)
            
            print(f"评论成功: {note_id} - {comment}")
            return { "comment_status": True, "comment_content": comment }
        except Exception as e:
            print(f"评论失败: {e}")
            return { "comment_status": False, "comment_content": "" }

    def interact_with_note(self, note_data: dict) -> dict:
        """
        与笔记互动（点赞+评论）
        :param note_data: 笔记数据
        :return: 互动结果
        """
        result = {
            "like_status": False,
            "comment_status": False,
            "comment_content": ""
        }
        
        ifnot MONITOR_CONFIG.get("AUTO_INTERACT"):
            return result

        note_id = note_data.get('note_id')
        ifnot note_id:
            return result

        result["like_status"] = self.like_note(note_id)
        
        comment_result = self.comment_note(note_id, note_data)

        result["comment_status"] = comment_result["comment_status"]
        
        result["comment_content"] = comment_result["comment_content"]
        
        return result

    def send_note_notification(self, note_data: dict, interact_result: dict = None):
        """
        发送笔记通知
        :param note_data: 笔记数据
        :param interact_result: 互动结果
        """
        note_url = f"https://www.xiaohongshu.com/explore/{note_data.get('note_id')}"
        user_name = note_data.get('user', {}).get('nickname', '未知用户')
        title = note_data.get('display_title', '无标题')
        type = note_data.get('type', '未知类型')
        time_str = time.strftime('%Y-%m-%d %H:%M:%S')
        
        content = [
            "小红书用户发布新笔记",
            f"用户：{user_name}",
            f"标题：{title}",
            f"链接：{note_url}",
            f"类型：{type}",
        ]
        
        if interact_result and MONITOR_CONFIG.get("AUTO_INTERACT"):
            like_status = "成功"if interact_result["like_status"] else"失败"
            content.append(f"点赞：{like_status}")
            
            if interact_result["comment_status"]:
                content.append(f"评论：成功")
                content.append(f"评论内容：{interact_result['comment_content']}")
            else:
                content.append(f"评论：失败")
        
        content.append(f"监控时间：{time_str}")
        
        self.wecom.send_text("\n".join(content))

    def monitor_user(self, user_id: str, interval: int):
        """
        监控用户动态
        :param user_id: 用户ID
        :param interval: 检查间隔(秒)
        """
        print(f"开始监控用户: {user_id}")
        
        whileTrue:
            try:
                latest_notes = self.get_latest_notes(user_id)
                
                existing_notes = self.db.get_user_notes_count(user_id)
                is_first_monitor = existing_notes == 0and len(latest_notes) > 1
                
                if is_first_monitor:
                    welcome_msg = (
                        f"欢迎使用 xhs-monitor 系统\n"
                        f"监控用户：{latest_notes[0].get('user', {}).get('nickname', user_id)}\n"
                        f"首次监控某用户时，不会对历史笔记进行自动点赞和评论，仅保存笔记记录\n"
                        f"以防止被系统以及用户发现"
                    )
                    self.wecom.send_text(welcome_msg)
                    
                    for note in latest_notes:
                        self.db.add_note_if_not_exists(note)
                else:
                    for note in latest_notes:
                        if self.db.add_note_if_not_exists(note):
                            print(f"发现新笔记: {note.get('display_title')}")
                            interact_result = self.interact_with_note(note)
                            self.send_note_notification(note, interact_result)
                        
            except Exception as e:
                error_msg = str(e)
                print(f"监控过程发生错误: {error_msg}")
            time.sleep(interval)

def main():
    monitor = XHSMonitor(
        cookie=XHS_CONFIG["COOKIE"],
        corpid=WECOM_CONFIG["CORPID"],
        agentid=WECOM_CONFIG["AGENTID"],
        secret=WECOM_CONFIG["SECRET"]
    )

    monitor.monitor_user(
        user_id=MONITOR_CONFIG["USER_ID"],
        interval=MONITOR_CONFIG["CHECK_INTERVAL"]
    )

if __name__ == "__main__":
    main() 
```

- 新增 `interact_with_note` 方法，用于与笔记互动（点赞和评论），并返回互动结果。
  - 如果配置模块中 `AUTO_INTERACT` 为 `False`，则直接返回互动结果。
  - 如果配置模块中 `AUTO_INTERACT` 为 `True`，则先通过 `like_note` 方法点赞笔记，再通过 `comment_note` 方法评论笔记，并返回互动结果。
- 新增 `like_note` 方法，用于点赞笔记。
  - `like_note` 方法会通过 `sleep` 方法添加点赞延迟， 减少被系统识别为机器人的概率。
  - 然后调用 `XhsClient` 的 `like_note` 方法实现点赞笔记。
- 新增 `comment_note` 方法，用于评论笔记。
  - `comment_note` 方法也会通过 `sleep` 方法添加评论延迟， 减少被系统识别为机器人的概率。
  - 由于小红书列表页的数据不全，没有包含笔记的正文内容信息，所以我们需要获取单篇笔记的详细信息，这里我们通过 `get_note_detail` 方法获取笔记的详细信息，然后将笔记的标题，正文内容，笔记类型拼接成一条内容，传入评论生成器的 `generate_comment` 方法，生成评论内容
  - 最后调用 `XhsClient` 的 `comment_note` 方法实现评论笔记。
- 新增 `get_note_detail` 方法，用于获取笔记的详细信息。
  - 我们通过 `XhsClient` 的 `post` 方法，构造请求体，获取笔记的详细信息。
- 修改 `__init__` 方法，添加 `CommentGenerator` 实例。
- 修改 `send_note_notification` 方法。
  - 新增 `interact_result` 参数，用于传递互动结果。
  - 如果配置模块中 `AUTO_INTERACT` 为 `True`，则将互动结果添加到通知内容中。
  - 如果配置模块中 `AUTO_INTERACT` 为 `False`，则只发送笔记通知，不发送互动结果。
- 修改 `monitor_user` 方法，添加首次监控的提醒。
  - 如果首次监控某用户，则发送欢迎信息到企业微信，并仅保存笔记记录，不进行互动, 以防止短时间内对同一用户的大量历史笔记互动，被系统以及用户发现。
  - 如果非首次监控，则根据配置进行互动。

## **运行效果**

执行 `python monitor.py` 后，可以看到如下效果：

![图片](data:image/svg+xml,%3C%3Fxml version='1.0' encoding='UTF-8'%3F%3E%3Csvg width='1px' height='1px' viewBox='0 0 1 1' version='1.1' xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink'%3E%3Ctitle%3E%3C/title%3E%3Cg stroke='none' stroke-width='1' fill='none' fill-rule='evenodd' fill-opacity='0'%3E%3Cg transform='translate(-249.000000, -126.000000)' fill='%23FFFFFF'%3E%3Crect x='249' y='126' width='1' height='1'%3E%3C/rect%3E%3C/g%3E%3C/g%3E%3C/svg%3E)![图片](https://mmbiz.qpic.cn/sz_mmbiz_jpg/UnmzujcphqseG1WnEqYVn1WTPeA8I9HzpwDmiaT7M73uDibMaKP6YkuP8XCKY5SG19NP2l0iaw5T4U7ialGtyuCfJA/640?wx_fmt=jpeg&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=1)

![图片](https://mmbiz.qpic.cn/sz_mmbiz_jpg/UnmzujcphqseG1WnEqYVn1WTPeA8I9HzUN3dvQn0e0LDt1OQGZibwnwydxnBD9ibOJAyibYpgQSFlHBW7hpZxn7TQ/640?wx_fmt=jpeg&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=2)

## **结语**

通过本篇教程，我们实现了自动点赞和评论功能，让我们在不错过女神笔记的同时，第一时间向她送上点赞和评论。 但是，PVP 是残酷的，即使我们第一时间向女神送上点赞和评论，也不一定能获得女神的青睐，所以，在接下来，我们将继续努力，不断优化我们的代码，让 PVP 变成 PVE ! 最终收获女神的芳心！

## **项目地址**

本教程的完整代码，请访问项目地址：https://github.com/beilunyang/xhs-monitor, 分支 `tutorial-2` 是本篇的完整代码。 如果这个项目对你有帮助,欢迎给个 Star ⭐️