import os
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, CallbackContext,
    MessageHandler, CallbackQueryHandler, ContextTypes,
    filters
)

# Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Telegram bot token from .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "webhook")  # can be anything
WEBHOOK_PATH = f"/{WEBHOOK_SECRET}"
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # full URL including Render domain

# Data structures
freights = [
    {"from": "Budapest", "to": "Berlin", "quantity": "33 raklap", "price": 950, "name": "Güntner Berlin"},
    {"from": "Győr", "to": "Lipcse", "quantity": "24 raklap", "price": 870, "name": "Audi AG"},
    {"from": "Kecskemét", "to": "Stuttgart", "quantity": "20 raklap", "price": 920, "name": "Mercedes-Benz"},
    {"from": "Nyíregyháza", "to": "Köln", "quantity": "30 raklap", "price": 890, "name": "Continental Nyíregyháza"},
    {"from": "Szeged", "to": "Hamburg", "quantity": "25 raklap", "price": 620, "name": "Pick Szeged"},
    {"from": "Debrecen", "to": "München", "quantity": "22 raklap", "price": 980, "name": "BMW Debrecen"},
]
accepted_freights = []

trailers = {
    "XYZ1234": {"status": "üres", "freight": None},
    "ABC5678": {"status": "üres", "freight": None},
    "DEF9012": {"status": "üres", "freight": None},
}

tractors = {
    "1111AAA": {"driver": "Nagy Péter", "trailer": "XYZ1234"},
    "2222BBB": {"driver": "Kiss Gábor", "trailer": "ABC5678"},
    "3333CCC": {"driver": "Tóth László", "trailer": "DEF9012"},
}

# Telegram handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Üdvözöllek a Fuvartestbotnál! 🚛\n"
        "/fuvarok - Aktuális fuvarajánlatok\n"
        "/elfogad <sorszám> - Fuvar elfogadása\n"
        "/szures <kulcsszo> - Fuvar szűrése város vagy mennyiség alapján\n"
        "/ajanlat - AI ajánlás a legjobb fuvarra\n"
        "/potkocsik - Pótkocsik állapota\n"
        "/valt <rendszám> - Pótkocsi állapotváltás\n"
        "/traktorok - Vontatók és sofőrök\n"
        "/rendel <rendszám> <fuvar_név> - Fuvar rendelése pótkocsihoz"
    )

async def fuvarok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not freights:
        await update.message.reply_text("Nincs elérhető fuvar.")
        return
    msg = "\n".join([f"{i+1}. {f['from']} → {f['to']}, {f['quantity']}, {f['price']} EUR"
                     for i, f in enumerate(freights)])
    await update.message.reply_text("📦 Elérhető fuvarok:\n" + msg)

async def elfogad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        index = int(context.args[0]) - 1
        freight = freights.pop(index)
        accepted_freights.append(freight)
        for key in trailers:
            if trailers[key]["freight"] == freight["name"]:
                trailers[key] = {"status": "üres", "freight": None}
        await update.message.reply_text(
            f"✅ Elfogadva: {freight['from']} → {freight['to']} ({freight['name']})"
        )
    except:
        await update.message.reply_text("Hibás sorszám vagy nincs ilyen fuvar.")

async def szures(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Használat: /szures <város vagy mennyiség>")
        return
    keyword = " ".join(context.args).lower()
    results = [f for f in freights if keyword in f["from"].lower() or keyword in f["to"].lower() or keyword in f["quantity"].lower()]
    if not results:
        await update.message.reply_text("Nincs találat.")
        return
    msg = "\n".join([f"{i+1}. {f['from']} → {f['to']}, {f['quantity']}, {f['price']} EUR"
                     for i, f in enumerate(results)])
    await update.message.reply_text("🔎 Szűrt fuvarok:\n" + msg)

async def ajanlat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not freights:
        await update.message.reply_text("Nincs elérhető fuvar.")
        return
    best = max(freights, key=lambda x: x["price"])
    await update.message.reply_text(
        f"🤖 AI ajánlás: {best['from']} → {best['to']}, {best['quantity']}, {best['price']} EUR\n"
        "💡 Célszerű mielőbb lefoglalni!"
    )

async def potkocsik(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = ""
    for rsz, data in trailers.items():
        freight_info = f" / {data['freight']}" if data['freight'] else ""
        msg += f"{rsz}: {data['status']}{freight_info}\n"
    await update.message.reply_text("🚛 Pótkocsik állapota:\n" + msg)

async def valt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        rsz = context.args[0]
        if rsz not in trailers:
            await update.message.reply_text("Ismeretlen rendszám.")
            return
        trailers[rsz]["status"] = "rakott" if trailers[rsz]["status"] == "üres" else "üres"
        if trailers[rsz]["status"] == "üres":
            trailers[rsz]["freight"] = None
        await update.message.reply_text(f"{rsz} új állapota: {trailers[rsz]['status']}")
    except:
        await update.message.reply_text("Használat: /valt <rendszám>")

async def rendel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        rsz = context.args[0]
        fname = " ".join(context.args[1:])
        if rsz not in trailers:
            await update.message.reply_text("Ismeretlen pótkocsi rendszám.")
            return
        trailers[rsz]["freight"] = fname
        trailers[rsz]["status"] = "rakott"
        await update.message.reply_text(f"{rsz} mostantól rakott / {fname}")
    except:
        await update.message.reply_text("Használat: /rendel <rendszám> <fuvar_név>")

async def traktorok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "\n".join([f"{plate}: {data['driver']} → {data['trailer']}"
                     for plate, data in tractors.items()])
    await update.message.reply_text("🚛 Vontatók és sofőrök:\n" + msg)

# FastAPI setup
app = FastAPI()
bot_app = Application.builder().token(BOT_TOKEN).build()

bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("fuvarok", fuvarok))
bot_app.add_handler(CommandHandler("elfogad", elfogad))
bot_app.add_handler(CommandHandler("szures", szures))
bot_app.add_handler(CommandHandler("ajanlat", ajanlat))
bot_app.add_handler(CommandHandler("potkocsik", potkocsik))
bot_app.add_handler(CommandHandler("valt", valt))
bot_app.add_handler(CommandHandler("rendel", rendel))
bot_app.add_handler(CommandHandler("traktorok", traktorok))

@app.on_event("startup")
async def on_startup():
    await bot_app.bot.set_webhook(url=WEBHOOK_URL + WEBHOOK_PATH)

@app.post(WEBHOOK_PATH)
async def handle(request: Request):
    data = await request.json()
    update = Update.de_json(data, bot_app.bot)
    await bot_app.process_update(update)
    return {"ok": True}
