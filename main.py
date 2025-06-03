import os
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, ContextTypes, filters, ConversationHandler
)

# Naplózás
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Fuvar és jármű adatok
fuvarok = []
potkocsik = {f"{i:03}{chr(65 + i%3)}{chr(66 + i%3)}{chr(67 + i%3)}": "üres" for i in range(1, 11)}
vontatok = {f"{1000+i}{chr(65 + i%5)}{chr(66 + i%4)}{chr(67 + i%3)}": None for i in range(1, 11)}

# Állapotok
(HONNAN, HOVA, MENNYI, AR) = range(4)

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
        "/rendeles – Fuvar kiválasztása\n"
    )

# Help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛠 Elérhető parancsok:\n"
        "/start – Indítás\n"
        "/help – Súgó\n"
        "/fuvarlist – Elérhető fuvarok\n"
        "/ujfuvar – Fuvarajánlat beküldése\n"
        "/potkocsik – Pótkocsik állapotai (rakott/üres)\n"
        "/vontatok – Vontatók hozzárendelései\n"
        "/rendeles – Részletes infó kért fuvarról"
    )

# Fuvarlista
async def fuvarlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not fuvarok:
        await update.message.reply_text("Nincs még elérhető fuvar.")
        return
    msg = "📦 Elérhető fuvarok:\n"
    for i, fuvar in enumerate(fuvarok, 1):
        msg += f"{i}. {fuvar['honnan']} → {fuvar['hova']} | {fuvar['mennyiseg']} | {fuvar['ar']} EUR\n"
    await update.message.reply_text(msg)

# Fuvarfelvitel lépései
async def ujfuvar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📍 Honnan indul a fuvar?")
    return HONNAN

async def honnan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["honnan"] = update.message.text
    await update.message.reply_text("🏁 Hová tart?")
    return HOVA

async def hova(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["hova"] = update.message.text
    await update.message.reply_text("📦 Milyen mennyiség (pl. 12 raklap)?")
    return MENNYI

async def mennyi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mennyiseg"] = update.message.text
    await update.message.reply_text("💶 Mekkora az ajánlott díj (EUR)?")
    return AR

async def ar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["ar"] = update.message.text
    fuvarok.append(dict(context.user_data))
    await update.message.reply_text("✅ Fuvar sikeresen rögzítve!")
    return ConversationHandler.END

# Részletek lekérdezése
async def rendeles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not fuvarok:
        await update.message.reply_text("Nincs elérhető fuvar.")
        return
    msg = "Melyik fuvar érdekel? Írd be a számát (pl. 1):"
    await update.message.reply_text(msg)
    return 0

async def rendeles_valasz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    index = int(update.message.text) - 1
    if 0 <= index < len(fuvarok):
        fuvar = fuvarok[index]
        await update.message.reply_text(
            f"📋 Részletek:\n"
            f"Honnan: {fuvar['honnan']}\n"
            f"Hová: {fuvar['hova']}\n"
            f"Mennyiség: {fuvar['mennyiseg']}\n"
            f"Ajánlat: {fuvar['ar']} EUR\n"
            f"AI javaslat: {'Jó ajánlat' if int(fuvar['ar']) > 600 else 'Alacsony ajánlat'}"
        )
    else:
        await update.message.reply_text("❌ Érvénytelen sorszám.")
    return ConversationHandler.END

# Pótkocsik állapota
async def potkocsik_allapot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "🚛 Pótkocsik állapota:\n"
    for rendszam, allapot in potkocsik.items():
        msg += f"{rendszam}: {allapot}\n"
    await update.message.reply_text(msg)

# Vontatók állapota
async def vontatok_allapot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "🚚 Vontatók és hozzárendelt pótkocsik:\n"
    for rendszam, potko in vontatok.items():
        msg += f"{rendszam} → {potko if potko else 'nincs hozzárendelve'}\n"
    await update.message.reply_text(msg)

# Fallback / kilépés
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚫 Művelet megszakítva.")
    return ConversationHandler.END

# Echo fallback
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Nem értettem, használj egy parancsot. (/help)")

# Fő program
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
        fallbacks=[CommandHandler("cancel", cancel)],
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("rendeles", rendeles)],
        states={0: [MessageHandler(filters.TEXT & ~filters.COMMAND, rendeles_valasz)]},
        fallbacks=[CommandHandler("cancel", cancel)],
    ))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    app.run_polling()
