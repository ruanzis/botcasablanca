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

LINK_CANAL_VERIFICACAO = "[https://t.me/oficialharidade](https://t.me/oficialharidade)"
LINK_CANAL = os.getenv("LINK_CANAL", "[https://t.me/+qrh5SObhV3xmODhh](https://t.me/+qrh5SObhV3xmODhh)")
LINK_SUPORTE = "[https://t.me/haridadenetwork](https://t.me/haridadenetwork)"
CAPA_PATH = "capa.jpg"

THUMB_CARD_URL = "[https://i.postimg.cc/9Fdfb4MV/Design-sem-nome.png](https://i.postimg.cc/9Fdfb4MV/Design-sem-nome.png)"

MISTICPAY_CLIENT_ID = os.getenv("MISTICPAY_CLIENT_ID", "ci_g35d35pglvgsj39")
MISTICPAY_CLIENT_SECRET = os.getenv("MISTICPAY_CLIENT_SECRET", "cs_xmi6kbhukucgc1syoymxugk3h")
WEBHOOK_BASE_URL = os.getenv("WEBHOOK_BASE_URL", "[https://botcasablanca.onrender.com](https://botcasablanca.onrender.com)")

ADMIN_ID = 7536040475
ADMIN_IDS = [7536040475]

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
USUARIOS_REGISTRADOS = set()
KEYS_GERADAS = {}        # {codigo: dados}
GIFTS_GERADOS = {}       # Nova variável global para gifts de saldo
PREVIEW_NOTIFICACAO = {} # Nova variável global para a IA do notificar

# --- CATÁLOGOS DINÂMICOS ---
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
        "nome": "🛸 Burlador de Selfie IA",
        "descricao": "Ferramenta eficaz para remoção de prev, facial, krunk e invasão de contas bancárias.",
        "preco": 150.00
    }
]

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
    }
]

CATALOGO_CONSULTAVEL = []
CATALOGO_LOGINS = []
CATALOGO_CCAUXILIAR = []

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
        # Categoria Produto salva a real para separar certinho nos catálogos
        "categoria_produto": card_raw.get("categoria_produto", card_raw.get("categoria", "STANDARD")).upper(),
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
        "categoria": "PLATINUM",
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

# Esvaziado para ler em Tempo Real do banco de DADOS_CARTOES acima (Correção Bug 1)
CATALOGO_UNITARIAS = []

# ==============================================================================
# FUNÇÕES DE NAVEGAÇÃO E PAGINAÇÃO
# ==============================================================================

def gerenciar_paginacao_botoes(lista_itens, pagina_atual, itens_por_pagina, prefixo_nav, callback_compra):
    total = len(lista_itens)
    inicio = pagina_atual * itens_por_pagina
    fim = inicio + itens_por_pagina
    fatia = lista_itens[inicio:fim]

    keyboard = []
    for item in fatia:
        nome = item.get("nome") or item.get("cc_mascarado") or "Produto"
        preco = item.get("preco", 0.0)
        qtd = f" ({item['qtd']})" if "qtd" in item else ""
        keyboard.append([InlineKeyboardButton(f"{nome} - R$ {preco:.2f}{qtd}", callback_data=f"{callback_compra}_{item['id']}")])

    nav = []
    if pagina_atual > 0:
        nav.append(InlineKeyboardButton("◀️ Anterior", callback_data=f"{prefixo_nav}_page_{pagina_atual - 1}"))
    if fim < total:
        nav.append(InlineKeyboardButton("Próximo ▶️", callback_data=f"{prefixo_nav}_page_{pagina_atual + 1}"))

    if nav:
        keyboard.append(nav)

    return keyboard

# ==============================================================================
# SISTEMA DE KEYS & GIFTS ADMINISTRATIVO
# ==============================================================================

