import requests
import json
import time
import os
from datetime import datetime

# ================== تنظیمات بله ==================
BOT_TOKEN = "603151917:blnGc0J56ClrSyk79xWxdpJnBdO-gyerPaU"
BASE_URL = f"https://tapi.bale.ai/bot{BOT_TOKEN}/"
BOT_USERNAME = "DownModBot"
CREATOR = "@TheAghaBanafshi"
STATE_FILE = "data.json"
TEMP_DIR = "temp_files"

# ============ آیدی مالک ============
OWNER_ID = 448424297

# ============ تنظیمات Modrinth ============
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

# ساخت دیکشنری برای جستجوی سریع‌تر: {version: index}
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


# ============ Modrinth API ============
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
        print(f"[Search] {e}")
        return []


def modrinth_get_versions(slug, game_version=None):
    try:
        params = {"include_changelog": "false"}
        if game_version:
            params["game_versions"] = json.dumps([game_version])
        r = requests.get(f"{MODRINTH_API}/project/{slug}/version", params=params,
                         headers={"User-Agent": MODRINTH_USER_AGENT}, timeout=20)
        return r.json()
    except Exception as e:
        print(f"[Versions] {e}")
        return []


# ============ مرتب‌سازی نسخه‌ها ============
def version_sort_key(v):
    """مرتب‌سازی بر اساس لیست مرجع نسخه‌های ماینکرفت"""
    gvs = v.get("game_versions", [])
    if not gvs:
        return 9999
    gv = gvs[0]
    return VERSION_INDEX.get(gv, 9999)


# ============ دکمه‌های شیشه‌ای ============
def build_main_keypad(user_id):
    rows = [
        [{"text": "🔍 جستجوی ماد", "callback_data": "menu_mod"}],
        [{"text": "📦 جستجوی ریسورس‌پک", "callback_data": "menu_rp"}],
        [{"text": "🎁 دعوت دوستان", "callback_data": "menu_invite"}],
        [{"text": "💰 سکه‌های من", "callback_data": "menu_coins"}],
    ]
    if user_id == OWNER_ID:
        rows.append([{"text": "⚙️ پنل ادمین", "callback_data": "admin_panel"}])
    return {"inline_keyboard": rows}


def build_admin_keypad():
    return {
        "inline_keyboard": [
            [{"text": "💰 دادن سکه به کاربر", "callback_data": "admin_give_coins"}],
            [{"text": "📢 دادن سکه به همه", "callback_data": "admin_broadcast_coins"}],
            [{"text": "📨 پیام همگانی", "callback_data": "admin_broadcast_message"}],
            [{"text": "🔗 ساخت کد دعوت با سکه", "callback_data": "admin_custom_start"}],
            [{"text": "📊 آمار کل", "callback_data": "admin_stats"}],
            [{"text": "👥 لیست اعضا", "callback_data": "admin_members"}],
            [{"text": "🔙 برگشت", "callback_data": "menu_back"}],
        ]
    }


def build_results_keypad(hits):
    rows = []
    for h in hits[:5]:
        slug = h.get("slug", "")
        title = h.get("title", "بدون نام")[:25]
        rows.append([{"text": f"📦 {title}", "callback_data": f"mod_{slug}"}])
    return {"inline_keyboard": rows}


def build_versions_keypad_paginated(versions, slug, page=0):
    total = len(versions)
    total_pages = (total + VERSIONS_PER_PAGE - 1) // VERSIONS_PER_PAGE
    start = page * VERSIONS_PER_PAGE
    end = min(start + VERSIONS_PER_PAGE, total)
    rows = []
    for i in range(start, end):
        v = versions[i]
        vname = (v.get("name") or v.get("version_number", "-"))[:25]
        gv = ", ".join(v.get("game_versions", [])[:1])
        rows.append([{"text": f"⬇️ {vname} ({gv})", "callback_data": f"ver_{slug}_{i}"}])
    nav_row = []
    if page > 0:
        nav_row.append({"text": "⬅️ صفحه قبل", "callback_data": f"page_{slug}_{page-1}"})
    if page < total_pages - 1:
        nav_row.append({"text": "صفحه بعد ➡️", "callback_data": f"page_{slug}_{page+1}"})
    if nav_row:
        rows.append(nav_row)
    rows.append([{"text": "🔙 برگشت", "callback_data": "menu_mod"}])
    return {"inline_keyboard": rows}


