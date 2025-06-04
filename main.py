import os
import logging
from fastapi import FastAPI, Request
from telegram import Update, Bot
from telegram.ext import (Application, CommandHandler, MessageHandler,
                          ConversationHandler, ContextTypes, filters)
from telegram.constants import ParseMode
import uvicorn

# --- Logging setup ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- Bot token ---
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # pl. https://fuvartestbot-xxxxx.onrender.com/webhook

# --- Data stores ---
fuvarok = [
    {"honnan": "Budapest", "hova": "Berlin", "mennyiseg": "12 raklap", "ar": "800"},
    {"honnan": "Győr", "hova": "Prága", "mennyiseg": "10 raklap", "ar": "720"},
    {"honnan": "Debrecen", "hova": "Milánó", "mennyiseg": "8 raklap", "ar": "950"},
    {"honnan": "Szeged", "hova": "Lipcse", "mennyiseg": "6 raklap", "ar": "600"},
    {"honnan": "Pécs", "hova": "Bécs", "mennyiseg": "14 raklap", "ar": "670"},
    {"honnan": "Miskolc", "hova": "Güntner Berlin", "mennyiseg": "20 raklap", "ar": "1000"}
]

potkocsik = {
    "001ABC": "rakott / Güntner Berlin",
    "002BCD": "üres",
    "003CDE": "rakott / Prága",
    "004DEF": "üres",
    "005EFG": "rakott / Bécs",
    "006FGH": "üres",
    "007GHI": "rakott / Lipcse",
    "008HIJ": "üres",
    "009IJK": "rakott / Milánó",
    "010JKL": "üres"
}

vontatok = {
    "1001ABC": "001ABC",
    "1002BCD": None,
    "1003CDE": "005EFG",
    "1004DEF": None,
    "1005EFG": "003CDE",
    "1006FGH": None,
    "1007GHI": "007GHI",
    "1008HIJ": None,
    "1009IJK": "009IJK",
    "1010JKL": None
}

(HONNAN, HOVA, MENNYI, AR) = range(4)

# --- FastAPI app init ---
app = FastAPI()
bot_app = Application.builder().token(BOT_TOKEN).build()

@app.post("/webhook")
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, bot_app.bot)
    await bot_app.process_update(update)
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"message": "Fuvartestbot Webhook aktiv."}

# --- Command handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "\n\n\ud83c\udf10 *Fuvartestbot aktív!* \n"
        "\n\ud83d\udcc5 /ujfuvar - Új fuvar hozzáadása"
        "\n\ud83d\udcbc /fuvarlist - Fuvarlista megtekintése"
        "\n\ud83d\udd0d /rendeles - Fuvar részletek lekérdezése"
        "\n\ud83d\ude9a /potkocsik - Pótkocsik állapota"
        "\n\ud83d\ude9b /vontatok - Vontatók hozzárendelése"
        "\n\u2696\ufe0f /allapotvaltas - Pótkocsi állapot váltás"
        "\n\ud83d\udc65 /hozzarendeles - Vontató hozzárendelés",
        parse_mode=ParseMode.MARKDOWN
    )

async def fuvarlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not fuvarok:
        await update.message.reply_text("\ud83d\udcc5 Nincs elérhető fuvar.")
        return
    msg = "\n".join([
        f"{i+1}. {f['honnan']} ➔ {f['hova']} | {f['mennyiseg']} | {f['ar']} EUR"
        for i, f in enumerate(fuvarok)
    ])
    await update.message.reply_text(f"\ud83d\udce6 Elérhető fuvarok:\n{msg}")

async def ujfuvar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("\ud83d\udccd Honnan indul a fuvar?")
    return HONNAN

async def honnan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["honnan"] = update.message.text
    await update.message.reply_text("\ud83c\udf1f Hová tart?")
    return HOVA

