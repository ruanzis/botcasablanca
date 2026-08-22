import asyncio
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
import requests
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
ID_CANAL = os.getenv("ID_CANAL", "1004302224747")
LINK_CANAL = os.getenv("LINK_CANAL", "https://t.me/+qrh5SObhV3xmODhh")
CAPA_PATH = "capa.jpg"

MISTICPAY_API_URL = os.getenv("MISTICPAY_API_URL", "https://api.misticpay.com/v1")
MISTICPAY_CLIENT_SECRET = os.getenv("MISTICPAY_CLIENT_SECRET", "")
WEBHOOK_BASE_URL = os.getenv("WEBHOOK_BASE_URL", "https://botcasablanca.onrender.com")

POLITICA_REEMBOLSO = (
    "Política de Reembolso\n\n"
    "⚠️ Caso o saldo esteja abaixo do mínimo garantido na pré-compra, "
    "solicite reembolso em até 20 minutos via @haridadenetwork, com vídeo mostrando cartão, valor e erro."
)

# ==================== BANCOS DE DADOS DO CATÁLOGO COMPLETO ====================
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

# TODO O SEU ESTOQUE INTEGRAL MANTIDO
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
    {
        "cc": "544169******8821",
        "banco": "ITAU UNIBANCO, S.A.",
        "nome": "MARCOS SILVA PEREIRA",
        "cpf": "01234567890",
        "serasa": "700",
        "bc": "500",
        "bin": "544169",
        "nivel": "FULL PLATINUM",
        "fornecedor": "Anon",
        "preco": 80,
    },
    {
        "cc": "234075******7031",
        "banco": "PICPAY BANK BANCO MULTIPLO S A",
        "nome": "SYLVIA RENATA PEREIRA ARAGAO NUNES",
        "cpf": "07167756709",
        "serasa": "966",
        "bc": "929",
        "bin": "234075",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": 80,
    },
    {
        "cc": "223113******3895",
        "banco": "BANCO BTG PACTUAL SA",
        "nome": "GUSTAVO DA FONSECA",
        "cpf": "30314150862",
        "serasa": "855",
        "bc": "922",
        "bin": "223113",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": 80,
    },
    {
        "cc": "222763******2034",
        "banco": "PICPAY BANK BANCO MULTIPLO S A",
        "nome": "ANNA KAREN SOUTELLO MENDES",
        "cpf": "26494698204",
        "serasa": "211",
        "bc": "205",
        "bin": "222763",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": 80,
    },
    {
        "cc": "498401******1159",
        "banco": "BANCO DO BRASIL, S.A.",
        "nome": "JOSIELMA FERREIRA DE QUEIROZ DA SILVA",
        "cpf": "88991717187",
        "serasa": "530",
        "bc": "691",
        "bin": "498401",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": 80,
    },
]

telegram_app = Application.builder().token(TOKEN).build()

# ==================== FUNÇÕES AUXILIARES ====================
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

# ==================== NAVEGAÇÃO & INTERFACES ====================
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
            logger.error(f"Erro ao carregar imagem de capa: {e}")

    await context.bot.send_message(chat_id=chat_id, text=texto, reply_markup=reply_markup, parse_mode="HTML")

