"""
Website Change Monitor - socialsecurity.wb.gov.in
SSL Legacy Renegotiation fix + Telegram Alert + GitHub Actions support
"""

import requests
import urllib3
import ssl
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

# ============================================================
#  CONFIGURATION — GitHub Secrets se aayega (hardcode mat karo)
# ============================================================
URL        = "https://socialsecurity.wb.gov.in/login"
STATE_FILE = "website_state.json"

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID", "")

# ============================================================


class LegacySSLAdapter(requests.adapters.HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        ctx.options |= 0x4
        ctx.check_hostname = False
        ctx.verify_mode    = ssl.CERT_NONE
        kwargs["ssl_context"] = ctx
        return super().init_poolmanager(*args, **kwargs)


def make_session():
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    session = requests.Session()
    session.mount("https://", LegacySSLAdapter())
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    })
    return session


def fetch_page(url):
    session = make_session()
    try:
        r = session.get(url, timeout=20)
        r.raise_for_status()
        print(f"[OK] Fetch successful — Status: {r.status_code}")
        return r.text
    except requests.exceptions.ConnectionError as e:
        print(f"[ERROR] Connection nahi hua: {e}")
    except requests.exceptions.Timeout:
        print("[ERROR] Timeout")
    except Exception as e:
        print(f"[ERROR] {e}")
    return None


def extract_state(html):
    soup = BeautifulSoup(html, "html.parser")
    state = {}

    state["links"] = [
        {"text": a.get_text(strip=True), "href": a["href"]}
        for a in soup.find_all("a", href=True)
    ]
    state["action_buttons"] = [
        {"text": a.get_text(strip=True), "href": a.get("href", "")}
        for a in soup.find_all("a", class_=lambda c: c and "premium-action-btn" in c)
    ]
    state["form_inputs"] = [
        {"name": inp.get("name",""), "type": inp.get("type",""), "placeholder": inp.get("placeholder","")}
        for inp in soup.find_all("input")
        if inp.get("type") not in ["hidden", "submit"]
    ]
    state["buttons"] = [b.get_text(strip=True) for b in soup.find_all("button")]
    state["headings"] = [
        {"tag": h.name, "text": h.get_text(strip=True)}
        for h in soup.find_all(["h1","h2","h3","h4"])
        if h.get_text(strip=True)
    ]
    footer = soup.find("footer")
    state["footer_links"] = (
        [{"text": a.get_text(strip=True), "href": a["href"]} for a in footer.find_all("a", href=True)]
        if footer else []
    )
    t = soup.find("title")
    state["page_title"] = t.get_text(strip=True) if t else ""
    return state


def find_changes(old, new):
    changes = []
    for section in new:
        old_val = old.get(section)
        new_val = new.get(section)

        if section == "page_title":
            if old_val != new_val:
                changes.append(f"📄 Page Title badla:\n  Pehle: {old_val}\n  Ab: {new_val}")
            continue

        old_set = {json.dumps(x, sort_keys=True, ensure_ascii=False) for x in (old_val or [])}
        new_set = {json.dumps(x, sort_keys=True, ensure_ascii=False) for x in (new_val or [])}

        label = section.replace("_", " ").title()
        for item in new_set - old_set:
            changes.append(f"✅ NEW {label} added:\n  {item}")
        for item in old_set - new_set:
            changes.append(f"❌ {label} removed:\n  {item}")
    return changes


def send_telegram(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[TELEGRAM] Token ya Chat ID missing!")
        return
    api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        r = requests.post(api_url, json=payload, timeout=10)
        if r.status_code == 200:
            print("[TELEGRAM] ✅ Message bheja gaya!")
        else:
            print(f"[TELEGRAM] ❌ {r.status_code} — {r.text}")
    except Exception as e:
        print(f"[TELEGRAM] ❌ {e}")


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def run_monitor():
    now = datetime.now().strftime("%d %b %Y, %I:%M:%S %p")
    print("=" * 55)
    print(f"  Website Monitor — {now}")
    print(f"  URL: {URL}")
    print("=" * 55)

    html = fetch_page(URL)
    if not html:
        msg = (f"⚠️ <b>Website Fetch FAILED</b>\n🕐 {now}\n🔗 {URL}\n\n"
               f"Website not responding.")
        print("\n[FAIL] Website fetch nahi ho saki.")
        send_telegram(msg)
        return

    new_state = extract_state(html)
    old_state  = load_state()

    if old_state is None:
        save_state(new_state)
        summary = (
            f"🟢 <b>Website Monitoring Initiated</b>\n🕐 {now}\n🔗 {URL}\n\n"
            f"Baseline Snapshot Saved:\n"
            f"  • Links: {len(new_state['links'])}\n"
            f"  • Action Buttons: {len(new_state['action_buttons'])}\n"
            f"  • Form Inputs: {len(new_state['form_inputs'])}\n"
            f"  • Headings: {len(new_state['headings'])}\n"
            f"  • Footer Links: {len(new_state['footer_links'])}\n"
            f"  • Page Title: {new_state['page_title']}"
        )
        print("\n[INFO] Pehli baar — baseline save ho gayi.")
        send_telegram(summary)
        return

    changes = find_changes(old_state, new_state)

    if changes:
        save_state(new_state)
        change_text = "\n".join(changes)
        msg = (
            f"🚨 <b>Website Change Detected!</b>\n🕐 {now}\n🔗 {URL}\n\n"
            f"<b>{len(changes)} change(s) :</b>\n\n{change_text}"
        )
        print(f"\n🚨 {len(changes)} CHANGE(S) !\n")
        for c in changes:
            print(f"  {c}")
        send_telegram(msg)
    else:
        print("\n✅ Koi change nahi mila. Website same hai.")


if __name__ == "__main__":
    run_monitor()
