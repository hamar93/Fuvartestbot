
import os
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")

# State definitions for conversation
FUVAR_HONNAN, FUVAR_HOVA, FUVAR_MENNYI, FUVAR_AR, FUVAR_JOVA = range(5)
VALTOZTAT_RENDSZAM, VALTOZTAT_ALLAPOT = range(5, 7)

fuvarok = []
potkocsik = {f"ABC{i:03}": "üres" for i in range(1, 11)}
vontatok = {f"{1000+i}{chr(65+i%26)}{chr(66+i%26)}{chr(67+i%26)}": None for i in range(10)}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        """Üdvözöllek! 👋 Én vagyok a Fuvartestbot, az AI alapú fuvarszervező.

        Írd be a /help parancsot az elérhető funkciókért."""
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📌 Elérhető parancsok:
"
        "/fuvarlist – Aktuális fuvarajánlatok
"
        "/ujfuvar – Új fuvarajánlat feltöltése
"
        "/potkocsi – Pótkocsi állapotok megtekintése
"
        "/valtoztat – Pótkocsi állapotának módosítása
"
        "/vontatok – Vontatók listája
"
        "/cancel – Művelet megszakítása"
    )

async def fuvarlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not fuvarok:
        await update.message.reply_text("Nincsenek elérhető fuvarok.")
    else:
        response = "📦 Fuvarajánlatok:
"
        for idx, f in enumerate(fuvarok, 1):
            response += f"{idx}. {f['honnan']} → {f['hova']}, {f['mennyiseg']} raklap, {f['ar']} EUR
"
        await update.message.reply_text(response)

async def potkocsi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = "🚛 Pótkocsik állapota:
"
    for rendszam, allapot in potkocsik.items():
        response += f"{rendszam}: {allapot}
"
    await update.message.reply_text(response)

async def vontatok_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = "🚚 Vontatók:
"
    for rendszam in vontatok:
        response += f"{rendszam}
"
    await update.message.reply_text(response)

# Fuvarfelvétel folyamata
async def ujfuvar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Honnan indul a fuvar?")
    return FUVAR_HONNAN

async def fuvar_hova(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["honnan"] = update.message.text
    await update.message.reply_text("Hová tart a fuvar?")
    return FUVAR_HOVA

async def fuvar_mennyiseg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["hova"] = update.message.text
    await update.message.reply_text("Hány raklap/paletta?")
    return FUVAR_MENNYI

async def fuvar_ar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mennyiseg"] = update.message.text
    await update.message.reply_text("Mi az ajánlott ár EUR-ban?")
    return FUVAR_AR

async def fuvar_jovahagy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["ar"] = update.message.text
    adat = context.user_data
    summary = f"📄 Áttekintés:
{adat['honnan']} → {adat['hova']}, {adat['mennyiseg']} raklap, {adat['ar']} EUR
Jóváhagyod? (igen/nem)"
    await update.message.reply_text(summary)
    return FUVAR_JOVA

async def fuvar_mentes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.lower() == "igen":
        fuvarok.append(context.user_data.copy())
        await update.message.reply_text("✅ Fuvar elmentve.")
    else:
        await update.message.reply_text("❌ Fuvar mentése megszakítva.")
    return ConversationHandler.END

# Állapotváltoztató folyamat
async def valtoztat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Melyik pótkocsi rendszámát módosítod?")
    return VALTOZTAT_RENDSZAM

async def valtoztat_allapot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rendszam = update.message.text
    if rendszam not in potkocsik:
        await update.message.reply_text("❌ Nincs ilyen rendszám a nyilvántartásban.")
        return ConversationHandler.END
    context.user_data["rendszam"] = rendszam
    await update.message.reply_text("Új állapot (rakott/üres)?")
    return VALTOZTAT_ALLAPOT

async def allapot_mentes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uj_allapot = update.message.text.lower()
    rendszam = context.user_data["rendszam"]
    if uj_allapot in ["rakott", "üres"]:
        potkocsik[rendszam] = uj_allapot
        await update.message.reply_text(f"✅ {rendszam} mostantól {uj_allapot}.")
    else:
        await update.message.reply_text("❌ Csak 'rakott' vagy 'üres' lehet.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⛔ Művelet megszakítva.")
    return ConversationHandler.END

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("fuvarlist", fuvarlist))
    app.add_handler(CommandHandler("potkocsi", potkocsi))
    app.add_handler(CommandHandler("vontatok", vontatok_command))

    fuvar_conv = ConversationHandler(
        entry_points=[CommandHandler("ujfuvar", ujfuvar)],
        states={
            FUVAR_HONNAN: [MessageHandler(filters.TEXT & ~filters.COMMAND, fuvar_hova)],
            FUVAR_HOVA: [MessageHandler(filters.TEXT & ~filters.COMMAND, fuvar_mennyiseg)],
            FUVAR_MENNYI: [MessageHandler(filters.TEXT & ~filters.COMMAND, fuvar_ar)],
            FUVAR_AR: [MessageHandler(filters.TEXT & ~filters.COMMAND, fuvar_jovahagy)],
            FUVAR_JOVA: [MessageHandler(filters.TEXT & ~filters.COMMAND, fuvar_mentes)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    allapot_conv = ConversationHandler(
        entry_points=[CommandHandler("valtoztat", valtoztat)],
        states={
            VALTOZTAT_RENDSZAM: [MessageHandler(filters.TEXT & ~filters.COMMAND, valtoztat_allapot)],
            VALTOZTAT_ALLAPOT: [MessageHandler(filters.TEXT & ~filters.COMMAND, allapot_mentes)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(fuvar_conv)
    app.add_handler(allapot_conv)
    app.add_handler(CommandHandler("cancel", cancel))
    app.run_polling()
