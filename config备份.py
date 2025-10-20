# 小红书配置
XHS_CONFIG = {
    "COOKIE": "abRequestId=e51663d8-5096-5dd3-9e8b-c6877c1adc22; xsecappid=xhs-pc-web; a1=1948d17355cdf278vvaiyed12tf5zdeox3qcueqyz30000190930; webId=9063cbd08a678ddcf6e6fa1abaef9ea2; gid=yj4YfyW4WDCYyj4YfyWq2qdA2SfiJWYhh03vAvudfyJ9iSq82ufdl7888yj8jq88qYiSD02d; x-hng=lang=zh-CN&domain=www.xiaohongshu.com; web_session=040069b1bc58bf57b26b501eda3a4b7a1e756b; webBuild=4.83.0; unread={%22ub%22:%2268f42379000000000302f980%22%2C%22ue%22:%2268f2469500000000040171b2%22%2C%22uc%22:29}; websectiga=82e85efc5500b609ac1166aaf086ff8aa4261153a448ef0be5b17417e4512f28; sec_poison_id=5085056d-b06d-43a6-97a7-081c585d46e9; acw_tc=0a00d14717608823240471352ed75f6da04751e17f048b695fb99ddf6794ec; loadts=1760882325029",  # 必需包含 a1、web_session 和 webId 字段
}

# 监控对象配置
MONITOR_TARGETS = [
  {
    "nickname": "恋与深空",
    "id": "5c9cd8ca000000001202cba7",
    "keyword": [
      "思念",
      "生日"
    ],
    "hot_gate": 40000
  },
  {
    "nickname": "光与夜之恋",
    "id": "5e0c44ae0000000001007cde",
    "keyword": [
      "生日"
    ],
    "hot_gate": 5000
  },
  {
    "nickname": "未定事件簿",
    "id": "617fa8a40000000002027760",
    "keyword": [
      "SSR",
      "SR",
      "MR",
      "生日",
      "复刻"
    ],
    "hot_gate": 5000
  },
  {
    "nickname": "世界之外",
    "id": "6246c1690000000021028819",
    "keyword": [
      "侧影",
      "生日"
    ],
    "hot_gate": 5000
  },
  {
    "nickname": "时空中的绘旅人",
    "id": "5f7963b1000000000101c473",
    "keyword": [
      "SSR",
      "SR",
      "CR",
      "生日"
    ],
    "hot_gate": 5000
  },
  {
    "nickname": "测试账号-请勿关注",
    "id": "673488e4000000001c0189ae",
    "keyword": [
      "贪玩",
      "生日"
    ],
    "hot_gate": 1
  }
]

# 监控配置
MONITOR_CONFIG = {
    "CHECK_INTERVAL": 60,  # 轮询频率，单位秒，默认1800
    "ERROR_COUNT": 10,  # 连续错误次数阈值
    "ERROR_RETRY_WAIT": 60,  # API 调用失败后的等待时间（秒）
    "HOT_GATE_DAYS": 5,  # 点赞达标检查的时间窗口（天）
    "FIRST_RUN_WINDOW_HOURS": 24,
    "LOG_DIR": "logs",
    "LOG_LEVEL": "INFO",
}

# Bark 推送配置
BARK_CONFIG = {
    "BASE_URL": "https://api.day.app",
    "DEVICE_KEY": [
        "XCi4Mv8K83vpaWPKZZjNDW",  # 百鬼手机
        "xJrGobCtApZZZ2NGXPaWtc",  # maemo 手机
    ],
    "GROUP": "xhs-monitor",
    "SOUND": "glass",
    "ICON": "",
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
7. 避免过于模板化的表达"""
} 