async def exibir_cartao_estoque(query, categoria_key: str, indice: int, max_estoque: int):
    cartao = DADOS_PLATINUM[indice % len(DADOS_PLATINUM)]
    cat_info = CATALOGO_UNITARIAS.get(categoria_key, {"nome": "PLATINUM", "preco": 80})

    texto_detalhes = (
        f"Número do Cartão: <code>{cartao['cc']}</code>\n"
        f"Banco: {cartao['banco']}\n"
        f"Categoria: {cat_info['nome']}\n"
        f"Tipo: Crédito\n"
        f"Nome: {cartao['nome']}\n"
        f"CPF: <code>{cartao['cpf']}</code>\n"
        f"Score Serasa: {cartao['serasa']}\n"
        f"Score BC: {cartao['bc']}\n\n"
        "Saldo mínimo garantido: R$ 1.200,00\n\n"
        f"Valor da Compra: R$ {cat_info['preco']},00\n"
        f"Fornecedor: {cartao.get('fornecedor', 'Anon')}\n\n"
        f"Cartão {indice + 1} de {max_estoque}"
    )

    keyboard = [
        [InlineKeyboardButton("✅ Comprar", callback_data=f"pagar_{categoria_key}_{indice}")],
        [
            InlineKeyboardButton("⏪ Anterior", callback_data=f"nav_{categoria_key}_{indice - 1}"),
            InlineKeyboardButton("Próximo ⏩", callback_data=f"nav_{categoria_key}_{indice + 1}"),
        ],
        [InlineKeyboardButton("❌ Cancelar", callback_data="sub_categoria_unitarias")],
    ]

    await query.message.edit_text(texto_detalhes, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

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
            parse_mode="HTML"
        )

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

    await update.message.reply_text("❌ <b>Falha ao gerar o PIX.</b>\nVerifique as credenciais da MisticPay.", parse_mode="HTML")

async def botao_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
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

    elif data == "categoria_full_dados":
        keyboard = [
            [InlineKeyboardButton("🔎 Buscar por BIN", callback_data="solicitar_busca_bin")],
            [InlineKeyboardButton("🔙 Voltar ao Menu Comprar", callback_data="menu_comprar")],
        ]
        await query.message.edit_text("🏛️ <b>ESTOQUE CC FULL DADOS</b>", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

    elif data == "solicitar_busca_bin":
        context.user_data["aguardando_bin"] = True
        await query.message.reply_text("🔍 Digite os 6 primeiros dígitos da BIN que deseja procurar:")

    elif data.startswith("nav_"):
        parts = data.split("_")
        cat_key, indice = parts[1], int(parts[2])
        max_estoque = CATALOGO_UNITARIAS.get(cat_key, {}).get("estoque", len(DADOS_PLATINUM))
        indice = indice % max_estoque
        await exibir_cartao_estoque(query, cat_key, indice, max_estoque)

    elif data.startswith("pagar_"):
        parts = data.split("_")
        cat_key = parts[1]
        cat_info = CATALOGO_UNITARIAS.get(cat_key, {"nome": "ITEM", "preco": 80})
        
        loop = asyncio.get_running_loop()
        dados_pix = await loop.run_in_executor(None, gerar_pix_misticpay, cat_info['preco'], user_id)
        
        if dados_pix:
            qr_code = dados_pix.get("qrcode") or dados_pix.get("pix_code") or dados_pix.get("copy_paste")
            await query.message.reply_text(
                f"⚡ <b>PAGAMENTO GERADO - {cat_info['nome']}</b>\n\nValor: R$ {cat_info['preco']:.2f}\n\nCopie o PIX:\n<code>{qr_code}</code>",
                parse_mode="HTML"
            )
        else:
            await query.message.reply_text("❌ Falha ao gerar PIX para este item.")

    elif data == "info":
        await query.message.reply_text(POLITICA_REEMBOLSO)
    elif data == "add_saldo":
        await query.message.reply_text("💳 Use o comando <code>/pix 50</code> para gerar um PIX no valor desejado.", parse_mode="HTML")
    elif data == "voltar_inicio":
        await query.message.delete()
        await enviar_menu_principal(update, context)

async def processar_texto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("aguardando_bin"):
        termo = update.message.text.strip()
        context.user_data["aguardando_bin"] = False
        resultados = [(i, item) for i, item in enumerate(DADOS_PLATINUM) if termo in item.get("bin", "") or termo in item["cc"]]

        if resultados:
            keyboard = [[InlineKeyboardButton(f"R$ {item['preco']} - {item['banco']}", callback_data=f"nav_platinum_{idx}")] for idx, item in resultados]
            await update.message.reply_text(f"🔍 <b>{len(resultados)} cartão(ões) encontrado(s):</b>", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        else:
            await update.message.reply_text("❌ Nenhum cartão encontrado para a BIN informada.")

# Registra Handlers
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("pix", pix_command))
telegram_app.add_handler(CallbackQueryHandler(botao_callback))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, processar_texto))

# ==================== FASTAPI APP ====================
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
