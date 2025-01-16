# 小红书配置
XHS_CONFIG = {
    "COOKIE": "你的小红书Cookie",  # 必需包含 a1、web_session 和 webId 字段
}

# 企业微信应用配置
WECOM_CONFIG = {
    "CORPID": "你的企业ID",  # 企业ID
    "AGENTID": "你的应用ID",  # 应用ID
    "SECRET": "你的应用Secret",  # 应用的Secret
}

# 监控配置
MONITOR_CONFIG = {
    "USER_ID": "要监控的用户ID",
    "CHECK_INTERVAL": 5,  # 建议至少5秒以上
    "ERROR_COUNT": 10,  # 连续错误次数
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
7. 避免过于模板化的表达"""
} 