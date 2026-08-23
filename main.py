import asyncio
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
import requests
import uvicorn
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
)

# Configuração de Logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurações de Ambiente
TOKEN = os.getenv("TELEGRAM_TOKEN", "8956870259:AAGR_gmp5h2pzwdYnqC_QScrigH8imPVoho")
ID_CANAL = os.getenv("ID_CANAL", "-1004302224747")
LINK_CANAL = os.getenv("LINK_CANAL", "https://t.me/+qrh5SObhV3xmODhh")
LINK_SUPORTE = "https://t.me/haridadenetwork"
CAPA_PATH = "capa.jpg"

MISTICPAY_API_URL = os.getenv("MISTICPAY_API_URL", "https://api.misticpay.com")
MISTICPAY_CLIENT_ID = os.getenv("MISTICPAY_CLIENT_ID", "")
MISTICPAY_CLIENT_SECRET = os.getenv("MISTICPAY_CLIENT_SECRET", "")
WEBHOOK_BASE_URL = os.getenv("WEBHOOK_BASE_URL", "https://botcasablanca.onrender.com")

POLITICA_REEMBOLSO = (
    "Política de Reembolso\n\n"
    "⚠️ Caso o saldo esteja abaixo do mínimo garantido na pré-compra, "
    "solicite reembolso em até 20 minutos via @haridadenetwork, "
    "com vídeo mostrando cartão, valor e erro."
)

CATALOGO_UNITARIAS = [
    {"nome": "PLATINUM", "preco": 80, "qtd": 525},
    {"nome": "PERSONAL", "preco": 50, "qtd": 55},
    {"nome": "GOLD", "preco": 50, "qtd": 174},
    {"nome": "ELO", "preco": 50, "qtd": 1},
    {"nome": "BUSINESS", "preco": 80, "qtd": 16},
    {"nome": "INFINITE", "preco": 120, "qtd": 413},
    {"nome": "BLACK", "preco": 120, "qtd": 114},
    {"nome": "SIGNATURE", "preco": 80, "qtd": 3},
    {"nome": "NUBANK GOLD", "preco": 35, "qtd": 501},
    {"nome": "NUBANK PLATINUM", "preco": 40, "qtd": 430},
]

DADOS_CARTOES = [
    {
        "id": "1",
        "cc": "542819******0150",
        "banco": "BANCO GENIAL SA",
        "categoria": "FULL PLATINUM",
        "tipo": "CREDIT",
        "nome": "CRISTIANO CACHEIRO MAHIA",
        "cpf": "03250698679",
        "bin": "542819",
        "fornecedor": "Anon",
        "preco": 80.00,
        "saldo_minimo": 1200.00,
    },
    {
        "id": "2",
        "cc": "544169******0487",
        "banco": "ITAU UNIBANCO, S.A.",
        "categoria": "PLATINUM",
        "tipo": "CREDIT",
        "nome": "ALEXANDRE CARVALHO CHANAN",
        "cpf": "18319050006",
        "bin": "544169",
        "fornecedor": "Anon",
        "preco": 80.00,
        "saldo_minimo": 1200.00,
    },
    {
        "id": "3",
        "cc": "543960******8821",
        "banco": "ITAU UNIBANCO, S.A.",
        "categoria": "FULL PLATINUM",
        "tipo": "CREDIT",
        "nome": "MARCOS SILVA OLIVEIRA",
        "cpf": "04421098712",
        "bin": "543960",
        "fornecedor": "Anon",
        "preco": 80.00,
        "saldo_minimo": 1200.00,
    },
]

telegram_app = Application.builder().token(TOKEN).build()

# ==================== UTILITÁRIOS & CANAL ====================
async def esta_no_canal(context: ContextTypes.DEFAULT_TYPE, user_id: int):
    try:
        membro = await context.bot.get_chat_member(chat_id=ID_CANAL, user_id=user_id)
        return membro.status in ["member", "administrator", "creator"]
    except Exception as e:
        logger.warning(f"Erro ao validar canal: {e}")
        return True

