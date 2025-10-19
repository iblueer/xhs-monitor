1. 进入目录并创建虚拟环境
   ```bash
   cd /root/app/xhs-monitor
      pyenv virtualenv 3.13.7 xhs-monitor-3.13 
      # ↑因为是用pyenv设置的local python，不能用python -m venv venv
      pyenv activate xhs-monitor-3.13
   ```

2. 安装依赖
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   python -m playwright install chromium
   ```

3. 配置文件
   ```bash
   cp config.example.py config.py
   ```
   根据你的实际信息编辑 config.py：填入 XHS_CONFIG（Cookie）、BARK_CONFIG 的 DEVICE_KEY 等，以及 MONITOR_TARGETS
 列表。

4. 首次运行检查
   ```bash
   python monitor.py
   ```
   观察日志输出，确认能正常获取笔记并推送（首次仅处理最近 24 小时内的新笔记）。

5. 长期运行（可选）
   - 使用 tmux/screen 保持会话：
   ```bash
   tmux new -s xhs-monitor
   pyenv activate xhs-monitor-3.13
   python monitor.py
   ```
   按 Ctrl+B → D 分离；tmux attach -t xhs-monitor 回去查看。
   - 或写简单的 systemd 服务（按需）。

6. 日志与维护
   - 终端输出即日志，可视需要定向重定向到文件，例如：
   ```bash
   python monitor.py >> monitor.log 2>&1
   ```
   - 定期更新 Cookie、检查 Bark 推送是否成功。

------------

切换环境

pyenv local 3.13.7

验证 & 环境配置
   1. 确认当前 shell 已切换到 Pyenv 的 Python：
      ```bash
      python -V
      which python
      ```
      若显示 Python 3.13.7 且路径位于
   ~/.pyenv/versions/3.13.7/bin/python，说明成功。

   2. 若准备专用环境，可创建虚拟环境：
      ```bash
      pyenv virtualenv 3.13.7 xhs-monitor-3.13
      pyenv activate xhs-monitor-3.13
      ```

   安装依赖

   bash
     cd /root/app/xhs-monitor
     pip install --upgrade pip
     pip install -r requirements.txt
     python -m playwright install chromium