import os
import requests
from playwright.sync_api import sync_playwright, TimeoutError

# 从环境变量读取配置
EMAIL = os.environ.get("USER_EMAIL")
PASSWORD = os.environ.get("USER_PASSWORD")
TG_TOKEN = os.environ.get("TG_BOT_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")

def send_tg_msg(text, photo_path=None):
    """发送文字或图片到 Telegram"""
    try:
        if photo_path:
            url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
            with open(photo_path, "rb") as photo:
                requests.post(url, data={"chat_id": TG_CHAT_ID, "caption": text}, files={"photo": photo})
        else:
            url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
            requests.post(url, data={"chat_id": TG_CHAT_ID, "text": text})
    except Exception as e:
        print(f"[!] Telegram 发送失败: {e}")

def run():
    with sync_playwright() as p:
        # 启动浏览器
        browser = p.chromium.launch(headless=True)
        # 设置较大的视口确保元素可见
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()

        try:
            # 1. 打开 Searcade 首页
            print("[*] 正在打开首页...")
            page.goto("https://searcade.com/en/", wait_until="networkidle")
            page.screenshot(path="step1_home.png")
            send_tg_msg("步骤 1: 已进入首页", "step1_home.png")

            # 点击 Login 链接
            print("[*] 正在点击登录入口...")
            page.click('//*[@id="navbarSupportedContent"]/ul[2]/li[2]/a')
            
            # 2. 等待跳转到 Userveria 授权页
            print("[*] 等待授权页面加载...")
            page.wait_for_selector('//*[@id="email"]', timeout=30000)
            page.screenshot(path="step2_auth_page.png")
            send_tg_msg(f"步骤 2: 已进入授权页\n当前URL: {page.url}", "step2_auth_page.png")

            # 输入 Email
            print("[*] 正在输入 Email...")
            page.fill('//*[@id="email"]', EMAIL)
            page.screenshot(path="step2_email_filled.png")

            # 3. 点击 Continue
            print("[*] 点击 Continue with email...")
            page.click('//*[@id="__nuxt"]/div/div/div[2]/div/div[2]/form/div/div[2]/button')
            
            # 4. 输入密码
            print("[*] 等待并输入密码...")
            page.wait_for_selector('//*[@id="password"]', timeout=15000)
            page.screenshot(path="step4_password_page.png")
            send_tg_msg("步骤 4: 密码框已出现", "step4_password_page.png")
            
            page.fill('//*[@id="password"]', PASSWORD)

            # 5. 点击最终登录
            print("[*] 执行最终登录...")
            page.click('//*[@id="__nuxt"]/div/div/div[2]/div/div[2]/form/div/div[3]/button')
            
            # 等待跳转完成或网络空闲
            page.wait_for_load_state("networkidle")
            time_now = page.evaluate("() => new Date().toLocaleString()")
            page.screenshot(path="step5_final.png")
            
            # 验证是否拿到 Token (根据你之前的逻辑，可能在 Cookie 或 localStorage)
            final_cookies = page.context.cookies()
            has_token = any('token' in c['name'].lower() for c in final_cookies)
            
            send_tg_msg(f"步骤 5: 登录操作完成\n时间: {time_now}\n检测到Cookie Token: {has_token}", "step5_final.png")

        except TimeoutError as e:
            page.screenshot(path="error_timeout.png")
            send_tg_msg(f"❌ 运行超时: 某个元素未能在规定时间内加载\n{str(e)}", "error_timeout.png")
        except Exception as e:
            page.screenshot(path="error_general.png")
            send_tg_msg(f"❌ 运行异常:\n{str(e)}", "error_general.png")
        finally:
            browser.close()

if __name__ == "__main__":
    run()
