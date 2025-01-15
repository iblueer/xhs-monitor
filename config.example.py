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
    "COMMENTS": [  # 随机选择一条评论
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