import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Alap naplózás
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Üdvözöllek! 👋 Én vagyok a Fuvartestbot, a mesterséges intelligencia alapú fuvarszervező asszisztensed.\n\n"
        "Használhatod a /help parancsot, ha szeretnéd megtudni, miben tudok segíteni."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛠 Elérhető funkciók:\n"
        "- Írd be magyarul, hogy milyen fuvart keresel vagy ajánlasz (pl. 'Van egy fuvarom Münchenből Tatára')\n"
        "- /start – Üdvözlés\n"
        "- /help – Ez a súgó\n"
        "- /fuvarlist – Teszt fuvarok megtekintése"
    )

async def fuvarlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = "📦 Fuvarajánlatok:\n"
    nyugat_magyar = [
        "Berlin → Győr – 22 raklap – 880 EUR",
        "Lyon → Szeged – 10 paletta – 770 EUR",
        "Milano → Budapest – 33 paletta – 990 EUR",
        "Frankfurt → Tatabánya – 12 paletta – 640 EUR",
        "Brüsszel → Pécs – 14 raklap – 710 EUR"
    ]
    magyar_nyugat = [
        "Budapest → Nürnberg – 11 raklap – 670 EUR",
        "Győr → Paris – 18 paletta – 890 EUR",
        "Szeged → Bologna – 6 raklap – 450 EUR",
        "Miskolc → Düsseldorf – 20 raklap – 920 EUR",
        "Tatabánya → Torino – 13 paletta – 770 EUR"
    ]
    response += "\n→ Nyugatról Magyarországra:\n" + "\n".join(nyugat_magyar)
    response += "\n\n→ Magyarországról Nyugatra:\n" + "\n".join(magyar_nyugat)
    await update.message.reply_text(response)

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    if "fuvar" in text:
        await update.message.reply_text(
            "📄 Kérlek, írd meg pontosan:\n"
            "- Honnan hova menne a fuvar?\n"
            "- Hány paletta vagy raklap?\n"
            "- Mekkora a tervezett díj vagy ajánlat?\n"
            "Példa: 5 paletta Münchenből Bresciába, 400 EUR ajánlattal."
        )
    else:
        await update.message.reply_text("Sajnálom, ezt nem értettem. Próbáld meg újrafogalmazni vagy használd a /help parancsot.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("fuvarlist", fuvarlist))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    app.run_polling()
