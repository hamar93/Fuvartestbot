from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters
)
import logging
import os

# Logging beállítás
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Környezeti változóból token beolvasás
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Fuvar rögzítés lépései
(HONNAN, HOVA, RAKLAP, IDOPONT, DIJ) = range(5)

# Ideiglenes tárolók
fuvarok = []
potkocsik = [
    {"rendszam": "ABC123", "statusz": "üres"},
    {"rendszam": "XYZ456", "statusz": "rakott"},
    {"rendszam": "LMN789", "statusz": "üres"},
    {"rendszam": "DEF321", "statusz": "rakott"},
    {"rendszam": "JKL654", "statusz": "üres"},
    {"rendszam": "QWE987", "statusz": "üres"},
    {"rendszam": "RTY432", "statusz": "rakott"},
    {"rendszam": "UIO876", "statusz": "üres"},
    {"rendszam": "PAS111", "statusz": "rakott"},
    {"rendszam": "ZXC222", "statusz": "üres"},
]

# Start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Üdvözöllek! 👋\n\n"
        "Én vagyok a Fuvartestbot, a mesterséges intelligencia alapú fuvarszervező asszisztensed.\n\n"
        "Használhatod a /help parancsot, ha szeretnéd megtudni, miben tudok segíteni."
    )

# Help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛠 Elérhető funkciók:\n"
        "- /start – Üdvözlés\n"
        "- /help – Ez a súgó\n"
        "- /fuvarlist – Teszt fuvarok\n"
        "- /ujfuvar – Új fuvarajánlat\n"
        "- /potkocsik – Pótkocsi lista\n"
        "- /alvo – Alvó módba kapcsolás"
    )

# Fuvar lista
async def fuvarlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nyugat_magyar = [
        "Berlin → Győr – 22 raklap – 880 EUR",
        "Lyon → Szeged – 10 paletta – 770 EUR",
        "Milano → Budapest – 33 paletta – 990 EUR",
        "Frankfurt → Tatabánya – 12 paletta – 640 EUR",
        "Brüsszel → Pécs – 14 raklap – 710 EUR",
    ]
    magyar_nyugat = [
        "Budapest → Nürnberg – 11 raklap – 670 EUR",
        "Győr → Paris – 18 paletta – 890 EUR",
        "Szeged → Bologna – 6 raklap – 450 EUR",
        "Miskolc → Düsseldorf – 20 raklap – 920 EUR",
        "Tatabánya → Torino – 13 paletta – 770 EUR",
    ]
    await update.message.reply_text(
        "📦 Fuvarajánlatok:\n\n"
        "→ Nyugatról Magyarországra:\n" + "\n".join(nyugat_magyar) +
        "\n\n→ Magyarországról Nyugatra:\n" + "\n".join(magyar_nyugat)
    )

# Fuvar indítás
async def uj_fuvar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📍 Honnan indul a fuvar?")
    return HONNAN

async def fuvar_honnan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["honnan"] = update.message.text
    await update.message.reply_text("📍 Hova tart a fuvar?")
    return HOVA

async def fuvar_hova(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["hova"] = update.message.text
    await update.message.reply_text("📦 Hány raklap/paletta?")
    return RAKLAP

async def fuvar_raklap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["raklap"] = update.message.text
    await update.message.reply_text("🗓 Mikorra az indulás?")
    return IDOPONT

async def fuvar_idopont(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["idopont"] = update.message.text
    await update.message.reply_text("💶 Mekkora a díj?")
    return DIJ

async def fuvar_dij(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["dij"] = update.message.text
    fuvar = context.user_data.copy()
    fuvarok.append(fuvar)
    await update.message.reply_text(
        f"✅ Fuvar rögzítve:\n{fuvar['honnan']} → {fuvar['hova']}\n"
        f"{fuvar['raklap']} raklap\nIdőpont: {fuvar['idopont']}\nDíj: {fuvar['dij']} EUR\n"
        "Feltöltés TIMOCOM-ra szimulálva... ✅"
    )
    return ConversationHandler.END

# Pótkocsi lekérdezés
async def potkocsik_listazasa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    szoveg = "🚛 Pótkocsik:\n"
    for p in potkocsik:
        szoveg += f"- {p['rendszam']}: {p['statusz']}\n"
    await update.message.reply_text(szoveg)

# Alvó mód
async def alvo_mod(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Alvó módba kapcsolva. Üzenetre ébred.")

# Echo fallback
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Nem értettem. Használd a /help parancsot.")

# App build
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("fuvarlist", fuvarlist))
app.add_handler(CommandHandler("potkocsik", potkocsik_listazasa))
app.add_handler(CommandHandler("alvo", alvo_mod))

# Fuvar beszélgetés
fuvar_conv = ConversationHandler(
    entry_points=[CommandHandler("ujfuvar", uj_fuvar)],
    states={
        HONNAN: [MessageHandler(filters.TEXT & ~filters.COMMAND, fuvar_honnan)],
        HOVA: [MessageHandler(filters.TEXT & ~filters.COMMAND, fuvar_hova)],
        RAKLAP: [MessageHandler(filters.TEXT & ~filters.COMMAND, fuvar_raklap)],
        IDOPONT: [MessageHandler(filters.TEXT & ~filters.COMMAND, fuvar_idopont)],
        DIJ: [MessageHandler(filters.TEXT & ~filters.COMMAND, fuvar_dij)],
    },
    fallbacks=[]
)
app.add_handler(fuvar_conv)

# Általános szöveg
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

# Indítás
app.run_polling()
