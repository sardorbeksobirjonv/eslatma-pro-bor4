from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import asyncio

TOKEN = "8579329186:AAEWR3XGBTTfIj9WOd8MEilKAJeVPPTWz0Q"

(
    TIL, KONTAKT, MINTQA,
    TUR, TARGET_ID,
    VAQT, MATN, QAYTA,
    MENU, OCHIR_ID,
    TAHRIR_ID, TAHRIR_TURI,
    TAHRIR_KIRITISH
) = range(13)

users = {}

# ================= YORDAMCHI =================
def parse_chat_id(text: str):
    text = text.strip()
    if text.startswith("@"):
        return text
    try:
        return int(text)
    except:
        return None

# ================= TIMEZONE =================
ZONE_MAP = {
    "toshkent": "Asia/Tashkent",
    "ташкент": "Asia/Tashkent",
    "moskva": "Europe/Moscow",
    "москва": "Europe/Moscow",
}

REPEAT = {
    "Ҳеч қачон": None,
    "Ҳар кун": timedelta(days=1),
    "Ҳар ҳафта": timedelta(weeks=1),
    "Ҳар ой": timedelta(days=30)
}

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users[update.effective_user.id] = {
        "reminders": [],
        "tz": ZoneInfo("Asia/Tashkent")
    }

    await update.message.reply_text(
            "🇺🇿 Ботдан фойдаланиш учун аввал тилни танланг\n\n🇷🇺 Чтобы воспользоваться ботом, сначала выберите язык",
        reply_markup=ReplyKeyboardMarkup(
            [["🇺🇿 Ўзбекча", "🇷🇺 Русский"]],
            resize_keyboard=True
        )
    )
    return TIL

# ================= LANGUAGE =================
async def til(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
            "📲 Ботдан фойдаланишни давом эттириш учун телефон рақамингизни юборинг",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("📱 Телефон рақамни юбориш", request_contact=True)]],
            resize_keyboard=True
        )
    )
    return KONTAKT

# ================= CONTACT =================
async def kontakt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌍 Минтақани ёзинг (масалан: Тошкент)",
        reply_markup=ReplyKeyboardRemove()
    )
    return MINTQA

# ================= REGION =================
async def mintqa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    for k, v in ZONE_MAP.items():
        if k in text:
            users[update.effective_user.id]["tz"] = ZoneInfo(v)
            await update.message.reply_text(
                "🔔 Еслатма турини танланг\nИлтимос, қуйидаги вариантлардан бирини танланг\n\n👤 Шахсий — еслатма фақат сизга кўринади\n\n👥 Гуруҳ — еслатма гуруҳда ишлайди\n\n📢 Канал — еслатма каналга юборилади\n\n📘 Қўлланма — ботдан қандай фойдаланишни билиш\nҚўлланмани очиш: https://t.me/your_manual_link",
                reply_markup=ReplyKeyboardMarkup(
                    [["Шахсий"], ["Гуруҳ"], ["Канал"]],
                    resize_keyboard=True
                )
            )
            return TUR

    await update.message.reply_text("❌ Минтақа топилмади, қайта ёзинг")
    return MINTQA

# ================= TYPE =================
async def tur(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users[update.effective_user.id]["current"] = {
        "type": update.message.text.lower()
    }

    if update.message.text.lower() in ["гуруҳ", "канал"]:
        await update.message.reply_text(
            "🆔 Гуруҳ / Канал ID ёки @username киритинг\n\n"
            "Мисол:\n-1001234567890\n@kanal_nomi"
        )
        return TARGET_ID

    await update.message.reply_text("⏰ Вақт (DD.MM.YYYY HH:MM)")
    return VAQT

# ================= TARGET =================
async def target_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = parse_chat_id(update.message.text)
    if chat_id is None:
        await update.message.reply_text("❌ Нотўғри ID")
        return TARGET_ID

    users[update.effective_user.id]["current"]["target_id"] = chat_id
    await update.message.reply_text("⏰ Вақт (DD.MM.YYYY HH:MM)")
    return VAQT

# ================= TIME =================
async def vaqt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        dt = datetime.strptime(update.message.text, "%d.%m.%Y %H:%M")
    except:
        await update.message.reply_text("❌ Формат нотўғри")
        return VAQT

    users[update.effective_user.id]["current"]["time"] = dt
    await update.message.reply_text("✏️ Матнни киритинг")
    return MATN

# ================= TEXT =================
async def matn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users[update.effective_user.id]["current"]["text"] = update.message.text
    await update.message.reply_text(
        "🔁 Такрорлансинми?",
        reply_markup=ReplyKeyboardMarkup(
            [["Ҳеч қачон", "Ҳар кун"], ["Ҳар ҳафта", "Ҳар ой"]],
            resize_keyboard=True
        )
    )
    return QAYTA

# ================= SAVE =================
async def qayta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = users[update.effective_user.id]
    cur = user["current"]

    cur["repeat"] = REPEAT[update.message.text]
    cur["id"] = len(user["reminders"]) + 1
    cur["task"] = asyncio.create_task(schedule(update.effective_user.id, cur, context))

    user["reminders"].append(cur)
    user.pop("current")

    await update.message.reply_text("✅ Еслатма сақланди")
    return await menu(update, context)

# ================= SCHEDULER =================
async def schedule(uid, r, context):
    tz = users[uid]["tz"]

    while True:
        now = datetime.now(tz)
        target = r["time"].replace(tzinfo=tz)

        if target <= now:
            if not r["repeat"]:
                return
            target += r["repeat"]

        await asyncio.sleep((target - now).total_seconds())

        chat_id = uid if r["type"] == "шахсий" else r["target_id"]

        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"⏰ Еслатма:\n\n{r['text']}"
            )
        except Exception as e:
            print("Юборишда хато:", e)

        if not r["repeat"]:
            return

        r["time"] = target