def build_versions_text(slug, total, page=0):
    total_pages = (total + VERSIONS_PER_PAGE - 1) // VERSIONS_PER_PAGE
    return f"📦 نسخه‌های {slug}\n\nصفحه {page+1} از {total_pages} | مجموع: {total} نسخه"


# ============ منو ============
def get_menu_text(user_id):
    coins = get_coins_display(user_id)
    return f"""🤖 ربات Modrinth (بله)

💰 سکه‌های شما: {coins}

🔍 برای جستجوی ماد، روی دکمه بزن یا بنویس: mod <نام>
📦 برای ریسورس‌پک: rp <نام>
🎁 /invite — لینک دعوت
💰 /coins — موجودی سکه

━━━━━━━━━━━━
{CREATOR}"""


# ============ ارسال فایل هوشمند ============
def send_mod_file(chat_id, file_url, filename, file_size=None):
    if file_size and file_size < MAX_PART_SIZE:
        result = send_document(chat_id, file_url, caption=f"📦 {filename}")
        if result and result.get("ok"):
            return True
        send_message(chat_id, "⚠️ ارسال مستقیم ممکن نشد. در حال دانلود و تقسیم...")
    send_message(chat_id, f"⏳ در حال دانلود {filename}...")
    os.makedirs(TEMP_DIR, exist_ok=True)
    local_path = os.path.join(TEMP_DIR, filename)
    if not download_file(file_url, local_path):
        send_message(chat_id, f"❌ دانلود ناموفق. لینک مستقیم:\n{file_url}")
        return False
    actual_size = os.path.getsize(local_path)
    if actual_size < MAX_PART_SIZE:
        result = send_document_file(chat_id, local_path, caption=f"📦 {filename}")
        os.remove(local_path)
        if result and result.get("ok"):
            return True
        send_message(chat_id, f"❌ ارسال ناموفق. لینک:\n{file_url}")
        return False
    send_message(chat_id, f"📦 فایل {actual_size // (1024*1024)} مگابایت است. در حال تقسیم...")
    parts = split_file(local_path)
    if not parts:
        send_message(chat_id, f"❌ تقسیم ناموفق. لینک:\n{file_url}")
        os.remove(local_path)
        return False
    total_parts = len(parts)
    for i, part_path in enumerate(parts, 1):
        part_name = os.path.basename(part_path)
        caption = f"📦 {filename} — بخش {i} از {total_parts}"
        result = send_document_file(chat_id, part_path, caption=caption)
        if not result or not result.get("ok"):
            send_message(chat_id, f"❌ ارسال بخش {i} ناموفق.")
        os.remove(part_path)
        time.sleep(0.5)
    os.remove(local_path)
    if total_parts > 1:
        send_message(
            chat_id,
            f"✅ {total_parts} بخش ارسال شد.\n\n"
            f"🔧 برای مونتاژ در ویندوز:\n"
            f"1. همه فایل‌ها را در یک پوشه بگذارید.\n"
            f"2. CMD را باز کنید و دستور زیر را بزنید:\n"
            f"`copy /b {filename}_part01.ext + {filename}_part02.ext + ... {filename}`\n\n"
            f"یا از نرم‌افزار HJSplit استفاده کنید."
        )
    return True


