import asyncio
import logging
import os
import requests
from fastapi import FastAPI, Request, HTTPException
from contextlib import asynccontextmanager
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

# Configuração de Logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== CONFIGURAÇÕES GERAIS ====================
TOKEN = os.getenv("TELEGRAM_TOKEN", "8956870259:AAGR_gmp5h2pzwdYnqC_QScrigH8imPVoho")
LINK_CANAL = "https://t.me/+qrh5SObhV3xmODhh"

# CONFIGURAÇÕES MISTICPAY
MISTICPAY_API_URL = "https://api.misticpay.com/v1"
MISTICPAY_CLIENT_SECRET = os.getenv("MISTICPAY_CLIENT_SECRET", "cs_xmi6kbhukucgc1syoymxugk3h")
WEBHOOK_BASE_URL = "https://botcasablanca.onrender.com"

POLITICA_REEMBOLSO = (
    "📜 *Política de Reembolso*\n\n"
    "⚠️ Caso o saldo esteja abaixo do mínimo garantido na pré-compra, "
    "solicite reembolso em até 20 minutos via @SOSAtendimento, com vídeo mostrando cartão, valor e erro."
)

# ==================== ESTOQUES DE UNITÁRIAS (CATÁLOGO) ====================
CATALOGO_UNITARIAS = {
    "platinum": {"nome": "PLATINUM", "preco": "R$ 80", "estoque": 526},
    "personal": {"nome": "PERSONAL", "preco": "R$ 50", "estoque": 55},
    "gold": {"nome": "GOLD", "preco": "R$ 50", "estoque": 175},
    "elo": {"nome": "ELO", "preco": "R$ 50", "estoque": 1},
    "business": {"nome": "BUSINESS", "preco": "R$ 80", "estoque": 16},
    "infinite": {"nome": "INFINITE", "preco": "R$ 120", "estoque": 418},
    "black": {"nome": "BLACK", "preco": "R$ 120", "estoque": 114},
    "personal_plat_charge": {"nome": "PERSONAL PLATINUM C...", "preco": "R$ 120", "estoque": 34},
    "personal_gold_charge": {"nome": "PERSONAL GOLD CHARG...", "preco": "R$ 120", "estoque": 14},
    "corporate_te": {"nome": "CORPORATE T&E", "preco": "R$ 80", "estoque": 172},
    "signature": {"nome": "SIGNATURE", "preco": "R$ 80", "estoque": 3},
    "purchasing": {"nome": "PURCHASING", "preco": "R$ 80", "estoque": 7},
    "nubank_gold": {"nome": "NUBANK GOLD", "preco": "R$ 35", "estoque": 610},
    "nubank_plat": {"nome": "NUBANK PLATINUM", "preco": "R$ 40", "estoque": 410},
}

# Inicialização do Bot
telegram_app = Application.builder().token(TOKEN).build()

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
        [InlineKeyboardButton("💳 Adicionar Saldo", callback_data="add_saldo")],
        [InlineKeyboardButton("📢 Canal Oficial", url=LINK_CANAL)],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.message.reply_text(texto, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(texto, reply_markup=reply_markup, parse_mode="Markdown")

# ==================== CATÁLOGO EM 2 COLUNAS ====================
async def exibir_catalogo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()

    keyboard = []
    linha_atual = []

    for key, item in CATALOGO_UNITARIAS.items():
        texto_botao = f"{item['preco']} {item['nome']} ({item['estoque']})"
        callback_data = f"comprar_{key}"
        
        linha_atual.append(InlineKeyboardButton(texto_botao, callback_data=callback_data))

        if len(linha_atual) == 2:
            keyboard.append(linha_atual)
            linha_atual = []

    if linha_atual:
        keyboard.append(linha_atual)

    keyboard.append([InlineKeyboardButton("🔙 Voltar", callback_data="menu_principal")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    texto = f"{POLITICA_REEMBOLSO}"

    if query:
        await query.message.reply_text(texto, reply_markup=reply_markup, parse_mode="Markdown")

# ==================== PROCESSAR COMPRA ====================
async def processar_clique_compra(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    produto_key = query.data.replace("comprar_", "")
    produto = CATALOGO_UNITARIAS.get(produto_key)

    if not produto:
        await query.message.reply_text("Produto não disponível no momento.")
        return

    texto_confirmacao = (
        f"🛒 *Detalhes do Item*\n\n"
        f"📌 *Produto:* {produto['nome']}\n"
        f"💰 *Preço:* {produto['preco']}\n"
        f"📦 *Estoque:* {produto['estoque']} disponíveis\n\n"
        "Clique no botão abaixo para gerar a cobrança PIX:"
    )

    botoes = [
        [InlineKeyboardButton("⚡ Pagar via PIX (MisticPay)", callback_data=f"gerar_pix_{produto_key}")],
        [InlineKeyboardButton("🔙 Voltar ao Catálogo", callback_data="menu_comprar")]
    ]

    await query.message.reply_text(texto_confirmacao, reply_markup=InlineKeyboardMarkup(botoes), parse_mode="Markdown")

# REGISTRO DE HANDLERS
telegram_app.add_handler(CommandHandler("start", enviar_menu_principal))
telegram_app.add_handler(CommandHandler("menu", enviar_menu_principal))
telegram_app.add_handler(CallbackQueryHandler(enviar_menu_principal, pattern="^menu_principal$"))
telegram_app.add_handler(CallbackQueryHandler(exibir_catalogo, pattern="^menu_comprar$"))
telegram_app.add_handler(CallbackQueryHandler(processar_clique_compra, pattern="^comprar_"))

# ==================== INTEGRAÇÃO FASTAPI / RENDER ====================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicia o bot do Telegram junto com o servidor FastAPI
    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.updater.start_polling()
    logger.info("Bot do Telegram iniciado no Render com sucesso!")
    yield
    # Parada graciosa ao desligar o servidor
    await telegram_app.updater.stop()
    await telegram_app.stop()
    await telegram_app.shutdown()

# Variável 'app' exigida pelo comando 'uvicorn main:app'
app = FastAPI(lifespan=lifespan)

@app.get("/")
async def health_check():
    return {"status": "ok", "bot": "online"}

@app.post("/misticpay-webhook")
async def misticpay_webhook(request: Request):
    data = await request.json()
    logger.info(f"Webhook recebido: {data}")
    return {"status": "success"}
