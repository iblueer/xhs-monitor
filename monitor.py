import json
import logging
import os
import time
from datetime import datetime, timedelta, timezone
from logging.handlers import TimedRotatingFileHandler
from typing import Dict, List, Optional

from xhs import XhsClient

from bark import BarkClient
from config import BARK_CONFIG, MONITOR_CONFIG, MONITOR_TARGETS, XHS_CONFIG
from db import Database
from utils import xhs_sign

APP_VERSION = "2024.10.20.1"

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
        self.next_hot_gate_check = 0
        self._setup_logger()
        self._log_startup_info()
        
    def send_error_notification(self, error_msg: str):
        time_str = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        body = f"错误信息：{error_msg}\n告警时间：{time_str}"
        self.notifier.send("异常告警", body, group="exception")
    
    def get_user_notes(self, user_id: str) -> List[dict]:
        try:
            res_data = self.client.get_user_notes(user_id)
            self.error_count = 0
            return res_data.get('notes', [])
            
        except Exception as e:
            error_msg = str(e)

            logging.error("获取用户笔记失败: %s", error_msg)

            time.sleep(self.error_wait)

            self.error_count += 1

            if self.error_count >= self.error_limit:
                self.send_error_notification(f"API 请求失败\n详细信息：{error_msg}")
                exit(-1)

            return []

    def run(self):
        logging.info("开始监控目标列表，共 %d 个监控对象", len(self.monitor_targets))
        while True:
            for target in self.monitor_targets:
                try:
                    self.process_new_posts(target)
                except Exception as exc:
                    logging.exception("处理 %s 新笔记失败", target.get('nickname'))
            now = time.time()
            if now >= self.next_hot_gate_check:
                logging.info("开始执行点赞达标检查")
                try:
                    self.process_hot_gate()
                except Exception as exc:
                    logging.exception("执行点赞达标检查失败")
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
            window_start = datetime.now(timezone.utc) - timedelta(hours=self.first_run_window_hours)

        for note in notes:
            published_at = self._extract_datetime(note)
            if not published_at:
                published_at = datetime.now(timezone.utc)
            note_record = json.loads(json.dumps(note))
            note_record["published_time"] = published_at.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            is_new = self.db.add_note_if_not_exists(note_record)

            if not is_new:
                continue
            if first_run and window_start and published_at < window_start:
                logging.info("首次运行忽略历史笔记: %s - %s", target.get('nickname', user_id), note.get('display_title'))
                continue
            if not first_run and last_time and published_at <= last_time:
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
            logging.info("关键词命中：%s | 标题：%s", matched, title)
            if not self.notifier.send(title_text, body, url, group=group):
                logging.error("关键词推送失败：%s", url)

    def process_hot_gate(self):
        since = datetime.now(timezone.utc) - timedelta(days=self.hot_gate_days)
        for target in self.monitor_targets:
            user_id = target.get("id")
            notes = self.get_user_notes(user_id)
            if not notes:
                continue
            hot_gate = target.get("hot_gate", 0)
            logging.info("检查点赞阈值：%s | 阈值：%s", target.get('nickname', user_id), hot_gate)
            for note in notes:
                note_id = note.get('note_id')
                stored_time_str = self.db.get_note_published_time(note_id)
                published_at = self._extract_datetime(note)
                if not published_at and stored_time_str:
                    fallback_time = self._to_datetime(stored_time_str)
                    if fallback_time:
                        logging.debug(
                            "API 未提供发布时间，使用数据库记录：note_id=%s | published_time=%s",
                            note_id,
                            fallback_time,
                        )
                        published_at = fallback_time
                if not published_at:
                    logging.debug("无法解析发布时间，跳过点赞检查：%s", note_id)
                    continue
                if published_at < since:
                    continue

                note_record = json.loads(json.dumps(note))
                note_record.setdefault("user", {})
                note_record["user"].setdefault("user_id", user_id)
                note_record["published_time"] = published_at.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                self.db.add_note_if_not_exists(note_record)

                if stored_time_str:
                    stored_dt = self._to_datetime(stored_time_str)
                    if stored_dt and published_at > stored_dt:
                        logging.debug(
                            "检测到发布时间更新：note_id=%s | old=%s | new=%s",
                            note_id,
                            stored_dt,
                            published_at,
                        )
                        self.db.update_published_time(
                            note_id,
                            published_at.strftime('%Y-%m-%d %H:%M:%S'),
                        )
                else:
                    logging.debug("记录新笔记发布时间：%s -> %s", note_id, published_at)
                    self.db.update_published_time(
                        note_id,
                        published_at.strftime('%Y-%m-%d %H:%M:%S'),
                    )
                like_count = self._extract_like_count(note)
                raw_like = note.get('liked_count')
                if raw_like is None:
                    raw_like = (note.get('note_card') or {}).get('liked_count')
                if raw_like is None:
                    raw_like = (note.get('interact_info') or {}).get('liked_count')
                logging.debug("点赞原始数据：note_id=%s | raw=%s", note_id, raw_like)
                previous_like = self.db.get_last_like_count(note_id)
                if previous_like is not None and like_count != previous_like:
                    logging.debug(
                        "点赞数变化：note_id=%s | old=%s | new=%s",
                        note_id,
                        previous_like,
                        like_count,
                    )
                self.db.update_last_like_count(note_id, like_count)
                logging.debug(
                    "点赞数据：note_id=%s | like_count=%s", note_id, like_count
                )
                if like_count < hot_gate:
                    logging.debug("点赞未达标：%s | 点赞：%s", note_id, like_count)
                    continue
                if self.db.is_hot_gate_notified(note_id):
                    logging.debug("已推送过点赞提醒：%s", note_id)
                    continue
                url = f"https://www.xiaohongshu.com/explore/{note_id}"
                body = f"点赞数：{like_count}\n时间：{published_at.strftime('%Y-%m-%d %H:%M:%S')}"
                group = "点赞达标提醒"
                title_text = f"{target.get('nickname', user_id)} 达到 {hot_gate}"
                if self.notifier.send(title_text, body, url, group=group):
                    self.db.mark_hot_gate_notified(note_id, user_id, like_count)
                    logging.info("点赞达标：%s | 点赞：%s", title_text, like_count)
                else:
                    logging.error("点赞达标推送失败：%s", url)

    def _extract_timestamp(self, note: Dict) -> Optional[int]:
        value = note.get('time') or note.get('timestamp')
        if not value:
            card = note.get('note_card') or {}
            value = card.get('time') or card.get('timestamp')
        if isinstance(value, str):
            cleaned = value.strip()
            if cleaned.isdigit():
                return int(cleaned)
            if cleaned.endswith('Z'):
                cleaned = cleaned[:-1] + '+00:00'
            try:
                dt = datetime.fromisoformat(cleaned)
                return int(dt.timestamp())
            except Exception:
                pass
        if isinstance(value, (int, float)):
            return int(value)
        return None

    def _extract_datetime(self, note: Dict) -> Optional[datetime]:
        ts = self._extract_timestamp(note)
        if ts:
            try:
                return datetime.fromtimestamp(ts, tz=timezone.utc)
            except Exception:
                return None
        text = note.get('published_time') or note.get('time')
        if isinstance(text, str):
            cleaned = text.strip()
            if cleaned.endswith('Z'):
                cleaned = cleaned[:-1] + '+00:00'
            for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S'):
                try:
                    return datetime.strptime(cleaned, fmt).replace(tzinfo=timezone.utc)
                except Exception:
                    continue
            try:
                return datetime.fromisoformat(cleaned).astimezone(timezone.utc)
            except Exception:
                return None
        return None

    def _extract_like_count(self, note: Dict) -> int:
        value = note.get('liked_count')
        if value is None:
            card = note.get('note_card') or {}
            value = card.get('liked_count')
        if value is None:
            detail = note.get('interact_info') or {}
            value = detail.get('liked_count')
        return self._parse_like_count(value)

    def _parse_like_count(self, raw) -> int:
        if raw is None:
            return 0
        if isinstance(raw, (int, float)):
            return int(raw)
        if not isinstance(raw, str):
            return 0

        text = raw.strip().lower().replace(',', '')
        multiplier = 1

        if text.endswith('万') or text.endswith('w'):
            multiplier = 10000
            text = text[:-1]
        elif text.endswith('千') or text.endswith('k'):
            multiplier = 1000
            text = text[:-1]

        try:
            amount = float(text)
            return int(amount * multiplier)
        except Exception:
            return 0

    def _to_datetime(self, value: str) -> Optional[datetime]:
        if not value:
            return None
        cleaned = value.strip()
        if cleaned.endswith('Z'):
            cleaned = cleaned[:-1] + '+00:00'
        for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S'):
            try:
                return datetime.strptime(cleaned, fmt).replace(tzinfo=timezone.utc)
            except Exception:
                continue
        try:
            return datetime.fromisoformat(cleaned).astimezone(timezone.utc)
        except Exception:
            return None
        return None

    def _setup_logger(self):
        log_dir = MONITOR_CONFIG.get("LOG_DIR", "logs")
        os.makedirs(log_dir, exist_ok=True)

        handler = TimedRotatingFileHandler(
            filename=os.path.join(log_dir, "monitor.log"),
            when="midnight",
            backupCount=7,
            encoding="utf-8",
        )
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)

        level_name = str(MONITOR_CONFIG.get("LOG_LEVEL", "INFO")).upper()
        log_level = getattr(logging, level_name, logging.INFO)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(log_level)
        logging.basicConfig(
            level=log_level,
            handlers=[handler, console_handler],
            force=True,
        )
        logging.getLogger().setLevel(log_level)
        self.log_level_name = level_name

    def _log_startup_info(self):
        device_keys = BARK_CONFIG.get("DEVICE_KEY", []) or []
        if isinstance(device_keys, str):
            device_keys = [device_keys]
        sanitized_bark = {
            "BASE_URL": BARK_CONFIG.get("BASE_URL"),
            "DEVICE_KEY_COUNT": len(device_keys),
            "GROUP": BARK_CONFIG.get("GROUP"),
            "SOUND": BARK_CONFIG.get("SOUND"),
            "ICON_PROVIDED": bool(BARK_CONFIG.get("ICON")),
        }
        sanitized_monitor = dict(MONITOR_CONFIG)
        sanitized_monitor["LOG_LEVEL"] = self.log_level_name
        sanitized_monitor.pop("COOKIE", None)
        target_summaries = []
        for target in self.monitor_targets:
            target_summaries.append({
                "nickname": target.get("nickname", target.get("id")),
                "id": target.get("id"),
                "keyword_count": len([kw for kw in target.get("keyword", []) if kw]),
                "hot_gate": target.get("hot_gate"),
            })
        config_snapshot = {
            "version": APP_VERSION,
            "monitor": sanitized_monitor,
            "bark": sanitized_bark,
            "targets": target_summaries,
            "cookie_present": bool(XHS_CONFIG.get("COOKIE")),
        }
        logging.info("xhs-monitor version: %s", APP_VERSION)
        logging.debug(
            "Loaded configuration: %s",
            json.dumps(config_snapshot, ensure_ascii=False),
        )

def main():
    monitor = XHSMonitor(
        cookie=XHS_CONFIG.get("COOKIE", ""),
        monitor_targets=MONITOR_TARGETS,
    )
    monitor.run()

if __name__ == "__main__":
    main() 