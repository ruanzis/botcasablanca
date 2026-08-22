import asyncio
import logging
import os
import requests
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# Configuração de Logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurações
TOKEN = os.getenv("TELEGRAM_TOKEN", "8956870259:AAGR_gmp5h2pzwdYnqC_QScrigH8imPVoho")
LINK_CANAL = os.getenv("LINK_CANAL", "https://t.me/+qrh5SObhV3xmODhh")
CAPA_PATH = "capa.jpg"

MISTICPAY_API_URL = os.getenv("MISTICPAY_API_URL", "https://api.misticpay.com/v1")
MISTICPAY_CLIENT_SECRET = os.getenv("MISTICPAY_CLIENT_SECRET", "")
WEBHOOK_BASE_URL = os.getenv("WEBHOOK_BASE_URL", "https://botcasablanca.onrender.com")

telegram_app = Application.builder().token(TOKEN).build()

# ==================== FUNÇÃO GERAR PIX ====================
def gerar_pix_misticpay(valor: float, telegram_id: int):
    if not MISTICPAY_CLIENT_SECRET:
        logger.error("MISTICPAY_CLIENT_SECRET ausente.")
        return None

    payload = {
        "amount": valor,
        "external_id": f"user_{telegram_id}",
        "postback_url": f"{WEBHOOK_BASE_URL}/misticpay-webhook",
    }
    
    headers = {
        "Authorization": f"Bearer {MISTICPAY_CLIENT_SECRET}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    try:
        response = requests.post(f"{MISTICPAY_API_URL}/pix/charge", json=payload, headers=headers, timeout=12)
        if response.status_code in [200, 201]:
            return response.json()
        return None
    except Exception as e:
        logger.error(f"Erro ao gerar PIX: {e}")
        return None

# ==================== HANDLERS ====================
async def enviar_menu_principal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    primeiro_nome = user.first_name if user else "Cliente"

    texto = (
        f"Olá <b>{primeiro_nome}</b>, seja bem-vindo ao <b>CasaBlanca Bot</b>! 🏛️✨\n\n"
        "Selecione uma opção abaixo para navegar pelo nosso catálogo:"
    )

    keyboard = [
        [
            InlineKeyboardButton("🛒 Comprar", callback_data="menu_comprar"),
            InlineKeyboardButton("ℹ️ Informações", callback_data="info"),
        ],
        [
            InlineKeyboardButton("🛠️ Ferramentas", callback_data="ferramentas"),
            InlineKeyboardButton("🎁 Indicações", callback_data="indicacoes"),
        ],
        [InlineKeyboardButton("💳 Adicionar Saldo", callback_data="add_saldo")],
        [InlineKeyboardButton("📢 Canal Oficial", url=LINK_CANAL)],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    chat_id = update.effective_chat.id

    if os.path.exists(CAPA_PATH):
        try:
            with open(CAPA_PATH, "rb") as photo:
                await context.bot.send_photo(chat_id=chat_id, photo=photo, caption=texto, reply_markup=reply_markup, parse_mode="HTML")
                return
        except Exception as e:
            logger.error(f"Erro imagem: {e}")

    await context.bot.send_message(chat_id=chat_id, text=texto, reply_markup=reply_markup, parse_mode="HTML")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await enviar_menu_principal(update, context)

# RESPOSTA AOS CLIQUES NOS BOTÕES
async def botao_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # Confirma o clique para tirar a animação de carregamento

    data = query.data
    if data == "menu_comprar":
        await query.message.reply_text("🛒 **Catálogo de Produtos:**\nEm breve novidades!", parse_mode="Markdown")
    elif data == "info":
        await query.message.reply_text("ℹ️ **Informações:** Suporte via @haridadenetwork", parse_mode="Markdown")
    elif data == "ferramentas":
        await query.message.reply_text("🛠️ **Ferramentas:** Escolha uma opção do menu.", parse_mode="Markdown")
    elif data == "indicacoes":
        await query.message.reply_text("🎁 **Indicações:** Compartilhe seu link de indicação!", parse_mode="Markdown")
    elif data == "add_saldo":
        await query.message.reply_text("💳 Use o comando `/pix 10` para adicionar R$ 10,00 de saldo.", parse_mode="Markdown")

async def pix_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if context.args:
        try:
            valor = float(context.args[0].replace(",", "."))
        except ValueError:
            await update.message.reply_text("❌ Use o exemplo: <code>/pix 10</code>", parse_mode="HTML")
            return
    else:
        valor = 10.0

    await update.message.reply_text(f"⏳ Gerando PIX no valor de <b>R$ {valor:.2f}</b>...", parse_mode="HTML")
    
    loop = asyncio.get_running_loop()
    dados_pix = await loop.run_in_executor(None, gerar_pix_misticpay, valor, user_id)

    if dados_pix:
        qr_code = dados_pix.get("qrcode") or dados_pix.get("pix_code") or dados_pix.get("copy_paste")
        if qr_code:
            resposta = f"✅ <b>PIX Gerado!</b>\n\n💰 <b>Valor:</b> R$ {valor:.2f}\n\nCopie o código:\n<code>{qr_code}</code>"
            await update.message.reply_text(resposta, parse_mode="HTML")
            return

    await update.message.reply_text("❌ <b>Falha ao gerar o PIX.</b>\nVerifique se preencheu a chave `MISTICPAY_CLIENT_SECRET` no Render.", parse_mode="HTML")

# Registra os manipuladores no Telegram
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("pix", pix_command))
telegram_app.add_handler(CallbackQueryHandler(botao_callback))  # RESOLVE O ERRO DOS BOTÕES

# ==================== FASTAPI ====================
@asynccontextmanager
async def lifespan(app: FastAPI):
    await telegram_app.initialize()
    await telegram_app.start()
    webhook_url = f"{WEBHOOK_BASE_URL.rstrip('/')}/telegram-webhook"
    await telegram_app.bot.set_webhook(url=webhook_url)
    yield
    await telegram_app.stop()
    await telegram_app.shutdown()

app = FastAPI(lifespan=lifespan)

@app.post("/telegram-webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"status": "online"}
