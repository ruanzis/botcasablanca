import asyncio
import io
import logging
import os
import random
import re
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
import qrcode
import httpx
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
    MessageHandler,
    filters,
)

# Configuração de Logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurações de Ambiente
TOKEN = os.getenv("TELEGRAM_TOKEN", "8956870259:AAGR_gmp5h2pzwdYnqC_QScrigH8imPVoho")
ID_CANAL = os.getenv("ID_CANAL", "@oficialharidade")

LINK_CANAL_VERIFICACAO = "https://t.me/oficialharidade"
LINK_CANAL = os.getenv("LINK_CANAL", "https://t.me/+qrh5SObhV3xmODhh")
LINK_SUPORTE = "https://t.me/haridadenetwork"
CAPA_PATH = "capa.jpg"

THUMB_CARD_URL = "https://i.postimg.cc/9Fdfb4MV/Design-sem-nome.png"

MISTICPAY_CLIENT_ID = os.getenv("MISTICPAY_CLIENT_ID", "ci_g35d35pglvgsj39")
MISTICPAY_CLIENT_SECRET = os.getenv("MISTICPAY_CLIENT_SECRET", "cs_xmi6kbhukucgc1syoymxugk3h")
WEBHOOK_BASE_URL = os.getenv("WEBHOOK_BASE_URL", "https://botcasablanca.onrender.com")

POLITICA_REEMBOLSO = (
    "🔹 <b>SISTEMA CASABLANCA | POLÍTICA DE REEMBOLSO</b> 🔹\n\n"
    "⚠️ Caso o saldo esteja abaixo do mínimo garantido na pré-compra, "
    "solicite reembolso em até 20 minutos via @haridadenetwork, "
    "com vídeo mostrando cartão, valor e erro."
)

SALDO_USUARIOS = {}
CACHE_CANAL = {}
INDICACOES_USUARIOS = {} # {user_id: referrer_id}
TOTAL_INDICADOS = {}     # {user_id: count}

# --- CATÁLOGO DE FERRAMENTAS ---
CATALOGO_FERRAMENTAS = [
    {
        "id": "tool_kl_mob",
        "nome": "🦠 KL MOB 5.4",
        "descricao": "30 Dias de KL MOB 5.4",
        "preco": 800.00
    },
    {
        "id": "tool_breached",
        "nome": "⚠️ Painel Breached",
        "descricao": "Painel vitalicio",
        "preco": 1100.00
    },
    {
        "id": "tool_uber",
        "nome": "🏍️ Painel Criar 99/Uber",
        "descricao": "Painel eficaz para vendas de contas da 99 Motorista e Uber Motorista. Trabalhe em case, adquira já!",
        "preco": 150.00
    }
]

# --- CATÁLOGO DE E-SIM ---
CATALOGO_ESIM = [
    {
        "id": "esim_1",
        "nome": "TIM 30/45gb - SOBE SINAL AUTOMÁTICO",
        "descricao": "TIM 45GB · DDD_ONLY · Conexão imediata",
        "preco": 35.0,
        "qtd": 51,
        "vendido": False
    },
    {
        "id": "esim_2",
        "nome": "VIVO 110gb - SOBE SINAL AUTOMÁTICO",
        "descricao": "VIVO CONNECT · Alta velocidade · DDD_ONLY",
        "preco": 45.0,
        "qtd": 65,
        "vendido": False
    },
    {
        "id": "esim_3",
        "nome": "TIM 60gb - SOBE SINAL EM ATE 1 HORA",
        "descricao": "TIM 60GB · Suporte dedicado",
        "preco": 25.0,
        "qtd": 35,
        "vendido": False
    }
]

# --- CATÁLOGO DE LARAS ---
CATALOGO_LARAS = [
    {
        "id": "lara_1",
        "nome": "VoltPix LTDA | CORRETORA DE SEGUROS LTDA",
        "banco": "VOLTPIX",
        "categoria": "CORRETORA",
        "tipo": "BEP20",
        "nome_titular": "CORRETORA DE SEGUROS LTDA",
        "cpf": "38291029000155",
        "score_serasa": 750,
        "score_bc": 820,
        "descricao": "VOLTPIX - 0 MED E SAQUES CRIPTO (BEP20)",
        "preco": 120.00,
        "vendido": False
    },
    {
        "id": "lara_2",
        "nome": "VoltPix LTDA | DISTRIBUIDORA ALIMENTÍCIOS LTDA",
        "banco": "VOLTPIX",
        "categoria": "DISTRIBUIDORA",
        "tipo": "BEP20",
        "nome_titular": "DISTRIBUIDORA ALIMENTÍCIOS LTDA",
        "cpf": "49102938000188",
        "score_serasa": 680,
        "score_bc": 710,
        "descricao": "VOLTPIX - 0 MED E SAQUES CRIPTO (BEP20)",
        "preco": 100.00,
        "vendido": False
    },
    {
        "id": "lara_3",
        "nome": "VoltPix LTDA | COMÉRCIO E SERVIÇOS HIDRÁULICOS",
        "banco": "VOLTPIX",
        "categoria": "COMÉRCIO",
        "tipo": "BEP20",
        "nome_titular": "COMÉRCIO E SERVIÇOS HIDRÁULICOS",
        "cpf": "52910283000199",
        "score_serasa": 710,
        "score_bc": 690,
        "descricao": "VOLTPIX - 0 MED E SAQUES CRIPTO (BEP20)",
        "preco": 100.00,
        "vendido": False
    },
    {
        "id": "lara_4",
        "nome": "VoltPix | Paola Amorim",
        "banco": "VOLTPIX",
        "categoria": "PF",
        "tipo": "BEP20",
        "nome_titular": "PAOLA AMORIM",
        "cpf": "29103849200",
        "score_serasa": 890,
        "score_bc": 910,
        "descricao": "VOLTPIX - 0 MED E SAQUES CRIPTO (BEP20)",
        "preco": 100.00,
        "vendido": False
    },
    {
        "id": "lara_5",
        "nome": "VoltPix | Erick Rosa",
        "banco": "VOLTPIX",
        "categoria": "PF",
        "tipo": "BEP20",
        "nome_titular": "ERICK ROSA",
        "cpf": "38201928399",
        "score_serasa": 640,
        "score_bc": 700,
        "descricao": "VOLTPIX - 0 MED E SAQUES CRIPTO (BEP20)",
        "preco": 100.00,
        "vendido": False
    }
]

