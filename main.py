import asyncio
import logging
import os
import requests
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Configuração de Logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== CONFIGURAÇÕES GERAIS ====================
TOKEN = os.getenv("TELEGRAM_TOKEN", "8956870259:AAGR_gmp5h2pzwdYnqC_QScrigH8imPVoho")
LINK_CANAL = os.getenv("LINK_CANAL", "https://t.me/+qrh5SObhV3xmODhh")
CAPA_PATH = "capa.jpg"  # Imagem local ou URL publica

# Credenciais MisticPay
MISTICPAY_API_URL = os.getenv("MISTICPAY_API_URL", "https://api.misticpay.com/v1")
MISTICPAY_CLIENT_SECRET = os.getenv("MISTICPAY_CLIENT_SECRET", "cs_xmi6kbhukucgc1syoymxugk3h")
WEBHOOK_BASE_URL = os.getenv("WEBHOOK_BASE_URL", "https://botcasablanca.onrender.com")

# Inicialização da Aplicação Telegram
telegram_app = Application.builder().token(TOKEN).build()

# ==================== FUNÇÃO GERAR PIX ====================
def gerar_pix_misticpay(valor: float, telegram_id: int):
    """Gera uma cobrança PIX na MisticPay."""
    if not MISTICPAY_CLIENT_SECRET:
        logger.error("ERRO: MISTICPAY_CLIENT_SECRET não configurado nas variáveis de ambiente.")
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
        response = requests.post(
            f"{MISTICPAY_API_URL}/pix/charge",
            json=payload,
            headers=headers,
            timeout=12
        )
        if response.status_code in [200, 201]:
            return response.json()
        else:
            logger.error(f"Erro MisticPay ({response.status_code}): {response.text}")
            return None
    except Exception as e:
        logger.error(f"Falha de conexão com MisticPay: {e}")
        return None

# ==================== HANDLERS DO TELEGRAM ====================
async def enviar_menu_principal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    primeiro_nome = user.first_name if user else "Cliente"

    # Usando HTML para evitar erros de renderização de caracteres especiais
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
        [
            InlineKeyboardButton("💳 Adicionar Saldo", callback_data="add_saldo")
        ],
        [InlineKeyboardButton("📢 Canal Oficial", url=LINK_CANAL)],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    chat_id = update.effective_chat.id

    # Envio seguro da Foto de Capa
    foto_enviada = False
    if os.path.exists(CAPA_PATH):
        try:
            with open(CAPA_PATH, "rb") as photo:
                await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=photo,
                    caption=texto,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
                foto_enviada = True
        except Exception as e:
            logger.error(f"Erro ao enviar imagem de capa: {e}")

    # Fallback: se a foto não existir ou falhar, envia apenas texto sem travar
    if not foto_enviada:
        if update.callback_query:
            await update.callback_query.message.reply_text(texto, reply_markup=reply_markup, parse_mode="HTML")
        else:
            await context.bot.send_message(chat_id=chat_id, text=texto, reply_markup=reply_markup, parse_mode="HTML")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await enviar_menu_principal(update, context)

async def pix_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Extrai o valor do comando /pix 10
    if context.args:
        try:
            valor = float(context.args[0].replace(",", "."))
            if valor <= 0:
                raise ValueError
        except ValueError:
            await update.message.reply_text("❌ Valor inválido. Exemplo correto: <code>/pix 10</code>", parse_mode="HTML")
            return
    else:
        valor = 10.0  # Valor padrão de teste

    msg_espera = await update.message.reply_text(f"⏳ Gerando PIX no valor de <b>R$ {valor:.2f}</b>...", parse_mode="HTML")
    
    # Executa a chamada em thread assíncrona para não bloquear o servidor
    loop = asyncio.get_running_loop()
    dados_pix = await loop.run_in_executor(None, gerar_pix_misticpay, valor, user_id)

    if dados_pix:
        qr_code = dados_pix.get("qrcode") or dados_pix.get("pix_code") or dados_pix.get("copy_paste")
        if qr_code:
            resposta = (
                f"✅ <b>PIX Gerado com Sucesso!</b>\n\n"
                f"💰 <b>Valor:</b> R$ {valor:.2f}\n\n"
                f"👇 Copie o código Pix Copia e Cola abaixo:\n"
                f"<code>{qr_code}</code>"
            )
            await update.message.reply_text(resposta, parse_mode="HTML")
            return

    await update.message.reply_text("❌ <b>Falha ao gerar o PIX.</b>\nVerifique se as credenciais MisticPay foram inseridas no painel do Render.", parse_mode="HTML")

# Registrar Handlers
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("pix", pix_command))

# ==================== LIFESPAN E FASTAPI ====================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicializa o bot do Telegram no carregamento do Web Service
    await telegram_app.initialize()
    await telegram_app.start()
    
    webhook_url = f"{WEBHOOK_BASE_URL.rstrip('/')}/telegram-webhook"
    await telegram_app.bot.set_webhook(url=webhook_url)
    logger.info(f"Webhook registrado com sucesso em: {webhook_url}")
    
    yield
    
    # Finalização limpa
    await telegram_app.stop()
    await telegram_app.shutdown()

app = FastAPI(lifespan=lifespan)

@app.post("/telegram-webhook")
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
        update = Update.de_json(data, telegram_app.bot)
        await telegram_app.process_update(update)
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Erro ao processar atualização do Telegram: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/misticpay-webhook")
async def misticpay_webhook(request: Request):
    try:
        dados = await request.json()
        logger.info(f"Retorno do Webhook MisticPay: {dados}")
        
        status = dados.get("status")
        external_id = str(dados.get("external_id", ""))
        
        if status in ["paid", "approved", "COMPLETED"] and external_id.startswith("user_"):
            user_id = int(external_id.replace("user_", ""))
            await telegram_app.bot.send_message(
                chat_id=user_id,
                text="🎉 <b>Pagamento PIX confirmado com sucesso!</b>",
                parse_mode="HTML"
            )
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Erro ao processar webhook MisticPay: {e}")
        return {"status": "error"}

@app.get("/")
async def root():
    return {"status": "online", "bot": "CasaBlanca Store"}
