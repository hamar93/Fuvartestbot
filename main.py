import os
import logging
from fastapi import FastAPI, Request
from telegram import Update, Bot
from telegram.ext import (
    Application, ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ConversationHandler, ContextTypes
)
from telegram.ext.webhook import WebhookServer
from telegram.constants import ParseMode
from dotenv import load_dotenv

# 🔧 Környezeti változók betöltése
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Pl. https://fuvartestbot-xxxx.onrender.com

# 🔧 Naplózás
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# 🧠 Adattárolók
fuvarok = []
potkocsik = {f"{i:03}{chr(65 + i%3)}{chr(66 + i%3)}{chr(67 + i%3)}": "üres" for i in range(1, 11)}
vontatok = {f"{1000+i}{chr(65 + i%5)}{chr(66 + i%4)}{chr(67 + i%3)}": None for i in range(1, 11)}

# 📍 Állapotok a ConversationHandler-hez
(HONNAN, HOVA, MENNYI, AR, RENDELES_INDEX) = range(5)

# 🚀 FastAPI app Render webhookhoz
app = FastAPI()

telegram_app: Application = ApplicationBuilder().token(BOT_TOKEN).build()

# =======================
# 📦 Fuvarkezelő funkciók
# =======================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚛 Üdv a Fuvartestbotnál!\n"
        "/ujfuvar – új fuvar rögzítése\n"
        "/fuvarlist – fuvarok listája\n"
        "/rendeles – fuvar kiválasztása\n"
        "/potkocsik – pótkocsik állapota\n"
        "/vontatok – vontatók állapota\n"
        "/help – parancslista"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛠 Elérhető parancsok:\n"
        "/start\n/help\n/fuvarlist\n/ujfuvar\n/rendeles\n/potkocsik\n/vontatok"
    )

async def fuvarlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not fuvarok:
        await update.message.reply_text("📭 Nincs elérhető fuvar.")
        return
    msg = "📋 Fuvarok:\n"
    for i, fuvar in enumerate(fuvarok, 1):
        msg += f"{i}. {fuvar['honnan']} → {fuvar['hova']} | {fuvar['mennyiseg']} | {fuvar['ar']} EUR\n"
    await update.message.reply_text(msg)

# =========================
# 🔄 Fuvar rögzítése lépésről lépésre
# =========================

async def ujfuvar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📍 Honnan indul a fuvar?")
    return HONNAN

async def honnan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["honnan"] = update.message.text
    await update.message.reply_text("🏁 Hová tart?")
    return HOVA

async def hova(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["hova"] = update.message.text
    await update.message.reply_text("📦 Milyen mennyiség?")
    return MENNYI

async def mennyi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mennyiseg"] = update.message.text
    await update.message.reply_text("💶 Ajánlott díj (EUR)?")
    return AR

async def ar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["ar"] = update.message.text
    fuvarok.append(dict(context.user_data))
    await update.message.reply_text("✅ Fuvar rögzítve.")
    return ConversationHandler.END

# ======================
# 🧐 Részletes rendelés
# ======================

async def rendeles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not fuvarok:
        await update.message.reply_text("❌ Nincs fuvar.")
        return ConversationHandler.END
    await update.message.reply_text("📥 Írd be a fuvar sorszámát:")
    return RENDELES_INDEX

async def rendeles_valasz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        index = int(update.message.text) - 1
        if 0 <= index < len(fuvarok):
            f = fuvarok[index]
            ai_tip = "✅ Jó ajánlat" if int(f["ar"]) > 600 else "⚠️ Alacsony ajánlat"
            await update.message.reply_text(
                f"📋 Részletek:\n"
                f"Honnan: {f['honnan']}\n"
                f"Hová: {f['hova']}\n"
                f"Mennyiség: {f['mennyiseg']}\n"
                f"Ár: {f['ar']} EUR\n"
                f"🤖 AI értékelés: {ai_tip}"
            )
        else:
            await update.message.reply_text("❌ Nincs ilyen fuvar.")
    except Exception:
        await update.message.reply_text("⚠️ Hibás formátum.")
    return ConversationHandler.END

# ======================
# 🚛 Pótkocsik állapota
# ======================

async def potkocsik_allapot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "🚛 Pótkocsik:\n"
    for rsz, status in potkocsik.items():
        msg += f"{rsz}: {status}\n"
    await update.message.reply_text(msg)

# 🚚 Vontatók hozzárendelése
async def vontatok_allapot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "🚚 Vontatók:\n"
    for rsz, potko in vontatok.items():
        msg += f"{rsz} → {potko if potko else 'nincs hozzárendelve'}\n"
    await update.message.reply_text(msg)

# 🛑 Kilépés
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Megszakítva.")
    return ConversationHandler.END

# ============================
# 🌐 FastAPI → Webhook handler
# ============================

@app.post("/")
async def handle_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, bot=telegram_app.bot)
    await telegram_app.update_queue.put(update)
    return {"status": "ok"}

# ================
# 🧠 Bot indulása
# ================

async def init_bot():
    await telegram_app.bot.set_webhook(WEBHOOK_URL)
    logging.info("🔗 Webhook beállítva.")

# ================
# ▶️ Bot konfigurálása
# ================

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("help", help_command))
telegram_app.add_handler(CommandHandler("fuvarlist", fuvarlist))
telegram_app.add_handler(CommandHandler("potkocsik", potkocsik_allapot))
telegram_app.add_handler(CommandHandler("vontatok", vontatok_allapot))

telegram_app.add_handler(ConversationHandler(
    entry_points=[CommandHandler("ujfuvar", ujfuvar)],
    states={
        HONNAN: [MessageHandler(filters.TEXT & ~filters.COMMAND, honnan)],
        HOVA: [MessageHandler(filters.TEXT & ~filters.COMMAND, hova)],
        MENNYI: [MessageHandler(filters.TEXT & ~filters.COMMAND, mennyi)],
        AR: [MessageHandler(filters.TEXT & ~filters.COMMAND, ar)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
))

telegram_app.add_handler(ConversationHandler(
    entry_points=[CommandHandler("rendeles", rendeles)],
    states={RENDELES_INDEX: [MessageHandler(filters.TEXT & ~filters.COMMAND, rendeles_valasz)]},
    fallbacks=[CommandHandler("cancel", cancel)],
))

# 🔁 Bot és webhook aktiválás induláskor
import asyncio
asyncio.get_event_loop().create_task(init_bot())