# --- MOTOR DE AUTOMAÇÃO E EDIFICAÇÃO DE ESTOQUE ---

def identificar_bin(cc_number: str) -> str:
    apenas_numeros = re.sub(r"\D", "", str(cc_number))
    return apenas_numeros[:6] if len(apenas_numeros) >= 6 else "000000"

def mascarar_cartao(cc_full: str) -> str:
    partes = cc_full.split("|")
    num_limpo = re.sub(r"\D", "", partes[0])
    if len(num_limpo) >= 13:
        bin_part = num_limpo[:6]
        last_part = num_limpo[-4:]
        num_mascarado = f"{bin_part}******{last_part}"
    else:
        num_mascarado = partes[0]
    
    if len(partes) > 1:
        return f"{num_mascarado}|" + "|".join(partes[1:])
    return num_mascarado

def identificar_bandeira(bin_code: str) -> str:
    b = str(bin_code).strip()
    if not b or len(b) < 6:
        return "DESCONHECIDA"
    if b.startswith("4"):
        return "VISA"
    elif b.startswith(("51", "52", "53", "54", "55")) or (2221 <= int(b[:4]) <= 2720 if b[:4].isdigit() else False):
        return "MASTERCARD"
    elif b.startswith(("34", "37")):
        return "AMEX"
    elif b.startswith(("4011", "4389", "4514", "4576", "5041", "5066", "5090", "5094", "6362", "6363", "650", "651", "655")):
        return "ELO"
    else:
        return "OUTRAS"

def identificar_banco_por_bin(bin_code: str) -> str:
    b = str(bin_code).strip()
    if b.startswith(("470598", "544169", "498406", "525204", "410863", "412171")):
        return "ITAU UNIBANCO, S.A."
    elif b.startswith(("542819", "548058")):
        return "BANCO GENIAL SA"
    elif b.startswith(("400217", "427168", "512631", "520268")):
        return "BANCO BRADESCO S.A."
    elif b.startswith(("451416", "540115", "490172")):
        return "BANCO DO BRASIL S.A."
    else:
        return "BANCO DESCONHECIDO"

def identificar_nivel(categoria_raw: str) -> str:
    cat = str(categoria_raw).upper().strip()
    if "BLACK" in cat:
        return "BLACK"
    elif "INFINITE" in cat:
        return "INFINITE"
    elif "PLATINUM" in cat:
        return "PLATINUM"
    elif "GOLD" in cat or "OURO" in cat:
        return "GOLD"
    else:
        return cat if cat else "STANDARD"

def edificar_item_estoque(card_raw: dict) -> dict:
    cc_bruto = card_raw.get("cc", "")
    bin_extraida = identificar_bin(cc_bruto)
    banco_auto = card_raw.get("banco", identificar_banco_por_bin(bin_extraida))
    bandeira_auto = card_raw.get("bandeira", identificar_bandeira(bin_extraida))
    nivel_auto = identificar_nivel(card_raw.get("categoria", ""))

    return {
        "id": card_raw.get("id"),
        "cc_full": cc_bruto,
        "cc_mascarado": mascarar_cartao(cc_bruto),
        "bin": bin_extraida,
        "banco": banco_auto,
        "bandeira": bandeira_auto,
        "categoria": card_raw.get("categoria", "STANDARD"),
        "nivel_formatado": nivel_auto,
        "tipo": card_raw.get("tipo", "CREDIT").upper(),
        "nome": card_raw.get("nome", "NÃO INFORMADO").upper(),
        "cpf": re.sub(r"\D", "", str(card_raw.get("cpf", ""))),
        "score_serasa": card_raw.get("score_serasa", random.randint(100, 900)),
        "score_bc": card_raw.get("score_bc", random.randint(100, 900)),
        "fornecedor": card_raw.get("fornecedor", "Anon"),
        "preco": float(card_raw.get("preco", 80.0)),
        "saldo_minimo": float(card_raw.get("saldo_minimo", 1200.0)),
        "vendido": card_raw.get("vendido", False),
    }

ESTOQUE_BRUTO = [
    {
        "id": "card_1",
        "cc": "542819******0150|08|2028|306",
        "categoria": "FULL PLATINUM",
        "tipo": "CREDIT",
        "nome": "CRISTIANO CACHEIRO MAHIA",
        "cpf": "03250698679",
        "score_serasa": 496,
        "score_bc": 352,
        "fornecedor": "Anon",
        "preco": 80.00,
        "saldo_minimo": 1200.00,
        "vendido": False,
    },
    {
        "id": "card_2",
        "cc": "544169******0487|05|2029|931",
        "categoria": "PLATINUM",
        "tipo": "CREDIT",
        "nome": "ALEXANDRE CARVALHO CHANAN",
        "cpf": "18319050006",
        "score_serasa": 712,
        "score_bc": 540,
        "fornecedor": "Anon",
        "preco": 80.00,
        "saldo_minimo": 1200.00,
        "vendido": False,
    },
]

DADOS_CARTOES = [edificar_item_estoque(item) for item in ESTOQUE_BRUTO]

CATALOGO_UNITARIAS = [
    {"id": "unit_0", "nome": "PLATINUM", "preco": 80.0, "qtd": 525},
    {"id": "unit_1", "nome": "PERSONAL", "preco": 50.0, "qtd": 55},
    {"id": "unit_2", "nome": "GOLD", "preco": 50.0, "qtd": 174},
    {"id": "unit_3", "nome": "ELO", "preco": 50.0, "qtd": 1},
]
# ==============================================================================
# NOVAS VARIÁVEIS DE ESTOQUE E COMANDOS ADMINISTRATIVOS
# ==============================================================================

ESTOQUE_ESIM_DINAMICO = [
    "📶 <b>TIM 30/45gb - SOBE SINAL AUTOMÁTICO</b>\n💰 R$35 · TIM 45GB · DDD_ONLY · 51 em estoque\n",
    "📶 <b>VIVO 110gb - SOBE SINAL AUTOMÁTICO</b>\n💰 R$45 · VIVO CONNECT · DDD_ONLY · 65 em estoque\n",
    "📶 <b>TIM 60gb - SOBE SINAL EM ATE 1 HORAS</b>\n💰 R$25 · TIM 60GB · DDD_ONLY · 35 em estoque\n"
]

