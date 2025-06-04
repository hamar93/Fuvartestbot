import os
import logging
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import (
    Application, ApplicationBuilder, CommandHandler,
    ContextTypes, MessageHandler, ConversationHandler, filters
)
import asyncio

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Környezeti változók
TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# FastAPI példány
app = FastAPI()

# Adatok
fuvarok = [
    {"honnan": "Budapest", "hova": "Berlin", "mennyiseg": "20 raklap", "ar": "700"},
    {"honnan": "Győr", "hova": "München", "mennyiseg": "33 raklap", "ar": "680"},
    {"honnan": "Szeged", "hova": "Prága", "mennyiseg": "15 raklap", "ar": "550"},
    {"honnan": "Debrecen", "hova": "Wien", "mennyiseg": "20 raklap", "ar": "610"},
    {"honnan": "Pécs", "hova": "Brno", "mennyiseg": "25 raklap", "ar": "590"},
    {"honnan": "Tatabánya", "hova": "Güntner Berlin", "mennyiseg": "30 raklap", "ar": "720"},
]

potkocsik = {f"{i+100}ABC": "üres" for i in range(10)}
vontatok = {f"{i+1000}XYZ": None for i in range(10)}
soforok = [f"Sofőr{i}" for i in range(1, 11)]

# Állapotok
(HONNAN, HOVA, MENNYI, AR) = range(4)

# Bot inicializálás
bot_app: Application = ApplicationBuilder().token(TOKEN).build()


# Parancsok
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚛 Üdvözöllek a Fuvartestbotnál!\n\n"
        "📌 Elérhető parancsok:\n"
        "/ujfuvar – Új fuvar feltöltése\n"
        "/fuvarlist – Fuvarok listázása\n"
        "/rendeles – Fuvar részletek\n"
        "/potkocsik – Pótkocsik állapota\n"
        "/vontatok – Vontatók állapota\n"
        "/allapotvaltas – Pótkocsi állapot váltás\n"
        "/hozzarendeles – Vontató hozzárendelés"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

async def fuvarlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not fuvarok:
        await update.message.reply_text("Nincs elérhető fuvar.")
        return
    msg = "\n".join([
        f"{i+1}. {f['honnan']} ➜ {f['hova']} | {f['mennyiseg']} | {f['ar']} EUR"
        for i, f in enumerate(fuvarok)
    ])
    await update.message.reply_text(msg)

async def ujfuvar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📍 Honnan indul a fuvar?")
    return HONNAN

async def honnan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["honnan"] = update.message.text
    await update.message.reply_text("🏁 Hová tart?")
    return HOVA

async def hova(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["hova"] = update.message.text
    await update.message.reply_text("📦 Milyen mennyiség (pl. 33 raklap)?")
    return MENNYI

async def mennyi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mennyiseg"] = update.message.text
    await update.message.reply_text("💰 Ajánlott díj (EUR)?")
    return AR

async def ar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["ar"] = update.message.text
    fuvarok.append(dict(context.user_data))
    await update.message.reply_text("✅ Fuvar sikeresen rögzítve.")
    return ConversationHandler.END

async def rendeles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not fuvarok:
        await update.message.reply_text("Nincs fuvar a listán.")
        return ConversationHandler.END
    await update.message.reply_text("🔢 Melyik fuvar részleteire vagy kíváncsi? Írd be a számát:")
    return 0

async def rendeles_valasz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        idx = int(update.message.text) - 1
        f = fuvarok[idx]
        ai = "💡 Jó ajánlat!" if int(f['ar']) >= 600 else "⚠️ Alacsony díj!"
        await update.message.reply_text(
            f"📦 Fuvar részletek:\n"
            f"Honnan: {f['honnan']}\n"
            f"Hová: {f['hova']}\n"
            f"Mennyiség: {f['mennyiseg']}\n"
            f"Ajánlat: {f['ar']} EUR\n{ai}"
        )
    except:
        await update.message.reply_text("❌ Hibás szám.")
    return ConversationHandler.END

async def potkocsik_allapot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "\n".join([f"{rendszam}: {allapot}" for rendszam, allapot in potkocsik.items()])
    await update.message.reply_text(f"🚛 Pótkocsik:\n{msg}")

async def vontatok_allapot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "\n".join([
        f"{v}: {p if p else 'nincs hozzárendelve'}"
        for v, p in vontatok.items()
    ])
    await update.message.reply_text(f"🚚 Vontatók:\n{msg}")

async def allapotvaltas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Írd be a pótkocsi rendszámát:")
    return 1

async def allapotvaltas_valasz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rendszam = update.message.text
    if rendszam in potkocsik:
        if potkocsik[rendszam] == "üres":
            potkocsik[rendszam] = f"rakott / {fuvarok[-1]['hova']}"
        else:
            potkocsik[rendszam] = "üres"
        await update.message.reply_text(f"✅ {rendszam} állapota: {potkocsik[rendszam]}")
    else:
        await update.message.reply_text("❌ Nem ismert rendszám.")
    return ConversationHandler.END

async def hozzarendeles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Add meg a vontató és a pótkocsi rendszámát szóközzel elválasztva (pl. 1001XYZ 101ABC):")
    return 2

async def hozzarendeles_valasz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        vontato, potkocsi = update.message.text.strip().split()
        if vontato in vontatok and potkocsi in potkocsik:
            vontatok[vontato] = potkocsi
            await update.message.reply_text(f"✅ {vontato} hozzárendelve: {potkocsi}")
        else:
            await update.message.reply_text("❌ Érvénytelen rendszám.")
    except:
        await update.message.reply_text("❌ Formátumhiba. Próbáld újra.")
    return ConversationHandler.END


# --- FastAPI webhook endpoint ---
@app.post("/")
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, bot_app.bot)
    await bot_app.process_update(update)
    return {"ok": True}


# --- Futás ---
async def main():
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("help", help_command))
    bot_app.add_handler(CommandHandler("fuvarlist", fuvarlist))
    bot_app.add_handler(CommandHandler("potkocsik", potkocsik_allapot))
    bot_app.add_handler(CommandHandler("vontatok", vontatok_allapot))

    bot_app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("ujfuvar", ujfuvar)],
        states={
            HONNAN: [MessageHandler(filters.TEXT & ~filters.COMMAND, honnan)],
            HOVA: [MessageHandler(filters.TEXT & ~filters.COMMAND, hova)],
            MENNYI: [MessageHandler(filters.TEXT & ~filters.COMMAND, mennyi)],
            AR: [MessageHandler(filters.TEXT & ~filters.COMMAND, ar)],
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
        states={1: [MessageHandler(filters.TEXT & ~filters.COMMAND, allapotvaltas_valasz)]},
        fallbacks=[]
    ))

    bot_app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("hozzarendeles", hozzarendeles)],
        states={2: [MessageHandler(filters.TEXT & ~filters.COMMAND, hozzarendeles_valasz)]},
        fallbacks=[]
    ))

    await bot_app.initialize()
    await bot_app.start()
    await bot_app.bot.set_webhook(url=WEBHOOK_URL)
    await bot_app.updater.start_polling()  # csak ideiglenes fallback, ha kell

if __name__ == "__main__":
    asyncio.run(main())
