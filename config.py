import requests
import json
import time
import os
from datetime import datetime

# ================== تنظیمات بله (از Secrets) ==================
BOT_TOKEN = os.environ.get("BALETOKEN", "603151917:blnGc0J56ClrSyk79xWxdpJnBdO-gyerPaU")
BASE_URL = f"https://tapi.bale.ai/bot{BOT_TOKEN}/"
BOT_USERNAME = "DownModBot"
CREATOR = "@TheAghaBanafshi"
STATE_FILE = "data.json"
TEMP_DIR = "temp_files"

# ============ توکن CurseForge (از Secrets) ============
CURSEFORGE_TOKEN = os.environ.get("CURSEFORGE_TOKEN", "")
CURSEFORGE_API = "https://api.curseforge.com/v1"
CURSEFORGE_HEADERS = {
    "x-api-key": CURSEFORGE_TOKEN,
    "Accept": "application/json"
}

# ============ آیدی مالک ============
OWNER_ID = 448424297

# ============ تنظیمات Modrinth (جاوا) ============
MODRINTH_API = "https://api.modrinth.com/v2"
MODRINTH_USER_AGENT = "BaleBot/1.0 (contact@example.com)"

last_update_id = None
user_data = {}
user_state = {}
waiting_for = {}
waiting_for_admin = {}
custom_start_ids = {}

MAX_PART_SIZE = 18 * 1024 * 1024
VERSIONS_PER_PAGE = 10

# ============ لیست مرجع نسخه‌های ماینکرفت (نزولی) ============
MINECRAFT_VERSION_ORDER = [
    "26.3", "26.2", "26.1", "26.1.2", "26.1.1",
    "1.21.11", "1.21.10", "1.21.9", "1.21.8", "1.21.7", "1.21.6", "1.21.5", "1.21.4", "1.21.3", "1.21.2", "1.21.1", "1.21",
    "1.20.6", "1.20.5", "1.20.4", "1.20.3", "1.20.2", "1.20.1", "1.20",
    "1.19.4", "1.19.3", "1.19.2", "1.19.1", "1.19",
    "1.18.2", "1.18.1", "1.18",
    "1.17.1", "1.17",
    "1.16.5", "1.16.4", "1.16.3", "1.16.2", "1.16.1", "1.16",
    "1.15.2", "1.15.1", "1.15",
    "1.14.4", "1.14.3", "1.14.2", "1.14.1", "1.14",
    "1.13.2", "1.13.1", "1.13",
    "1.12.2", "1.12.1", "1.12",
    "1.11.2", "1.11.1", "1.11",
    "1.10.2", "1.10.1", "1.10",
    "1.9.4", "1.9.3", "1.9.2", "1.9.1", "1.9",
    "1.8.9", "1.8.8", "1.8.7", "1.8.6", "1.8.5", "1.8.4", "1.8.3", "1.8.2", "1.8.1", "1.8",
    "1.7.10", "1.7.9", "1.7.8", "1.7.7", "1.7.6", "1.7.5", "1.7.4", "1.7.3", "1.7.2",
    "1.6.4", "1.6.2", "1.6.1", "1.6",
    "1.5.2", "1.5.1", "1.5",
    "1.4.7", "1.4.6", "1.4.5", "1.4.4", "1.4.2",
    "1.3.2", "1.3.1",
    "1.2.5", "1.2.4", "1.2.3", "1.2.2", "1.2.1",
    "1.1", "1.0",
]

VERSION_INDEX = {v: i for i, v in enumerate(MINECRAFT_VERSION_ORDER)}


# ============ ذخیره و بازیابی ============
def load_state():
    global last_update_id, user_data, custom_start_ids
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                last_update_id = data.get("last_update_id")
                user_data = data.get("user_data", {})
                custom_start_ids = data.get("custom_start_ids", {})
        except Exception as e:
            print(f"[State] خطا: {e}")
            last_update_id = None
            user_data = {}
            custom_start_ids = {}


def save_state():
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "last_update_id": last_update_id,
                "user_data": user_data,
                "custom_start_ids": custom_start_ids
            }, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[State] خطا در ذخیره: {e}")


def get_user(user_id):
    uid = str(user_id)
    if uid not in user_data:
        user_data[uid] = {
            "coins": 0.0,
            "last_daily": None,
            "invited_by": None,
            "has_started": False,
            "name": "",
            "username": ""
        }
    return user_data[uid]


def get_coins_display(user_id):
    if user_id == OWNER_ID:
        return "∞"
    u = get_user(user_id)
    return f"{u['coins']:.1f}"


