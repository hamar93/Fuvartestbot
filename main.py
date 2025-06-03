import os
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, ContextTypes,
    ConversationHandler, filters
)

# --- Logging setup ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- Bot token ---
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")

# --- Data stores ---
fuvarok = []
potkocsik = {f"{i:03}{chr(65 + i%3)}{chr(66 + i%3)}{chr(67 + i%3)}": "üres" for i in range(1, 11)}
vontatok = {f"{1000+i}{chr(65 + i%5)}{chr(66 + i%4)}{chr(67 + i%3)}": None for i in range(1, 11)}

# --- States for ConversationHandlers ---
(HONNAN, HOVA, MENNYI, AR) = range(4)

# --- Commands ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✈️ Üdv a Fuvartestbotnál!

"
        "Parancsok:
"
        "/ujfuvar - Fuvarajánlat feltöltése
"
        "/fuvarlist - Elérhető fuvarok
"
        "/rendeles - Fuvar részletek
"
        "/potkocsik - Pótkocsik állapota
"
        "/vontatok - Vontatók hozzárendelése
"
        "/allapotvaltas - Pótkocsi állapot váltás
"
        "/hozzarendeles - Vontató hozzárendelés"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

# --- Fuvar kezelés ---
async def fuvarlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not fuvarok:
        await update.message.reply_text("📆 Nincs még fuvar a rendszerben.")
        return
    msg = "\n".join([
        f"{i+1}. {f['honnan']} ➔ {f['hova']} | {f['mennyiseg']} | {f['ar']} EUR"
        for i, f in enumerate(fuvarok)
    ])
    await update.message.reply_text(f"📦 Fuvarok:\n{msg}")

async def ujfuvar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📍 Honnan indul a fuvar?")
    return HONNAN

async def honnan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["honnan"] = update.message.text
    await update.message.reply_text("🌟 Hová tart?")
    return HOVA

async def hova(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["hova"] = update.message.text
    await update.message.reply_text("🚚 Milyen mennyiség? (pl. 12 raklap)")
    return MENNYI

async def mennyi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mennyiseg"] = update.message.text
    await update.message.reply_text("💶 Ajánlat összege EUR?")
    return AR

async def ar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["ar"] = update.message.text
    fuvarok.append(dict(context.user_data))
    await update.message.reply_text("✅ Fuvar rögzítve!")
    return ConversationHandler.END

# --- Fuvar részletek ---
async def rendeles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not fuvarok:
        await update.message.reply_text("❌ Nincs fuvar a listán.")
        return ConversationHandler.END
    await update.message.reply_text("🔍 Melyik fuvar? (szám)")
    return 0

async def rendeles_valasz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        idx = int(update.message.text) - 1
        f = fuvarok[idx]
        ai_ertekeles = "💡 Ajánlott!" if int(f['ar']) >= 600 else "⚠️ Alacsony ár!"
        await update.message.reply_text(
            f"📅 Fuvar:
Honnan: {f['honnan']}
Hova: {f['hova']}
Mennyiség: {f['mennyiseg']}
Ár: {f['ar']} EUR\n{ai_ertekeles}"
        )
    except:
        await update.message.reply_text("❌ Hibás sorszám.")
    return ConversationHandler.END

# --- Pótkocsik ---
async def potkocsik_allapot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "\n".join([f"{rendszam}: {allapot}" for rendszam, allapot in potkocsik.items()])
    await update.message.reply_text(f"🚛 Pótkocsik:\n{msg}")

async def allapotvaltas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚛 Add meg a pótkocsi rendszámát:")
    return 0

async def allapotvaltas_valasz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rendszam = update.message.text
    if rendszam in potkocsik:
        potkocsik[rendszam] = "rakott" if potkocsik[rendszam] == "üres" else "üres"
        await update.message.reply_text(f"✅ {rendszam} állapota megváltozott: {potkocsik[rendszam]}")
    else:
        await update.message.reply_text("❌ Nincs ilyen pótkocsi.")
    return ConversationHandler.END

# --- Vontatók ---
async def vontatok_allapot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "\n".join([
        f"{vontato}: {potko if potko else 'nincs hozzárendelve'}"
        for vontato, potko in vontatok.items()
    ])
    await update.message.reply_text(f"🚚 Vontatók:\n{msg}")

async def hozzarendeles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚚 Add meg a vontató rendszámát:")
    return 0

async def hozzarendeles_valasz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.split()
    if len(text) != 2:
        await update.message.reply_text("❌ Használat: rendszám1 rendszám2")
        return ConversationHandler.END
    vontato, potko = text
    if vontato in vontatok and potko in potkocsik:
        vontatok[vontato] = potko
        await update.message.reply_text(f"✅ {vontato} hozzárendelve: {potko}")
    else:
        await update.message.reply_text("❌ Hibás rendszámok.")
    return ConversationHandler.END

# --- Main ---
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
        states={0: [MessageHandler(filters.TEXT & ~filters.COMMAND, rendeles_valasz)]},
        fallbacks=[]
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("allapotvaltas", allapotvaltas)],
        states={0: [MessageHandler(filters.TEXT & ~filters.COMMAND, allapotvaltas_valasz)]},
        fallbacks=[]
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("hozzarendeles", hozzarendeles)],
        states={0: [MessageHandler(filters.TEXT & ~filters.COMMAND, hozzarendeles_valasz)]},
        fallbacks=[]
    ))

    app.run_polling()