# ================= MENU =================
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📌 Асосий меню",
        reply_markup=ReplyKeyboardMarkup(
            [
                ["➕ Янги еслатма"],
                ["📋 Рўйхат"],
                ["✏️ Таҳрирлаш"],
                ["❌ Ўчириш"]
            ],
            resize_keyboard=True
        )
    )
    return MENU

# ================= LIST =================
def reminder_list(user):
    if not user["reminders"]:
        return "📭 Еслатмалар йўқ"

    return "\n\n".join(
        f"ID:{r['id']} — {r['text']}\n"
        f"🕒 {r['time'].strftime('%d.%m.%Y %H:%M')}\n"
        f"🔁 {'Ҳеч қачон' if not r['repeat'] else 'Такрор'} | {r['type'].title()}"
        for r in user["reminders"]
    )

# ================= MENU HANDLER =================
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t = update.message.text
    user = users[update.effective_user.id]

    if t == "➕ Янги еслатма":
        await update.message.reply_text("🌍 Минтақани ёзинг")
        return MINTQA

    if t == "📋 Рўйхат":
        await update.message.reply_text(reminder_list(user))
        return MENU

    if t == "❌ Ўчириш":
        await update.message.reply_text(
            "❌ Ўчириш учун ID ни киритинг:\n\n" + reminder_list(user)
        )
        return OCHIR_ID

    if t == "✏️ Таҳрирлаш":
        await update.message.reply_text(
            "✏️ Таҳрирлаш учун ID ни киритинг:\n\n" + reminder_list(user)
        )
        return TAHRIR_ID

    return MENU

# ================= DELETE =================
async def ochir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text.isdigit():
        return await menu(update, context)

    rid = int(update.message.text)
    user = users[update.effective_user.id]

    for r in user["reminders"]:
        if r["id"] == rid:
            r["task"].cancel()
            user["reminders"].remove(r)
            await update.message.reply_text("✅ Ўчирилди")
            return await menu(update, context)

    await update.message.reply_text("❌ ID топилмади")
    return await menu(update, context)

# ================= EDIT =================
async def tahrir_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text.isdigit():
        return await menu(update, context)

    rid = int(update.message.text)
    user = users[update.effective_user.id]

    for r in user["reminders"]:
        if r["id"] == rid:
            user["edit"] = r
            await update.message.reply_text(
                "Нимани ўзгартириш?",
                reply_markup=ReplyKeyboardMarkup(
                    [["Матн"], ["Вақт"]],
                    resize_keyboard=True
                )
            )
            return TAHRIR_TURI

    await update.message.reply_text("❌ ID нотўғри")
    return await menu(update, context)

async def tahrir_turi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users[update.effective_user.id]["edit_type"] = update.message.text
    await update.message.reply_text("Янги қийматни киритинг", reply_markup=ReplyKeyboardRemove())
    return TAHRIR_KIRITISH

async def tahrir_kirit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = users[update.effective_user.id]
    r = user["edit"]

    if user["edit_type"] == "Вақт":
        try:
            r["time"] = datetime.strptime(update.message.text, "%d.%m.%Y %H:%M")
        except:
            await update.message.reply_text("❌ Формат нотўғри")
            return TAHRIR_KIRITISH
    else:
        r["text"] = update.message.text

    r["task"].cancel()
    r["task"] = asyncio.create_task(schedule(update.effective_user.id, r, context))

    user.pop("edit")
    await update.message.reply_text("✅ Таҳрирланди")
    return await menu(update, context)

# ================= MAIN =================
def main():
    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            TIL: [MessageHandler(filters.TEXT, til)],
            KONTAKT: [MessageHandler(filters.CONTACT, kontakt)],
            MINTQA: [MessageHandler(filters.TEXT, mintqa)],
            TUR: [MessageHandler(filters.TEXT, tur)],
            TARGET_ID: [MessageHandler(filters.TEXT, target_id)],
            VAQT: [MessageHandler(filters.TEXT, vaqt)],
            MATN: [MessageHandler(filters.TEXT, matn)],
            QAYTA: [MessageHandler(filters.TEXT, qayta)],
            MENU: [MessageHandler(filters.TEXT, menu_handler)],
            OCHIR_ID: [MessageHandler(filters.TEXT, ochir)],
            TAHRIR_ID: [MessageHandler(filters.TEXT, tahrir_id)],
            TAHRIR_TURI: [MessageHandler(filters.TEXT, tahrir_turi)],
            TAHRIR_KIRITISH: [MessageHandler(filters.TEXT, tahrir_kirit)],
        },
        fallbacks=[]
    )

    app.add_handler(conv)
    app.run_polling()

if __name__ == "__main__":
    main()
