import asyncio
import logging
import os
from contextlib import asynccontextmanager

import requests
from fastapi import FastAPI, HTTPException, Request
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultArticle,
    InputTextMessageContent,
    Update,
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    InlineQueryHandler,
    MessageHandler,
    filters,
)

# Configuração de Logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== CONFIGURAÇÕES GERAIS ====================
# As variáveis buscam do ambiente; os valores padrão servem apenas para testes locais
TOKEN = os.getenv("TELEGRAM_TOKEN", "SEU_TELEGRAM_TOKEN_AQUI")
ID_CANAL = int(os.getenv("ID_CANAL", "-1004302224747"))
LINK_CANAL = os.getenv("LINK_CANAL", "https://t.me/+qrh5SObhV3xmODhh")
NOME_FOTO = "capa.jpg"
FOTO_CATEGORIAS = "categorias.jpg"

# CONFIGURAÇÕES MISTICPAY
MISTICPAY_API_URL = "https://api.misticpay.com/v1"
MISTICPAY_CLIENT_ID = os.getenv("MISTICPAY_CLIENT_ID", "")
MISTICPAY_CLIENT_SECRET = os.getenv("MISTICPAY_CLIENT_SECRET", "")
WEBHOOK_BASE_URL = os.getenv("WEBHOOK_BASE_URL", "https://botcasablanca.onrender.com")

POLITICA_REEMBOLSO = (
    "📜 *Política de Reembolso*\n\n"
    "⚠️ Caso o saldo esteja abaixo do mínimo garantido na pré-compra, "
    "solicite reembolso em até 20 minutos via @haridadenetwork, com vídeo mostrando cartão, valor e erro."
)

# ==================== ESTOQUES DE UNITÁRIAS (CATÁLOGO) ====================
CATALOGO_UNITARIAS = {
    "platinum": {"nome": "PLATINUM", "preco": "R$ 80", "estoque": 565},
    "gold": {"nome": "GOLD", "preco": "R$ 50", "estoque": 176},
    "personal": {"nome": "PERSONAL", "preco": "R$ 50", "estoque": 55},
    "business": {"nome": "BUSINESS", "preco": "R$ 80", "estoque": 162},
    "elo": {"nome": "ELO", "preco": "R$ 50", "estoque": 24},
    "black": {"nome": "BLACK", "preco": "R$ 120", "estoque": 118},
    "personal_plat_charge": {
        "nome": "PERSONAL PLATINUM CHARGE",
        "preco": "R$ 120",
        "estoque": 34,
    },
    "personal_gold_charge": {
        "nome": "PERSONAL GOLD CHARGE",
        "preco": "R$ 120",
        "estoque": 14,
    },
    "signature": {"nome": "SIGNATURE", "preco": "R$ 80", "estoque": 6},
    "nubank_gold": {"nome": "NUBANK GOLD", "preco": "R$ 35", "estoque": 526},
    "nubank_plat": {"nome": "NUBANK PLATINUM", "preco": "R$ 40", "estoque": 441},
    "classic": {"nome": "CLASSIC", "preco": "R$ 30", "estoque": 201},
    "standard": {"nome": "STANDARD", "preco": "R$ 20", "estoque": 104},
    "infinite": {"nome": "INFINITE", "preco": "R$ 90", "estoque": 88},
}

# Inicialização Global da Aplicação Telegram
telegram_app = Application.builder().token(TOKEN).build()

# ==================== UTILITÁRIOS DA MISTICPAY ====================
def gerar_pix_misticpay(valor: float, telegram_id: int):
    """
    Função para fazer a requisição de pagamento via MisticPay.
    """
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

# Checagem de canal protegida contra travamentos
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

# ==================== PAINEL PRINCIPAL & MENUS ====================
async def enviar_menu_principal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    primeiro_nome = user.first_name if user else "Cliente"

    texto = (
        f"Olá *{primeiro_nome}*, seja bem-vindo ao *CasaBlanca Bot*! 🏛️✨\n\n"
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

    try:
        if os.path.exists(NOME_FOTO):
            with open(NOME_FOTO, "rb") as foto:
                if update.callback_query:
                    await update.callback_query.message.reply_photo(
                        photo=foto,
                        caption=texto,
                        reply_markup=reply_markup,
                        parse_mode="Markdown",
                    )
                else:
                    await update.message.reply_photo(
                        photo=foto,
                        caption=texto,
                        reply_markup=reply_markup,
                        parse_mode="Markdown",
                    )
        else:
            if update.callback_query:
                await update.callback_query.message.reply_text(
                    texto, reply_markup=reply_markup, parse_mode="Markdown"
                )
            else:
                await update.message.reply_text(
                    texto, reply_markup=reply_markup, parse_mode="Markdown"
                )
    except Exception as e:
        logger.error(f"Erro ao enviar menu: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await enviar_menu_principal(update, context)

# ==================== FASTAPI & INTEGRACAO ====================
@asynccontextmanager
async def lifespan(app: FastAPI):
    await telegram_app.initialize()
    await telegram_app.start()
    yield
    await telegram_app.stop()

app = FastAPI(lifespan=lifespan)

@app.post("/telegram-webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return {"status": "ok"}

# Adicionar o handler do comando /start
telegram_app.add_handler(CommandHandler("start", start))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
