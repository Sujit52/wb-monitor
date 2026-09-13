import re
import random
import string
import requests
import os

URL = "https://danael.fun/create/cloudfront/"

# GitHub Secrets se aayega
TG_TOKEN = os.environ["TG_TOKEN"]
TG_CHAT_ID = os.environ["TG_CHAT_ID"]
FIXED_PASSWORD = os.environ.get("FIXED_PASSWORD", "973497")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:150.0) Gecko/20100101 Firefox/150.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://danael.fun",
    "Referer": "https://danael.fun/create/cloudfront/",
    "Upgrade-Insecure-Requests": "1",
    "Connection": "keep-alive",
}


def random_user():
    return "Sd" + "".join(random.choices(string.ascii_letters + string.digits, k=6))


def nikaal(html, label):
    pattern = rf"{label}\s*</span>\s*<span[^>]*class=['\"]value[^'\"]*['\"][^>]*>(.*?)</span>"
    m = re.search(pattern, html, re.S)
    return m.group(1).strip() if m else None


def nikaal_ssh_host(html):
    m = re.search(r"Host:\s*([^\s<]+)", html)
    return m.group(1).strip() if m else None


def telegram_bhej(message):
    try:
        tg_url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        r = requests.post(
            tg_url,
            data={
                "chat_id": TG_CHAT_ID,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
            timeout=15,
        )
        print(f"Telegram: {r.status_code}")
        return r.status_code == 200
    except Exception as e:
        print(f"Telegram error: {e}")
        return False


def account_banao(server="usa"):
    session = requests.Session()
    session.headers.update(HEADERS)
    session.get(URL, timeout=20)

    username = random_user()
    password = FIXED_PASSWORD

    data = {"username": username, "password": password, "server_choice": server}
    r = session.post(URL, data=data, timeout=20)
    html = r.text

    if "Account Created" not in html and "Cuenta Creada" not in html:
        print(f"Account nahi bana — status {r.status_code}")
        return None

    return {
        "ssh_user": nikaal(html, "Username"),
        "password": nikaal(html, "Password"),
        "uuid": nikaal(html, "UUID (V2RAY)"),
        "server_name": nikaal(html, "SERVER"),
        "expiry": nikaal(html, "EXPIRY"),
        "host": nikaal_ssh_host(html),
    }


def main():
    print("Account bana raha hun...")
    acc = account_banao(server="usa")
 #server= mein konsa server create karna hai woh likho jese brazil server create karna hai toh kansas add karna hai
    #Singapore 🇸🇬 usa
    #Brazil 🇧🇷 kansas
    #Indonesia 🇮🇩 indonesia

    if acc:
        print(f"Ban gaya: {acc['ssh_user']}")
        msg = (
            f"✅ <b>Auto Account Created</b>\n\n"
            f"👤 <b>Username:</b> <code>{acc['ssh_user']}</code>\n"
            f"🔑 <b>Password:</b> <code>{acc['password']}</code>\n"
            f"🌐 <b>Host:</b> <code>{acc['host']}</code>\n\n"
            f"<b>Extra:</b>\n"
            f"UUID: <code>{acc['uuid']}</code>\n"
            f"Server: {acc['server_name']}\n"
            f"Expiry: {acc['expiry']}"
        )
        telegram_bhej(msg)
    else:
        print("Fail hua")
        telegram_bhej("❌ <b>Auto Account Failed</b>\n\nDanael.fun pe account nahi ban paya. Kal phir try karega.")


if __name__ == "__main__":
    main()
