import os
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters,
    ConversationHandler
)
from telegram.constants import ParseMode

# Naplózás
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Pl.: https://yourdomain.com/bot
PORT = int(os.getenv("PORT", "8443"))

# Fuvar és jármű adatok
fuvarok = []
potkocsik = {f"{i:03}{chr(65 + i%3)}{chr(66 + i%3)}{chr(67 + i%3)}": "üres" for i in range(1, 11)}
vontatok = {f"{1000+i}{chr(65 + i%5)}{chr(66 + i%4)}{chr(67 + i%3)}": None for i in range(1, 11)}

# Állapotok
(HONNAN, HOVA, MENNYI, AR, REND_VALASZ, ALLAPOTMODOSITAS, HOZZARENDEL) = range(7)

# Start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Üdvözöllek! 🚛\nÉn vagyok a Fuvartestbot.\n\n"
        "📋 Használható parancsok:\n"
        "/help – Súgó\n"
        "/fuvarlist – Elérhető fuvarok\n"
        "/ujfuvar – Új fuvar feltöltése\n"
        "/potkocsik – Pótkocsik állapota\n"
        "/vontatok – Vontatók állapota\n"
        "/allapotvaltas – Pótkocsi állapot módosítása\n"
        "/hozzarendeles – Pótkocsi hozzárendelése vontatóhoz\n"
        "/rendeles – Fuvar kiválasztása részletes adatokkal\n"
    )

# Help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Használható parancsok: /start, /ujfuvar, /fuvarlist, /potkocsik, /vontatok, /allapotvaltas, /hozzarendeles, /rendeles")

# Fuvarlista
async def fuvarlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not fuvarok:
        await update.message.reply_text("Nincs még elérhető fuvar.")
        return
    msg = "📦 Elérhető fuvarok:\n"
    for i, fuvar in enumerate(fuvarok, 1):
        msg += f"{i}. {fuvar['honnan']} → {fuvar['hova']} | {fuvar['mennyiseg']} | {fuvar['ar']} EUR\n"
    await update.message.reply_text(msg)

# Fuvarfelvitel
async def ujfuvar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📍 Honnan indul a fuvar?")
    return HONNAN

async def honnan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['honnan'] = update.message.text
    await update.message.reply_text("🏁 Hová tart?")
    return HOVA

async def hova(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['hova'] = update.message.text
    await update.message.reply_text("📦 Milyen mennyiség?")
    return MENNYI

async def mennyi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['mennyiseg'] = update.message.text
    await update.message.reply_text("💶 Ajánlott díj (EUR)?")
    return AR

async def ar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['ar'] = update.message.text
    fuvarok.append(dict(context.user_data))
    await update.message.reply_text("✅ Fuvar rögzítve!")
    return ConversationHandler.END

# Részletes fuvarinfó
async def rendeles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not fuvarok:
        await update.message.reply_text("❌ Nincs elérhető fuvar.")
        return ConversationHandler.END
    await update.message.reply_text("Írd be a fuvar sorszámát:")
    return REND_VALASZ

async def rendeles_valasz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        index = int(update.message.text) - 1
        fuvar = fuvarok[index]
        ai_tip = "✅ Jó ajánlat" if int(fuvar['ar']) >= 600 else "⚠️ Alacsony ajánlat"
        msg = (
            f"📄 Fuvar részletei:\n"
            f"Honnan: {fuvar['honnan']}\n"
            f"Hová: {fuvar['hova']}\n"
            f"Mennyiség: {fuvar['mennyiseg']}\n"
            f"Ár: {fuvar['ar']} EUR\n"
            f"AI értékelés: {ai_tip}"
        )
        await update.message.reply_text(msg)
    except:
        await update.message.reply_text("❌ Hibás sorszám.")
    return ConversationHandler.END

# Állapotváltás
async def allapotvaltas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Írd be a pótkocsi rendszámát, amit módosítanál:")
    return ALLAPOTMODOSITAS

async def allapotvaltas_valasz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rendszam = update.message.text.strip().upper()
    if rendszam in potkocsik:
        jelenlegi = potkocsik[rendszam]
        uj = "rakott" if jelenlegi == "üres" else "üres"
        potkocsik[rendszam] = uj
        await update.message.reply_text(f"🔄 Állapot frissítve: {rendszam} → {uj}")
    else:
        await update.message.reply_text("❌ Nincs ilyen rendszám.")
    return ConversationHandler.END

# Hozzárendelés
async def hozzarendeles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Írd be: [vontató rendszám] [pótkocsi rendszám] (szóközzel elválasztva)")
    return HOZZARENDEL

async def hozzarendeles_valasz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        vontato, potko = update.message.text.upper().split()
        if vontato in vontatok and potko in potkocsik:
            vontatok[vontato] = potko
            await update.message.reply_text(f"🔗 Hozzárendelve: {vontato} ⇄ {potko}")
        else:
            await update.message.reply_text("❌ Helytelen rendszám(ok).")
    except:
        await update.message.reply_text("❌ Helytelen formátum.")
    return ConversationHandler.END

# Állapotlekérdezések
async def potkocsik_allapot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "🚛 Pótkocsik állapota:\n"
    for rendszam, allapot in potkocsik.items():
        msg += f"{rendszam}: {allapot}\n"
    await update.message.reply_text(msg)

async def vontatok_allapot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "🚚 Vontatók és hozzárendelt pótkocsik:\n"
    for rendszam, potko in vontatok.items():
        msg += f"{rendszam} → {potko if potko else 'nincs hozzárendelve'}\n"
    await update.message.reply_text(msg)

# Echo
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Nem értem. Írd be: /help")

# Fő
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("fuvarlist", fuvarlist))
    app.add_handler(CommandHandler("potkocsik", potkocsik_allapot))
    app.add_handler(CommandHandler("vontatok", vontatok_allapot))

    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("ujfuvar", ujfuvar)],
        states={
            HONNAN: [MessageHandler(filters.TEXT & ~filters.COMMAND, honnan)],
            HOVA: [MessageHandler(filters.TEXT & ~filters.COMMAND, hova)],
            MENNYI: [MessageHandler(filters.TEXT & ~filters.COMMAND, mennyi)],
            AR: [MessageHandler(filters.TEXT & ~filters.COMMAND, ar)],
        },
        fallbacks=[]
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("rendeles", rendeles)],
        states={REND_VALASZ: [MessageHandler(filters.TEXT & ~filters.COMMAND, rendeles_valasz)]},
        fallbacks=[]
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("allapotvaltas", allapotvaltas)],
        states={ALLAPOTMODOSITAS: [MessageHandler(filters.TEXT & ~filters.COMMAND, allapotvaltas_valasz)]},
        fallbacks=[]
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("hozzarendeles", hozzarendeles)],
        states={HOZZARENDEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, hozzarendeles_valasz)]},
        fallbacks=[]
    ))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Webhook aktiválás
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=BOT_TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}"
    )