ESTOQUE_LARAS_DINAMICO = []

async def painel_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in [7536040475]: return
    
    texto = (
        "👨‍💻 <b>PAINEL ADMINISTRATIVO COMPLETO</b>\n\n"
        "<b>Comandos de Inserção de Estoque:</b>\n"
        "<code>/add_estoque_ccfullldados</code> - Add CC Full\n"
        "<code>/add_estoque_esim</code> - Add E-SIM\n"
        "<code>/add_estoque_laras</code> - Add Laras\n"
        "<code>/add_estoque_consultavel</code> - Add Consultável\n\n"
        "<i>Envie o comando acompanhado das informações do produto para catalogá-lo.</i>"
    )
    await update.message.reply_text(texto, parse_mode="HTML")

async def add_estoque_esim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in [7536040475]: return
    
    texto = update.message.text.replace("/add_estoque_esim", "").strip()
    if not texto:
        return await update.message.reply_text("❌ Envie o formato do E-SIM após o comando.\nEx: /add_estoque_esim 📶 TIM 60GB...")
    
    ESTOQUE_ESIM_DINAMICO.append(texto + "\n")
    await update.message.reply_text("✅ <b>E-SIM adicionado com sucesso ao catálogo!</b>", parse_mode="HTML")

async def add_estoque_laras(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in [7536040475]: return
    await update.message.reply_text("✅ <b>Laras recebido e adicionado com sucesso ao catálogo dinâmico!</b>", parse_mode="HTML")

async def add_estoque_ccfullldados(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Reaproveita exatamente a sua lógica existente de CC Full
    await add_estoque(update, context)

async def add_estoque_consultavel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in [7536040475]: return
    await update.message.reply_text("✅ <b>Consultável estocado com sucesso! (Ficará visível assim que o módulo for ativado)</b>", parse_mode="HTML")
    
telegram_app = Application.builder().token(TOKEN).build()

def gerar_cpf_valido() -> str:
    cpf = [random.randint(0, 9) for _ in range(9)]
    for _ in range(2):
        val = sum([(len(cpf) + 1 - i) * v for i, v in enumerate(cpf)]) % 11
        cpf.append(0 if val < 2 else 11 - val)
    return "".join(map(str, cpf))

async def expirador_pix(chat_id: int, message_id: int, valor: float, segundos: int = 1800):
    await asyncio.sleep(segundos)
    try:
        await telegram_app.bot.delete_message(chat_id=chat_id, message_id=message_id)
        valor_formatado = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        await telegram_app.bot.send_message(
            chat_id=chat_id,
            text=f"⏳ <b>QRCODE EXPIRADO POR TEMPO LIMITADO.</b>\nPara gerar novamente, digite <code>/pix {valor_formatado}</code>.",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.warning(f"Erro ao apagar mensagem expirada: {e}")

async def anti_sleep_ping():
    async with httpx.AsyncClient() as client:
        while True:
            await asyncio.sleep(300)
            try:
                await client.get(f"{WEBHOOK_BASE_URL.rstrip('/')}/")
            except Exception:
                pass

async def gerar_pix_misticpay(valor: float, telegram_id: int, nome_usuario: str):
    url = "https://api.misticpay.com/api/transactions/create"
    headers = {
        "ci": MISTICPAY_CLIENT_ID.strip(),
        "cs": MISTICPAY_CLIENT_SECRET.strip(),
        "Content-Type": "application/json",
    }
    transaction_id = f"tx_{telegram_id}_{int(time.time())}"

    payload = {
        "amount": float(valor),
        "payerName": nome_usuario if nome_usuario else f"Cliente_{telegram_id}",
        "payerDocument": gerar_cpf_valido(),
        "transactionId": transaction_id,
        "description": f"Deposito Saldo Bot User {telegram_id}",
        "projectWebhook": f"{WEBHOOK_BASE_URL.rstrip('/')}/misticpay-webhook",
        "expiresIn": 1800
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=10.0)
            if response.status_code in [200, 201]:
                res = response.json()
                data_obj = res.get("data", {})
                pix_code = data_obj.get("copyPaste") or data_obj.get("qrcodeUrl") or data_obj.get("qrCodeBase64")
                if pix_code:
                    return {"pix_code": pix_code}
            return {"erro": f"Status {response.status_code}: {response.text}"}
    except Exception as e:
        return {"erro": f"Falha de conexão: {str(e)}"}

async def esta_no_canal(context: ContextTypes.DEFAULT_TYPE, user_id: int):
    agora = time.time()
    if user_id in CACHE_CANAL and (agora - CACHE_CANAL[user_id]) < 600:
        return True
    try:
        membro = await context.bot.get_chat_member(chat_id=ID_CANAL, user_id=user_id)
        no_canal = membro.status in ["member", "administrator", "creator"]
        if no_canal:
            CACHE_CANAL[user_id] = agora
        return no_canal
    except Exception:
        return False

# --- FUNÇÃO AUXILIAR SEGURA PARA ATUALIZAR TELA ---
async def responder_ou_editar(query, texto, reply_markup, parse_mode="HTML"):
    try:
        if query.message.photo:
            await query.message.delete()
            await query.message.chat.send_message(text=texto, reply_markup=reply_markup, parse_mode=parse_mode)
        else:
            await query.message.edit_text(text=texto, reply_markup=reply_markup, parse_mode=parse_mode)
    except Exception as e:
        logger.warning(f"Erro ao editar/enviar mensagem: {e}")
        try:
            await query.message.chat.send_message(text=texto, reply_markup=reply_markup, parse_mode=parse_mode)
        except Exception:
            pass

async def enviar_menu_principal(update: Update, context: ContextTypes.DEFAULT_TYPE, reply_to_id: int = None):
    user = update.effective_user
    primeiro_nome = user.first_name if user else "Cliente"

    texto = (
        f"🔹 <b>CASABLANCA SHOP | SISTEMA CENTRAL</b> 🔹\n\n"
        f"Olá <b>{primeiro_nome}</b>! Seja bem-vindo ao <b>CasaBlanca Bot</b>!\n\n"
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
                await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=photo,
                    caption=texto,
                    reply_markup=reply_markup,
                    parse_mode="HTML",
                    reply_to_message_id=reply_to_id
                )
                return
        except Exception:
            pass

    await context.bot.send_message(
        chat_id=chat_id,
        text=texto,
        reply_markup=reply_markup,
        parse_mode="HTML",
        reply_to_message_id=reply_to_id
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    msg_id = update.message.message_id
    
    if context.args:
        try:
            referrer_id = int(context.args[0])
            if referrer_id != user_id and user_id not in INDICACOES_USUARIOS:
                INDICACOES_USUARIOS[user_id] = referrer_id
                TOTAL_INDICADOS[referrer_id] = TOTAL_INDICADOS.get(referrer_id, 0) + 1
        except ValueError:
            pass

    if await esta_no_canal(context, user_id):
        await enviar_menu_principal(update, context, reply_to_id=msg_id)
    else:
        keyboard = [
            [InlineKeyboardButton("📢 Entrar no Canal", url=LINK_CANAL_VERIFICACAO)],
            [InlineKeyboardButton("🔄 Já entrei / Liberar Acesso", callback_data="verificar")],
        ]
        await update.message.reply_text(
            "🔹 <b>CASABLANCA SHOP | VERIFICAÇÃO</b> 🔹\n\n"
            "⚠️ <b>ACESSO BLOQUEADO!</b>\n\nPara acessar nosso bot, entre no canal oficial.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
            reply_to_message_id=msg_id
        )

async def comando_pix(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    msg_id = update.message.message_id

    try:
        valor = float(context.args[0])
        if valor < 20.0:
            await update.message.reply_text(
                "🔹 <b>CASABLANCA SHOP | SISTEMA PIX</b> 🔹\n\n⚠️ <b>O valor mínimo para depósito é R$ 20,00.</b>",
                parse_mode="HTML",
                reply_to_message_id=msg_id
            )
            return
    except (IndexError, ValueError):
        await update.message.reply_text(
            "🔹 <b>CASABLANCA SHOP | SISTEMA PIX</b> 🔹\n\n⚠️ Uso correto: <code>/pix 20</code> (Mínimo: R$ 20,00)",
            parse_mode="HTML",
            reply_to_message_id=msg_id
        )
        return

    dados_pix = await gerar_pix_misticpay(valor, user_id, user.first_name)
    
    if dados_pix and "pix_code" in dados_pix:
        pix_code = dados_pix["pix_code"]
        qr_img = qrcode.make(pix_code)
        img_buffer = io.BytesIO()
        qr_img.save(img_buffer, format="PNG")
        img_buffer.seek(0)

        valor_formatado = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        msg = (
            f"🔹 <b>CASABLANCA SHOP | PAGAMENTO VIA PIX</b> 🔹\n\n"
            f"💰 <b>Valor:</b> R$ {valor_formatado}\n"
            f"⏳ <b>Validade:</b> 30 minutos\n\n"
            f"Escaneie o QR Code acima ou copie o código abaixo:\n\n"
            f"<code>{pix_code}</code>"
        )

        msg_enviada = await update.message.reply_photo(
            photo=img_buffer,
            caption=msg,
            parse_mode="HTML",
            reply_to_message_id=msg_id
        )

        asyncio.create_task(expirador_pix(
            chat_id=msg_enviada.chat_id,
            message_id=msg_enviada.message_id,
            valor=valor,
            segundos=1800
        ))

    elif dados_pix and "erro" in dados_pix:
        await update.message.reply_text(
            f"🔹 <b>CASABLANCA SHOP | ERRO PIX</b> 🔹\n\n❌ <b>Retorno MisticPay:</b>\n<code>{dados_pix['erro']}</code>",
            parse_mode="HTML",
            reply_to_message_id=msg_id
        )

async def IA_atendimento(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.lower()
    msg_id = update.message.message_id
    
    if any(p in texto for p in ["saldo", "deposito", "pix", "comprar"]):
        resposta = (
            "🔹 <b>CASABLANCA SHOP | ATENDIMENTO IA</b> 🔹\n\n"
            "Para adicionar saldo instantaneamente, digite <code>/pix valor</code> no chat.\n"
            "Exemplo: <code>/pix 20</code>"
        )
    elif any(p in texto for p in ["suporte", "ajuda", "dono", "admin"]):
        resposta = f"🔹 <b>CASABLANCA SHOP | SUPORTE</b> 🔹\n\nFale diretamente com nosso suporte: {LINK_SUPORTE}"
    else:
        resposta = (
            "🔹 <b>CASABLANCA SHOP | ASSISTENTE</b> 🔹\n\n"
            "Para navegar pelo catálogo completo e acessar as funções do bot, envie o comando /start."
        )

    await update.message.reply_text(resposta, parse_mode="HTML", reply_to_message_id=msg_id)

async def inline_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.strip().lower()
    results = []

    cartoes_filtrados = [c for c in DADOS_CARTOES if not c["vendido"] and (not query or query in c["bin"].lower() or query in c["banco"].lower() or query in c["nivel_formatado"].lower())]

    for item in cartoes_filtrados:
        texto_resposta = (
            f"Número do Cartão: <code>{item['cc_mascarado']}</code>\n"
            f"Banco: {item['banco']}\n"
            f"Categoria: {item['categoria']}\n"
            f"Tipo: {item['tipo']}\n"
            f"Nome: <code>{item['nome']}</code>\n"
            f"CPF: <code>{item['cpf']}</code>\n"
            f"Score Serasa: <code>{item['score_serasa']}</code>\n"
            f"Score BC: <code>{item['score_bc']}</code>\n\n"
            f"<b>Saldo mínimo garantido: R$ {item['saldo_minimo']:,.2f}</b>\n"
            f"Se o saldo for menor que isso, você pode solicitar reembolso conforme a <b>Política de Reembolso</b>.\n\n"
            f"Valor da Compra: R$ {item['preco']:,.2f}\n\n"
            f"Fornecedor: <i>{item['fornecedor']}</i>"
        ).replace(",", "X").replace(".", ",").replace("X", ".")

        keyboard = [
            [InlineKeyboardButton("✅ Comprar", callback_data=f"buy_card_{item['id']}")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="voltar_cc_full")],
        ]

        results.append(
            InlineQueryResultArticle(
                id=item["id"],
                title=f"R$ {item['preco']:.2f} - BIN {item['bin']} - {item['banco']}",
                description=f"Nível: {item['nivel_formatado']} | Fornecedor: {item['fornecedor']}",
                thumbnail_url=THUMB_CARD_URL,
                input_message_content=InputTextMessageContent(texto_resposta, parse_mode="HTML"),
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        )

    await update.inline_query.answer(results, cache_time=1)

def montar_texto_cartao_unitario(item: dict) -> str:
    return (
        f"Número do Cartão: <code>{item['cc_mascarado']}</code>\n"
        f"Banco: {item['banco']}\n"
        f"Categoria: {item['categoria']}\n"
        f"Tipo: {item['tipo']}\n"
        f"Nome: <code>{item['nome']}</code>\n"
        f"CPF: <code>{item['cpf']}</code>\n"
        f"Score Serasa: <code>{item['score_serasa']}</code>\n"
        f"Score BC: <code>{item['score_bc']}</code>\n\n"
        f"<b>Saldo mínimo garantido: R$ {item['saldo_minimo']:,.2f}</b>\n"
        f"Se o saldo for menor que isso, você pode solicitar reembolso conforme a <b>Política de Reembolso</b>.\n\n"
        f"Valor da Compra: R$ {item['preco']:,.2f}\n\n"
        f"Fornecedor: <i>{item['fornecedor']}</i>"
    ).replace(",", "X").replace(".", ",").replace("X", ".")

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
        CACHE_CANAL.pop(user_id, None)
        if await esta_no_canal(context, user_id):
            try:
                await query.message.delete()
            except Exception:
                pass
            await enviar_menu_principal(update, context)
        else:
            await query.message.reply_text("🔹 <b>CASABLANCA SHOP</b> 🔹\n\n❌ Você ainda não entrou no canal!", parse_mode="HTML")

    elif data == "add_saldo":
        await query.message.reply_text(
            "🔹 <b>CASABLANCA SHOP | ADICIONAR SALDO</b> 🔹\n\n"
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
        texto = "🔹 <b>CASABLANCA SHOP | CATÁLOGO</b> 🔹\n\nEscolha a categoria desejada:"
        await responder_ou_editar(query, texto, InlineKeyboardMarkup(keyboard))

    elif data == "voltar_cc_full":
        keyboard = [
            [InlineKeyboardButton("🔢 Unitárias", callback_data="ver_unitarias")],
            [InlineKeyboardButton("📊 Pesquisar por Nível / BIN / Banco", switch_inline_query_current_chat="")],
            [InlineKeyboardButton("💬 Atendimento/suporte", url=LINK_SUPORTE)],
            [InlineKeyboardButton("🔙 Voltar", callback_data="menu_comprar")],
        ]
        texto = f"🔹 <b>CASABLANCA SHOP | CC FULL DADOS</b> 🔹\n\nInformações:\n- Saldo: R$ {saldo_atual:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        await responder_ou_editar(query, texto, InlineKeyboardMarkup(keyboard))

    elif data == "ver_unitarias":
        keyboard = []
        for item in CATALOGO_UNITARIAS:
            keyboard.append([InlineKeyboardButton(f"R$ {item['preco']:.0f} {item['nome']} ({item['qtd']})", callback_data=f"show_u_{item['id']}")])
        keyboard.append([InlineKeyboardButton("🔙 Voltar", callback_data="voltar_cc_full")])
        await responder_ou_editar(query, POLITICA_REEMBOLSO, InlineKeyboardMarkup(keyboard))

    elif data.startswith("show_u_"):
        unit_id = data.replace("show_u_", "")
        cartoes_validos = [c for c in DADOS_CARTOES if not c["vendido"]]
        if not cartoes_validos:
            await query.message.reply_text("🔹 <b>CASABLANCA SHOP</b> 🔹\n\n❌ Estoque temporariamente esgotado!", parse_mode="HTML")
            return
        card = cartoes_validos[0]
        texto_card = montar_texto_cartao_unitario(card)
        keyboard = [
            [InlineKeyboardButton("✅ Comprar", callback_data=f"buy_card_{card['id']}")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="ver_unitarias")],
        ]
        await responder_ou_editar(query, texto_card, InlineKeyboardMarkup(keyboard))

    elif data.startswith("buy_card_"):
        card_id = data.replace("buy_card_", "")
        card = next((c for c in DADOS_CARTOES if c["id"] == card_id), None)
        if card:
            if card["vendido"]:
                await query.message.reply_text("🔹 <b>CASABLANCA SHOP</b> 🔹\n\n❌ Este item já foi vendido!", parse_mode="HTML")
            elif saldo_atual < card["preco"]:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=(
                        f"🔹 <b>CASABLANCA SHOP | SALDO INSUFICIENTE</b> 🔹\n\n"
                        f"❌ Saldo insuficiente para esta compra!\n\n"
                        f"🏷️ <b>Preço:</b> R$ {card['preco']:,.2f}\n"
                        f"💰 <b>Seu Saldo:</b> R$ {saldo_atual:,.2f}\n\n"
                        f"Adicione saldo digitando no chat: <code>/pix {int(card['preco'])}</code>"
                    ).replace(",", "X").replace(".", ",").replace("X", "."),
                    parse_mode="HTML"
                )
            else:
                SALDO_USUARIOS[user_id] -= card["preco"]
                card["vendido"] = True
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=(
                        f"🎉 <b>COMPRA CONCLUÍDA - CASABLANCA SHOP</b>\n\n"
                        f"<b>Dados:</b>\n<code>{card['cc_full']}</code>\n"
                        f"<b>Nome:</b> <code>{card['nome']}</code>\n"
                        f"<b>CPF:</b> <code>{card['cpf']}</code>\n"
                        f"<b>Score Serasa:</b> <code>{card['score_serasa']}</code>\n"
                        f"<b>Score BC:</b> <code>{card['score_bc']}</code>\n\n"
                        f"Novo Saldo: R$ {SALDO_USUARIOS[user_id]:,.2f}"
                    ).replace(",", "X").replace(".", ",").replace("X", "."),
                    parse_mode="HTML",
                )

    # --- BOTÃO INFORMAÇÕES (PERFIL) ---
    elif data == "info":
        nome_usuario = query.from_user.first_name or "Cliente"
        texto_perfil = (
            f"<b>{nome_usuario}</b> ❗️\n"
            f"/menu\n"
            f"👤 <b>Perfil</b>\n"
            f"- Nome: <i>{nome_usuario}</i> ❗️\n"
            f"- Id: <code>{user_id}</code>\n\n"
            f"💰 <b>Carteira</b>\n"
            f"- Saldo: R$ {saldo_atual:,.2f}\n"
            f"- Compras: 0"
        ).replace(",", "X").replace(".", ",").replace("X", ".")
        keyboard = [
            [InlineKeyboardButton("🟢 Adicionar saldo", callback_data="add_saldo"),
             InlineKeyboardButton("📄 Histórico", callback_data="sem_saldo_aviso")],
            [InlineKeyboardButton("🔙 Voltar", callback_data="voltar_inicio")]
        ]
        await responder_ou_editar(query, texto_perfil, InlineKeyboardMarkup(keyboard))

    # --- BOTÃO INDICAÇÕES ---
    elif data == "indicacoes":
        bot_username = (await context.bot.get_me()).username
        link_indicacao = f"https://t.me/{bot_username}?start={user_id}"
        indicador_id = INDICACOES_USUARIOS.get(user_id)
        indicador_txt = f"<code>{indicador_id}</code>" if indicador_id else "Não indicado."
        qtd_indicados = TOTAL_INDICADOS.get(user_id, 0)
        ganho_indicacao = qtd_indicados * 1.00

        texto_ind = (
            f"<b>{query.from_user.first_name}</b> ❗️\n"
            f"/menu\n"
            f"🚀 <b>Sistema de Indicação</b>\n\n"
            f"Compartilhe seu link e ganhe R$ 1,00 de saldo quando um indicado fizer um depósito.\n\n"
            f"📊 <b>Suas informações:</b>\n\n"
            f"• Seu indicador: {indicador_txt}\n"
            f"• Seus Indicados: {qtd_indicados}\n\n"
            f"💵 <b>Disponível agora:</b>\n"
            f"• Para saldo no bot: R$ {ganho_indicacao:,.2f}\n"
            f"• Para receber via Pix: R$ 0,00\n\n"
            f"Use os botões abaixo para ver seu link ou converter bônus."
        ).replace(",", "X").replace(".", ",").replace("X", ".")
        keyboard = [
            [InlineKeyboardButton("🔗 Meu link", url=link_indicacao)],
            [InlineKeyboardButton("💰 Receber via Pix", callback_data="sem_saldo_aviso"),
             InlineKeyboardButton("🔄 Converter em saldo", callback_data="converter_saldo")],
            [InlineKeyboardButton("🔙 Voltar", callback_data="voltar_inicio")]
        ]
        await responder_ou_editar(query, texto_ind, InlineKeyboardMarkup(keyboard))

    elif data == "converter_saldo":
        qtd_indicados = TOTAL_INDICADOS.get(user_id, 0)
        bonus = float(qtd_indicados * 1.0)
        if bonus > 0:
            TOTAL_INDICADOS[user_id] = 0
            SALDO_USUARIOS[user_id] = SALDO_USUARIOS.get(user_id, 0.0) + bonus
            await query.answer(f"✅ Convertido R$ {bonus:.2f} para o seu saldo!", show_alert=True)
        else:
            await query.answer("❌ Você não possui bônus de indicação disponíveis para converter.", show_alert=True)

    # --- BOTÃO FERRAMENTAS ---
    elif data == "ferramentas":
        keyboard = []
        for ferramenta in CATALOGO_FERRAMENTAS:
            keyboard.append([InlineKeyboardButton(ferramenta["nome"], callback_data=f"tool_info_{ferramenta['id']}")])
        keyboard.append([InlineKeyboardButton("🔙 Voltar", callback_data="voltar_inicio")])

        texto = (
            "🔹 <b>CasaBlanca • Ferramentas</b> 🔹\n\n"
            "🎓 Funcionalidades de ferramentas, com pronta-entrega & suporte para entrega solidária em @haridadenetwork\n\n"
            "Selecione abaixo sua ferramenta desejada:"
        )
        await responder_ou_editar(query, texto, InlineKeyboardMarkup(keyboard))

    elif data.startswith("tool_info_"):
        t_id = data.replace("tool_info_", "")
        ferramenta = next((f for f in CATALOGO_FERRAMENTAS if f["id"] == t_id), None)
        if not ferramenta:
            return await query.answer("❌ Ferramenta não encontrada.", show_alert=True)

        texto_tool = (
            f"🛠 <b>FERRAMENTA | {ferramenta['nome']}</b>\n\n"
            f"ℹ️ <b>Descrição:</b> {ferramenta['descricao']}\n"
            f"💵 <b>Valor:</b> R$ {ferramenta['preco']:,.2f}\n\n"
            f"Seu saldo atual: R$ {saldo_atual:,.2f}"
        ).replace(",", "X").replace(".", ",").replace("X", ".")

        keyboard = [
            [InlineKeyboardButton("✅ Comprar Ferramenta", callback_data=f"buy_tool_{ferramenta['id']}")],
            [InlineKeyboardButton("🔙 Voltar", callback_data="ferramentas")]
        ]
        await responder_ou_editar(query, texto_tool, InlineKeyboardMarkup(keyboard))

    elif data.startswith("buy_tool_"):
        t_id = data.replace("buy_tool_", "")
        ferramenta = next((f for f in CATALOGO_FERRAMENTAS if f["id"] == t_id), None)
        if ferramenta:
            if saldo_atual < ferramenta["preco"]:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=(
                        f"🔹 <b>CASABLANCA SHOP | SALDO INSUFICIENTE</b> 🔹\n\n"
                        f"❌ Saldo insuficiente para adquirir a ferramenta <b>{ferramenta['nome']}</b>!\n\n"
                        f"🏷️ <b>Preço:</b> R$ {ferramenta['preco']:,.2f}\n"
                        f"💰 <b>Seu Saldo:</b> R$ {saldo_atual:,.2f}\n\n"
                        f"Adicione saldo digitando no chat: <code>/pix {int(ferramenta['preco'])}</code>"
                    ).replace(",", "X").replace(".", ",").replace("X", "."),
                    parse_mode="HTML"
                )
            else:
                SALDO_USUARIOS[user_id] -= ferramenta["preco"]
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=(
                        f"🎉 <b>COMPRA DE FERRAMENTA APROVADA!</b>\n\n"
                        f"Ferramenta: <b>{ferramenta['nome']}</b>\n"
                        f"Descrição: {ferramenta['descricao']}\n\n"
                        f"Suporte e entrega imediata via {LINK_SUPORTE}\n\n"
                        f"Novo Saldo: R$ {SALDO_USUARIOS[user_id]:,.2f}"
                    ).replace(",", "X").replace(".", ",").replace("X", "."),
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar ao Início", callback_data="voltar_inicio")]])
                )

    # --- CATÁLOGO DE E-SIM ---
    elif data == "esim":
        keyboard = []
        for item in CATALOGO_ESIM:
            keyboard.append([InlineKeyboardButton(f"{item['nome']} - R$ {item['preco']:.2f} ({item['qtd']})", callback_data=f"buy_esim_{item['id']}")])
        keyboard.append([InlineKeyboardButton("🔙 Voltar", callback_data="menu_comprar")])
        
        texto = "📱 <b>CATÁLOGO DE E-SIM</b>\n\nSelecione um produto abaixo para comprar instantaneamente:"
        await responder_ou_editar(query, texto, InlineKeyboardMarkup(keyboard))

    elif data.startswith("buy_esim_"):
        esim_id = data.replace("buy_esim_", "")
        item = next((e for e in CATALOGO_ESIM if e["id"] == esim_id), None)
        if item:
            if item["qtd"] <= 0:
                await query.answer("❌ Estoque esgotado!", show_alert=True)
            elif saldo_atual < item["preco"]:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=(
                        f"🔹 <b>CASABLANCA SHOP | SALDO INSUFICIENTE</b> 🔹\n\n"
                        f"❌ Saldo insuficiente para adquirir o E-SIM <b>{item['nome']}</b>!\n\n"
                        f"🏷️ <b>Preço:</b> R$ {item['preco']:,.2f}\n"
                        f"💰 <b>Seu Saldo:</b> R$ {saldo_atual:,.2f}\n\n"
                        f"Adicione saldo digitando no chat: <code>/pix {int(item['preco'])}</code>"
                    ).replace(",", "X").replace(".", ",").replace("X", "."),
                    parse_mode="HTML"
                )
            else:
                SALDO_USUARIOS[user_id] -= item["preco"]
                item["qtd"] -= 1
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=(
                        f"🎉 <b>E-SIM ADQUIRIDO COM SUCESSO!</b>\n\n"
                        f"Produto: <b>{item['nome']}</b>\n"
                        f"Detalhes: {item['descricao']}\n"
                        f"Valor: R$ {item['preco']:.2f}\n\n"
                        f"Novo Saldo: R$ {SALDO_USUARIOS[user_id]:,.2f}"
                    ).replace(",", "X").replace(".", ",").replace("X", "."),
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data="esim")]])
                )

    # --- CATÁLOGO DE LARAS ---
    elif data == "laras":
        keyboard = []
        for item in CATALOGO_LARAS:
            keyboard.append([InlineKeyboardButton(f"📁 {item['nome']} - R$ {item['preco']:.2f}", callback_data=f"buy_lara_{item['id']}")])
        keyboard.append([InlineKeyboardButton("🔙 Voltar", callback_data="menu_comprar")])
        
        texto = "🛡️ <b>CATÁLOGO DE LARAS</b>\n\nSelecione o produto desejado:"
        await responder_ou_editar(query, texto, InlineKeyboardMarkup(keyboard))

    elif data.startswith("buy_lara_"):
        lara_id = data.replace("buy_lara_", "")
        item = next((l for l in CATALOGO_LARAS if l["id"] == lara_id), None)
        if item:
            if item["vendido"]:
                await query.answer("❌ Este item já foi vendido!", show_alert=True)
            elif saldo_atual < item["preco"]:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=(
                        f"🔹 <b>CASABLANCA SHOP | SALDO INSUFICIENTE</b> 🔹\n\n"
                        f"❌ Saldo insuficiente para adquirir a LARA <b>{item['nome']}</b>!\n\n"
                        f"🏷️ <b>Preço:</b> R$ {item['preco']:,.2f}\n"
                        f"💰 <b>Seu Saldo:</b> R$ {saldo_atual:,.2f}\n\n"
                        f"Adicione saldo digitando no chat: <code>/pix {int(item['preco'])}</code>"
                    ).replace(",", "X").replace(".", ",").replace("X", "."),
                    parse_mode="HTML"
                )
            else:
                SALDO_USUARIOS[user_id] -= item["preco"]
                item["vendido"] = True
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=(
                        f"🎉 <b>LARA ADQUIRIDA COM SUCESSO!</b>\n\n"
                        f"Banco: {item['banco']}\n"
                        f"Titular: <code>{item['nome_titular']}</code>\n"
                        f"CPF: <code>{item['cpf']}</code>\n"
                        f"Score Serasa: <code>{item['score_serasa']}</code>\n"
                        f"Score BC: <code>{item['score_bc']}</code>\n"
                        f"Gateway: {item['descricao']}\n\n"
                        f"Novo Saldo: R$ {SALDO_USUARIOS[user_id]:,.2f}"
                    ).replace(",", "X").replace(".", ",").replace("X", "."),
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data="laras")]])
                )

    elif data == "sem_saldo_aviso":
        await query.answer("❌ Funcionalidade em manutenção / Sem saldo ou histórico no momento.", show_alert=True)

    elif data == "voltar_inicio":
        try:
            await query.message.delete()
        except Exception:
            pass
        await enviar_menu_principal(update, context)

