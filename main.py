import os, sys, time, requests
from pathlib import Path
from seleniumbase import SB

# --- 配置区 ---
# 从 GitHub Secrets 读取
EMAIL = os.environ.get("USER_EMAIL")
PASSWORD = os.environ.get("USER_PASSWORD")
TG_TOKEN = os.environ.get("TG_BOT_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")

TARGET_URL = "https://searcade.com/en/"
OUTPUT_DIR = Path("output/screenshots")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# --- 工具函数 ---
def send_tg_msg(text, img_path=None):
    if not TG_TOKEN or not TG_CHAT_ID: return
    try:
        base_url = f"https://api.telegram.org/bot{TG_TOKEN}"
        requests.post(f"{base_url}/sendMessage", json={"chat_id": TG_CHAT_ID, "text": text})
        if img_path and Path(img_path).exists():
            with open(img_path, "rb") as f:
                requests.post(f"{base_url}/sendPhoto", data={"chat_id": TG_CHAT_ID}, files={"photo": f})
    except Exception as e:
        print(f"[TG ERROR] {e}")

def shot(stage: str) -> str:
    filename = f"searcade_{int(time.time())}_{stage}.png"
    p = OUTPUT_DIR / filename
    return str(p)

# --- 核心逻辑 ---
def handle_cf_turnstile(sb):
    """过 CF 验证的关键模块"""
    try:
        # 检查是否存在 CF 框架
        if sb.is_element_present('iframe[src*="cloudflare"]'):
            print("[INFO] 发现 Cloudflare 验证，尝试自动点击...")
            time.sleep(2)
            sb.uc_gui_click_captcha() # 使用你代码里的过 CF 模块
            time.sleep(4)
    except:
        pass

def main():
    # UC 模式启动配置
    opts = {
        "uc": True,             # 开启 Undetected 模式
        "test": True, 
        "locale": "en", 
        "headed": False,        # GitHub Actions 设为 False
        "timeout_multiplier": 1.5 
    }

    with SB(**opts) as sb:
        try:
            # 1. 进入首页
            print("[*] 打开首页...")
            sb.uc_open_with_reconnect(TARGET_URL, reconnect_time=5.0)
            img1 = shot("home")
            sb.save_screenshot(img1)
            send_tg_msg("1. 已进入首页", img1)

            # 2. 点击登录链接 (使用你提供的 XPATH)
            login_xpath = '//*[@id="navbarSupportedContent"]/ul[2]/li[2]/a'
            sb.wait_for_element_visible(login_xpath, timeout=10)
            sb.click(login_xpath)
            print("[*] 已点击登录入口，等待跳转...")

            # 3. 处理跳转后的 CF 验证
            time.sleep(5) 
            handle_cf_turnstile(sb)
            
            # 检查 Email 输入框是否存在
            email_xpath = '//*[@id="email"]'
            if not sb.is_element_visible(email_xpath):
                # 如果没看到输入框，可能还在验证页面，再点一次
                handle_cf_turnstile(sb)

            # 4. 输入邮箱
            sb.wait_for_element_visible(email_xpath, timeout=20)
            img2 = shot("auth_page")
            sb.save_screenshot(img2)
            send_tg_msg("2. 进入授权页/过CF成功", img2)

            sb.type(email_xpath, EMAIL)
            # 点击 Continue (使用你提供的 XPATH)
            sb.click('//*[@id="__nuxt"]/div/div/div[2]/div/div[2]/form/div/div[2]/button')
            print("[*] 已提交邮箱")

            # 5. 输入密码
            pwd_xpath = '//*[@id="password"]'
            sb.wait_for_element_visible(pwd_xpath, timeout=15)
            sb.type(pwd_xpath, PASSWORD)
            
            img3 = shot("pwd_page")
            sb.save_screenshot(img3)

            # 点击最终登录 (使用你提供的 XPATH)
            sb.click('//*[@id="__nuxt"]/div/div/div[2]/div/div[2]/form/div/div[3]/button')
            print("[*] 正在执行最终登录...")

            # 6. 完成并确认
            time.sleep(8) # 等待回调跳转
            img4 = shot("final")
            sb.save_screenshot(img4)
            
            curr_url = sb.get_current_url()
            send_tg_msg(f"✅ 登录流程完成！\n最终URL: {curr_url}", img4)

        except Exception as e:
            err_img = shot("error")
            sb.save_screenshot(err_img)
            send_tg_msg(f"❌ 运行异常: {str(e)}", err_img)
            print(f"[ERROR] {e}")

if __name__ == "__main__":
    main()
