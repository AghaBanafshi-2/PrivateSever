from config import *

# ============ دکمه‌های شیشه‌ای ============
def build_main_keypad(user_id):
    rows = [
        [{"text": "🔍 ماد (Java)", "callback_data": "menu_mod"}],
        [{"text": "📦 ریسورس‌پک (Java)", "callback_data": "menu_rp"}],
        [{"text": "🪨 ماد (Bedrock)", "callback_data": "menu_bedrock_mod"}],
        [{"text": "🎨 ریسورس‌پک (Bedrock)", "callback_data": "menu_bedrock_rp"}],
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


def build_modrinth_results_keypad(hits):
    rows = []
    for h in hits[:5]:
        slug = h.get("slug", "")
        title = h.get("title", "بدون نام")[:25]
        rows.append([{"text": f"📦 {title}", "callback_data": f"mod_{slug}"}])
    return {"inline_keyboard": rows}


def build_curseforge_results_keypad(hits):
    rows = []
    for h in hits[:5]:
        mod_id = h.get("id")
        title = h.get("name", "بدون نام")[:25]
        rows.append([{"text": f"🪨 {title}", "callback_data": f"cf_{mod_id}"}])
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
    return f"""🤖 ربات دانلود مود (Java + Bedrock)

💰 سکه‌های شما: {coins}

🔍 ماد (Java): mod <نام>
📦 ریسورس‌پک (Java): rp <نام>
🪨 ماد (Bedrock): bmod <نام>
🎨 ریسورس‌پک (Bedrock): brp <نام>
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

            if mode == "mod":
                hits = modrinth_search(query, "mod")
                if not hits:
                    send_message(chat_id, "❌ نتیجه‌ای یافت نشد.")
                    return
                send_message(chat_id, "🔎 نتایج (روی دکمه بزن):", reply_markup=build_modrinth_results_keypad(hits))
            elif mode == "rp":
                hits = modrinth_search(query, "resourcepack")
                if not hits:
                    send_message(chat_id, "❌ نتیجه‌ای یافت نشد.")
                    return
                send_message(chat_id, "🔎 نتایج (روی دکمه بزن):", reply_markup=build_modrinth_results_keypad(hits))
            elif mode == "bedrock_mod":
                hits = curseforge_search(query, is_resourcepack=False)
                if not hits:
                    send_message(chat_id, "❌ نتیجه‌ای یافت نشد.")
                    return
                send_message(chat_id, "🔎 نتایج (روی دکمه بزن):", reply_markup=build_curseforge_results_keypad(hits))
            elif mode == "bedrock_rp":
                hits = curseforge_search(query, is_resourcepack=True)
                if not hits:
                    send_message(chat_id, "❌ نتیجه‌ای یافت نشد.")
                    return
                send_message(chat_id, "🔎 نتایج (روی دکمه بزن):", reply_markup=build_curseforge_results_keypad(hits))
            return

        lower_text = text.lower()
        if lower_text.startswith("bmod ") or lower_text == "bmod":
            text = "/" + text
        elif lower_text.startswith("brp ") or lower_text == "brp":
            text = "/" + text
        elif lower_text.startswith("mod ") or lower_text == "mod":
            text = "/" + text
        elif lower_text.startswith("rp ") or lower_text == "rp":
            text = "/" + text

        if text == "/bmod" or text.startswith("/bmod "):
            if len(text.split()) < 2:
                send_message(chat_id, "❌ مثال: bmod furniture")
                return
            arg = text.split(maxsplit=1)[1].strip()
            send_message(chat_id, f"⏳ جستجوی ماد بدراک «{arg}»...")
            hits = curseforge_search(arg, is_resourcepack=False)
            if not hits:
                send_message(chat_id, "❌ نتیجه‌ای یافت نشد.")
                return
            send_message(chat_id, "🔎 نتایج (روی دکمه بزن):", reply_markup=build_curseforge_results_keypad(hits))
            return

        if text == "/brp" or text.startswith("/brp "):
            if len(text.split()) < 2:
                send_message(chat_id, "❌ مثال: brp faithful")
                return
            arg = text.split(maxsplit=1)[1].strip()
            send_message(chat_id, f"⏳ جستجوی ریسورس‌پک بدراک «{arg}»...")
            hits = curseforge_search(arg, is_resourcepack=True)
            if not hits:
                send_message(chat_id, "❌ نتیجه‌ای یافت نشد.")
                return
            send_message(chat_id, "🔎 نتایج (روی دکمه بزن):", reply_markup=build_curseforge_results_keypad(hits))
            return

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
            send_message(chat_id, "🔎 نتایج (روی دکمه بزن):", reply_markup=build_modrinth_results_keypad(hits))
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
            send_message(chat_id, "🔎 نتایج (روی دکمه بزن):", reply_markup=build_modrinth_results_keypad(hits))
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
            send_message(chat_id, "🔍 نام ماد (Java) را بنویس:")
            return
        if data == "menu_rp":
            waiting_for[chat_id] = "rp"
            send_message(chat_id, "📦 نام ریسورس‌پک (Java) را بنویس:")
            return
        if data == "menu_bedrock_mod":
            waiting_for[chat_id] = "bedrock_mod"
            send_message(chat_id, "🪨 نام ماد (Bedrock) را بنویس:")
            return
        if data == "menu_bedrock_rp":
            waiting_for[chat_id] = "bedrock_rp"
            send_message(chat_id, "🎨 نام ریسورس‌پک (Bedrock) را بنویس:")
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
            versions_sorted = sorted(versions, key=version_sort_key, reverse=False)
            user_state[chat_id] = {"slug": slug, "versions": versions_sorted, "page": 0}
            keypad = build_versions_keypad_paginated(versions_sorted, slug, 0)
            text = build_versions_text(slug, len(versions_sorted), 0)
            send_message(chat_id, text, reply_markup=keypad)
            return

        if data.startswith("cf_"):
            mod_id = data[3:]
            send_message(chat_id, f"⏳ دریافت فایل‌های CurseForge...")
            files = curseforge_get_files(mod_id)
            if not files:
                send_message(chat_id, "❌ فایلی یافت نشد.")
                return
            # ارسال آخرین فایل
            f = files[0]
            file_url = f.get("downloadUrl")
            filename = f.get("fileName", "file.jar")
            if not file_url:
                send_message(chat_id, "❌ لینک دانلود یافت نشد.")
                return
            send_mod_file(chat_id, file_url, filename)
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
    print(f"🤖 ربات دانلود مود شروع شد | {CREATOR}")
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