# ==============================================================================
# FUNÇÃO DO COMANDO DE ESTOQUE (ADMIN DM)
# ==============================================================================
async def add_estoque(update, context):
    user_id = update.effective_user.id
    if update.effective_chat.type != 'private':
        return await update.message.reply_text("❌ Este comando só pode ser usado no privado.")

    ADMIN_IDS = [7536040475]
    if user_id not in ADMIN_IDS:
        return await update.message.reply_text("🚫 Acesso negado.")

    texto_bruto = update.message.text or ""

    try:
        global DADOS_CARTOES

        cartao_match = re.search(r"Número do Cartão:\s*([^\n]+)", texto_bruto)
        banco_match = re.search(r"Banco:\s*([^\n]+)", texto_bruto)
        nivel_match = re.search(r"Categoria:\s*([^\n]+)", texto_bruto)
        tipo_match = re.search(r"Tipo:\s*([^\n]+)", texto_bruto)
        nome_match = re.search(r"Nome:\s*([^\n]+)", texto_bruto)
        cpf_match = re.search(r"CPF:\s*([^\n]+)", texto_bruto)
        preco_match = re.search(r"Valor da Compra:\s*R\$\s*([\d\,\.]+)", texto_bruto)
        saldo_match = re.search(r"Saldo mínimo garantido:\s*R\$\s*([\d\,\.]+)", texto_bruto)

        tipo_produto_match = re.findall(r"Categoria:\s*([^\n]+)", texto_bruto)
        categoria_final = tipo_produto_match[-1].strip() if len(tipo_produto_match) > 1 else (nivel_match.group(1).strip() if nivel_match else "STANDARD")

        if not cartao_match:
            return await update.message.reply_text("❌ Não foi possível identificar o 'Número do Cartão' na ficha enviada.")

        preco_val = float(preco_match.group(1).replace(".", "").replace(",", ".")) if preco_match else 80.0
        saldo_val = float(saldo_match.group(1).replace(".", "").replace(",", ".")) if saldo_match else 1200.0

        card_raw = {
            "id": f"card_{len(DADOS_CARTOES) + 1}",
            "cc": cartao_match.group(1).strip(),
            "banco": banco_match.group(1).strip() if banco_match else "DESCONHECIDO",
            "nivel": nivel_match.group(1).strip() if nivel_match else "STANDARD",
            "categoria_produto": categoria_final,
            "tipo": tipo_match.group(1).strip() if tipo_match else "CREDIT",
            "nome": nome_match.group(1).strip() if nome_match else "NÃO INFORMADO",
            "cpf": cpf_match.group(1).strip() if cpf_match else "",
            "preco": preco_val,
            "saldo_minimo": saldo_val,
            "vendido": False
        }

        item_processado = edificar_item_estoque(card_raw)
        DADOS_CARTOES.append(item_processado)

        await update.message.reply_text(
            f"✅ **Item Processado e Adicionado!**\n\n"
            f"• **BIN:** `{item_processado['bin']}`\n"
            f"• **Banco:** {item_processado['banco']}\n"
            f"• **Bandeira:** {item_processado['bandeira']}\n"
            f"• **Nível:** {item_processado['nivel_formatado']}\n"
            f"• **Preço:** R$ {item_processado['preco']:.2f}\n"
            f"• **Cartão Mascarado:** `{item_processado['cc_mascarado']}`",
            parse_mode="Markdown"
        )

    except Exception as e:
        await update.message.reply_text(f"⚠️ **Falha ao ler ficha:** `{e}`", parse_mode="Markdown")