# ============ ارسال پیام ============
def send_message(chat_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    try:
        r = requests.post(BASE_URL + "sendMessage", json=payload, timeout=30)
        return r.json()
    except Exception as e:
        print(f"[Send] {e}")
        return None


def edit_message(chat_id, message_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "message_id": message_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    try:
        r = requests.post(BASE_URL + "editMessageText", json=payload, timeout=30)
        return r.json()
    except Exception as e:
        print(f"[Edit] {e}")
        return None


def answer_callback(callback_query_id, text=""):
    payload = {"callback_query_id": callback_query_id}
    if text:
        payload["text"] = text
    try:
        requests.post(BASE_URL + "answerCallbackQuery", json=payload, timeout=10)
    except:
        pass


# ============ ارسال فایل ============
def send_document(chat_id, document_url, caption=""):
    payload = {"chat_id": chat_id, "document": document_url}
    if caption:
        payload["caption"] = caption
    try:
        r = requests.post(BASE_URL + "sendDocument", json=payload, timeout=120)
        return r.json()
    except Exception as e:
        print(f"[sendDocument] {e}")
        return None


def send_document_file(chat_id, file_path, caption=""):
    try:
        with open(file_path, "rb") as f:
            files = {"document": f}
            data = {"chat_id": chat_id}
            if caption:
                data["caption"] = caption
            r = requests.post(BASE_URL + "sendDocument", data=data, files=files, timeout=120)
            return r.json()
    except Exception as e:
        print(f"[sendDocumentFile] {e}")
        return None


# ============ تقسیم فایل ============
def split_file(file_path, part_size=MAX_PART_SIZE):
    os.makedirs(TEMP_DIR, exist_ok=True)
    parts = []
    base_name = os.path.basename(file_path)
    name, ext = os.path.splitext(base_name)
    try:
        with open(file_path, "rb") as f:
            part_num = 1
            while True:
                chunk = f.read(part_size)
                if not chunk:
                    break
                part_path = os.path.join(TEMP_DIR, f"{name}_part{part_num:02d}{ext}")
                with open(part_path, "wb") as pf:
                    pf.write(chunk)
                parts.append(part_path)
                part_num += 1
    except Exception as e:
        print(f"[Split] خطا: {e}")
        return []
    return parts


def download_file(url, dest_path):
    try:
        r = requests.get(url, stream=True, timeout=120)
        r.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"[Download] خطا: {e}")
        return False


# ============ Modrinth API (جاوا) ============
def modrinth_search(query, project_type="mod", limit=5):
    try:
        params = {
            "query": query,
            "limit": limit,
            "facets": json.dumps([[f"project_type:{project_type}"]])
        }
        r = requests.get(f"{MODRINTH_API}/search", params=params,
                         headers={"User-Agent": MODRINTH_USER_AGENT}, timeout=20)
        return r.json().get("hits", [])
    except Exception as e:
        print(f"[Modrinth Search] {e}")
        return []


def modrinth_get_versions(slug):
    try:
        r = requests.get(f"{MODRINTH_API}/project/{slug}/version",
                         params={"include_changelog": "false"},
                         headers={"User-Agent": MODRINTH_USER_AGENT}, timeout=20)
        return r.json()
    except Exception as e:
        print(f"[Modrinth Versions] {e}")
        return []


# ============ CurseForge API (بدراک) ============
def curseforge_search(query, is_resourcepack=False, limit=5):
    if not CURSEFORGE_TOKEN:
        print("[CurseForge] توکن تنظیم نشده است.")
        return []
    try:
        class_id = 12 if is_resourcepack else 6
        params = {
            "gameId": 432,
            "classId": class_id,
            "searchFilter": query,
            "pageSize": limit,
            "sortOrder": "desc"
        }
        r = requests.get(f"{CURSEFORGE_API}/mods/search", params=params,
                         headers=CURSEFORGE_HEADERS, timeout=20)
        data = r.json()
        return data.get("data", [])
    except Exception as e:
        print(f"[CurseForge Search] {e}")
        return []


def curseforge_get_files(mod_id):
    if not CURSEFORGE_TOKEN:
        return []
    try:
        r = requests.get(f"{CURSEFORGE_API}/mods/{mod_id}/files",
                         headers=CURSEFORGE_HEADERS, timeout=20)
        data = r.json()
        return data.get("data", [])
    except Exception as e:
        print(f"[CurseForge Files] {e}")
        return []


# ============ مرتب‌سازی نسخه‌ها (Modrinth) ============
def version_sort_key(v):
    gvs = v.get("game_versions", [])
    if not gvs:
        return 9999
    gv = gvs[0]
    return VERSION_INDEX.get(gv, 9999)
