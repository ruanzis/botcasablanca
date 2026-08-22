import asyncio
import logging
import os
import requests
from fastapi import FastAPI, Request, HTTPException
from contextlib import asynccontextmanager
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
TOKEN = os.getenv("TELEGRAM_TOKEN", "8956870259:AAGR_gmp5h2pzwdYnqC_QScrigH8imPVoho")
ID_CANAL = -1004302224747
LINK_CANAL = "https://t.me/+qrh5SObhV3xmODhh"
NOME_FOTO = "capa.jpg"
FOTO_CATEGORIAS = "categorias.jpg"

# CONFIGURAÇÕES MISTICPAY
MISTICPAY_API_URL = "https://api.misticpay.com/v1"
MISTICPAY_CLIENT_ID = os.getenv("MISTICPAY_CLIENT_ID", "ci_g35d35pglvgsj39")
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

# Inicialização Global do Telegram Bot
telegram_app = Application.builder().token(TOKEN).build()

# ==================== UTILITÁRIOS DA MISTICPAY ====================
def gerar_pix_misticpay(valor: float, telegram_id: int):
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
        logger.error(f"Erro MisticPay: {response.status_code} - {response.text}")
        return None
    except Exception as e:
        logger.error(f"Falha ao conectar com MisticPay: {e}")
        return None

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

# ==================== CATÁLOGO EM 2 COLUNAS (NOVO) ====================
async def exibir_catalogo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()

    keyboard = []
    linha_atual = []

    # Monta os botões do catálogo dinamicamente em 2 colunas
    for key, item in CATALOGO_UNITARIAS.items():
        texto_botao = f"{item['preco']} {item['nome']} ({item['estoque']})"
        callback_data = f"comprar_{key}"
        
        linha_atual.append(InlineKeyboardButton(texto_botao, callback_data=callback_data))

        if len(linha_atual) == 2:
            keyboard.append(linha_atual)
            linha_atual = []

    if linha_atual:
        keyboard.append(linha_atual)

    # Botão de voltar
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

# ==================== GERENCIADOR DE COMANDOS E CALLBACKS ====================
def setup_handlers(app: Application):
    app.add_handler(CommandHandler("start", enviar_menu_principal))
    app.add_handler(CommandHandler("menu", enviar_menu_principal))
    
    # Callbacks dos menus
    app.add_handler(CallbackQueryHandler(enviar_menu_principal, pattern="^menu_principal$"))
    app.add_handler(CallbackQueryHandler(exibir_catalogo, pattern="^menu_comprar$"))
    app.add_handler(CallbackQueryHandler(processar_clique_compra, pattern="^comprar_"))

if __name__ == "__main__":
    setup_handlers(telegram_app)
    logger.info("Bot rodando com sucesso...")
    telegram_app.run_polling()
