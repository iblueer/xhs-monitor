import os
from pathlib import Path
from playwright.sync_api import sync_playwright
from time import sleep
from datetime import datetime

def xhs_sign(uri, data=None, a1="", web_session=""):
    last_err = None
    for _ in range(10):
        try:
            with sync_playwright() as playwright:
                base_dir = Path(__file__).resolve().parent
                stealth_js_path = str(base_dir / "public" / "stealth.min.js")
                if not Path(stealth_js_path).exists():
                    raise FileNotFoundError(f"stealth script missing: {stealth_js_path}")

                chromium = playwright.chromium
                headless_env = os.getenv("XHS_HEADLESS", "1").lower()
                headless = headless_env not in {"0", "false", "no"}
                launch_kwargs = {}
                if os.getenv("XHS_NO_SANDBOX", "").strip():
                    launch_kwargs["args"] = ["--no-sandbox"]

                browser = chromium.launch(headless=headless, **launch_kwargs)
                browser_context = browser.new_context()
                browser_context.add_init_script(path=stealth_js_path)
                context_page = browser_context.new_page()
                context_page.goto("https://www.xiaohongshu.com", wait_until="domcontentloaded")

                cookies = [
                    {"name": "a1", "value": a1 or "", "domain": ".xiaohongshu.com", "path": "/"},
                ]
                if web_session:
                    cookies.append({"name": "web_session", "value": web_session, "domain": ".xiaohongshu.com", "path": "/"})
                browser_context.add_cookies(cookies)

                context_page.reload(wait_until="domcontentloaded")
                wait_ms = int(os.getenv("XHS_SIGN_WAIT_MS", "1000"))
                sleep(wait_ms / 1000.0)

                context_page.wait_for_function(
                    "() => typeof window._webmsxyw === 'function'",
                    timeout=15000,
                )
                encrypt_params = context_page.evaluate(
                    "([url, data]) => window._webmsxyw(url, data)", [uri, data]
                )
                return {"x-s": encrypt_params["X-s"], "x-t": str(encrypt_params["X-t"])}
        except Exception as e:
            last_err = e
            # 常见：未安装浏览器（需要 `playwright install`）或 Linux 依赖缺失（需要 `playwright install-deps`）
            continue
    raise Exception(f"重试了这么多次还是无法签名成功，寄寄寄 | last_error: {last_err}")


def parse_timestamp(timestamp: int) -> str:
    if not timestamp:
        return ""
    try:
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return ""