async def enviar_menu_principal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    primeiro_nome = user.first_name if user else "Cliente"

    texto = (
        f"Olá <b>{primeiro_nome}</b> ! , seja bem-vindo ao <b>CasaBlanca Bot!</b> 🏛️✨\n\n"
        "Selecione uma opção abaixo para navegar pelo nosso catálogo:"
    )

    keyboard = [
        [
            InlineKeyboardButton("🛒 Comprar", callback_data="menu_comprar"),
            InlineKeyboardButton("ℹ️ Informações", callback_data="info"),
        ],
        [
            InlineKeyboardButton("🔧 Ferramentas", callback_data="ferramentas"),
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
            logger.error(f"Erro ao enviar capa: {e}")

    await context.bot.send_message(chat_id=chat_id, text=texto, reply_markup=reply_markup, parse_mode="HTML")

# ==================== HANDLERS PRINCIPAIS ====================
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
            parse_mode="HTML"
        )

# ==================== INLINE QUERY (PESQUISA POR BIN) ====================
async def inline_bin_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.strip().lower()
    results = []

    cartoes_filtrados = [c for c in DADOS_CARTOES if query in c["bin"].lower()] if query else DADOS_CARTOES

    for item in cartoes_filtrados:
        texto_resposta = (
            f"Número do Cartão: {item['cc']}\n"
            f"Banco: {item['banco']}\n"
            f"Categoria: {item['categoria']}\n"
            f"Tipo: {item['tipo']}\n"
            f"NOME: {item['nome']}\n"
            f"CPF: {item['cpf']}\n\n"
            f"<b>Saldo mínimo garantido: R$ {item['saldo_minimo']:,.2f}</b>\n"
            f"Se o saldo for menor que isso, você pode solicitar reembolso conforme a <b>Política de Reembolso</b>.\n\n"
            f"Valor da Compra: R$ {item['preco']:,.2f}\n\n"
            f"Fornecedor: <i>{item['fornecedor']}</i>"
        ).replace(",", "X").replace(".", ",").replace("X", ".")

        keyboard = [
            [InlineKeyboardButton("✅ Comprar", callback_data=f"buy_card_{item['id']}")],
            [
                InlineKeyboardButton("⬅️ Anterior", callback_data=f"nav_card_prev_{item['id']}"),
                InlineKeyboardButton("Próximo ➡️", callback_data=f"nav_card_next_{item['id']}"),
            ],
            [InlineKeyboardButton("❌ Cancelar", callback_data="voltar_cc_full")],
        ]

        results.append(
            InlineQueryResultArticle(
                id=item["id"],
                title=f"R$ {item['preco']:.2f} - {item['bin']} - {item['banco']}",
                description=f"Nível: {item['categoria']} - Full: ✅\nFornecedor: {item['fornecedor']}",
                input_message_content=InputTextMessageContent(texto_resposta, parse_mode="HTML"),
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        )

    await update.inline_query.answer(results, cache_time=1)

# ==================== CALLBACK QUERY HANDLER ====================
async def botao_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "verificar":
        if await esta_no_canal(context, query.from_user.id):
            await query.message.delete()
            await enviar_menu_principal(update, context)
        else:
            await query.message.reply_text("❌ Você ainda não entrou no canal!")

    elif data == "menu_comprar":
        keyboard = [
            [InlineKeyboardButton("💳 CC FULL DADOS", callback_data="voltar_cc_full")],
            [InlineKeyboardButton("📱 E-SIM", callback_data="esim"), InlineKeyboardButton("📁 CONSULTÁVEL", callback_data="consultavel")],
            [InlineKeyboardButton("💳 CC AUXILIAR", callback_data="cc_auxiliar"), InlineKeyboardButton("🛡️ LARAS", callback_data="laras")],
            [InlineKeyboardButton("🗽 Login's", callback_data="logins")],
            [InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_inicio")],
        ]
        await query.message.edit_text(
            "🛒 <b>SELEÇÃO DE CATEGORIAS</b>\n\nEscolha a categoria que deseja explorar:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )

    elif data == "voltar_cc_full":
        keyboard = [
            [InlineKeyboardButton("🔢 Unitárias", callback_data="ver_unitarias")],
            [
                InlineKeyboardButton("📊 Nível", callback_data="nivel"),
                InlineKeyboardButton("🔍 Bin", switch_inline_query_current_chat=""),
            ],
            [
                InlineKeyboardButton("🏦 banco", callback_data="banco"),
                InlineKeyboardButton("🇧🇷 Bandeira", callback_data="bandeira"),
            ],
            [InlineKeyboardButton("💬 Atendimento/suporte", url=LINK_SUPORTE)],
            [InlineKeyboardButton("🔙 Voltar", callback_data="menu_comprar")],
        ]
        texto = "Informações\n- Saldo: R$ 0,00"
        if query.message.photo:
            await query.message.delete()
            await context.bot.send_message(chat_id=query.message.chat_id, text=texto, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await query.message.edit_text(texto, reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "ver_unitarias":
        keyboard = []
        for i in range(0, len(CATALOGO_UNITARIAS), 2):
            row = []
            item1 = CATALOGO_UNITARIAS[i]
            row.append(InlineKeyboardButton(f"R$ {item1['preco']} {item1['nome']} ({item1['qtd']})", callback_data=f"buy_unit_{i}"))
            if i + 1 < len(CATALOGO_UNITARIAS):
                item2 = CATALOGO_UNITARIAS[i+1]
                row.append(InlineKeyboardButton(f"R$ {item2['preco']} {item2['nome']} ({item2['qtd']})", callback_data=f"buy_unit_{i+1}"))
            keyboard.append(row)

        keyboard.append([InlineKeyboardButton("🔙 Voltar", callback_data="voltar_cc_full")])
        await query.message.edit_text(POLITICA_REEMBOLSO, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

    elif data == "voltar_inicio":
        try:
            await query.message.delete()
        except Exception:
            pass
        await enviar_menu_principal(update, context)

# Registra os Handlers
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(InlineQueryHandler(inline_bin_search))
telegram_app.add_handler(CallbackQueryHandler(botao_callback))

# ==================== FASTAPI APP & RENDER WEBHOOK ====================
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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
