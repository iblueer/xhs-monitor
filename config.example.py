import os
from pathlib import Path


def _load_cookie() -> str:
    """Load XHS cookie from environment or fallback file."""

    env_cookie = os.getenv("XHS_COOKIE")
    if env_cookie:
        return env_cookie.strip()

    cookie_file = os.getenv("XHS_COOKIE_FILE")
    candidate_path = Path(cookie_file) if cookie_file else Path(__file__).with_name("cookie.txt")

    if candidate_path.exists():
        content = candidate_path.read_text(encoding="utf-8").strip()
        if content:
            return content

    raise RuntimeError(
        "XHS cookie not provided. Set XHS_COOKIE environment variable or place "
        "a non-empty cookie string in cookie.txt (or specify XHS_COOKIE_FILE)."
    )


# 小红书配置
XHS_CONFIG = {
    "COOKIE": _load_cookie(),  # 必需包含 a1、web_session 和 webId 字段
}

# 监控对象配置
MONITOR_TARGETS = [
    {
        "nickname": "恋与深空",
        "id": "5c9cd8ca000000001202cba7",
        "keyword": ["思念", "生日"],
        "hot_gate": 40000,
    },
]

# 监控配置
MONITOR_CONFIG = {
    "CHECK_INTERVAL": 1800,  # 轮询频率，单位秒
    "ERROR_COUNT": 10,  # 连续错误次数阈值
    "ERROR_RETRY_WAIT": 60,  # API 调用失败后的等待时间（秒）
    "HOT_GATE_DAYS": 5,  # 点赞达标检查的时间窗口（天）
    "FIRST_RUN_WINDOW_HOURS": 24,  # 初次运行仅关注最近24小时笔记
    "LOG_DIR": "logs",
    "LOG_LEVEL": "INFO",
}

# Bark 推送配置
BARK_CONFIG = {
    "BASE_URL": "https://api.day.app",
    "DEVICE_KEY": ["你的设备密钥"],
    "GROUP": "xhs-monitor",
    "SOUND": "glass",
    "ICON": "",
}