async def comando_gerar_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS and user_id != ADMIN_ID:
        await update.message.reply_text("❌ Acesso negado. Apenas administradores podem criar keys.")
        return

    texto = update.message.text.replace("/gerar_key", "").strip()
    if not texto:
        await update.message.reply_text(
            "⚠️ Envie os dados no formato correto pós o comando.\n\nExemplo:\n"
            "/gerar_key Numero: 5358 0781 1289 7445\nTitular: Letícia Carvalho\nValidade: 09/27\nCVV: 492\nBanco: Safra\nBandeira: MASTERCARD\nTipo: BLACK\nBase: Infinity\nBIN: 535807\nCPF: 204.886.542-48\nData Nasc: 02/03/1967"
        )
        return

    patterns = {
        "numero": r"Numero:\s*(.*)",
        "titular": r"Titular:\s*(.*)",
        "validade": r"Validade:\s*(.*)",
        "cvv": r"CVV:\s*(.*)",
        "banco": r"Banco:\s*(.*)",
        "bandeira": r"Bandeira:\s*(.*)",
        "tipo": r"Tipo:\s*(.*)",
        "base": r"Base:\s*(.*)",
        "bin": r"BIN:\s*(.*)",
        "cpf": r"CPF:\s*(.*)",
        "data_nasc": r"Data Nasc:\s*(.*)"
    }
    data = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, texto, re.IGNORECASE)
        data[key] = match.group(1).strip() if match else "Não informado"

    codigo = f"KEY-{random.randint(100000, 999999)}"
    data["resgatado"] = False
    KEYS_GERADAS[codigo] = data

    await update.message.reply_text(
        f"✅ Key gerada com sucesso!\n\nCódigo de resgate: <code>{codigo}</code>\n\nPara resgatar, qualquer pessoa pode usar:\n<code>/key {codigo}</code>", 
        parse_mode="HTML"
    )

async def comando_resgatar_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Envie o código da key. Exemplo: /key KEY-123456")
        return
    
    codigo = context.args[0].strip()
    
    if codigo not in KEYS_GERADAS:
        await update.message.reply_text("❌ Key inválida ou não encontrada.")
        return
        
    if KEYS_GERADAS[codigo].get("resgatado"):
        await update.message.reply_text("❌ Esta key já foi resgatada.")
        return
        
    KEYS_GERADAS[codigo]["resgatado"] = True
    d = KEYS_GERADAS[codigo]
    
    mensagem = (
        "✅ Cartão comprado com Sucesso!\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "💳 DADOS DO FULL\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🔢 Número: {d['numero']}\n"
        f"👤 Titular: {d['titular']}\n"
        f"📅 Validade: {d['validade']}\n"
        f"🔐 CVV: {d['cvv']}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📊 INFORMAÇÕES\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🏦 Banco: {d['banco']}\n"
        f"💎 Bandeira: {d['bandeira']}\n"
        f"⭐ Tipo: {d['tipo']}\n"
        f"🌟 Base: {d['base']}\n"
        f"🔢 BIN: {d['bin']}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🔒 DADOS BLOQUEADOS\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📄 CPF: {d['cpf']}\n"
        f"🎂 Data Nasc: {d['data_nasc']}\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "💰 Cartão Resgatado com sucesso!"
    )
    
    await update.message.reply_text(mensagem)

