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
NOME_FOTO = "capa.jpg"

# CONFIGURAÇÕES MISTICPAY
MISTICPAY_API_URL = "https://api.misticpay.com/v1"
MISTICPAY_CLIENT_SECRET = os.getenv("MISTICPAY_CLIENT_SECRET", "cs_xmi6kbhukucgc1syoymxugk3h")
WEBHOOK_BASE_URL = "https://botcasablanca.onrender.com"

POLITICA_REEMBOLSO = (
    "📜 *Política de Reembolso*\n\n"
    "⚠️ Caso o saldo esteja abaixo do mínimo garantido na pré-compra, "
    "solicite reembolso em até 20 minutos via @SOSAtendimento, com vídeo mostrando cartão, valor e erro."
)

# Banco de dados temporário de saldo em memória (telegram_id: valor)
SALDOS_USUARIOS = {}

# ==================== DADOS DOS CATÁLOGOS ====================
CATALOGO_UNITARIAS = {
    "platinum": {"nome": "PLATINUM", "preco_num": 80.0, "preco": "R$ 80", "estoque": 526},
    "personal": {"nome": "PERSONAL", "preco_num": 50.0, "preco": "R$ 50", "estoque": 55},
    "gold": {"nome": "GOLD", "preco_num": 50.0, "preco": "R$ 50", "estoque": 175},
    "elo": {"nome": "ELO", "preco_num": 50.0, "preco": "R$ 50", "estoque": 1},
    "business": {"nome": "BUSINESS", "preco_num": 80.0, "preco": "R$ 80", "estoque": 16},
    "infinite": {"nome": "INFINITE", "preco_num": 120.0, "preco": "R$ 120", "estoque": 418},
    "black": {"nome": "BLACK", "preco_num": 120.0, "preco": "R$ 120", "estoque": 114},
    "personal_plat_charge": {"nome": "PERSONAL PLATINUM C...", "preco_num": 120.0, "preco": "R$ 120", "estoque": 34},
    "personal_gold_charge": {"nome": "PERSONAL GOLD CHARG...", "preco_num": 120.0, "preco": "R$ 120", "estoque": 14},
    "corporate_te": {"nome": "CORPORATE T&E", "preco_num": 80.0, "preco": "R$ 80", "estoque": 172},
    "signature": {"nome": "SIGNATURE", "preco_num": 80.0, "preco": "R$ 80", "estoque": 3},
    "purchasing": {"nome": "PURCHASING", "preco_num": 80.0, "preco": "R$ 80", "estoque": 7},
    "nubank_gold": {"nome": "NUBANK GOLD", "preco_num": 35.0, "preco": "R$ 35", "estoque": 610},
    "nubank_plat": {"nome": "NUBANK PLATINUM", "preco_num": 40.0, "preco": "R$ 40", "estoque": 410},
}

CATALOGO_ESIM = {
    "esim_vivo": {"nome": "eSIM VIVO", "preco_num": 45.0, "preco": "R$ 45", "estoque": 12},
    "esim_claro": {"nome": "eSIM CLARO", "preco_num": 45.0, "preco": "R$ 45", "estoque": 8},
    "esim_tim": {"nome": "eSIM TIM", "preco_num": 45.0, "preco": "R$ 45", "estoque": 15},
}

CATALOGO_AUXILIAR = {
    "consultas": {"nome": "CONSULTA COMPLETA", "preco_num": 15.0, "preco": "R$ 15", "estoque": 99},
    "score": {"nome": "AUMENTO DE SCORE", "preco_num": 100.0, "preco": "R$ 100", "estoque": 5},
}

# Inicialização do Bot
telegram_app = Application.builder().token(TOKEN).build()

