import os
import logging
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import (
    Application, ApplicationBuilder, CommandHandler,
    MessageHandler, ConversationHandler, ContextTypes, filters
)
from telegram.ext._httpxrequest import HTTPXRequest

# --- Logging setup ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# --- Environment variables ---
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# --- FastAPI for webhook ---
app = FastAPI()

# --- Data stores ---
fuvarok = [
    {"honnan": "Budapest", "hova": "Berlin", "mennyiseg": "33 raklap", "ar": "850"},
    {"honnan": "Győr", "hova": "Prága", "mennyiseg": "24 raklap", "ar": "620"},
    {"honnan": "Szeged", "hova": "Milánó", "mennyiseg": "12 tonna", "ar": "700"},
    {"honnan": "Debrecen", "hova": "Hamburg", "mennyiseg": "10 raklap", "ar": "580"},
    {"honnan": "Pécs", "hova": "Brno", "mennyiseg": "15 tonna", "ar": "660"},
    {"honnan": "Sopron", "hova": "Lipcse", "mennyiseg": "20 raklap", "ar": "610"},
]
potkocsik = {f"{i:03}{chr(65+i%3)}{chr(66+i%3)}{chr(67+i%3)}": "üres" for i in range(1, 11)}
vontatok = {f"{1000+i}{chr(65+i%5)}{chr(66+i%4)}{chr(67+i%3)}": None for i in range(1, 11)}

# --- States ---
(HONNAN, HOVA, MENNYI, AR) = range(4)

# --- Command handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚛 Üdvözöllek a Fuvartestbotnál!
"
        "Használható parancsok:
"
        "/ujfuvar – Fuvar feltöltés
"
        "/fuvarlist – Fuvarok listázása
"
        "/rendeles – Fuvar részletei
"
        "/potkocsik – Pótkocsik állapota
"
        "/vontatok – Vontatók listája
"
        "/allapotvaltas – Pótkocsi állapot váltás
"
        "/hozzarendeles – Vontató hozzárendelés"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

async def fuvarlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not fuvarok:
        await update.message.reply_text("❌ Nincs elérhető fuvar.")
        return
    msg = "\n".join([
        f"{i+1}. {f['honnan']} → {f['hova']} | {f['mennyiseg']} | {f['ar']} EUR"
        for i, f in enumerate(fuvarok)
    ])
    await update.message.reply_text(f"📦 Elérhető fuvarok:
{msg}")

async def ujfuvar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📍 Honnan indul a fuvar?")
    return HONNAN

async def honnan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["honnan"] = update.message.text
    await update.message.reply_text("🏁 Hová tart?")
    return HOVA

async def hova(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["hova"] = update.message.text
    await update.message.reply_text("📦 Mennyiség?")
    return MENNYI

async def mennyi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mennyiseg"] = update.message.text
    await update.message.reply_text("💶 Ár (EUR)?")
    return AR

async def ar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["ar"] = update.message.text
    fuvarok.append(dict(context.user_data))
    await update.message.reply_text("✅ Fuvar rögzítve!")
    return ConversationHandler.END

async def rendeles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not fuvarok:
        await update.message.reply_text("❌ Nincs fuvar a listán.")
        return ConversationHandler.END
    await update.message.reply_text("🔢 Melyik fuvar érdekel? Írd be a sorszámot.")
    return 0

async def rendeles_valasz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        idx = int(update.message.text) - 1
        f = fuvarok[idx]
        ai_ertekeles = "✅ Jó ajánlat!" if int(f["ar"]) >= 600 else "⚠️ Alacsony ajánlat!"
        await update.message.reply_text(
            f"📋 Fuvar részletek:
"
            f"Honnan: {f['honnan']}
"
            f"Hova: {f['hova']}
"
            f"Mennyiség: {f['mennyiseg']}
"
            f"Ajánlat: {f['ar']} EUR
"
            f"{ai_ertekeles}"
        )
    except Exception:
        await update.message.reply_text("❌ Hibás szám.")
    return ConversationHandler.END

async def potkocsik_allapot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "\n".join([f"{r}: {a}" for r, a in potkocsik.items()])
    await update.message.reply_text(f"🚛 Pótkocsik állapota:
{msg}")

async def allapotvaltas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Írd be a pótkocsi rendszámát:")
    return 0

async def allapotvaltas_valasz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rendszam = update.message.text.strip()
    if rendszam in potkocsik:
        aktualis = potkocsik[rendszam]
        if aktualis == "üres":
            potkocsik[rendszam] = f"rakott / {fuvarok[-1]['hova']}" if fuvarok else "rakott"
        else:
            potkocsik[rendszam] = "üres"
        await update.message.reply_text(f"🔄 {rendszam} új állapot: {potkocsik[rendszam]}")
    else:
        await update.message.reply_text("❌ Nincs ilyen pótkocsi.")
    return ConversationHandler.END

async def vontatok_allapot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "\n".join([f"{v}: {p if p else 'nincs hozzárendelve'}" for v, p in vontatok.items()])
    await update.message.reply_text(f"🚚 Vontatók:
{msg}")

async def hozzarendeles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Írd be: vontató pótkocsi (pl. 1001ABC DEF)")
    return 0

async def hozzarendeles_valasz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        vontato, potko = update.message.text.strip().split()
        if vontato in vontatok and potko in potkocsik:
            vontatok[vontato] = potko
            await update.message.reply_text(f"✅ {vontato} hozzárendelve: {potko}")
        else:
            await update.message.reply_text("❌ Hibás rendszámok.")
    except:
        await update.message.reply_text("❌ Használat: vontato potkocsi")
    return ConversationHandler.END

# --- Setup application ---
application = ApplicationBuilder().token(BOT_TOKEN).updater(None).request(HTTPXRequest()).build()

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(CommandHandler("fuvarlist", fuvarlist))
application.add_handler(CommandHandler("potkocsik", potkocsik_allapot))
application.add_handler(CommandHandler("vontatok", vontatok_allapot))

application.add_handler(ConversationHandler(
    entry_points=[CommandHandler("ujfuvar", ujfuvar)],
    states={
        HONNAN: [MessageHandler(filters.TEXT & ~filters.COMMAND, honnan)],
        HOVA: [MessageHandler(filters.TEXT & ~filters.COMMAND, hova)],
        MENNYI: [MessageHandler(filters.TEXT & ~filters.COMMAND, mennyi)],
        AR: [MessageHandler(filters.TEXT & ~filters.COMMAND, ar)],
    },
    fallbacks=[]
))

application.add_handler(ConversationHandler(
    entry_points=[CommandHandler("rendeles", rendeles)],
    states={0: [MessageHandler(filters.TEXT & ~filters.COMMAND, rendeles_valasz)]},
    fallbacks=[]
))

application.add_handler(ConversationHandler(
    entry_points=[CommandHandler("allapotvaltas", allapotvaltas)],
    states={0: [MessageHandler(filters.TEXT & ~filters.COMMAND, allapotvaltas_valasz)]},
    fallbacks=[]
))

application.add_handler(ConversationHandler(
    entry_points=[CommandHandler("hozzarendeles", hozzarendeles)],
    states={0: [MessageHandler(filters.TEXT & ~filters.COMMAND, hozzarendeles_valasz)]},
    fallbacks=[]
))

# --- FastAPI route for Telegram webhook ---
@app.post("/")
async def webhook_handler(request: Request):
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"status": "ok"}

# --- Start webhook ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=10000)