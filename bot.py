import asyncio
import random
import requests
import os
import json
import tempfile
from rubka.asynco import Robot
from rubka.context import Message
from rubka.button import InlineBuilder

# ================== تنظیمات ==================
BOT_TOKEN = "CHFECH0DYZCBBDASKUFCACXHNYJCWBPPTKWTQPXPAVXBERAAQHNPRTSDFQTBITPL"
API_BASE = "https://apis.parssource.ir"
CREATOR = "@TheAghaBanafshi"
STATE_FILE = "rubika_state.json"

bot = Robot(token=BOT_TOKEN)

user_data = {}
rps_pending = {}

# ============ دیتابیس محلی ============
LOCAL_JOKS = [
    "به دوستم گفتم چرا اینقدر خوشحالی؟ گفت: نمیدونم، فقط خوشحالم! 😂",
    "دکتر به بیمار: باید ورزش کنی. بیمار: دکتر، من هر روز میدوم! دکتر: کجا؟ بیمار: دنبال اتوبوس! 🏃",
    "یه روز یه تنبل تصمیم گرفت کار کنه... ولی بعد پشیمون شد و خوابید. 😴",
    "گفتم خسته‌ام، گفت برو بخواب. گفتم گشنمه، گفت برو بخور. گفتم حوصلم سر رفته، گفت برو بیرون. گفتم تنهام، گفت... برو یه دوست پیدا کن! 😂",
    "معلم: چرا تکلیفت رو ننوشتی؟ شاگرد: چون نمیخواستم استرس داشته باشی! 😅",
]

LOCAL_FACTS = [
    "🐙 قلب اختاپوس سه تا داره!",
    "🍯 عسل تنها غذایی هست که هرگز خراب نمی‌شه.",
    "🌍 زمین هر ثانیه ۳۰ کیلومتر دور خورشید حرکت می‌کنه.",
    "🦈 کوسه‌ها از زمان دایناسورها وجود داشتن، حتی قبل از درخت‌ها!",
]

LOCAL_FTARS = [
    "😨 وقتی می‌خوابی، بدنت فلج می‌شه تا خوابت رو بازی نکنی!",
    "👻 توی تاریکی، مغزت چیزهایی می‌بینه که وجود ندارن.",
]

LOCAL_ANGIZE = [
    "💪 هر روز که تلاش می‌کنی، یه قدم به رویاهات نزدیک‌تری.",
    "🔥 شکست پایان نیست، شروع دوباره‌ست.",
]

LOCAL_BIOS = [
    "✨ زندگی زیباست، فقط باید درست ببینیش.",
    "🌙 آرام باش، همه چیز درست می‌شه.",
]

CHALLENGE_TRUTHS = ["آخرین باری که گریه کردی کِی بود؟", "بزرگ‌ترین ترست چیه؟"]
CHALLENGE_DARES = ["به یکی از اعضای گروه بگو دوستش داری!", "یه آهنگ بخون!"]

GREETING_RESPONSES = ["درود دوست عزیز 😁", "سلام داش خوبی", "سیلامم", "عه سلام آنلاین شدی بلاخره"]
KHOB_RESPONSES = ["خب به جمالت"]
KHOBIS_RESPONSES = ["خوبم شما خوبی؟"]
ALO_RESPONSES = ["چیشدههههههه"]
BAD_WORDS = ["فحش", "کسشر", "احمق", "خنگ", "کونی"]


# ============ تشخیص پیوی ============
def is_private_chat(chat_id):
    cid = str(chat_id)
    return cid.startswith("b0") or cid.startswith("u0")


# ============ ذخیره ============
def load_state():
    global user_data
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                user_data = json.load(f)
        except:
            user_data = {}

def save_state():
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(user_data, f, ensure_ascii=False, indent=2)
    except:
        pass

def get_user(uid, name="", username=""):
    uid = str(uid)
    if uid not in user_data:
        user_data[uid] = {"name": name or "نامشخص", "username": username or "-",
                          "id": uid, "score": 0, "wins": 0, "warnings": 0}
    else:
        if name: user_data[uid]["name"] = name
        if username and username != "-": user_data[uid]["username"] = username
    return user_data[uid]


# ============ ابزار ============
def fix_encoding(text):
    if not text: return text
    try:
        cleaned = text.encode("latin-1", errors="ignore").decode("utf-8", errors="ignore")
        return "".join(ch for ch in cleaned if ch.isprintable() or ch in "‌‍").strip() or text
    except: return text

