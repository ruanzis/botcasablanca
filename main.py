import asyncio
import logging
import os
import time
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

# Credenciais MisticPay
MISTICPAY_CLIENT_ID = os.getenv("MISTICPAY_CLIENT_ID", "ci_g35d35pglvgsj39")
MISTICPAY_CLIENT_SECRET = os.getenv("MISTICPAY_CLIENT_SECRET", "cs_xmi6kbhukucgc1syoymxugk3h")
WEBHOOK_BASE_URL = os.getenv("WEBHOOK_BASE_URL", "https://botcasablanca.onrender.com")

POLITICA_REEMBOLSO = (
    "<b>Política de Reembolso</b>\n\n"
    "⚠️ Caso o saldo esteja abaixo do mínimo garantido na pré-compra, "
    "solicite reembolso em até 20 minutos via @haridadenetwork, "
    "com vídeo mostrando cartão, valor e erro."
)

SALDO_USUARIOS = {}

CATALOGO_UNITARIAS = [
    {"id": "unit_0", "nome": "PLATINUM", "preco": 80.0, "qtd": 525},
    {"id": "unit_1", "nome": "PERSONAL", "preco": 50.0, "qtd": 55},
    {"id": "unit_2", "nome": "GOLD", "preco": 50.0, "qtd": 174},
    {"id": "unit_3", "nome": "ELO", "preco": 50.0, "qtd": 1},
    {"id": "unit_4", "nome": "BUSINESS", "preco": 80.0, "qtd": 16},
    {"id": "unit_5", "nome": "INFINITE", "preco": 413, "qtd": 413},
    {"id": "unit_6", "nome": "BLACK", "preco": 120.0, "qtd": 114},
    {"id": "unit_7", "nome": "SIGNATURE", "preco": 80.0, "qtd": 3},
    {"id": "unit_8", "nome": "NUBANK GOLD", "preco": 35.0, "qtd": 501},
    {"id": "unit_9", "nome": "NUBANK PLATINUM", "preco": 40.0, "qtd": 430},
]

DADOS_CARTOES = [
    {
        "id": "card_1",
        "cc": "542819******0150|08|2028|306",
        "banco": "BANCO GENIAL SA",
        "categoria": "FULL PLATINUM",
        "tipo": "CREDIT",
        "nome": "CRISTIANO CACHEIRO MAHIA",
        "cpf": "03250698679",
        "bin": "542819",
        "fornecedor": "Anon",
        "preco": 80.00,
        "saldo_minimo": 1200.00,
        "vendido": False,
    },
    {
        "id": "card_2",
        "cc": "544169******0487|05|2029|931",
        "banco": "ITAU UNIBANCO, S.A.",
        "categoria": "PLATINUM",
        "tipo": "CREDIT",
        "nome": "ALEXANDRE CARVALHO CHANAN",
        "cpf": "18319050006",
        "bin": "544169",
        "fornecedor": "Anon",
        "preco": 80.00,
        "saldo_minimo": 1200.00,
        "vendido": False,
    },
]

telegram_app = Application.builder().token(TOKEN).build()

# ==================== MISTICPAY API INTEGRACAO (AJUSTADA PELA DOC) ====================
def gerar_pix_misticpay(valor: float, telegram_id: int, nome_usuario: str):
    url = "https://api.misticpay.com/api/transactions/create"
    headers = {
        "ci": MISTICPAY_CLIENT_ID,
        "cs": MISTICPAY_CLIENT_SECRET,
        "Content-Type": "application/json",
    }
    
    transaction_id = f"tx_{telegram_id}_{int(time.time())}"

    # Payload exato exigido pela MisticPay
    payload = {
        "amount": valor,
        "payerName": nome_usuario if nome_usuario else f"Cliente_{telegram_id}",
        "payerDocument": "12345678909",  # CPF fictício sem formatação
        "transactionId": transaction_id,
        "description": f"Deposito Saldo User {telegram_id}",
        "projectWebhook": f"{WEBHOOK_BASE_URL}/misticpay-webhook"
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=12)
        logger.info(f"MisticPay Response [{response.status_code}]: {response.text}")

        if response.status_code in [200, 201]:
            res = response.json()
            # MisticPay retorna 'copyPaste' para o Pix Copia e Cola
            data_obj = res.get("data", {})
            pix_code = data_obj.get("copyPaste") or data_obj.get("qrcodeUrl")
            
            if pix_code:
                return {"pix_code": pix_code}
        else:
            # Retorna o erro exato da MisticPay para você depurar
            return {"erro": f"HTTP {response.status_code} - {response.text}"}
            
    except Exception as e:
        logger.error(f"Erro de conexão MisticPay: {e}")
        return {"erro": str(e)}
        
    return None

