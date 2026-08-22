import asyncio
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
import requests
import uvicorn
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# ==================== CONFIGURAÇÃO DE LOGS ====================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== VARIÁVEIS DE AMBIENTE ====================
TOKEN = os.getenv("TELEGRAM_TOKEN", "8956870259:AAGR_gmp5h2pzwdYnqC_QScrigH8imPVoho")
ID_CANAL = os.getenv("ID_CANAL", "-1004302224747")  # IDs de canais começam com -100
LINK_CANAL = os.getenv("LINK_CANAL", "https://t.me/+qrh5SObhV3xmODhh")
CAPA_PATH = "capa.jpg"

MISTICPAY_API_URL = os.getenv("MISTICPAY_API_URL", "https://api.misticpay.com/v1")
MISTICPAY_CLIENT_SECRET = os.getenv("MISTICPAY_CLIENT_SECRET", "")
WEBHOOK_BASE_URL = os.getenv("WEBHOOK_BASE_URL", "")

POLITICA_REEMBOLSO = (
    "Política de Reembolso\n\n"
    "⚠️ Caso o saldo esteja abaixo do mínimo garantido na pré-compra, "
    "solicite reembolso em até 20 minutos via @haridadenetwork, com vídeo mostrando cartão, valor e erro."
)

CATALOGO_UNITARIAS = {
    "platinum": {"nome": "PLATINUM", "preco": 80, "estoque": 521},
    "gold": {"nome": "GOLD", "preco": 50, "estoque": 176},
    "personal": {"nome": "PERSONAL", "preco": 50, "estoque": 55},
    "business": {"nome": "BUSINESS", "preco": 80, "estoque": 162},
    "elo": {"nome": "ELO", "preco": 50, "estoque": 24},
    "black": {"nome": "BLACK", "preco": 120, "estoque": 118},
    "personal_plat_charge": {"nome": "PERSONAL PLATINUM CHARGE", "preco": 120, "estoque": 34},
    "personal_gold_charge": {"nome": "PERSONAL GOLD CHARGE", "preco": 120, "estoque": 14},
    "signature": {"nome": "SIGNATURE", "preco": 80, "estoque": 6},
    "nubank_gold": {"nome": "NUBANK GOLD", "preco": 35, "estoque": 501},
    "nubank_plat": {"nome": "NUBANK PLATINUM", "preco": 40, "estoque": 430},
    "classic": {"nome": "CLASSIC", "preco": 30, "estoque": 201},
    "standard": {"nome": "STANDARD", "preco": 20, "estoque": 104},
    "infinite": {"nome": "INFINITE", "preco": 90, "estoque": 88},
}

DADOS_PLATINUM = [
    {
        "cc": "435086******3663",
        "banco": "ITAU UNIBANCO HOLDING, S.A.",
        "nome": "CELSO MARCELO RAMOS MARTINS",
        "cpf": "01490398759",
        "serasa": "461",
        "bc": "647",
        "bin": "435086",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": 80,
    },
    {
        "cc": "542819******0150",
        "banco": "BANCO GENIAL SA",
        "nome": "CRISTIANO CACHEIRO MAHIA",
        "cpf": "03250698679",
        "serasa": "306",
        "bc": "93",
        "bin": "542819",
        "nivel": "FULL PLATINUM",
        "fornecedor": "Anon",
        "preco": 80,
    },
]

telegram_app = Application.builder().token(TOKEN).build()

