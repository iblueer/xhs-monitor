import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from xhs import XhsClient

from bark import BarkClient
from config import BARK_CONFIG, MONITOR_CONFIG, MONITOR_TARGETS, XHS_CONFIG
from db import Database
from utils import xhs_sign

class XHSMonitor:
    DAILY_SECONDS = 86400

    def __init__(self, cookie: str, monitor_targets: List[Dict]):
        self.client = XhsClient(cookie=cookie, sign=xhs_sign)
        self.notifier = BarkClient(
            base_url=BARK_CONFIG.get("BASE_URL", "https://api.day.app"),
            device_key=BARK_CONFIG.get("DEVICE_KEY", ""),
            group=BARK_CONFIG.get("GROUP", ""),
            sound=BARK_CONFIG.get("SOUND", ""),
            icon=BARK_CONFIG.get("ICON", ""),
        )
        self.db = Database()
        self.error_count = 0
        self.monitor_targets = monitor_targets
        self.check_interval = MONITOR_CONFIG.get("CHECK_INTERVAL", 1800)
        self.error_limit = MONITOR_CONFIG.get("ERROR_COUNT", 10)
        self.error_wait = MONITOR_CONFIG.get("ERROR_RETRY_WAIT", 60)
        self.hot_gate_days = MONITOR_CONFIG.get("HOT_GATE_DAYS", 5)
        self.first_run_window_hours = MONITOR_CONFIG.get("FIRST_RUN_WINDOW_HOURS", 24)
        self.next_hot_gate_check = time.time()
        
    def send_error_notification(self, error_msg: str):
        time_str = time.strftime('%Y-%m-%d %H:%M:%S')
        body = f"错误信息：{error_msg}\n告警时间：{time_str}"
        self.notifier.send("异常告警", body, group="exception")
    
    def get_user_notes(self, user_id: str) -> List[dict]:
        try:
            res_data = self.client.get_user_notes(user_id)
            self.error_count = 0
            return res_data.get('notes', [])
            
        except Exception as e:
            error_msg = str(e)

            print(f"获取用户笔记失败: {error_msg}")

            time.sleep(self.error_wait)

            self.error_count += 1

            if self.error_count >= self.error_limit:
                self.send_error_notification(f"API 请求失败\n详细信息：{error_msg}")
                exit(-1)

            return []

    def run(self):
        print("开始监控目标列表")
        while True:
            for target in self.monitor_targets:
                try:
                    self.process_new_posts(target)
                except Exception as exc:
                    print(f"处理 {target.get('nickname')} 新笔记失败: {exc}")
            now = time.time()
            if now >= self.next_hot_gate_check:
                try:
                    self.process_hot_gate()
                except Exception as exc:
                    print(f"执行点赞达标检查失败: {exc}")
                self.next_hot_gate_check = now + self.DAILY_SECONDS
            time.sleep(self.check_interval)

    def process_new_posts(self, target: Dict):
        user_id = target.get("id")
        notes = self.get_user_notes(user_id)
        if not notes:
            return
        notes.sort(key=lambda x: self._extract_timestamp(x) or 0)
        last_time_str = self.db.get_latest_note_time(user_id)
        last_time = self._to_datetime(last_time_str) if last_time_str else None
        first_run = last_time is None
        window_start = None
        if first_run:
            window_start = datetime.utcnow() - timedelta(hours=self.first_run_window_hours)

        for note in notes:
            published_at = self._extract_datetime(note)
            published_str = published_at.strftime("%Y-%m-%d %H:%M:%S") if published_at else ""
            note_record = dict(note)
            note_record["published_time"] = published_str
            self.db.add_note_if_not_exists(note_record)

            if not published_at:
                continue
            if first_run:
                if window_start and published_at < window_start:
                    continue
            elif last_time and published_at <= last_time:
                continue

            title = note.get('display_title') or note.get('title') or ''
            keywords = target.get('keyword', [])
            matched = [kw for kw in keywords if kw and kw in title]
            if not matched:
                continue

            url = f"https://www.xiaohongshu.com/explore/{note.get('note_id')}"
            body = f"命中关键词：{', '.join(matched)}\n标题：{title}"
            group = "重要更新提醒"
            title_text = f"{target.get('nickname', user_id)} 有新动态"
            self.notifier.send(title_text, body, url, group=group)

    def process_hot_gate(self):
        since = datetime.utcnow() - timedelta(days=self.hot_gate_days)
        for target in self.monitor_targets:
            user_id = target.get("id")
            notes = self.get_user_notes(user_id)
            if not notes:
                continue
            hot_gate = target.get("hot_gate", 0)
            for note in notes:
                published_at = self._extract_datetime(note)
                if not published_at or published_at < since:
                    continue
                like_count = self._extract_like_count(note)
                if like_count < hot_gate:
                    continue
                note_id = note.get('note_id')
                if self.db.is_hot_gate_notified(note_id):
                    continue
                url = f"https://www.xiaohongshu.com/explore/{note_id}"
                body = f"点赞数：{like_count}\n时间：{published_at.strftime('%Y-%m-%d %H:%M:%S')}"
                group = "点赞达标提醒"
                title_text = f"{target.get('nickname', user_id)} 达到 {hot_gate}"
                if self.notifier.send(title_text, body, url, group=group):
                    self.db.mark_hot_gate_notified(note_id, user_id, like_count)

    def _extract_timestamp(self, note: Dict) -> Optional[int]:
        value = note.get('time') or note.get('timestamp')
        if not value:
            card = note.get('note_card') or {}
            value = card.get('time') or card.get('timestamp')
        if isinstance(value, str):
            if value.isdigit():
                return int(value)
            try:
                dt = datetime.fromisoformat(value)
                return int(dt.timestamp())
            except Exception:
                return None
        if isinstance(value, (int, float)):
            return int(value)
        return None

    def _extract_datetime(self, note: Dict) -> Optional[datetime]:
        ts = self._extract_timestamp(note)
        if ts:
            try:
                return datetime.utcfromtimestamp(ts)
            except Exception:
                return None
        text = note.get('published_time') or note.get('time')
        if isinstance(text, str):
            for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S'):
                try:
                    return datetime.strptime(text, fmt)
                except Exception:
                    continue
        return None

    def _extract_like_count(self, note: Dict) -> int:
        value = note.get('liked_count')
        if value is None:
            card = note.get('note_card') or {}
            value = card.get('liked_count')
        if value is None:
            detail = note.get('interact_info') or {}
            value = detail.get('liked_count')
        try:
            return int(value)
        except Exception:
            return 0

    def _to_datetime(self, value: str) -> Optional[datetime]:
        if not value:
            return None
        for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S'):
            try:
                return datetime.strptime(value, fmt)
            except Exception:
                continue
        return None

def main():
    monitor = XHSMonitor(
        cookie=XHS_CONFIG.get("COOKIE", ""),
        monitor_targets=MONITOR_TARGETS,
    )
    monitor.run()

if __name__ == "__main__":
    main() 