async def enviar_com_foto_se_existir(chat_id, context, texto, reply_markup):
    if os.path.exists(NOME_FOTO):
        with open(NOME_FOTO, "rb") as foto:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=foto,
                caption=texto,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
    else:
        await context.bot.send_message(
            chat_id=chat_id,
            text=texto,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

# ==================== MENU PRINCIPAL ====================
async def enviar_menu_principal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    primeiro_nome = user.first_name if user else "Cliente"
    chat_id = update.effective_chat.id
    user_id = user.id if user else 0

    saldo_atual = SALDOS_USUARIOS.get(user_id, 0.0)

    if update.callback_query:
        await update.callback_query.answer()

    texto = (
        f"Olá *{primeiro_nome}*, seja bem-vindo ao *CasaBlanca Bot*! 🏛️✨\n\n"
        f"💰 *Seu Saldo:* R$ {saldo_atual:.2f}\n\n"
        "Selecione uma opção abaixo para navegar:"
    )

    keyboard = [
        [
            InlineKeyboardButton("🛒 Comprar", callback_data="menu_categorias"),
            InlineKeyboardButton("💳 Adicionar Saldo", callback_data="add_saldo"),
        ],
        [
            InlineKeyboardButton("🛠️ Ferramentas", callback_data="ferramentas"),
            InlineKeyboardButton("🎁 Indicações", callback_data="indicacoes"),
        ],
        [InlineKeyboardButton("ℹ️ Informações", callback_data="info")],
        [InlineKeyboardButton("📢 Canal Oficial", url=LINK_CANAL)],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        try:
            await update.callback_query.message.edit_text(texto, reply_markup=reply_markup, parse_mode="Markdown")
        except Exception:
            await enviar_com_foto_se_existir(chat_id, context, texto, reply_markup)
    else:
        await enviar_com_foto_se_existir(chat_id, context, texto, reply_markup)

# ==================== ADICIONAR SALDO (PIX) ====================
async def exibir_opcao_add_saldo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()

    user_id = update.effective_user.id
    saldo_atual = SALDOS_USUARIOS.get(user_id, 0.0)

    texto = (
        f"💳 *Adicionar Saldo via PIX*\n\n"
        f"💰 *Saldo Atual:* R$ {saldo_atual:.2f}\n\n"
        "Escolha um valor para recarregar sua carteira:"
    )

    keyboard = [
        [
            InlineKeyboardButton("R$ 15", callback_data="pix_15"),
            InlineKeyboardButton("R$ 35", callback_data="pix_35"),
            InlineKeyboardButton("R$ 50", callback_data="pix_50"),
        ],
        [
            InlineKeyboardButton("R$ 80", callback_data="pix_80"),
            InlineKeyboardButton("R$ 100", callback_data="pix_100"),
            InlineKeyboardButton("R$ 120", callback_data="pix_120"),
        ],
        [InlineKeyboardButton("🔙 Voltar ao Menu Principal", callback_data="menu_principal")]
    ]

    await query.message.edit_text(texto, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# ==================== CATEGORIAS & CATÁLOGO (2 COLUNAS) ====================
async def exibir_menu_categorias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()

    texto = "📂 *Selecione uma Categoria de Produtos:*"

    keyboard = [
        [InlineKeyboardButton("💳 CC Full Dados", callback_data="cat_ccfulldados")],
        [InlineKeyboardButton("📱 eSIM", callback_data="cat_esim")],
        [InlineKeyboardButton("🛠️ Auxiliar / Outros", callback_data="cat_auxiliar")],
        [InlineKeyboardButton("🔙 Voltar ao Menu Principal", callback_data="menu_principal")]
    ]

    await query.message.edit_text(texto, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def exibir_catalogo_especifico(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()

    categoria = query.data.replace("cat_", "")
    
    if categoria == "ccfulldados":
        dados_catalogo = CATALOGO_UNITARIAS
        titulo = "💳 *Catálogo CC Full Dados*"
    elif categoria == "esim":
        dados_catalogo = CATALOGO_ESIM
        titulo = "📱 *Catálogo eSIM*"
    elif categoria == "auxiliar":
        dados_catalogo = CATALOGO_AUXILIAR
        titulo = "🛠️ *Serviços Auxiliares*"
    else:
        dados_catalogo = {}
        titulo = "Catálogo"

    keyboard = []
    linha_atual = []

    for key, item in dados_catalogo.items():
        texto_botao = f"{item['preco']} {item['nome']} ({item['estoque']})"
        callback_data = f"comprar_{key}"
        
        linha_atual.append(InlineKeyboardButton(texto_botao, callback_data=callback_data))

        if len(linha_atual) == 2:
            keyboard.append(linha_atual)
            linha_atual = []

    if linha_atual:
        keyboard.append(linha_atual)

    keyboard.append([InlineKeyboardButton("🔙 Voltar às Categorias", callback_data="menu_categorias")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    texto = f"{titulo}\n\n{POLITICA_REEMBOLSO}"

    await query.message.edit_text(texto, reply_markup=reply_markup, parse_mode="Markdown")

# ==================== PROCESSAMENTO DE COMPRA COM VALIDAÇÃO DE SALDO ====================
async def processar_clique_compra(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    produto_key = query.data.replace("comprar_", "")
    
    todos_produtos = {**CATALOGO_UNITARIAS, **CATALOGO_ESIM, **CATALOGO_AUXILIAR}
    produto = todos_produtos.get(produto_key)

    if not produto:
        await query.message.reply_text("Produto não disponível no momento.")
        return

    saldo_usuario = SALDOS_USUARIOS.get(user_id, 0.0)
    preco_item = produto["preco_num"]

    # SE TIVER SALDO SUFICIENTE
    if saldo_usuario >= preco_item:
        # Debita o valor do saldo do cliente
        SALDOS_USUARIOS[user_id] -= preco_item
        produto["estoque"] -= 1

        texto_sucesso = (
            f"✅ *Compra realizada com sucesso!*\n\n"
            f"📦 *Produto:* {produto['nome']}\n"
            f"💰 *Valor pago:* {produto['preco']}\n"
            f"💵 *Seu Novo Saldo:* R$ {SALDOS_USUARIOS[user_id]:.2f}\n\n"
            "📩 O material foi resgatado e processado!"
        )
        botoes = [[InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="menu_principal")]]
        await query.message.edit_text(texto_sucesso, reply_markup=InlineKeyboardMarkup(botoes), parse_mode="Markdown")

    # SE NÃO TIVER SALDO SUFICIENTE
    else:
        texto_erro = (
            f"❌ *Saldo Insuficiente!*\n\n"
            f"📌 *Produto:* {produto['nome']}\n"
            f"💰 *Preço do Produto:* {produto['preco']}\n"
            f"💳 *Seu Saldo Atual:* R$ {saldo_usuario:.2f}\n\n"
            "Adicione saldo à sua conta via PIX para realizar esta compra."
        )

        botoes = [
            [InlineKeyboardButton("💳 Adicionar Saldo", callback_data="add_saldo")],
            [InlineKeyboardButton("🔙 Voltar às Categorias", callback_data="menu_categorias")]
        ]
        await query.message.edit_text(texto_erro, reply_markup=InlineKeyboardMarkup(botoes), parse_mode="Markdown")

# REGISTRO DE HANDLERS
telegram_app.add_handler(CommandHandler("start", enviar_menu_principal))
telegram_app.add_handler(CommandHandler("menu", enviar_menu_principal))

telegram_app.add_handler(CallbackQueryHandler(enviar_menu_principal, pattern="^menu_principal$"))
telegram_app.add_handler(CallbackQueryHandler(exibir_opcao_add_saldo, pattern="^add_saldo$"))
telegram_app.add_handler(CallbackQueryHandler(exibir_menu_categorias, pattern="^menu_categorias$"))
telegram_app.add_handler(CallbackQueryHandler(exibir_catalogo_especifico, pattern="^cat_"))
telegram_app.add_handler(CallbackQueryHandler(processar_clique_compra, pattern="^comprar_"))

# ==================== FASTAPI / RENDER ====================
@asynccontextmanager
async def lifespan(app: FastAPI):
    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.updater.start_polling()
    logger.info("Bot rodando com sucesso no Render!")
    yield
    await telegram_app.updater.stop()
    await telegram_app.stop()
    await telegram_app.shutdown()

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def health_check():
    return {"status": "ok", "bot": "online"}

@app.post("/misticpay-webhook")
async def misticpay_webhook(request: Request):
    data = await request.json()
    logger.info(f"Webhook MisticPay recebido: {data}")
    # Quando a MisticPay confirma o pagamento, o valor é somado na conta do usuário
    return {"status": "success"}