# ==================== FUNÇÕES AUXILIARES ====================
def gerar_pix_misticpay(valor: float, telegram_id: int):
    if not MISTICPAY_CLIENT_SECRET:
        return None

    payload = {
        "amount": valor,
        "external_id": f"user_{telegram_id}",
        "postback_url": f"{WEBHOOK_BASE_URL}/misticpay-webhook",
    }
    headers = {
        "Authorization": f"Bearer {MISTICPAY_CLIENT_SECRET}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(f"{MISTICPAY_API_URL}/pix/charge", json=payload, headers=headers, timeout=12)
        if response.status_code in [200, 201]:
            return response.json()
        return None
    except Exception as e:
        logger.error(f"Erro PIX: {e}")
        return None

async def esta_no_canal(context: ContextTypes.DEFAULT_TYPE, user_id: int):
    try:
        membro = await context.bot.get_chat_member(chat_id=ID_CANAL, user_id=user_id)
        return membro.status in ["member", "administrator", "creator"]
    except Exception as e:
        logger.warning(f"Aviso ao checar canal: {e}")
        return True  # Retorna True em caso de erro para não bloquear o usuário totalmente

# ==================== INTERFACES ====================
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
            logger.error(f"Erro ao carregar capa: {e}")

    await context.bot.send_message(chat_id=chat_id, text=texto, reply_markup=reply_markup, parse_mode="HTML")

# ==================== HANDLERS TELEGRAM ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if await esta_no_canal(context, user_id):
        await enviar_menu_principal(update, context)
    else:
        keyboard = [
            [InlineKeyboardButton("📢 Entrar no Canal", url=LINK_CANAL)],
            [InlineKeyboardButton("🔄 Já entrei / Liberar Acesso", callback_data="verificar")],
        ]
        await update.message.reply_text(
            "⚠️ <b>ACESSO BLOQUEADO!</b>\n\nPara acessar nosso bot, entre no canal oficial.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )

async def botao_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # <--- Essencial para soltar a animação do botão no Telegram
    user_id = query.from_user.id
    data = query.data

    if data == "verificar":
        if await esta_no_canal(context, user_id):
            await query.message.delete()
            await enviar_menu_principal(update, context)
        else:
            await query.message.reply_text("❌ Você ainda não entrou no canal!")

    elif data == "menu_comprar":
        keyboard = [
            [InlineKeyboardButton("📱 CC Unitárias", callback_data="sub_categoria_unitarias")],
            [InlineKeyboardButton("📁 ESTOQUE CC FULL DADOS", callback_data="categoria_full_dados")],
            [InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_inicio")],
        ]
        await query.message.edit_text("🛒 <b>SELEÇÃO DE CATEGORIAS DE COMPRA</b>", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

    elif data == "sub_categoria_unitarias":
        texto = "🛒 <b>ESTOQUE DE CCs UNITÁRIAS:</b>\n\n"
        keyboard = []
        for chave, item in CATALOGO_UNITARIAS.items():
            texto += f"• {item['nome']} - R$ {item['preco']} (Estoque: {item['estoque']})\n"
            keyboard.append([InlineKeyboardButton(f"{item['nome']} - R$ {item['preco']}", callback_data=f"nav_{chave}_0")])

        keyboard.append([InlineKeyboardButton("🔙 Voltar", callback_data="menu_comprar")])
        await query.message.edit_text(texto, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

    elif data == "info":
        await query.message.reply_text(POLITICA_REEMBOLSO)

    elif data == "add_saldo":
        await query.message.reply_text("💳 Use o comando <code>/pix 50</code> para gerar um PIX no valor desejado.", parse_mode="HTML")

    elif data == "voltar_inicio":
        try:
            await query.message.delete()
        except Exception:
            pass
        await enviar_menu_principal(update, context)

# Registra os Handlers
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CallbackQueryHandler(botao_callback))

# ==================== SERVIDOR FASTAPI ====================
@asynccontextmanager
async def lifespan(app: FastAPI):
    await telegram_app.initialize()
    await telegram_app.start()
    if WEBHOOK_BASE_URL:
        webhook_url = f"{WEBHOOK_BASE_URL.rstrip('/')}/telegram-webhook"
        await telegram_app.bot.set_webhook(url=webhook_url)
        logger.info(f"Webhook configurado: {webhook_url}")
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

if __name__ == "__main__":
    # Se rodar localmente pelo terminal (python main.py)
    if not WEBHOOK_BASE_URL:
        print("🤖 Rodando Bot localmente via POLLING...")
        telegram_app.run_polling()
    else:
        # Se estiver no servidor Render
        uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
