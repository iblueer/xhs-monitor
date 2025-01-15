from xhs import XhsClient
import time
from typing import List
from config import XHS_CONFIG, WECOM_CONFIG, MONITOR_CONFIG
from utils import xhs_sign
from db import Database
from wecom import WecomMessage
import random

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
            return True
        except Exception as e:
            print(f"点赞失败: {e}")
            return False

    def comment_note(self, note_id: str) -> bool:
        """
        评论笔记
        :param note_id: 笔记ID
        :return: 是否成功
        """
        try:
            time.sleep(MONITOR_CONFIG["COMMENT_DELAY"])  # 添加延迟，避免操作过快
            comment = random.choice(MONITOR_CONFIG["COMMENTS"])
            self.client.comment_note(note_id, comment)
            print(f"评论成功: {note_id} - {comment}")
            return True
        except Exception as e:
            print(f"评论失败: {e}")
            return False

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
        
        if not MONITOR_CONFIG.get("AUTO_INTERACT"):
            return result

        note_id = note_data.get('note_id')
        if not note_id:
            return result

        result["like_status"] = self.like_note(note_id)
        
    
        comment = random.choice(MONITOR_CONFIG["COMMENTS"])
        result["comment_content"] = comment
        result["comment_status"] = self.comment_note(note_id)
            
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
            like_status = "成功" if interact_result["like_status"] else "失败"
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
        
        while True:
            try:
                latest_notes = self.get_latest_notes(user_id)

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