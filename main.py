
import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from telegram import Update, Bot
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from telegram.ext.webhook import WebhookServer

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

app = FastAPI()
bot_app = Application.builder().token(BOT_TOKEN).build()

# Teszt fuvarok
fuvarok = [
    {"id": 1, "felado": "Budapest", "cimzett": "Berlin", "mennyiseg": 22, "arak": "1200 EUR"},
    {"id": 2, "felado": "Győr", "cimzett": "Wien", "mennyiseg": 10, "arak": "500 EUR"},
    {"id": 3, "felado": "Szeged", "cimzett": "Munchen", "mennyiseg": 33, "arak": "1400 EUR"},
    {"id": 4, "felado": "Debrecen", "cimzett": "Prága", "mennyiseg": 18, "arak": "800 EUR"},
    {"id": 5, "felado": "Pécs", "cimzett": "Zagreb", "mennyiseg": 24, "arak": "900 EUR"},
    {"id": 6, "felado": "Tatabánya", "cimzett": "Ljubljana", "mennyiseg": 26, "arak": "950 EUR"},
]

potkocsik = {
    "ABC123": {"allapot": "üres", "fuvar": None},
    "XYZ789": {"allapot": "rakott", "fuvar": "Budapest–Berlin"},
    "QWE456": {"allapot": "rakott", "fuvar": "Szeged–Munchen"},
}

traktorok = {
    "AAA111": "Kovács Péter",
    "BBB222": "Nagy László",
    "CCC333": "Szabó Erika",
}

# Kezdő üzenet
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚛 Üdvözöllek a Fuvartestbotnál!
"
        "Használható parancsok:
"
        "/fuvarok - Fuvarok listája
"
        "/ajanlat - Ajánlat generálás
"
        "/elfogad <fuvar_id> - Fuvar elfogadása
"
        "/szures <varos> - Fuvarok szűrése város alapján
"
        "/potkocsik - Pótkocsik listája
"
        "/rendel <rendszam> <fuvar> - Fuvar rendelése pótkocsihoz
"
        "/traktorok - Vontatók és sofőrök listája"
    )

async def fuvarok_listazasa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not fuvarok:
        await update.message.reply_text("Nincs elérhető fuvar.")
    else:
        szoveg = "📦 Elérhető fuvarok:
"
        for fuvar in fuvarok:
            szoveg += (
                f"#{fuvar['id']} {fuvar['felado']} ➝ {fuvar['cimzett']} | "
                f"{fuvar['mennyiseg']}t | {fuvar['arak']}
"
            )
        await update.message.reply_text(szoveg)

async def elfogad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Használat: /elfogad <fuvar_id>")
        return
    try:
        fuvar_id = int(context.args[0])
        fuvar = next((f for f in fuvarok if f["id"] == fuvar_id), None)
        if not fuvar:
            await update.message.reply_text("Nem található ilyen fuvar.")
            return
        fuvarok.remove(fuvar)
        await update.message.reply_text(
            f"✅ A fuvar elfogadva: {fuvar['felado']} ➝ {fuvar['cimzett']} ({fuvar['mennyiseg']}t)"
        )
    except ValueError:
        await update.message.reply_text("A fuvar ID szám legyen.")

async def szures(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Használat: /szures <varos>")
        return
    varos = context.args[0].lower()
    talalatok = [
        f for f in fuvarok
        if varos in f["felado"].lower() or varos in f["cimzett"].lower()
    ]
    if not talalatok:
        await update.message.reply_text("Nincs találat.")
    else:
        szoveg = "🔍 Szűrt fuvarok:
"
        for f in talalatok:
            szoveg += (
                f"#{f['id']} {f['felado']} ➝ {f['cimzett']} | "
                f"{f['mennyiseg']}t | {f['arak']}
"
            )
        await update.message.reply_text(szoveg)

async def potkocsik_listaja(update: Update, context: ContextTypes.DEFAULT_TYPE):
    szoveg = "🚚 Pótkocsik állapota:
"
    for rendszam, adat in potkocsik.items():
        allapot = adat["allapot"]
        fuvar = adat["fuvar"] if adat["fuvar"] else "nincs hozzárendelve"
        szoveg += f"{rendszam} / {allapot} / {fuvar}
"
    await update.message.reply_text(szoveg)

async def rendel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Használat: /rendel <rendszam> <fuvar>")
        return
    rendszam = context.args[0].upper()
    fuvar = " ".join(context.args[1:])
    if rendszam in potkocsik:
        potkocsik[rendszam]["allapot"] = "rakott"
        potkocsik[rendszam]["fuvar"] = fuvar
        await update.message.reply_text(f"{rendszam} mostantól rakott: {fuvar}")
    else:
        await update.message.reply_text("Ismeretlen rendszám.")

async def traktor_lista(update: Update, context: ContextTypes.DEFAULT_TYPE):
    szoveg = "🚜 Traktorok és sofőrök:
"
    for rendszam, sofor in traktorok.items():
        szoveg += f"{rendszam} – {sofor}
"
    await update.message.reply_text(szoveg)

async def ajanlat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not fuvarok:
        await update.message.reply_text("Nincs ajánlható fuvar.")
        return
    top_fuvar = max(fuvarok, key=lambda f: f["mennyiseg"])
    await update.message.reply_text(
        f"🤖 Ajánlatunk: {top_fuvar['felado']} ➝ {top_fuvar['cimzett']} "
        f"{top_fuvar['mennyiseg']}t ({top_fuvar['arak']})"
    )

# Handler regisztráció
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("fuvarok", fuvarok_listazasa))
bot_app.add_handler(CommandHandler("elfogad", elfogad))
bot_app.add_handler(CommandHandler("szures", szures))
bot_app.add_handler(CommandHandler("potkocsik", potkocsik_listaja))
bot_app.add_handler(CommandHandler("rendel", rendel))
bot_app.add_handler(CommandHandler("traktorok", traktor_lista))
bot_app.add_handler(CommandHandler("ajanlat", ajanlat))

@app.post(f"/{BOT_TOKEN}")
async def webhook_endpoint(request: Request):
    data = await request.json()
    update = Update.de_json(data, bot_app.bot)
    await bot_app.process_update(update)
    return {"ok": True}

# Webhook indítása
if __name__ == "__main__":
    import uvicorn
    bot_app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        url_path=BOT_TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}"
    )