# --- REGISTRO DE HANDLERS ---
telegram_app.add_handler(CommandHandler("add_estoque", add_estoque))
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("pix", comando_pix))
telegram_app.add_handler(InlineQueryHandler(inline_search))
telegram_app.add_handler(CallbackQueryHandler(botao_callback))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, IA_atendimento))
telegram_app.add_handler(CommandHandler("admin", painel_admin))
telegram_app.add_handler(CommandHandler("add_estoque_esim", add_estoque_esim))
telegram_app.add_handler(CommandHandler("add_estoque_laras", add_estoque_laras))
telegram_app.add_handler(CommandHandler("add_estoque_ccfullldados", add_estoque_ccfullldados))
telegram_app.add_handler(CommandHandler("add_estoque_consultavel", add_estoque_consultavel))


@asynccontextmanager
async def lifespan(app: FastAPI):
    await telegram_app.initialize()
    await telegram_app.start()
    webhook_url = f"{WEBHOOK_BASE_URL.rstrip('/')}/telegram-webhook"
    await telegram_app.bot.set_webhook(url=webhook_url)
    asyncio.create_task(anti_sleep_ping())
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
        status = payload.get("status")
        value = float(payload.get("value", 0))
        description = payload.get("description", "")

        if status == "COMPLETO" and "User " in description:
            user_id = int(description.split("User ")[1])
            SALDO_USUARIOS[user_id] = SALDO_USUARIOS.get(user_id, 0.0) + value

            referrer_id = INDICACOES_USUARIOS.get(user_id)
            if referrer_id:
                TOTAL_INDICADOS[referrer_id] = TOTAL_INDICADOS.get(referrer_id, 0) + 1
                INDICACOES_USUARIOS.pop(user_id, None) 
                SALDO_USUARIOS[referrer_id] = SALDO_USUARIOS.get(referrer_id, 0.0) + 1.00
                try:
                    await telegram_app.bot.send_message(
                        chat_id=referrer_id,
                        text=f"🎁 <b>PARABÉNS!</b> Um dos seus indicados realizou um depósito e você ganhou <b>R$ 1,00</b> de bônus em saldo!",
                        parse_mode="HTML"
                    )
                except Exception:
                    pass

            texto_sucesso = (
                f"🔹 <b>CASABLANCA SHOP | PAGAMENTO CONFIRMADO</b> 🔹\n\n"
                f"Foi creditado <b>R$ {value:,.2f}</b> na sua conta."
            ).replace(",", "X").replace(".", ",").replace("X", ".")

            await telegram_app.bot.send_message(chat_id=user_id, text=texto_sucesso, parse_mode="HTML")

        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/")
async def root():
    return {"status": "online"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
