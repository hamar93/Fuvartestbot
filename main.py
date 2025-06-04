import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackContext, MessageHandler,
    filters, CallbackQueryHandler
)

# Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# Command Handlers
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "Üdvözöllek a Fuvartestbotnál! 🚛
"
        "/fuvarok - Aktuális fuvarajánlatok
"
        "/elfogad <sorszám> - Fuvar elfogadása
"
        "/szures <kulcsszo> - Fuvar szűrése város vagy mennyiség alapján
"
        "/ajanlat - AI ajánlás a legjobb fuvarra
"
        "/potkocsik - Pótkocsik állapota
"
        "/valt <rendszám> - Pótkocsi állapotváltás
"
        "/traktorok - Vontatók és sofőrök
"
        "/rendel <rendszám> <fuvar_név> - Fuvar rendelése pótkocsihoz
"
    )

async def fuvarok(update: Update, context: CallbackContext):
    if not freights:
        await update.message.reply_text("Nincs elérhető fuvar.")
        return
    msg = ""
    for i, f in enumerate(freights, 1):
        msg += f"{i}. {f['from']} → {f['to']}, {f['quantity']}, {f['price']} EUR
"
    await update.message.reply_text("📦 Elérhető fuvarok:
" + msg)

async def elfogad(update: Update, context: CallbackContext):
    try:
        index = int(context.args[0]) - 1
        freight = freights.pop(index)
        accepted_freights.append(freight)
        # free any trailer that had this freight
        for key in trailers:
            if trailers[key]["freight"] == freight["name"]:
                trailers[key] = {"status": "üres", "freight": None}
        await update.message.reply_text(f"✅ Elfogadva: {freight['from']} → {freight['to']} ({freight['name']})")
    except Exception as e:
        await update.message.reply_text("Hibás sorszám vagy nincs ilyen fuvar.")

async def szures(update: Update, context: CallbackContext):
    if not context.args:
        await update.message.reply_text("Használat: /szures <város vagy mennyiség>")
        return
    keyword = " ".join(context.args).lower()
    results = [f for f in freights if keyword in f["from"].lower() or keyword in f["to"].lower() or keyword in f["quantity"].lower()]
    if not results:
        await update.message.reply_text("Nincs találat.")
        return
    msg = ""
    for i, f in enumerate(results, 1):
        msg += f"{i}. {f['from']} → {f['to']}, {f['quantity']}, {f['price']} EUR
"
    await update.message.reply_text("🔎 Szűrt fuvarok:
" + msg)

async def ajanlat(update: Update, context: CallbackContext):
    if not freights:
        await update.message.reply_text("Nincs elérhető fuvar.")
        return
    best = max(freights, key=lambda x: x["price"])
    await update.message.reply_text(
        f"🤖 AI ajánlás: {best['from']} → {best['to']}, {best['quantity']}, {best['price']} EUR
"
        f"💡 Célszerű mielőbb lefoglalni!"
    )

async def potkocsik(update: Update, context: CallbackContext):
    msg = ""
    for rsz, data in trailers.items():
        freight_info = f" / {data['freight']}" if data['freight'] else ""
        msg += f"{rsz}: {data['status']}{freight_info}
"
    await update.message.reply_text("🚛 Pótkocsik állapota:
" + msg)

async def valt(update: Update, context: CallbackContext):
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

async def rendel(update: Update, context: CallbackContext):
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

async def traktorok(update: Update, context: CallbackContext):
    msg = ""
    for plate, data in tractors.items():
        trailer_info = data['trailer']
        msg += f"{plate}: {data['driver']} → {trailer_info}
"
    await update.message.reply_text("🚛 Vontatók és sofőrök:
" + msg)

# Bot entry
def main():
    import os
    from dotenv import load_dotenv
    load_dotenv()
    token = os.getenv("BOT_TOKEN")

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("fuvarok", fuvarok))
    app.add_handler(CommandHandler("elfogad", elfogad))
    app.add_handler(CommandHandler("szures", szures))
    app.add_handler(CommandHandler("ajanlat", ajanlat))
    app.add_handler(CommandHandler("potkocsik", potkocsik))
    app.add_handler(CommandHandler("valt", valt))
    app.add_handler(CommandHandler("rendel", rendel))
    app.add_handler(CommandHandler("traktorok", traktorok))

    app.run_polling()

if __name__ == "__main__":
    main()