# ============ لیست اعضا ============
def get_members_list():
    lines = ["👥 لیست اعضای ربات:\n"]
    count = 0
    for uid, u in user_data.items():
        name = u.get("name") or "نامشخص"
        username = u.get("username") or "-"
        coins = u.get("coins", 0)
        lines.append(f"👤 {name}\n🔗 @{username}\n🆔 {uid}\n💰 {coins:.1f} سکه\n")
        count += 1
    if count == 0:
        return "❌ هیچ عضوی یافت نشد."
    lines.append(f"📊 مجموع: {count} عضو")
    return "\n".join(lines)


# ============ پردازش آپدیت ============
def handle_update(update):
    global last_update_id, custom_start_ids

    if "message" in update:
        msg = update["message"]
        chat_id = msg["chat"]["id"]
        user_id = msg.get("from", {}).get("id")
        text = (msg.get("text") or "").strip()
        user_name = msg.get("from", {}).get("first_name", "")
        user_username = msg.get("from", {}).get("username", "")
        if not text or not user_id:
            return

        u = get_user(user_id)
        if user_name:
            u["name"] = user_name
        if user_username:
            u["username"] = user_username

        if chat_id in waiting_for_admin:
            mode = waiting_for_admin.pop(chat_id)
            if mode == "give_coins":
                parts = text.split()
                if len(parts) < 2:
                    send_message(chat_id, "❌ فرمت صحیح: <آیدی عددی> <مقدار سکه>\nمثال: 123456789 50")
                    return
                try:
                    target_id = int(parts[0])
                    amount = float(parts[1])
                except ValueError:
                    send_message(chat_id, "❌ آیدی و مقدار باید عدد باشند.")
                    return
                target = get_user(target_id)
                target["coins"] += amount
                save_state()
                send_message(chat_id, f"✅ {amount} سکه به کاربر {target_id} داده شد.\nموجودی جدید: {target['coins']:.1f}")
                return

            if mode == "broadcast_coins":
                try:
                    amount = float(text.strip())
                except ValueError:
                    send_message(chat_id, "❌ مقدار سکه باید عدد باشد.")
                    return
                count = 0
                for uid in list(user_data.keys()):
                    user_data[uid]["coins"] += amount
                    try:
                        send_message(int(uid), f"📢 {amount} سکه به طور همگانی فرستاده شد!\n💰 موجودی جدید: {user_data[uid]['coins']:.1f}")
                    except:
                        pass
                    count += 1
                save_state()
                send_message(chat_id, f"✅ {amount} سکه به {count} کاربر داده شد و به همه اعلان فرستاده شد.")
                return

            if mode == "broadcast_message":
                count = 0
                failed = 0
                for uid in list(user_data.keys()):
                    try:
                        result = send_message(int(uid), f"📨 پیام از طرف مدیریت:\n\n{text}")
                        if result and result.get("ok"):
                            count += 1
                        else:
                            failed += 1
                    except:
                        failed += 1
                    time.sleep(0.05)
                send_message(chat_id, f"✅ پیام همگانی ارسال شد.\n📤 موفق: {count}\n❌ ناموفق: {failed}")
                return

            if mode == "custom_start_id":
                parts = text.split()
                if len(parts) < 3:
                    send_message(chat_id, "❌ فرمت صحیح: <start_id> <تعداد سکه> <single|multi>\nمثال: BotNew1405 10 single")
                    return
                custom_id = parts[0].strip()
                try:
                    coins_amount = float(parts[1])
                except ValueError:
                    send_message(chat_id, "❌ تعداد سکه باید عدد باشد.")
                    return
                use_type = parts[2].strip().lower()
                if use_type not in ("single", "multi"):
                    send_message(chat_id, "❌ نوع استفاده باید single یا multi باشد.")
                    return
                if not custom_id or " " in custom_id:
                    send_message(chat_id, "❌ start_id نباید فاصله داشته باشد.")
                    return
                single_use = (use_type == "single")
                custom_start_ids[custom_id] = {
                    "coins": coins_amount,
                    "single_use": single_use,
                    "used_by": []
                }
                save_state()
                link = f"https://ble.ir/{BOT_USERNAME}?start={custom_id}"
                type_label = "یکبار مصرف" if single_use else "چندبار مصرف"
                send_message(
                    chat_id,
                    f"✅ کد جدید!\n\n"
                    f"🔗 لینک کد:\n{link}\n\n"
                    f"💰 تعداد سکه: {coins_amount}\n"
                    f"🔁 نوع: {type_label}\n\n"
                    f"{'این کد فقط برای اولین نفر کار می‌کند.' if single_use else 'هر کاربری که با این لینک وارد شود، سکه می‌گیرد.'}"
                )
                return

        if text.startswith("/start"):
            parts = text.split(maxsplit=1)
            param = parts[1].strip() if len(parts) > 1 else None

            if not u.get("has_started"):
                if param and param in custom_start_ids:
                    entry = custom_start_ids[param]
                    if entry.get("single_use") and entry.get("used_by"):
                        send_message(chat_id, "❌ این کد قبلاً استفاده شده است.")
                    else:
                        coins_amount = entry["coins"]
                        u["coins"] += coins_amount
                        entry["used_by"].append(str(user_id))
                        save_state()
                        send_message(chat_id, f"🎁 {coins_amount} سکه هدیه دریافت کردی!")
                elif param and param.isdigit() and str(param) != str(user_id):
                    inviter_id = param
                    if inviter_id in user_data:
                        user_data[inviter_id]["coins"] += 5.0
                        u["invited_by"] = inviter_id
                        save_state()
                        try:
                            send_message(int(inviter_id), "🎉 یک نفر با لینک شما وارد ربات شد! +۵ سکه")
                        except:
                            pass
                u["has_started"] = True
                save_state()

            today = datetime.now().strftime("%Y-%m-%d")
            if u.get("last_daily") != today:
                u["coins"] += 2.0
                u["last_daily"] = today
                save_state()
                daily_msg = "\n\n🎁 +۲ سکه روزانه دریافت کردی!"
            else:
                daily_msg = ""

            send_message(chat_id, get_menu_text(user_id) + daily_msg, reply_markup=build_main_keypad(user_id))
            return

        if text == "/admin":
            if user_id != OWNER_ID:
                send_message(chat_id, "❌ شما دسترسی به این بخش ندارید.")
                return
            send_message(chat_id, "⚙️ پنل ادمین:", reply_markup=build_admin_keypad())
            return

        if text == "/members":
            if user_id != OWNER_ID:
                send_message(chat_id, "❌ شما دسترسی به این بخش ندارید.")
                return
            members_text = get_members_list()
            if len(members_text) > 4000:
                for i in range(0, len(members_text), 4000):
                    send_message(chat_id, members_text[i:i+4000])
            else:
                send_message(chat_id, members_text)
            return

        if chat_id in waiting_for:
            mode = waiting_for.pop(chat_id)
            query = text.strip()
            if not query:
                send_message(chat_id, "❌ نام را وارد کن.")
                return
            send_message(chat_id, f"⏳ جستجوی «{query}»...")
            project_type = "mod" if mode == "mod" else "resourcepack"
            hits = modrinth_search(query, project_type)
            if not hits:
                send_message(chat_id, "❌ نتیجه‌ای یافت نشد.")
                return
            send_message(chat_id, "🔎 نتایج (روی دکمه بزن):", reply_markup=build_results_keypad(hits))
            return

        lower_text = text.lower()
        if lower_text.startswith("mod ") or lower_text == "mod":
            text = "/" + text
        elif lower_text.startswith("rp ") or lower_text == "rp":
            text = "/" + text

        if text == "/mod" or text.startswith("/mod "):
            if len(text.split()) < 2:
                send_message(chat_id, "❌ مثال: mod sodium")
                return
            arg = text.split(maxsplit=1)[1].strip()
            send_message(chat_id, f"⏳ جستجوی ماد «{arg}»...")
            hits = modrinth_search(arg, "mod")
            if not hits:
                send_message(chat_id, "❌ نتیجه‌ای یافت نشد.")
                return
            send_message(chat_id, "🔎 نتایج (روی دکمه بزن):", reply_markup=build_results_keypad(hits))
            return

        if text == "/rp" or text.startswith("/rp "):
            if len(text.split()) < 2:
                send_message(chat_id, "❌ مثال: rp faithful")
                return
            arg = text.split(maxsplit=1)[1].strip()
            send_message(chat_id, f"⏳ جستجوی ریسورس‌پک «{arg}»...")
            hits = modrinth_search(arg, "resourcepack")
            if not hits:
                send_message(chat_id, "❌ نتیجه‌ای یافت نشد.")
                return
            send_message(chat_id, "🔎 نتایج (روی دکمه بزن):", reply_markup=build_results_keypad(hits))
            return

        if text == "/invite":
            link = f"https://ble.ir/{BOT_USERNAME}?start={user_id}"
            send_message(chat_id, f"🎁 لینک دعوت اختصاصی شما:\n\n{link}\n\nبا هر نفر که از این لینک وارد بشه، ۵ سکه می‌گیری!")
            return

        if text == "/coins":
            send_message(chat_id, f"💰 سکه‌های شما: {get_coins_display(user_id)}")
            return

    if "callback_query" in update:
        cq = update["callback_query"]
        cq_id = cq["id"]
        chat_id = cq["message"]["chat"]["id"]
        message_id = cq["message"]["message_id"]
        user_id = cq["from"]["id"]
        data = cq.get("data", "")

        answer_callback(cq_id)

        u = get_user(user_id)

        if data == "menu_back":
            send_message(chat_id, get_menu_text(user_id), reply_markup=build_main_keypad(user_id))
            return

        if data == "menu_mod":
            waiting_for[chat_id] = "mod"
            send_message(chat_id, "🔍 نام ماد را بنویس (بدون اسلش):")
            return
        if data == "menu_rp":
            waiting_for[chat_id] = "rp"
            send_message(chat_id, "📦 نام ریسورس‌پک را بنویس (بدون اسلش):")
            return
        if data == "menu_invite":
            link = f"https://ble.ir/{BOT_USERNAME}?start={user_id}"
            send_message(chat_id, f"🎁 لینک دعوت اختصاصی شما:\n\n{link}\n\nبا هر نفر که از این لینک وارد بشه، ۵ سکه می‌گیری!")
            return
        if data == "menu_coins":
            send_message(chat_id, f"💰 سکه‌های شما: {get_coins_display(user_id)}")
            return

        if data == "admin_panel":
            if user_id != OWNER_ID:
                send_message(chat_id, "❌ شما دسترسی به این بخش ندارید.")
                return
            send_message(chat_id, "⚙️ پنل ادمین:", reply_markup=build_admin_keypad())
            return
        if data == "admin_give_coins":
            if user_id != OWNER_ID:
                return
            waiting_for_admin[chat_id] = "give_coins"
            send_message(chat_id, "💰 آیدی عددی و مقدار سکه را بفرست:\nمثال: 123456789 50")
            return
        if data == "admin_broadcast_coins":
            if user_id != OWNER_ID:
                return
            waiting_for_admin[chat_id] = "broadcast_coins"
            send_message(chat_id, "📢 مقدار سکه را برای دادن به همه کاربران بفرست:\nمثال: 10")
            return
        if data == "admin_broadcast_message":
            if user_id != OWNER_ID:
                return
            waiting_for_admin[chat_id] = "broadcast_message"
            send_message(chat_id, "📨 متن پیام همگانی را بفرست:")
            return
        if data == "admin_custom_start":
            if user_id != OWNER_ID:
                return
            waiting_for_admin[chat_id] = "custom_start_id"
            send_message(chat_id, "🔗 start_id، تعداد سکه و نوع را بفرست:\nمثال: BotNew1405 10 single\n\nsingle = یکبار مصرف\nmulti = چندبار مصرف")
            return
        if data == "admin_stats":
            if user_id != OWNER_ID:
                return
            total_users = len(user_data)
            total_coins = sum(u.get("coins", 0) for u in user_data.values())
            send_message(chat_id, f"📊 آمار:\n\n👥 تعداد کاربران: {total_users}\n💰 مجموع سکه‌ها: {total_coins:.1f}")
            return
        if data == "admin_members":
            if user_id != OWNER_ID:
                return
            members_text = get_members_list()
            if len(members_text) > 4000:
                for i in range(0, len(members_text), 4000):
                    send_message(chat_id, members_text[i:i+4000])
            else:
                send_message(chat_id, members_text)
            return

        if data.startswith("mod_"):
            slug = data[4:]
            send_message(chat_id, f"⏳ دریافت نسخه‌های «{slug}»...")
            versions = modrinth_get_versions(slug)
            if not versions:
                send_message(chat_id, "❌ نسخه‌ای یافت نشد.")
                return
            # مرتب‌سازی بر اساس لیست مرجع (نسخه‌های جدیدتر اول)
            versions_sorted = sorted(versions, key=version_sort_key, reverse=False)
            user_state[chat_id] = {"slug": slug, "versions": versions_sorted, "page": 0}
            keypad = build_versions_keypad_paginated(versions_sorted, slug, 0)
            text = build_versions_text(slug, len(versions_sorted), 0)
            send_message(chat_id, text, reply_markup=keypad)
            return

        if data.startswith("page_"):
            parts = data.split("_")
            if len(parts) < 3:
                return
            slug = parts[1]
            page = int(parts[2])
            state = user_state.get(chat_id)
            if not state or state.get("slug") != slug:
                send_message(chat_id, "❌ لطفاً دوباره جستجو کن.")
                return
            versions = state.get("versions", [])
            state["page"] = page
            keypad = build_versions_keypad_paginated(versions, slug, page)
            text = build_versions_text(slug, len(versions), page)
            edit_message(chat_id, message_id, text, reply_markup=keypad)
            return

        if data.startswith("ver_"):
            parts = data.split("_")
            if len(parts) < 3:
                return
            slug = parts[1]
            idx = int(parts[2])
            state = user_state.get(chat_id)
            if not state or state.get("slug") != slug:
                send_message(chat_id, "❌ لطفاً دوباره جستجو کن.")
                return
            versions = state.get("versions", [])
            if idx >= len(versions):
                send_message(chat_id, "❌ نسخه نامعتبر.")
                return
            v = versions[idx]
            files = v.get("files", [])
            if not files:
                send_message(chat_id, "❌ فایلی برای این نسخه نیست.")
                return
            file_url = files[0].get("url")
            filename = files[0].get("filename", "file.jar")
            file_size = files[0].get("size")
            send_mod_file(chat_id, file_url, filename, file_size)
            return


# ============ حلقه اصلی ============
def get_updates():
    payload = {}
    if last_update_id is not None:
        payload["offset"] = last_update_id + 1
    try:
        r = requests.post(BASE_URL + "getUpdates", json=payload, timeout=40)
        data = r.json()
        if data.get("ok"):
            return data.get("result", [])
        return []
    except Exception as e:
        print(f"[Updates] {e}")
        return []


def main():
    global last_update_id
    load_state()
    os.makedirs(TEMP_DIR, exist_ok=True)
    print(f"🤖 ربات Modrinth (بله) شروع شد | {CREATOR}")
    print(f"🔗 لینک ربات: https://ble.ir/{BOT_USERNAME}")
    print(f"👑 مالک: {OWNER_ID}")
    while True:
        try:
            updates = get_updates()
            if updates:
                for u in updates:
                    try:
                        handle_update(u)
                    except Exception as e:
                        print(f"[Process] {e}")
                    uid = u.get("update_id")
                    if uid is not None:
                        last_update_id = uid
                        save_state()
            time.sleep(1)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[Main] {e}")
            time.sleep(3)


if __name__ == "__main__":
    main()