async def hova(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["hova"] = update.message.text
    await update.message.reply_text("\ud83d\ude9a Milyen mennyiség? (pl. 12 raklap)")
    return MENNYI

async def mennyi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mennyiseg"] = update.message.text
    await update.message.reply_text("\ud83d\udcb6 Ajánlat összege EUR?")
    return AR

async def ar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["ar"] = update.message.text
    fuvarok.append(dict(context.user_data))
    await update.message.reply_text("\u2705 Fuvar rögzítve!")
    return ConversationHandler.END

async def rendeles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not fuvarok:
        await update.message.reply_text("\u274c Nincs fuvar a listán.")
        return ConversationHandler.END
    await update.message.reply_text("\ud83d\udd0d Melyik fuvar? (sorszám)")
    return 0

async def rendeles_valasz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        idx = int(update.message.text) - 1
        f = fuvarok[idx]
        ai_ertekeles = "\ud83d\udca1 Ajánlott!" if int(f['ar']) >= 600 else "\u26a0\ufe0f Alacsony ár!"
        await update.message.reply_text(
            f"\ud83d\udcc5 Fuvar:\nHonnan: {f['honnan']}\nHova: {f['hova']}\nMennyiség: {f['mennyiseg']}\nÁr: {f['ar']} EUR\n{ai_ertekeles}"
        )
    except:
        await update.message.reply_text("\u274c Hibás sorszám.")
    return ConversationHandler.END

async def potkocsik_allapot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "\n".join([f"{rendszam}: {allapot}" for rendszam, allapot in potkocsik.items()])
    await update.message.reply_text(f"\ud83d\ude9a Pótkocsik:\n{msg}")

async def allapotvaltas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("\ud83d\ude9a Add meg a pótkocsi rendszámát:")
    return 0

async def allapotvaltas_valasz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rendszam = update.message.text
    if rendszam in potkocsik:
        if "üres" in potkocsik[rendszam]:
            potkocsik[rendszam] = "rakott / ismeretlen"
        else:
            potkocsik[rendszam] = "üres"
        await update.message.reply_text(f"\u2705 {rendszam} állapota megváltozott: {potkocsik[rendszam]}")
    else:
        await update.message.reply_text("\u274c Nincs ilyen pótkocsi.")
    return ConversationHandler.END

async def vontatok_allapot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "\n".join([
        f"{vontato}: {potko if potko else 'nincs hozzárendelve'}"
        for vontato, potko in vontatok.items()
    ])
    await update.message.reply_text(f"\ud83d\ude9b Vontatók:\n{msg}")

async def hozzarendeles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("\ud83d\ude9b Add meg a vontató és pótkocsi rendszámait szóközzel elválasztva:")
    return 0

async def hozzarendeles_valasz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.split()
    if len(text) != 2:
        await update.message.reply_text("\u274c Használat: rendszám1 rendszám2")
        return ConversationHandler.END
    vontato, potko = text
    if vontato in vontatok and potko in potkocsik:
        vontatok[vontato] = potko
        await update.message.reply_text(f"\u2705 {vontato} hozzárendelve: {potko}")
    else:
        await update.message.reply_text("\u274c Hibás rendszámok.")
    return ConversationHandler.END

# --- Bot init ---
async def setup():
    bot = Bot(token=BOT_TOKEN)
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")

    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("fuvarlist", fuvarlist))
    bot_app.add_handler(CommandHandler("potkocsik", potkocsik_allapot))
    bot_app.add_handler(CommandHandler("vontatok", vontatok_allapot))

    bot_app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("ujfuvar", ujfuvar)],
        states={
            HONNAN: [MessageHandler(filters.TEXT & ~filters.COMMAND, honnan)],
            HOVA: [MessageHandler(filters.TEXT & ~filters.COMMAND, hova)],
            MENNYI: [MessageHandler(filters.TEXT & ~filters.COMMAND, mennyi)],
            AR: [MessageHandler(filters.TEXT & ~filters.COMMAND, ar)]
        },
        fallbacks=[]
    ))

    bot_app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("rendeles", rendeles)],
        states={0: [MessageHandler(filters.TEXT & ~filters.COMMAND, rendeles_valasz)]},
        fallbacks=[]
    ))

    bot_app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("allapotvaltas", allapotvaltas)],
        states={0: [MessageHandler(filters.TEXT & ~filters.COMMAND, allapotvaltas_valasz)]},
        fallbacks=[]
    ))

    bot_app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("hozzarendeles", hozzarendeles)],
        states={0: [MessageHandler(filters.TEXT & ~filters.COMMAND, hozzarendeles_valasz)]},
        fallbacks=[]
    ))

import asyncio
if __name__ == "__main__":
    asyncio.run(setup())
    uvicorn.run("main:app", host="0.0.0.0", port=10000)