# Nova funcionalidade de Gift
async def comando_gerar_gift(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS and user_id != ADMIN_ID:
        return await update.message.reply_text("❌ Acesso negado. Apenas administradores podem criar gifts.")

    texto = update.message.text.replace("/gerar_gift", "").strip()
    match = re.search(r"valor:\s*([\d\.\,]+)\s*quantidade:\s*(\d+)", texto, re.IGNORECASE)
    
    if not match:
        return await update.message.reply_text("⚠️ Formato inválido. Use:\n/gerar_gift valor: 50 quantidade: 1")
        
    valor = float(match.group(1).replace(",", "."))
    qtd = int(match.group(2))
    
    # Gerando código único
    letras_numeros = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    codigo = "".join(random.choices(letras_numeros, k=7))
    
    GIFTS_GERADOS[codigo] = {
        "valor": valor,
        "quantidade": qtd,
        "usos": 0,
        "resgatados_por": []
    }
    
    msg = (
        f"✅ Gift gerado com sucesso!\n\n"
        f"🎁 <b>Código:</b> <code>{codigo}</code>\n"
        f"💰 <b>Valor:</b> R$ {valor:.2f}\n"
        f"🔄 <b>Quantidade:</b> {qtd}\n\n"
        f"Para resgatar, use:\n<code>/gift {codigo}</code>"
    )
    await update.message.reply_text(msg, parse_mode="HTML")

async def comando_resgatar_gift(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        return await update.message.reply_text("⚠️ Envie o código do gift. Exemplo: /gift P0L8340")
        
    codigo = context.args[0].strip()
    
    if codigo not in GIFTS_GERADOS:
        return await update.message.reply_text("❌ Gift inválido ou não encontrado.")
        
    gift = GIFTS_GERADOS[codigo]
    
    if user_id in gift["resgatados_por"]:
        return await update.message.reply_text("❌ Você já resgatou este gift!")
        
    if gift["usos"] >= gift["quantidade"]:
        return await update.message.reply_text("❌ Este gift já atingiu o limite de resgates.")
        
    # Adicionando o saldo
    saldo_antigo = SALDO_USUARIOS.get(user_id, 0.0)
    SALDO_USUARIOS[user_id] = saldo_antigo + gift["valor"]
    
    gift["usos"] += 1
    gift["resgatados_por"].append(user_id)
    
    msg = (
        f"✅ Gift card resgatado com sucesso!\n\n"
        f"💰 Valor adicionado: R$ {gift['valor']:.2f}\n"
        f"💳 Novo saldo: R$ {SALDO_USUARIOS[user_id]:.2f}"
    )
    await update.message.reply_text(msg)

# ==============================================================================
# NOTIFICAÇÃO GLOBAL (Atualizada para IA Funcionalidade Nova)
# ==============================================================================

async def comando_notificar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS and user_id != ADMIN_ID:
        return await update.message.reply_text("🚫 Acesso negado.")

    # Verifica se é reply para salvar no cache
    if update.message.reply_to_message:
        PREVIEW_NOTIFICACAO[user_id] = {"tipo": "reply", "msg_obj": update.message.reply_to_message}
    else:
        html_text = update.message.caption_html if update.message.photo else update.message.text_html
        html_text = html_text or ""
        html_text = re.sub(r"^/notificar\s*", "", html_text, flags=re.IGNORECASE).strip()

        if not html_text and not update.message.photo:
            return await update.message.reply_text("⚠️ Envie a mensagem após o comando (com ou sem foto) ou responda a uma mensagem com /notificar.", parse_mode="HTML")

        photo_id = update.message.photo[-1].file_id if update.message.photo else None
        PREVIEW_NOTIFICACAO[user_id] = {"tipo": "direto", "texto": html_text, "foto": photo_id}

    keyboard = [
        [InlineKeyboardButton("✅ Confirmar Postagem", callback_data="conf_notif")],
        [InlineKeyboardButton("✏️ Editar / Cancelar", callback_data="canc_notif")]
    ]
    
    await update.message.reply_text("👀 <b>PRÉVIA DA MENSAGEM GERADA PELA IA:</b>\nVerifique como ficou e escolha uma opção abaixo:", parse_mode="HTML")
    
    if PREVIEW_NOTIFICACAO[user_id]["tipo"] == "reply":
        await PREVIEW_NOTIFICACAO[user_id]["msg_obj"].copy(chat_id=user_id, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        if PREVIEW_NOTIFICACAO[user_id]["foto"]:
            await context.bot.send_photo(chat_id=user_id, photo=PREVIEW_NOTIFICACAO[user_id]["foto"], caption=PREVIEW_NOTIFICACAO[user_id]["texto"], parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await context.bot.send_message(chat_id=user_id, text=PREVIEW_NOTIFICACAO[user_id]["texto"], parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

async def comando_remover_estoque(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS and user_id != ADMIN_ID:
        return await update.message.reply_text("🚫 Acesso negado.")

    await exibir_painel_remocao(update, context, page=0)

async def exibir_painel_remocao(update_or_query, context, page=0, itens_por_pagina=5):
    todos_itens = []
    for c in DADOS_CARTOES:
        if not c.get("vendido"):
            todos_itens.append({"id": c["id"], "tipo": "CC Full", "nome": f"{c['banco']} - {c['bin']}", "cat": "cartoes"})
    for e in CATALOGO_ESIM:
        if not e.get("vendido"):
            todos_itens.append({"id": e["id"], "tipo": "E-SIM", "nome": e["nome"], "cat": "esim"})
    for l in CATALOGO_LARAS:
        if not l.get("vendido"):
            todos_itens.append({"id": l["id"], "tipo": "Lara", "nome": l["nome"], "cat": "laras"})
    for c in CATALOGO_CONSULTAVEL:
        if not c.get("vendido"):
            todos_itens.append({"id": c["id"], "tipo": "Consultavel", "nome": c["nome"], "cat": "consultavel"})
    for lg in CATALOGO_LOGINS:
        if not lg.get("vendido"):
            todos_itens.append({"id": lg["id"], "tipo": "Login", "nome": lg["nome"], "cat": "logins"})
    for ca in CATALOGO_CCAUXILIAR:
        if not ca.get("vendido"):
            todos_itens.append({"id": ca["id"], "tipo": "CC Auxiliar", "nome": ca["nome"], "cat": "ccaux"})

    if not todos_itens:
        texto = "📦 <b>Gerenciamento de Estoque</b>\n\nNenhum item em estoque no momento."
        if hasattr(update_or_query, "message") and update_or_query.message:
            await update_or_query.message.reply_text(texto, parse_mode="HTML")
        elif hasattr(update_or_query, "edit_message_text"):
            await update_or_query.edit_message_text(texto, parse_mode="HTML")
        return

    total_paginas = (len(todos_itens) + itens_por_pagina - 1) // itens_por_pagina
    page = max(0, min(page, total_paginas - 1))

    inicio = page * itens_por_pagina
    fim = inicio + itens_por_pagina
    fatia = todos_itens[inicio:fim]

    texto = f"📦 <b>PAINEL DE REMOÇÃO DE ESTOQUE</b> (Página {page+1}/{total_paginas})\n\nSelecione um item para remover permanentemente:"
    keyboard = []

    for item in fatia:
        keyboard.append([
            InlineKeyboardButton(f"❌ [{item['tipo']}] {item['nome']}", callback_data=f"del_item_{item['cat']}_{item['id']}")
        ])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️ Anterior", callback_data=f"rem_page_{page-1}"))
    if page < total_paginas - 1:
        nav.append(InlineKeyboardButton("Próximo ▶️", callback_data=f"rem_page_{page+1}"))

    if nav:
        keyboard.append(nav)

    reply_markup = InlineKeyboardMarkup(keyboard)

    if hasattr(update_or_query, "message") and update_or_query.message and not hasattr(update_or_query, "data"):
        await update_or_query.message.reply_text(texto, reply_markup=reply_markup, parse_mode="HTML")
    else:
        await update_or_query.edit_message_text(texto, reply_markup=reply_markup, parse_mode="HTML")

# ==============================================================================
# INSERÇÃO DINÂMICA DE ESTOQUE POR COMANDOS ADMINISTRATIVOS
# ==============================================================================

async def painel_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS and user_id != ADMIN_ID: return
    
    texto = (
        "👨‍💻 <b>PAINEL ADMINISTRATIVO COMPLETO</b>\n\n"
        "<b>Comandos de Inserção de Estoque:</b>\n"
        "<code>/add_estoque_ccfullldados</code> - Add CC Full (Lote/Único)\n"
        "<code>/add_estoque_esim</code> - Add E-SIM\n"
        "<code>/add_estoque_laras</code> - Add Laras\n"
        "<code>/add_estoque_consultavel</code> - Add Consultável\n"
        "<code>/add_estoque_logins</code> - Add Logins\n"
        "<code>/add_estoque_ccauxiliar</code> - Add CC Auxiliar\n\n"
        "<b>Outros Comandos:</b>\n"
        "<code>/gerar_key</code> - Gerar Key de Resgate\n"
        "<code>/gerar_gift</code> - Gerar Gift de Saldo\n"
        "<code>/notificar</code> - Mandar mensagem geral (Com Prévia IA)\n"
        "<code>/remover_estoque</code> - Menu interativo de remoção"
    )
    await update.message.reply_text(texto, parse_mode="HTML")

async def add_estoque_esim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS and user_id != ADMIN_ID: return
    
    texto = update.message.text.replace("/add_estoque_esim", "").strip()
    if not texto:
        return await update.message.reply_text("❌ Envie o formato: <code>/add_estoque_esim Nome | Descrição | Preço</code>", parse_mode="HTML")
    
    partes = [p.strip() for p in texto.split("|")]
    nome = partes[0]
    desc = partes[1] if len(partes) > 1 else "Conexão imediata"
    preco = float(partes[2].replace("R$", "").replace(",", ".").strip()) if len(partes) > 2 else 35.0

    item_id = f"esim_{len(CATALOGO_ESIM) + 1}_{random.randint(100,999)}"
    CATALOGO_ESIM.append({
        "id": item_id,
        "nome": nome,
        "descricao": desc,
        "preco": preco,
        "qtd": 1,
        "vendido": False
    })
    await update.message.reply_text(f"✅ <b>E-SIM adicionado com sucesso ao catálogo!</b>\n\n📱 {nome} - R$ {preco:.2f}", parse_mode="HTML")

async def add_estoque_laras(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS and user_id != ADMIN_ID: return

    texto = update.message.text.replace("/add_estoque_laras", "").strip()
    if not texto:
        return await update.message.reply_text("❌ Envie o formato: <code>/add_estoque_laras Nome | Banco | Titular | CPF | Preço</code>", parse_mode="HTML")

    partes = [p.strip() for p in texto.split("|")]
    nome = partes[0]
    banco = partes[1] if len(partes) > 1 else "VOLTPIX"
    titular = partes[2] if len(partes) > 2 else "NÃO INFORMADO"
    cpf = partes[3] if len(partes) > 3 else "00000000000"
    preco = float(partes[4].replace("R$", "").replace(",", ".").strip()) if len(partes) > 4 else 100.0

    item_id = f"lara_{len(CATALOGO_LARAS) + 1}_{random.randint(100,999)}"
    CATALOGO_LARAS.append({
        "id": item_id,
        "nome": nome,
        "banco": banco,
        "categoria": "PF/PJ",
        "tipo": "BEP20",
        "nome_titular": titular,
        "cpf": cpf,
        "score_serasa": 750,
        "score_bc": 800,
        "descricao": f"{banco} - 0 MED E SAQUES",
        "preco": preco,
        "vendido": False
    })
    await update.message.reply_text(f"✅ <b>Lara adicionada com sucesso ao catálogo!</b>\n\n🛡️ {nome} - R$ {preco:.2f}", parse_mode="HTML")

async def add_estoque_ccfullldados(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await add_estoque(update, context)

async def add_estoque_consultavel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS and user_id != ADMIN_ID: return

    texto = update.message.text.replace("/add_estoque_consultavel", "").strip()
    if not texto:
        return await update.message.reply_text("❌ Envie o formato: <code>/add_estoque_consultavel Nome | Descrição | Preço</code>", parse_mode="HTML")

    partes = [p.strip() for p in texto.split("|")]
    nome = partes[0]
    desc = partes[1] if len(partes) > 1 else "Consultável completo"
    preco = float(partes[2].replace("R$", "").replace(",", ".").strip()) if len(partes) > 2 else 50.0

    item_id = f"cons_{len(CATALOGO_CONSULTAVEL) + 1}_{random.randint(100,999)}"
    CATALOGO_CONSULTAVEL.append({
        "id": item_id,
        "nome": nome,
        "descricao": desc,
        "preco": preco,
        "vendido": False
    })
    await update.message.reply_text(f"✅ <b>Consultável adicionado com sucesso ao catálogo!</b>\n\n📁 {nome} - R$ {preco:.2f}", parse_mode="HTML")

async def add_estoque_logins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS and user_id != ADMIN_ID: return

    texto = update.message.text.replace("/add_estoque_logins", "").strip()
    if not texto:
        return await update.message.reply_text("❌ Envie o formato: <code>/add_estoque_logins Nome | Descrição | Preço</code>", parse_mode="HTML")

    partes = [p.strip() for p in texto.split("|")]
    nome = partes[0]
    desc = partes[1] if len(partes) > 1 else "Acesso exclusivo"
    preco = float(partes[2].replace("R$", "").replace(",", ".").strip()) if len(partes) > 2 else 40.0

    item_id = f"login_{len(CATALOGO_LOGINS) + 1}_{random.randint(100,999)}"
    CATALOGO_LOGINS.append({
        "id": item_id,
        "nome": nome,
        "descricao": desc,
        "preco": preco,
        "vendido": False
    })
    await update.message.reply_text(f"✅ <b>Login adicionado com sucesso ao catálogo!</b>\n\n🗽 {nome} - R$ {preco:.2f}", parse_mode="HTML")

async def add_estoque_ccauxiliar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS and user_id != ADMIN_ID: return

    texto = update.message.text.replace("/add_estoque_ccauxiliar", "").strip()
    if not texto:
        return await update.message.reply_text("❌ Envie o formato: <code>/add_estoque_ccauxiliar Nome | Descrição | Preço</code>", parse_mode="HTML")

    partes = [p.strip() for p in texto.split("|")]
    nome = partes[0]
    desc = partes[1] if len(partes) > 1 else "CC Auxiliar"
    preco = float(partes[2].replace("R$", "").replace(",", ".").strip()) if len(partes) > 2 else 30.0

    item_id = f"ccaux_{len(CATALOGO_CCAUXILIAR) + 1}_{random.randint(100,999)}"
    CATALOGO_CCAUXILIAR.append({
        "id": item_id,
        "nome": nome,
        "descricao": desc,
        "preco": preco,
        "vendido": False
    })
    await update.message.reply_text(f"✅ <b>CC Auxiliar adicionado com sucesso ao catálogo!</b>\n\n💳 {nome} - R$ {preco:.2f}", parse_mode="HTML")

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
    url = "[https://api.misticpay.com/api/transactions/create](https://api.misticpay.com/api/transactions/create)"
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
    USUARIOS_REGISTRADOS.add(user_id)
    msg_id = update.message.message_id
    
    # Verificação de grupo/canal
    if update.effective_chat.type in ['group', 'supergroup', 'channel']:
        me = await context.bot.get_me()
        keyboard = [[InlineKeyboardButton("💬 Conversar no Privado", url=f"[https://t.me/](https://t.me/){me.username}?start=true")]]
        await update.message.reply_text(
            "👋 <b>Olá! Eu sou o Casablanca Bot.</b>\n\n"
            "Para utilizar minhas funcionalidades e navegar pelo catálogo completo, por favor, me chame no privado!",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        return

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
    texto = update.