# ==================== CONTROLE CANAL & MENUS ====================
async def esta_no_canal(context: ContextTypes.DEFAULT_TYPE, user_id: int):
    try:
        membro = await context.bot.get_chat_member(chat_id=ID_CANAL, user_id=user_id)
        return membro.status in ["member", "administrator", "creator"]
    except Exception as e:
        logger.warning(f"Erro validacao canal: {e}")
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
            logger.error(f"Erro capa: {e}")

    await context.bot.send_message(chat_id=chat_id, text=texto, reply_markup=reply_markup, parse_mode="HTML")

# ==================== COMANDOS ====================
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

async def comando_pix(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    try:
        valor = float(context.args[0])
        if valor < 20.0:
            await update.message.reply_text("⚠️ <b>O valor mínimo para depósito é R$ 20,00.</b>", parse_mode="HTML")
            return
    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ Uso correto: <code>/pix 20</code> (Mínimo: R$ 20,00)", parse_mode="HTML")
        return

    dados_pix = gerar_pix_misticpay(valor, user_id, user.first_name)
    if dados_pix and dados_pix.get("pix_code"):
        pix_code = dados_pix["pix_code"]
        msg = (
            f"💳 <b>PAGAMENTO VIA PIX GERADO</b>\n\n"
            f"<b>Valor:</b> R$ {valor:,.2f}\n\n"
            f"Copie o código abaixo e pague no seu app de banco:\n\n"
            f"<code>{pix_code}</code>"
        ).replace(",", "X").replace(".", ",").replace("X", ".")
        await update.message.reply_text(msg, parse_mode="HTML")
    else:
        await update.message.reply_text("❌ Falha ao gerar PIX MisticPay. Verifique a API ou tente novamente.")

# ==================== PESQUISA POR BIN (INLINE) ====================
async def inline_bin_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.strip().lower()
    results = []

    cartoes_filtrados = [c for c in DADOS_CARTOES if not c["vendido"] and query in c["bin"].lower()] if query else [c for c in DADOS_CARTOES if not c["vendido"]]

    for item in cartoes_filtrados:
        texto_resposta = (
            f"Número do Cartão: {item['cc'][:12]}****\n"
            f"Banco: {item['banco']}\n"
            f"Categoria: {item['categoria']}\n"
            f"Tipo: {item['tipo']}\n"
            f"NOME: {item['nome']}\n"
            f"CPF: {item['cpf']}\n\n"
            f"<b>Saldo mínimo garantido: R$ {item['saldo_minimo']:,.2f}</b>\n"
            f"Se o saldo for menor, solicite reembolso conforme a <b>Política de Reembolso</b>.\n\n"
            f"Valor da Compra: R$ {item['preco']:,.2f}\n\n"
            f"Fornecedor: <i>{item['fornecedor']}</i>"
        ).replace(",", "X").replace(".", ",").replace("X", ".")

        keyboard = [
            [InlineKeyboardButton("✅ Comprar", callback_data=f"buy_card_{item['id']}")],
            [
                InlineKeyboardButton("⬅️ Anterior", callback_data="nav_prev"),
                InlineKeyboardButton("Próximo ➡️", callback_data="nav_next"),
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

# ==================== CALLBACKS E COMPRAS ====================
async def botao_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception:
        pass

    user_id = query.from_user.id
    data = query.data
    chat_id = query.message.chat_id

    saldo_atual = SALDO_USUARIOS.get(user_id, 0.0)

    if data == "verificar":
        if await esta_no_canal(context, user_id):
            await query.message.delete()
            await enviar_menu_principal(update, context)
        else:
            await query.message.reply_text("❌ Você ainda não entrou no canal!")

    elif data == "add_saldo":
        await query.message.reply_text(
            "💳 <b>Adicionar Saldo</b>\n\n"
            "O valor mínimo de depósito é <b>R$ 20,00</b>.\n"
            "Digite no chat o comando com o valor desejado:\n\n"
            "Exemplo: <code>/pix 20</code>",
            parse_mode="HTML"
        )

    elif data == "menu_comprar":
        keyboard = [
            [InlineKeyboardButton("💳 CC FULL DADOS", callback_data="voltar_cc_full")],
            [InlineKeyboardButton("📱 E-SIM", callback_data="esim"), InlineKeyboardButton("📁 CONSULTÁVEL", callback_data="consultavel")],
            [InlineKeyboardButton("💳 CC AUXILIAR", callback_data="cc_auxiliar"), InlineKeyboardButton("🛡️ LARAS", callback_data="laras")],
            [InlineKeyboardButton("🗽 Login's", callback_data="logins")],
            [InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_inicio")],
        ]
        markup = InlineKeyboardMarkup(keyboard)
        if query.message.photo:
            await query.message.delete()
            await context.bot.send_message(chat_id=chat_id, text="🛒 <b>SELEÇÃO DE CATEGORIAS</b>\n\nEscolha a categoria:", reply_markup=markup, parse_mode="HTML")
        else:
            await query.message.edit_text("🛒 <b>SELEÇÃO DE CATEGORIAS</b>\n\nEscolha a categoria:", reply_markup=markup, parse_mode="HTML")

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
        texto = f"Informações\n- Saldo: R$ {saldo_atual:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        markup = InlineKeyboardMarkup(keyboard)

        if query.message.photo:
            await query.message.delete()
            await context.bot.send_message(chat_id=chat_id, text=texto, reply_markup=markup)
        else:
            await query.message.edit_text(texto, reply_markup=markup)

    elif data == "ver_unitarias":
        keyboard = []
        for item in CATALOGO_UNITARIAS:
            keyboard.append([InlineKeyboardButton(f"R$ {item['preco']:.0f} {item['nome']} ({item['qtd']})", callback_data=f"buy_u_{item['id']}")])

        keyboard.append([InlineKeyboardButton("🔙 Voltar", callback_data="voltar_cc_full")])
        await query.message.edit_text(POLITICA_REEMBOLSO, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

    elif data.startswith("buy_u_"):
        unit_id = data.replace("buy_u_", "")
        item = next((x for x in CATALOGO_UNITARIAS if x["id"] == unit_id), None)
        if item:
            if saldo_atual < item["preco"]:
                await query.message.reply_text(
                    f"❌ <b>SALDO INSUFICIENTE!</b>\n\n"
                    f"Preço: R$ {item['preco']:,.2f}\n"
                    f"Seu Saldo: R$ {saldo_atual:,.2f}\n\n"
                    f"Adicione saldo digitando: <code>/pix {int(item['preco'])}</code>",
                    parse_mode="HTML",
                )
            elif item["qtd"] <= 0:
                await query.message.reply_text("❌ Estoque esgotado para este produto!")
            else:
                SALDO_USUARIOS[user_id] -= item["preco"]
                item["qtd"] -= 1
                await query.message.reply_text(
                    f"✅ <b>COMPRA REALIZADA COM SUCESSO!</b>\n\n"
                    f"Item: {item['nome']}\n"
                    f"Valor: R$ {item['preco']:,.2f}\n"
                    f"Novo Saldo: R$ {SALDO_USUARIOS[user_id]:,.2f}",
                    parse_mode="HTML",
                )

    elif data.startswith("buy_card_"):
        card_id = data.replace("buy_card_", "")
        card = next((c for c in DADOS_CARTOES if c["id"] == card_id), None)
        if card:
            if card["vendido"]:
                await query.message.reply_text("❌ Este cartão já foi vendido!")
            elif saldo_atual < card["preco"]:
                await query.message.reply_text(
                    f"❌ <b>SALDO INSUFICIENTE!</b>\n\n"
                    f"Preço do cartão: R$ {card['preco']:,.2f}\n"
                    f"Seu Saldo: R$ {saldo_atual:,.2f}\n\n"
                    f"Adicione saldo digitando: <code>/pix {int(card['preco'])}</code>",
                    parse_mode="HTML",
                )
            else:
                SALDO_USUARIOS[user_id] -= card["preco"]
                card["vendido"] = True
                await query.message.reply_text(
                    f"🎉 <b>COMPRA CONCLUÍDA!</b>\n\n"
                    f"<b>Dados do Cartão:</b>\n<code>{card['cc']}</code>\n"
                    f"<b>Nome:</b> {card['nome']}\n"
                    f"<b>CPF:</b> {card['cpf']}\n"
                    f"<b>Banco:</b> {card['banco']}\n\n"
                    f"Novo Saldo: R$ {SALDO_USUARIOS[user_id]:,.2f}",
                    parse_mode="HTML",
                )

    elif data == "voltar_inicio":
        try:
            await query.message.delete()
        except Exception:
            pass
        await enviar_menu_principal(update, context)

# Registra Handlers
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("pix", comando_pix))
telegram_app.add_handler(InlineQueryHandler(inline_bin_search))
telegram_app.add_handler(CallbackQueryHandler(botao_callback))

# ==================== FASTAPI APP & WEBHOOKS ====================
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

@app.post("/misticpay-webhook")
async def misticpay_webhook(request: Request):
    try:
        payload = await request.json()
        logger.info(f"Webhook MisticPay recebido: {payload}")

        status = payload.get("status")
        value = float(payload.get("value", 0))
        description = payload.get("description", "")

        # Pega o ID do usuario a partir da descricao
        if status == "COMPLETO" and "User " in description:
            user_id = int(description.split("User ")[1])
            SALDO_USUARIOS[user_id] = SALDO_USUARIOS.get(user_id, 0.0) + value

            texto_sucesso = (
                f"✅ <b>PAGAMENTO CONFIRMADO!</b>\n\n"
                f"Foi creditado <b>R$ {value:,.2f}</b> na sua conta."
            ).replace(",", "X").replace(".", ",").replace("X", ".")

            await telegram_app.bot.send_message(chat_id=user_id, text=texto_sucesso, parse_mode="HTML")

        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Erro webhook MisticPay: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/")
async def root():
    return {"status": "online"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
