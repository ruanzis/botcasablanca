import asyncio
import logging
import os
import requests
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# Configuração de Logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== CONFIGURAÇÕES GERAIS ====================
TOKEN = os.getenv("TELEGRAM_TOKEN", "8956870259:AAGR_gmp5h2pzwdYnqC_QScrigH8imPVoho")
ID_CANAL = -1004302224747
LINK_CANAL = "https://t.me/+qrh5SObhV3xmODhh"
NOME_FOTO = "capa.jpg"
FOTO_CATEGORIAS = "categorias.jpg"

# MISTICPAY CONFIGURAÇÕES
MISTICPAY_API_URL = "https://api.misticpay.com/v1"
MISTICPAY_CLIENT_ID = os.getenv("MISTICPAY_CLIENT_ID", "SEU_CLIENT_ID")
MISTICPAY_CLIENT_SECRET = os.getenv("MISTICPAY_CLIENT_SECRET", "SEU_CLIENT_SECRET")
WEBHOOK_BASE_URL = os.getenv("WEBHOOK_BASE_URL", "https://botcasablanca.onrender.com")

POLITICA_REEMBOLSO = (
    "Política de Reembolso\n\n"
    "⚠️ Caso o saldo esteja abaixo do mínimo garantido na pré-compra, "
    "solicite reembolso em até 20 minutos via @haridadenetwork, com vídeo mostrando cartão, valor e erro."
)

# Inicialização da Aplicação Telegram
telegram_app = Application.builder().token(TOKEN).build()

# ==================== UTILITÁRIOS DA MISTICPAY ====================
def gerar_pix_misticpay(valor: float, telegram_id: int):
    """Fazer a requisição de pagamento via MisticPay."""
    payload = {
        "amount": valor,
        "external_id": f"user_{telegram_id}",
        "postback_url": f"{WEBHOOK_BASE_URL}/misticpay-webhook",
    }
    
    headers = {
        "Authorization": f"Bearer {MISTICPAY_CLIENT_SECRET}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(f"{MISTICPAY_API_URL}/pix/charge", json=payload, headers=headers, timeout=10)
        if response.status_code in [200, 201]:
            return response.json()
        else:
            logger.error(f"Erro MisticPay: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Falha ao conectar com MisticPay: {e}")
        return None

# Checagem de canal protegida
async def esta_no_canal(context: ContextTypes.DEFAULT_TYPE, user_id: int):
    try:
        membro = await asyncio.wait_for(
            context.bot.get_chat_member(chat_id=ID_CANAL, user_id=user_id),
            timeout=4.0,
        )
        return membro.status in ["member", "administrator", "creator"]
    except Exception as e:
        logger.warning(f"Aviso ao checar canal: {e}")
        return True

# ==================== COMANDOS DO TELEGRAM ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await enviar_menu_principal(update, context)

async def pix_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /pix para gerar cobrança via MisticPay"""
    user_id = update.effective_user.id
    
    # Exemplo: /pix 50 ou /pix
    if context.args:
        try:
            valor = float(context.args[0].replace(",", "."))
        except ValueError:
            await update.message.reply_text("❌ Valor inválido. Use exemplo: `/pix 50` ou `/pix 50.00`", parse_mode="Markdown")
            return
    else:
        valor = 50.00  # Valor padrão caso não seja especificado

    await update.message.reply_text(f"⏳ Gerando PIX no valor de R$ {valor:.2f}...")
    dados_pix = gerar_pix_misticpay(valor, user_id)

    if dados_pix and "qrcode" in dados_pix:
        qr_code = dados_pix.get("qrcode")
        pix_copy_paste = dados_pix.get("pix_code", qr_code)
        
        texto = (
            f"✅ **PIX Gerado com Sucesso!**\n\n"
            f"💰 **Valor:** R$ {valor:.2f}\n\n"
            f"👇 Copie o código abaixo para pagar:\n`{pix_copy_paste}`"
        )
        await update.message.reply_text(texto, parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Falha ao gerar o PIX. Verifique as credenciais da MisticPay.")

async def enviar_menu_principal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    primeiro_nome = user.first_name if user else "Cliente"

    texto = (
        f"Olá **{primeiro_nome}**, seja bem-vindo ao **CasaBlanca Bot**! 🏛️✨\n\n"
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
        [
            InlineKeyboardButton("💳 Adicionar Saldo", callback_data="add_saldo")
        ],
        [InlineKeyboardButton("📢 Canal Oficial", url=LINK_CANAL)],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.message.reply_text(texto, reply_markup=reply_markup, parse_mode="Markdown")
    elif update.message:
        await update.message.reply_text(texto, reply_markup=reply_markup, parse_mode="Markdown")

# Registrar Handlers no Bot
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("pix", pix_command))

# ==================== SERVIDOR FASTAPI E WEBHOOKS ====================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Configurações na inicialização do servidor no Render
    await telegram_app.initialize()
    await telegram_app.start()
    webhook_url = f"{WEBHOOK_BASE_URL}/telegram-webhook"
    await telegram_app.bot.set_webhook(url=webhook_url)
    logger.info(f"Webhook registrado em: {webhook_url}")
    
    yield
    
    # Encerramento do servidor
    await telegram_app.stop()
    await telegram_app.shutdown()

app = FastAPI(lifespan=lifespan)

@app.post("/telegram-webhook")
async def telegram_webhook(request: Request):
    """Recebe atualizações do Telegram via Webhook"""
    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return {"status": "ok"}

@app.post("/misticpay-webhook")
async def misticpay_webhook(request: Request):
    """Recebe confirmações de pagamento da MisticPay"""
    dados = await request.json()
    logger.info(f"Webhook MisticPay Recebido: {dados}")
    
    # Exemplo simples de notificação via Bot após confirmação do Pix
    status = dados.get("status")
    external_id = dados.get("external_id", "")
    
    if status in ["paid", "approved"] and external_id.startswith("user_"):
        user_id = int(external_id.replace("user_", ""))
        await telegram_app.bot.send_message(
            chat_id=user_id,
            text="🎉 **Pagamento PIX confirmado com sucesso!** Seu saldo/compra foi atualizado."
        )
    return {"status": "success"}

@app.get("/")
async def health_check():
    return {"status": "Bot Casablanca Online!"}
