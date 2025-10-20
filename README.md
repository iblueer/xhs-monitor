# xhs-monitor

多账号、小红书运营场景的自动监控工具：定时拉取账号最新笔记，判断是否命中关键词或达到点赞阈值，并通过 Bark 同时推送到多台 iOS 设备。

## 功能一览

- **多账号监控**：`MONITOR_TARGETS` 数组支持配置多个账号，独立的关键词和点赞阈值。
- **关键词提醒**：每次轮询（由 `CHECK_INTERVAL` 决定）检查新笔记标题，命中关键词即时推送「重要更新提醒」。
- **点赞达标提醒 (Hot-Gate)**：默认每天执行一次（启动时先跑一次），点赞首次达到 `hot_gate` 阈值就推送「点赞达标提醒」。
- **多设备 Bark 推送**：`DEVICE_KEY` 支持数组，多个 key 会逐一推送，任何一次成功视为整体成功。
- **数据库追踪**：`notes.db` 记录笔记发布时间、点赞数和已推送记录，避免重复提醒。
- **详尽日志**：`logs/monitor.log` 包含 DEBUG 级别的发布时间回退、点赞原始值等诊断信息。

## 目录说明

- `monitor.py`：核心监控逻辑（轮询、关键词匹配、hot-gate 检查、推送）。
- `db.py`：SQLite 封装，管理笔记信息、点赞数和通知历史。
- `bark.py`：Bark 推送客户端，支持多设备发送、自定义分组音效。
- `config.py` / `config.example.py`：运行配置；生产环境请复制后自定义。
- `logs/`：日志目录，按天滚动保留 7 份。
- `notes.db`：SQLite 数据库文件。

## 快速上手

### 1. 准备环境

- 推荐 Python ≥ 3.9，若服务器系统 Python 无法升级（如云主机锁定 3.8），需使用 **pyenv** 安装：
  ```bash
  curl https://pyenv.run | bash
  pyenv install 3.13.7
  pyenv virtualenv 3.13.7 xhs-monitor-3.13
  pyenv activate xhs-monitor-3.13
  ```
- 安装依赖：
  ```bash
  pip install -r requirements.txt
  ```

### 2. 配置项目

1. 复制配置模板：
   ```bash
   cp config.example.py config.py
   ```
2. 填写关键参数：
   - `XHS_CONFIG.COOKIE`：必须包含 `a1`、`web_session`、`webId` 等字段；注意 Cookie 有效期有限，需定期更新。
   - `MONITOR_TARGETS`（数组）：
     - `nickname`：推送展示的账号名称。
     - `id`：小红书用户 ID。
     - `keyword`：关键词列表，任意命中标题即推送。
     - `hot_gate`：点赞阈值（整数）。
   - `MONITOR_CONFIG`：
     - `CHECK_INTERVAL`：轮询间隔（秒），决定新笔记检查频率。
     - `HOT_GATE_DAYS`：hot-gate 检查时只关注最近 N 天的笔记。
     - `FIRST_RUN_WINDOW_HOURS`：首次运行仅处理最近 N 小时内的笔记，防止历史笔记刷屏。
     - `LOG_LEVEL`：`DEBUG` 建议在调试时期使用。
   - `BARK_CONFIG.DEVICE_KEY`：支持字符串或列表，使用列表即可推送多台设备。

### 3. 运行

```bash
pyenv activate xhs-monitor-3.13  # 若使用 pyenv
python monitor.py
```

建议在 tmux / screen 中运行，以便 SSH 断开也能持续监控。

## 运行机制

- **新笔记检测**：按 `CHECK_INTERVAL` 周期拉取笔记，按发布时间排序后逐条处理；命中关键词即刻推送。
- **点赞达标检查**：程序启动时立即执行一次；之后每隔 24 小时运行一次。点赞首次达到 `hot_gate` 阈值时推送，并写入 `hot_gate_notifications`，避免重复提醒。
- **数据库信息**：
  - `notes` 表保存发布时间、标题、最新点赞数等。
  - `hot_gate_notifications` 表记录推送过的笔记 ID、点赞数与时间。
- **日志**：
  - `INFO` 显示关键流程（启动、命中、推送结果）。
  - `DEBUG` 记录发布时间回退逻辑、点赞原始值、点赞数变化等，有助排查。

## 常见问题与排坑建议

| 场景 | 说明 / 解决方案 |
| --- | --- |
| 服务器 Python 版本过旧 | 使用 **pyenv** 安装新版 Python，再创建虚拟环境运行。|
| Cookie 过期/失效 | 重新在浏览器抓取最新 Cookie，确保包含必要字段。|
| 首次运行提醒过多 | 调低 `FIRST_RUN_WINDOW_HOURS`（如 12），限制首次处理的笔记范围。|
| 热门提醒未触发 | 查看 `logs/monitor.log` 中 `点赞原始数据`、`点赞数据` 日志，并确认 `hot_gate_notifications` 是否已有记录。|
| 运行多个配置 | 同机多实例运行时，建议复制项目目录，确保 `config.py`、`notes.db`、`logs/` 互不影响。|
| Bark 推送失败 | 检查日志中的 Bark 响应码、确认设备 key 正确且网络未被屏蔽。|

## 数据与运维

- **数据库操作**：
  - 备份：`cp notes.db notes.db.bak`
  - 查询热门提醒：`sqlite3 notes.db "SELECT * FROM hot_gate_notifications ORDER BY notified_time DESC;"`
- **日志查看**：`tail -f logs/monitor.log`
- **升级流程**：
  1. 覆盖更新后的 `monitor.py`、`db.py`、`bark.py` 等文件。
  2. 重启脚本，观察日志出现最新 `xhs-monitor version` 行，确认新代码已运行。

## 教程与扩展

- [追女神必备！使用 Python 构建小红书用户动态监控系统](./docs/追女神必备！使用%20Python%20构建小红书用户动态监控系统.md)
- [追女神必备！使用 Python 构建小红书用户动态监控系统（二）- 实现自动点赞和评论功能](./docs/追女神必备！使用%20Python%20构建小红书用户动态监控系统（二）-%20实现自动点赞和评论功能.md)

> 注意：上面教程涉及早期「企业微信推送」「自动互动」逻辑，本项目已切换为 Bark 推送并移除自动点赞/评论，请参考本文档为准。

## 贡献

欢迎提交 Issue / PR，或分享你的部署经验，一起完善小红书监控工具链。