def add_creator(text):
    return text + f"\n\n━━━━━━━━━━━━\nسازنده: {CREATOR}" if CREATOR else text

def call_api(endpoint, params=None):
    try:
        r = requests.get(f"{API_BASE}/{endpoint}", params=params, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        return r.json()
    except Exception as e:
        print(f"[API] {endpoint}: {e}"); return None

def get_info(message):
    raw = getattr(message, 'raw_data', {}) or {}
    return (raw.get('sender_id') or message.sender_id,
            raw.get('sender_name') or "",
            raw.get('sender_username') or "")

def get_replied_info(message):
    raw = getattr(message, 'raw_data', {}) or {}
    r = raw.get('reply_to_message') or raw.get('new_message', {}).get('reply_to_message')
    if r: return r.get('sender_id'), r.get('sender_name') or "", r.get('sender_username') or ""
    return None, "", ""


# ============ فرمت‌دهنده‌ها ============
def fmt_myket(data, query):
    if not data or not data.get("ok"): return f"❌ نتیجه‌ای برای «{query}» یافت نشد."
    items = data.get("data", [])[:10]
    if not items: return f"❌ نتیجه‌ای برای «{query}» یافت نشد."
    lines = [f"🔎 نتایج مایکت برای «{query}»:\n"]
    for i, item in enumerate(items, 1):
        title = fix_encoding(item.get("title", "بدون نام"))
        link = item.get("link", "")
        pkg = item.get("package", "")
        lines.append(f"{i}. {title}\n   📄 {link}")
        if pkg: lines.append(f"   ⬇️ myket://download/{pkg}")
    return add_creator("\n\n".join(lines))

def fmt_music(data, prefix="🎵"):
    if not data or not data.get("ok"): return "❌ موزیکی یافت نشد."
    results = data.get("results", [])
    if not results: return "❌ موزیکی یافت نشد."
    lines = [f"{prefix} {len(results)} موزیک:\n"]
    for i, m in enumerate(results, 1):
        title = fix_encoding(m.get("title", "بدون نام"))
        artist = fix_encoding(m.get("artist") or "-")
        dl = m.get("download_url", "")
        lines.append(f"{i}. {title}\n   🎤 {artist}")
        if dl: lines.append(f"   ⬇️ {dl}")
    return add_creator("\n\n".join(lines))

def fmt_aparat(data):
    if not data or not data.get("ok"): return "❌ خطا."
    links = data.get("download_links", [])
    if not links: return "❌ لینکی نبود."
    lines = ["🎬 آپارات:\n"]
    for l in links:
        q, size, url = l.get("quality", "-"), l.get("size", "-"), l.get("url", "")
        lines.append(f"• {q} ({size}): {url}")
    return add_creator("\n".join(lines))

def fmt_simple(data, prefix):
    if not data: return f"{prefix} ❌"
    if isinstance(data, dict):
        for key in ("result", "text", "output", "value", "data"):
            if key in data and not isinstance(data[key], (dict, list)):
                return add_creator(f"{prefix} {fix_encoding(str(data[key]))}")
    return add_creator(f"{prefix} {fix_encoding(str(data))}")

def fmt_arz(data):
    if not data or not data.get("currencies"): return "❌ خطا."
    lines = ["💰 ارزها:\n"]
    for it in data["currencies"][:10]:
        lines.append(f"• {fix_encoding(it.get('name', '-'))}: خرید {it.get('price_buy', '-')} | فروش {it.get('price_sell', '-')}")
    return add_creator("\n".join(lines))

def fmt_tala(data):
    if not data or not isinstance(data.get("result"), list): return "❌ خطا."
    lines = ["💰 طلا و سکه:\n"]
    for it in data["result"]:
        n = fix_encoding(it.get("name", "-"))
        p = it.get("price", "-")
        try: p = f"{int(float(str(p).replace(',', ''))):,}"
        except: pass
        lines.append(f"• {n}: {p} تومان")
    return add_creator("\n".join(lines))


# ============ سرگرمی ============
def get_jok():
    data = call_api("jok")
    if data and isinstance(data, dict):
        for k in ("result", "jok", "text", "joke"):
            v = data.get(k)
            if isinstance(v, str) and v.strip(): return add_creator(f"😄 {fix_encoding(v.strip())}")
    return add_creator(f"😄 {random.choice(LOCAL_JOKS)}")

def get_fact():
    data = call_api("fact")
    if data and isinstance(data, dict):
        for k in ("result", "fact", "text"):
            v = data.get(k)
            if isinstance(v, str) and v.strip(): return add_creator(f"💡 {fix_encoding(v.strip())}")
    return add_creator(f"💡 {random.choice(LOCAL_FACTS)}")

def get_ftars():
    data = call_api("ftars")
    if data and isinstance(data, dict):
        for k in ("result", "fact", "text"):
            v = data.get(k)
            if isinstance(v, str) and v.strip(): return add_creator(f"😨 {fix_encoding(v.strip())}")
    return add_creator(f"😨 {random.choice(LOCAL_FTARS)}")

def get_angize():
    data = call_api("angize")
    if data and isinstance(data, dict):
        for k in ("result", "text", "angize"):
            v = data.get(k)
            if isinstance(v, str) and v.strip(): return add_creator(f"💪 {fix_encoding(v.strip())}")
    return add_creator(f"💪 {random.choice(LOCAL_ANGIZE)}")

def get_bio():
    data = call_api("bio")
    if data and isinstance(data, dict):
        for k in ("result", "bio", "text"):
            v = data.get(k)
            if isinstance(v, str) and v.strip(): return add_creator(f"📝 {fix_encoding(v.strip())}")
    return add_creator(f"📝 {random.choice(LOCAL_BIOS)}")

def get_challenge():
    data = call_api("challenge")
    if data and data.get("status") == "success":
        items = []
        for it in data.get("data", []):
            q = fix_encoding(it.get("question", "")).strip()
            if q: items.append({"type": it.get("type",""), "question": q})
        if items:
            chosen = random.choice(items)
            tm = {"truth":"🤔 حقیقت","dare":"🔥 جرئت"}
            label = tm.get(chosen["type"], "🎲")
            return add_creator(f"🎯 چالش:\n\n{label}\n   {chosen['question']}")
    if random.random() < 0.5:
        return add_creator(f"🎯 چالش:\n\n🤔 حقیقت\n   {random.choice(CHALLENGE_TRUTHS)}")
    return add_creator(f"🎯 چالش:\n\n🔥 جرئت\n   {random.choice(CHALLENGE_DARES)}")


# ============ منو ============
MENU = f"""🤖 ربات همه‌کاره

🔍 /search | /جستجو <نام>
🎵 /rmusic | /موزیک
🎬 /aparat | /آپارات <لینک>
🔊 /voice | /ویس <متن>

🛠 /adad | /عدد
🔤 /morse | /مورس
💰 /arz | /ارز
🪙 /tala | /طلا

🎮 /rps | /سنگ — سنگ کاغذ قیچی
🎲 /dice | /تاس
🪙 /flip | /شیر
😄 /jok | /جوک
💡 /fact | /فکت
🎯 /challenge | /چالش

📊 /profile | /آمار

━━━━━━━━━━━━
{CREATOR}"""

KEYWORD_COMMANDS = {
    "شروع": "/start", "راهنما": "/help",
    "جستجو": "/search", "سرچ": "/search",
    "موزیک": "/rmusic", "آهنگ": "/rmusic",
    "آپارات": "/aparat", "ویس": "/voice", "صدا": "/voice",
    "عدد": "/adad", "مورس": "/morse", "ارز": "/arz", "طلا": "/tala",
    "جوک": "/jok", "فکت": "/fact", "چالش": "/challenge",
    "سنگ": "/rps", "تاس": "/dice", "شیر": "/flip",
    "پروفایل": "/profile", "آمار": "/profile",
}

def normalize(text):
    p = text.split(maxsplit=1)
    if p[0].lower() in KEYWORD_COMMANDS:
        arg = p[1].strip() if len(p) > 1 else ""
        return f"{KEYWORD_COMMANDS[p[0].lower()]} {arg}".strip()
    return text


def build_profile(u):
    return f"""📊 آمار:

👤 نام: {u['name']}
🔗 یوزرنیم: {u['username']}
🆔 آیدی: {u['id']}
⭐ امتیاز: {u['score']}
🏆 بردها: {u['wins']}
⚠️ اخطار: {u['warnings']}"""


RPS_CHOICES = ["سنگ", "کاغذ", "قیچی"]
RPS_MAP = {"1": "سنگ", "2": "کاغذ", "3": "قیچی", "سنگ": "سنگ", "کاغذ": "کاغذ", "قیچی": "قیچی"}

def resolve_rps(user_choice, bot_choice, u):
    if user_choice == bot_choice:
        return "🤝 مساوی!"
    elif (user_choice == "سنگ" and bot_choice == "قیچی") or \
         (user_choice == "کاغذ" and bot_choice == "سنگ") or \
         (user_choice == "قیچی" and bot_choice == "کاغذ"):
        u["score"] += 5
        u["wins"] += 1
        return "🎉 تو بردی! +۵ امتیاز"
    return "😢 من بردم!"


# ============ هندلر پیام ============
@bot.on_message()
async def handle_message(bot: Robot, message: Message):
    chat_id = message.chat_id
    raw_text = (message.text or "").strip()
    sender_id, sender_name, sender_uname = get_info(message)
    if not chat_id or not raw_text or not sender_id:
        return

    u = get_user(sender_id, sender_name, sender_uname)
    is_private = is_private_chat(chat_id)

    # فحش
    if any(w in raw_text for w in BAD_WORDS):
        u["warnings"] += 1
        save_state()
        if u["warnings"] >= 4:
            try:
                await bot.kick_chat_member(chat_id, sender_id)
                await message.reply("🚫 بن شد به دلیل ۴ اخطار.")
                u["warnings"] = 0
            except Exception as e:
                await message.reply(f"⚠️ بن نشد: {e}")
        else:
            await message.reply(f"⚠️ اخطار {u['warnings']}/۴")
        save_state()
        return

    low = raw_text.lower()
    if low == "سلام": await message.reply(random.choice(GREETING_RESPONSES)); return
    if low == "خب": await message.reply(random.choice(KHOB_RESPONSES)); return
    if low == "خوبی": await message.reply(random.choice(KHOBIS_RESPONSES)); return
    if low == "الو": await message.reply(random.choice(ALO_RESPONSES)); return

    # RPS گروه
    if chat_id in rps_pending and not is_private:
        opponent_id = rps_pending[chat_id]
        val = raw_text.strip().lower()
        if val.startswith("/rps "): val = val[5:].strip()
        if val in RPS_MAP:
            if sender_id == opponent_id:
                await message.reply("❌ این نوبت حریفته!")
                return
            user_choice = RPS_MAP[val]
            bot_choice = random.choice(RPS_CHOICES)
            result = resolve_rps(user_choice, bot_choice, u)
            save_state()
            opp = get_user(opponent_id)
            del rps_pending[chat_id]
            await message.reply(
                f"🪨📄✂️ نتیجه:\n"
                f"🧑 {u['name']}: {user_choice}\n"
                f"🧑 {opp['name']}: {bot_choice}\n\n"
                f"{result}\n\n"
                f"⭐ {u['name']}: {u['score']} | {opp['name']}: {opp['score']}"
            )
        return

    text = normalize(raw_text)

    if text == "/start": await message.reply(MENU); return

    if text == "/profile":
        rid, rname, runame = get_replied_info(message)
        if rid:
            tu = get_user(rid, rname, runame); save_state()
            await message.reply(build_profile(tu))
        else:
            save_state()
            await message.reply(build_profile(u))
        return

    # RPS
    if text == "/rps":
        if is_private:
            try:
                builder = InlineBuilder()
                inline_keypad = builder.row(
                    builder.button_simple("rps_rock", "🪨 سنگ"),
                    builder.button_simple("rps_paper", "📄 کاغذ"),
                    builder.button_simple("rps_scissors", "✂️ قیچی"),
                ).build()
                await message.reply("🪨📄✂️ انتخاب کن:", inline_keypad=inline_keypad)
            except Exception as e:
                print(f"[Inline] خطا: {e}")
                await message.reply("🪨📄✂️ انتخاب کن:\n1️⃣ سنگ\n2️⃣ کاغذ\n3️⃣ قیچی\n\nبنویس: /rps 1")
        else:
            rps_pending[chat_id] = sender_id
            await message.reply(
                "🪨📄✂️ سنگ کاغذ قیچی (دو نفره)\n\n"
                "نفر دوم: روی پیام نفر اول ریپلای بزن و انتخاب کن:\n"
                "1️⃣ سنگ\n2️⃣ کاغذ\n3️⃣ قیچی\n\n"
                "مثال: ریپلای + /rps 1"
            )
        return

    if text.startswith("/rps "):
        val = text[5:].strip().lower()
        if val in RPS_MAP:
            user_choice = RPS_MAP[val]
            bot_choice = random.choice(RPS_CHOICES)
            result = resolve_rps(user_choice, bot_choice, u)
            save_state()
            await message.reply(
                f"🧑 تو: {user_choice}\n🤖 من: {bot_choice}\n\n{result}\n⭐ امتیاز: {u['score']}"
            )
        else:
            await message.reply("❌ /rps 1 (سنگ)، 2 (کاغذ)، 3 (قیچی)")
        return

    if text == "/dice": await message.reply(f"🎲 {random.randint(1,6)}"); return
    if text == "/flip": await message.reply(f"🪙 {random.choice(['شیر 🦁','خط ➖'])}"); return
    if text == "/jok": await message.reply(get_jok()); return
    if text == "/fact": await message.reply(get_fact()); return
    if text == "/ftars": await message.reply(get_ftars()); return
    if text == "/angize": await message.reply(get_angize()); return
    if text == "/bio": await message.reply(get_bio()); return
    if text == "/challenge": await message.reply(get_challenge()); return

    if text.startswith("/search "):
        arg = text[8:].strip()
        await message.reply(f"⏳ جستجوی «{arg}»...")
        await message.reply(fmt_myket(call_api("myket", {"text": arg, "lang": "fa", "count": 10}), arg))
        return

    if text == "/rmusic":
        await message.reply("⏳ دریافت موزیک...")
        await message.reply(fmt_music(call_api("rmusic", {"limit": 3})))
        return

    if text.startswith("/aparat "):
        arg = text[8:].strip()
        await message.reply("⏳ دریافت...")
        await message.reply(fmt_aparat(call_api("dlap", {"url": arg})))
        return

    if text.startswith("/voice ") or text.startswith("/ویس "):
        arg = text.split(maxsplit=1)[1] if len(text.split(maxsplit=1)) > 1 else ""
        if not arg: await message.reply("❌ مثال: /voice سلام"); return
        await message.reply("⏳ ساخت صدا...")
        data = call_api("voice", {"text": arg})
        if data and data.get("ok"):
            url = data.get("audio_url") or data.get("result")
            if url:
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                        path = tmp.name
                    r = requests.get(url, timeout=60)
                    if r.status_code == 200:
                        with open(path, "wb") as f: f.write(r.content)
                        try: await bot.send_voice(chat_id, path)
                        except Exception as e: await message.reply(f"❌ ارسال ویس: {e}\nلینک: {url}")
                        os.remove(path)
                    else:
                        await message.reply(f"❌ دانلود نشد. لینک: {url}")
                except Exception as e:
                    await message.reply(f"❌ {e}")
            else:
                await message.reply("❌ لینکی نبود.")
        return

    if text.startswith("/adad "):
        arg = text[6:].strip()
        await message.reply(fmt_simple(call_api("adad", {"text": arg}), "🔢"))
        return

    if text.startswith("/morse "):
        arg = text[7:].strip()
        await message.reply(fmt_simple(call_api("morse", {"text": arg}), "🔤"))
        return

    if text == "/arz": await message.reply(fmt_arz(call_api("arzp"))); return
    if text == "/tala": await message.reply(fmt_tala(call_api("tala"))); return


# ============ هندلر کلیک دکمه (فقط پیوی) ============
@bot.on_callback()
async def handle_callback(bot: Robot, message: Message):
    print(f"[Callback] RAW: {message.aux_data}")
    
    if not is_private_chat(message.chat_id):
        return
    
    try:
        btn_id = message.aux_data.button_id
    except Exception as e:
        print(f"[Callback] خطا: {e}")
        return
    
    print(f"[Callback] button_id: {btn_id}")
    
    if not btn_id: return

    sender_id = message.sender_id
    choice_map = {"rps_rock": "سنگ", "rps_paper": "کاغذ", "rps_scissors": "قیچی"}
    user_choice = choice_map.get(btn_id)
    
    if not user_choice:
        print(f"[Callback] دکمه ناشناخته: {btn_id}")
        return

    bot_choice = random.choice(RPS_CHOICES)
    u = get_user(sender_id)
    result = resolve_rps(user_choice, bot_choice, u)
    save_state()
    await message.reply(
        f"🧑 تو: {user_choice}\n🤖 من: {bot_choice}\n\n{result}\n⭐ امتیاز: {u['score']}"
    )


if __name__ == "__main__":
    load_state()
    print(f"🤖 ربات همه‌کاره شروع شد | {CREATOR}")
    asyncio.run(bot.run())
