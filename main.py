import os
import logging
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    ConversationHandler, MessageHandler, filters
)

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# Adatok
fuvarok = [
    {"honnan": "Budapest", "hova": "Berlin", "mennyiseg": "33 raklap", "ar": "850"},
    {"honnan": "Győr", "hova": "Brno", "mennyiseg": "24 raklap", "ar": "600"},
    {"honnan": "Szeged", "hova": "Milánó", "mennyiseg": "12 raklap", "ar": "1100"},
]
potkocsik = {f"TR{i:02}ABC": "üres" for i in range(1, 11)}
traktorok = {f"{1000+i}XYZ": None for i in range(1, 11)}

(HONNAN, HOVA, MENNYI, AR) = range(4)

# Parancsok
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚛 Üdvözöllek a Fuvartestbotnál!
"
        "Parancsok:
"
        "/ujfuvar – Fuvarajánlat feltöltése
"
        "/fuvarok – Fuvarok listája
"
        "/elfogad – Fuvar elfogadása
"
        "/szures – Fuvar szűrése
"
        "/ajanlat – AI ajánlat
"
        "/potkocsik – Pótkocsik állapota
"
        "/traktorok – Traktorok állapota
"
        "/valt – Állapotváltás
"
        "/rendel – Pótkocsi rendelés fuvarhoz"
    )

async def fuvarok_listaja(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not fuvarok:
        await update.message.reply_text("Nincs elérhető fuvar.")
        return
    msg = "
".join([f"{i+1}. {f['honnan']} -> {f['hova']} ({f['mennyiseg']}, {f['ar']} EUR)" for i, f in enumerate(fuvarok)])
    await update.message.reply_text(msg)

async def potkocsik_allapot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "
".join([f"{r}: {a}" for r, a in potkocsik.items()])
    await update.message.reply_text(f"Pótkocsik:
{msg}")

async def traktorok_allapot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "
".join([f"{r}: {p if p else 'nincs'}" for r, p in traktorok.items()])
    await update.message.reply_text(f"Traktorok:
{msg}")

app = FastAPI()

@app.on_event("startup")
async def startup():
    from telegram.ext import Application
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("fuvarok", fuvarok_listaja))
    application.add_handler(CommandHandler("potkocsik", potkocsik_allapot))
    application.add_handler(CommandHandler("traktorok", traktorok_allapot))

    await application.bot.set_webhook(url=WEBHOOK_URL)
    app.state.application = application

@app.post("/")
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, app.state.application.bot)
    await app.state.application.process_update(update)
    return {"ok": True}