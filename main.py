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
import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

# Carrega variáveis locais de um arquivo .env se você estiver testando no seu computador
load_dotenv()

# Pega o conteúdo do JSON que estará salvo nas configurações do servidor/GitHub Actions
firebase_config_str = os.getenv("FIREBASE_CREDENTIALS_JSON")

if firebase_config_str:
    # Se a variável existir (usado no servidor/produção)
    cred_dict = json.loads(firebase_config_str)
    cred = credentials.Certificate(cred_dict)
else:
    # Se estiver rodando localmente no seu PC usando o arquivo JSON direto
    cred = credentials.Certificate("firebase_key.json")

firebase_admin.initialize_app(cred)
db = firestore.client()

# Teste rápido de conexão com o Firestore
try:
    print("Conexão com o Firebase Firestore estabelecida com sucesso!")
except Exception as e:
    print(f"Erro ao conectar com o Firebase: {e}")
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

# Link Direto extraído da sua imagem no Postimages
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
# estoque.py
# --- FUNÇÃO DE LEITURA E PARSER INTELIGENTE DO CARTÃO ---
import re

def extrair_dados_cartao(texto):
    """
    Lê o texto do cartão enviado e extrai as informações estruturadas
    exatamente no formato exigido para salvar no Firestore.
    """
    def pegar(padrao, texto_base, tipo=str, default=None):
        match = re.search(padrao, texto_base, re.IGNORECASE)
        if match:
            val = match.group(1).strip()
            if val.upper() in ["N/D", "ND", "NAO INFORMADO", "-"]:
                return default
            if tipo == float:
                val_limpo = val.replace("R$", "").replace(".", "").replace(",", ".").strip()
                try:
                    return float(val_limpo)
                except ValueError:
                    return default
            return val
        return default

    cartao_dict = {
        "bin": pegar(r"Número do Cartão:\s*(.+)", texto),
        "banco": pegar(r"Banco:\s*(.+)", texto),
        "categoria": pegar(r"Categoria:\s*(.+)", texto),
        "tipo": pegar(r"Tipo:\s*(.+)", texto),
        "nome": pegar(r"Nome:\s*(.+)", texto),
        "cpf": pegar(r"CPF:\s*([\d\.\-]+)", texto),
        "score_serasa": pegar(r"Score Serasa:\s*(.+)", texto),
        "score_bc": pegar(r"Score BC:\s*(\d+)", texto, int),
        "preco": pegar(r"Valor da Compra:\s*R\$\s*([\d\.,]+)", texto),
        "limite_garantido": pegar(r"Saldo mínimo garantido:\s*R\$\s*([\d\.,]+)", texto, float),
        "posicao": pegar(r"(Cartão\s*\d+\s*de\s*\d+)", texto)
    }
    
    return cartao_dict
---------------------------------------------------------
estoque_novos_cartoes = [
    {
        "cartao": "470598******8057",
        "banco": "ITAU UNIBANCO, S.A.",
        "categoria": "PLATINUM",
        "tipo": "Crédito",
        "nome": "ROSIANE MARINHO DE CARVALHO",
        "cpf": "49685007420",
        "score_serasa": 129,
        "score_bc": 542,
        "preco": "80,00",
        "limite_garantido": 1200.00,
        "posicao": "62 de 520"
    },
    {
        "cartao": "489391******2990",
        "banco": "ITAU UNIBANCO, S.A.",
        "categoria": "PLATINUM",
        "tipo": "Crédito",
        "nome": "MAURICIO BARBOSA CHAGAS",
        "cpf": "22638482315",
        "score_serasa": 858,
        "score_bc": 438,
        "preco": "80,00",
        "limite_garantido": 1200.00,
        "posicao": "63 de 520"
    },
    {
        "cartao": "498401******5730",
        "banco": "BANCO DO BRASIL, S.A.",
        "categoria": "PLATINUM",
        "tipo": "Crédito",
        "nome": "AUTONOMESTA BENICIO COELHO",
        "cpf": "07795041353",
        "score_serasa": 59,
        "score_bc": 25,
        "preco": "80,00",
        "limite_garantido": 1200.00,
        "posicao": "64 de 520"
    },
    {
        "cartao": "400497******3960",
        "banco": "BANCO LAFISE BANCENTRO",
        "categoria": "PLATINUM",
        "tipo": "Crédito",
        "nome": "LUCIANO NEUMANN",
        "cpf": "64175782087",
        "score_serasa": None,
        "score_bc": 200,
        "preco": "80,00",
        "limite_garantido": 1200.00,
        "posicao": "65 de 520"
    },
    {
        "cartao": "470598******4516",
        "banco": "ITAU UNIBANCO, S.A.",
        "categoria": "PLATINUM",
        "tipo": "Crédito",
        "nome": "VIVIANE BACHMANN",
        "cpf": "96957050904",
        "score_serasa": None,
        "score_bc": 862,
        "preco": "80,00",
        "limite_garantido": 1200.00,
        "posicao": "66 de 520"
    },
    {
        "cartao": "523431******4504",
        "banco": "ITAU UNIBANCO, S.A.",
        "categoria": "PLATINUM",
        "tipo": "Crédito",
        "nome": "SILVANA APARECIDA ULBRICH",
        "cpf": "04318683958",
        "score_serasa": None,
        "score_bc": 523,
        "preco": "80,00",
        "limite_garantido": 1200.00,
        "posicao": "67 de 520"
    },
    {
        "cartao": "470598******5916",
        "banco": "ITAU UNIBANCO, S.A.",
        "categoria": "PLATINUM",
        "tipo": "Crédito",
        "nome": "LETICIA SILVA MACEDO DE SA",
        "cpf": "76930440353",
        "score_serasa": 141,
        "score_bc": 96,
        "preco": "80,00",
        "limite_garantido": 1200.00,
        "posicao": "68 de 520"
    },
    {
        "cartao": "554906******4373",
        "banco": "BANCO DO BRASIL, S.A.",
        "categoria": "PLATINUM",
        "tipo": "Crédito",
        "nome": "JOSE PEDRO PEREIRA JUNIOR",
        "cpf": "61618837320",
        "score_serasa": 424,
        "score_bc": 362,
        "preco": "80,00",
        "limite_garantido": 1200.00,
        "posicao": "69 de 520"
    },
    {
        "cartao": "415275******4133",
        "banco": "PORTOSEG S.A. CREDITO FINANCIAMENTO E INVESTIM...",
        "categoria": "PLATINUM",
        "tipo": "Crédito",
        "nome": "HUDISON LOCH HASKEL",
        "cpf": "05949292960",
        "score_serasa": None,
        "score_bc": 940,
        "preco": "80,00",
        "limite_garantido": 1200.00,
        "posicao": "70 de 520"
    },
    {
        "cartao": "531681******6381",
        "banco": "ITAU UNIBANCO, S.A.",
        "categoria": "PLATINUM",
        "tipo": "Crédito",
        "nome": "SEBASTIAO DE SOUZA NASCIMENTO FILHO",
        "cpf": "13153200106",
        "score_serasa": 799,
        "score_bc": 771,
        "preco": "80,00",
        "limite_garantido": 1200.00,
        "posicao": "71 de 520"
    },
    {
        "cartao": "470598******3922",
        "banco": "ITAU UNIBANCO, S.A.",
        "categoria": "PLATINUM",
        "tipo": "Crédito",
        "nome": "ROZANA GOMES DO NASCIMENTO DA SILVA",
        "cpf": "59473789149",
        "score_serasa": 596,
        "score_bc": 317,
        "preco": "80,00",
        "limite_garantido": 1200.00,
        "posicao": "72 de 520"
    },
    {
        "cartao": "422007******6782",
        "banco": "ITAU UNIBANCO, S.A.",
        "categoria": "PLATINUM",
        "tipo": "Crédito",
        "nome": "CARLOS SANTANA MATHEUS",
        "cpf": "69926824749",
        "score_serasa": 80,
        "score_bc": 814,
        "preco": "80,00",
        "limite_garantido": 1200.00,
        "posicao": "73 de 520"
    },
    {
        "cartao": "470598******7330",
        "banco": "ITAU UNIBANCO, S.A.",
        "categoria": "PLATINUM",
        "tipo": "Crédito",
        "nome": "ANTONIO GOMES DA SILVA",
        "cpf": "20902735187",
        "score_serasa": 136,
        "score_bc": 160,
        "preco": "80,00",
        "limite_garantido": 1200.00,
        "posicao": "74 de 520"
    },
    {
        "cartao": "415275******4212",
        "banco": "PORTOSEG S.A. CREDITO FINANCIAMENTO E INVESTIM...",
        "categoria": "PLATINUM",
        "tipo": "Crédito",
        "nome": "THATIANE LIMA DA SILVA BACK",
        "cpf": "95907750200",
        "score_serasa": 219,
        "score_bc": 433,
        "preco": "80,00",
        "limite_garantido": 1200.00,
        "posicao": "75 de 520"
    },
    {
        "cartao": "514945******4408",
        "banco": "ITAU UNIBANCO, S.A.",
        "categoria": "PLATINUM",
        "tipo": "Crédito",
        "nome": "STEFANNI MOURA DO NASCIMENTO",
        "cpf": "06912570194",
        "score_serasa": 1,
        "score_bc": 0,
        "preco": "80,00",
        "limite_garantido": 1200.00,
        "posicao": "76 de 520"
    },
    {
        "cartao": "498401******0300",
        "banco": "BANCO DO BRASIL, S.A.",
        "categoria": "PLATINUM",
        "tipo": "Crédito",
        "nome": "ADRIANA TOMASINI",
        "cpf": "86252577120",
        "score_serasa": 572,
        "score_bc": 513,
        "preco": "80,00",
        "limite_garantido": 1200.00,
        "posicao": "77 de 520"
    },
    {
        "cartao": "523431******2024",
        "banco": "ITAU UNIBANCO, S.A.",
        "categoria": "PLATINUM",
        "tipo": "Crédito",
        "nome": "MARIA MADALENA MANGANARO",
        "cpf": "08306984854",
        "score_serasa": 563,
        "score_bc": 888,
        "preco": "80,00",
        "limite_garantido": 1200.00,
        "posicao": "78 de 520"
    },
    {
        "cartao": "464128******5204",
        "banco": "BANCO BRADESCO CARTOES, S.A.",
        "categoria": "PLATINUM",
        "tipo": "Crédito",
        "nome": "CARLOSNAICK GONCALVES DE SOUZA",
        "cpf": "31280862734",
        "score_serasa": 306,
        "score_bc": 508,
        "preco": "80,00",
        "limite_garantido": 1200.00,
        "posicao": "79 de 520"
    },
    {
        "cartao": "422007******3346",
        "banco": "ITAU UNIBANCO, S.A.",
        "categoria": "PLATINUM",
        "tipo": "Crédito",
        "nome": "FARAH MARIA ALVIM DE SOUZA HOLANDA",
        "cpf": "04070803416",
        "score_serasa": 514,
        "score_bc": 869,
        "preco": "80,00",
        "limite_garantido": 1200.00,
        "posicao": "80 de 520"
    },
    {
        "cartao": "414506******7584",
        "banco": "ITAU UNIBANCO, S.A.",
        "categoria": "PLATINUM",
        "tipo": "Crédito",
        "nome": "FABIANA MORGAN LOPES CORDEIRO",
        "cpf": "28818701800",
        "score_serasa": 448,
        "score_bc": 150,
        "preco": "80,00",
        "limite_garantido": 1200.00,
        "posicao": "81 de 520"
    },
    {
        "cartao": "523431******5434",
        "banco": "ITAU UNIBANCO, S.A.",
        "categoria": "PLATINUM",
        "tipo": "Crédito",
        "nome": "EDUARDO MOURA ABREU BARROSO DE SIQUEIRA",
        "cpf": "16592576898",
        "score_serasa": 28,
        "score_bc": 42,
        "preco": "80,00",
        "limite_garantido": 1200.00,
        "posicao": "82 de 520"
    },
    {
        "cartao": "422007******9711",
        "banco": "ITAU UNIBANCO, S.A.",
        "categoria": "PLATINUM",
        "tipo": "Crédito",
        "nome": "FABRICIO ALMEIDA",
        "cpf": "98693107887",
        "score_serasa": 26,
        "score_bc": 31,
        "preco": "80,00",
        "limite_garantido": 1200.00,
        "posicao": "83 de 520"
    },
    {
        "cartao": "415275******9216",
        "banco": "PORTOSEG S.A. CREDITO FINANCIAMENTO E INVESTIM...",
        "categoria": "PLATINUM",
        "tipo": "Crédito",
        "nome": "INGRID ARAMBURU TIAGO DE ALMEIDA",
        "cpf": "05798472175",
        "score_serasa": 234,
        "score_bc": 306,
        "preco": "80,00",
        "limite_garantido": 1200.00,
        "posicao": "84 de 520"
    },
    {
        "cartao": "403002******4019",
        "banco": "BV FINANCEIRA S.A. CREDITO FINANCIAMENTO E INV...",
        "categoria": "PLATINUM",
        "tipo": "Crédito",
        "nome": "NATAN MATEUS GRZEBIELUCKAS",
        "cpf": "04564175084",
        "score_serasa": 1,
        "score_bc": 653,
        "preco": "80,00",
        "limite_garantido": 1200.00,
        "posicao": "85 de 520"
    },
    {
        "cartao": "470598******5086",
        "banco": "ITAU UNIBANCO, S.A.",
        "categoria": "PLATINUM",
        "tipo": "Crédito",
        "nome": "JOBSON SANCHEZ GARCIA",
        "cpf": "11662941889",
        "score_serasa": 324,
        "score_bc": 183,
        "preco": "80,00",
        "limite_garantido": 1200.00,
        "posicao": "86 de 520"
    }
]
# --- MOTOR DE AUTOMAÇÃO E EDIFICAÇÃO DE ESTOQUE ---

def identificar_bin(cc_number: str) -> str:
    """Extrai exatamente os 6 primeiros dígitos numéricos do cartão."""
    apenas_numeros = re.sub(r"\D", "", str(cc_number))
    return apenas_numeros[:6] if len(apenas_numeros) >= 6 else "000000"

def mascarar_cartao(cc_full: str) -> str:
    """Mascara o cartão preservando os 6 primeiros e os 4 últimos dígitos."""
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
    """Identificação automatizada de bandeira por faixa de BIN."""
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
    elif b.startswith(("6011", "65")):
        return "DISCOVER"
    elif b.startswith(("301", "305", "36", "38")):
        return "DINERS"
    elif b.startswith(("3841", "6062", "6370")):
        return "HIPERCARD"
    elif b.startswith(("3528", "3589")):
        return "JCB"
    else:
        return "OUTRAS"

def identificar_banco_por_bin(bin_code: str) -> str:
    """Reconhecimento automatizado do Banco Emissor através do BIN."""
    b = str(bin_code).strip()
    if b.startswith(("470598", "544169", "498406", "525204", "410863", "412171")):
        return "ITAU UNIBANCO, S.A."
    elif b.startswith(("542819", "548058")):
        return "BANCO GENIAL SA"
    elif b.startswith(("509423", "603689")):
        return "PLUXEE INSTITUICAO DE PAGAMENTO BRASIL SA"
    elif b.startswith(("400217", "427168", "512631", "520268")):
        return "BANCO BRADESCO S.A."
    elif b.startswith(("451416", "540115", "490172")):
        return "BANCO DO BRASIL S.A."
    elif b.startswith(("516292", "550209", "522774")):
        return "BANCO SANTANDER BRASIL S.A."
    elif b.startswith(("518029", "516220")):
        return "NUBANK - NUPAGAMENTOS S.A."
    elif b.startswith(("506722", "506723", "506724")):
        return "BANCO INTER S.A."
    elif b.startswith(("104", "204", "506728")):
        return "CAIXA ECONOMICA FEDERAL"
    else:
        return "BANCO DESCONHECIDO"

def identificar_nivel(categoria_raw: str) -> str:
    """Padronização limpa de Categoria/Nível."""
    cat = str(categoria_raw).upper().strip()
    
    if "BLACK" in cat:
        return "BLACK"
    elif "INFINITE" in cat:
        return "INFINITE"
    elif "PLATINUM" in cat:
        return "PLATINUM"
    elif "GOLD" in cat or "OURO" in cat:
        return "GOLD"
    elif "SIGNATURE" in cat:
        return "SIGNATURE"
    elif "PREPAID" in cat or "VOUCHER" in cat:
        return "PREPAID"
    elif "BUSINESS" in cat or "CORPORATE" in cat:
        return "BUSINESS"
    elif "STANDARD" in cat or "CLASSIC" in cat:
        return "STANDARD"
    else:
        return cat if cat else "STANDARD"

def edificar_item_estoque(card_raw: dict) -> dict:
    """Reconhece, calcula e edifica todos os campos do cartão no estoque."""
    cc_bruto = card_raw.get("cc", "")
    bin_extraida = identificar_bin(cc_bruto)
    
    banco_auto = card_raw.get("banco")
    if not banco_auto or banco_auto == "DESCONHECIDO":
        banco_auto = identificar_banco_por_bin(bin_extraida)

    bandeira_auto = card_raw.get("bandeira")
    if not bandeira_auto:
        bandeira_auto = identificar_bandeira(bin_extraida)

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
        "fornecedor": "Anon",
        "preco": 80.00,
        "saldo_minimo": 1200.00,
        "vendido": False,
    },
    {
        "id": "card_3",
        "cc": "509423******7847",
        "categoria": "PREPAID MULTIPLE VOUCHER",
        "tipo": "DEBIT",
        "nome": "DANIELE SILVA DE OLIVEIRA",
        "cpf": "09078890690",
        "fornecedor": "Anon",
        "preco": 50.00,
        "saldo_minimo": 500.00,
        "vendido": False,
    },
    {
        "id": "card_4",
        "cc": "470598******5141",
        "categoria": "PLATINUM",
        "tipo": "CREDIT",
        "nome": "ALESSANDRO FERNANDES GOMES PEREIRA",
        "cpf": "11257194780",
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
    {"id": "unit_4", "nome": "BUSINESS", "preco": 80.0, "qtd": 16},
    {"id": "unit_5", "nome": "INFINITE", "preco": 413, "qtd": 413},
    {"id": "unit_6", "nome": "BLACK", "preco": 120.0, "qtd": 114},
    {"id": "unit_7", "nome": "SIGNATURE", "preco": 80.0, "qtd": 3},
    {"id": "unit_8", "nome": "NUBANK GOLD", "preco": 35.0, "qtd": 501},
    {"id": "unit_9", "nome": "NUBANK PLATINUM", "preco": 40.0, "qtd": 430},
]

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
    except Exception as e:
        print(f"Erro ao verificar canal: {e}")
        # Retorna False para forçar o usuário a entrar ou para você ver o erro nos logs do Render
        return False

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

    cartoes_filtrados = []
    for c in DADOS_CARTOES:
        if c["vendido"]:
            continue
        if not query or (
            query in c["bin"].lower() or 
            query in c["banco"].lower() or 
            query in c["categoria"].lower() or 
            query in c["nivel_formatado"].lower() or
            query in c["bandeira"].lower()
        ):
            cartoes_filtrados.append(c)

    for item in cartoes_filtrados:
        texto_resposta = (
            f"Número do Cartão: {item['cc_mascarado']}\n"
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
                InlineKeyboardButton("⬅️ Anterior", callback_data="nav_prev"),
                InlineKeyboardButton("Próximo ➡️", callback_data="nav_next"),
            ],
            [InlineKeyboardButton("❌ Cancelar", callback_data="voltar_cc_full")],
        ]

        results.append(
            InlineQueryResultArticle(
                id=item["id"],
                title=f"R$ {item['preco']:.2f} - BIN {item['bin']} - {item['banco']}",
                description=f"Nível: {item['nivel_formatado']} | Bandeira: {item['bandeira']}\nFornecedor: {item['fornecedor']}",
                thumbnail_url=THUMB_CARD_URL,
                input_message_content=InputTextMessageContent(texto_resposta, parse_mode="HTML"),
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        )

    await update.inline_query.answer(results, cache_time=1)

def montar_texto_cartao_unitario(item: dict) -> str:
    """Monta a exibição pré-compra idêntica à imagem 3 do cliente."""
    return (
        f"Número do Cartão: {item['cc_mascarado']}\n"
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
            await query.message.delete()
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
        markup = InlineKeyboardMarkup(keyboard)
        texto = "🔹 <b>CASABLANCA SHOP | CATÁLOGO</b> 🔹\n\nEscolha a categoria desejada:"
        if query.message.photo:
            await query.message.delete()
            await context.bot.send_message(chat_id=chat_id, text=texto, reply_markup=markup, parse_mode="HTML")
        else:
            await query.message.edit_text(texto, reply_markup=markup, parse_mode="HTML")

    elif data == "voltar_cc_full":
        keyboard = [
            [InlineKeyboardButton("🔢 Unitárias", callback_data="ver_unitarias")],
            [
                InlineKeyboardButton("📊 Nível", switch_inline_query_current_chat=""),
                InlineKeyboardButton("🔍 Bin", switch_inline_query_current_chat=""),
            ],
            [
                InlineKeyboardButton("🏦 Banco", switch_inline_query_current_chat=""),
                InlineKeyboardButton("🇧🇷 Bandeira", switch_inline_query_current_chat=""),
            ],
            [InlineKeyboardButton("💬 Atendimento/suporte", url=LINK_SUPORTE)],
            [InlineKeyboardButton("🔙 Voltar", callback_data="menu_comprar")],
        ]
        texto = f"🔹 <b>CASABLANCA SHOP | CC FULL DADOS</b> 🔹\n\nInformações:\n- Saldo: R$ {saldo_atual:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        markup = InlineKeyboardMarkup(keyboard)

        if query.message.photo:
            await query.message.delete()
            await context.bot.send_message(chat_id=chat_id, text=texto, reply_markup=markup, parse_mode="HTML")
        else:
            await query.message.edit_text(texto, reply_markup=markup, parse_mode="HTML")

    elif data == "ver_unitarias":
        keyboard = []
        for item in CATALOGO_UNITARIAS:
            keyboard.append([InlineKeyboardButton(f"R$ {item['preco']:.0f} {item['nome']} ({item['qtd']})", callback_data=f"show_u_{item['id']}")])

        keyboard.append([InlineKeyboardButton("🔙 Voltar", callback_data="voltar_cc_full")])
        await query.message.edit_text(POLITICA_REEMBOLSO, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

    elif data.startswith("show_u_"):
        unit_id = data.replace("show_u_", "")
        cartoes_validos = [c for c in DADOS_CARTOES if not c["vendido"]]
        
        if not cartoes_validos:
            await query.message.reply_text("🔹 <b>CASABLANCA SHOP</b> 🔹\n\n❌ Estoque temporariamente esgotado para esta categoria!", parse_mode="HTML")
            return

        idx = 0
        card = cartoes_validos[idx]
        texto_card = montar_texto_cartao_unitario(card)

        keyboard = [
            [InlineKeyboardButton("✅ Comprar", callback_data=f"buy_card_{card['id']}")],
            [
                InlineKeyboardButton("⬅️ Anterior", callback_data=f"u_nav_{unit_id}_{idx - 1}"),
                InlineKeyboardButton("Próximo ➡️", callback_data=f"u_nav_{unit_id}_{idx + 1}"),
            ],
            [InlineKeyboardButton("❌ Cancelar", callback_data="ver_unitarias")],
        ]

        await query.message.edit_text(texto_card, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

    elif data.startswith("u_nav_"):
        partes = data.split("_")
        unit_id = partes[2]
        idx = int(partes[3])

        cartoes_validos = [c for c in DADOS_CARTOES if not c["vendido"]]
        if not cartoes_validos:
            await query.message.reply_text("🔹 <b>CASABLANCA SHOP</b> 🔹\n\n❌ Estoque esgotado!", parse_mode="HTML")
            return

        idx = idx % len(cartoes_validos)
        card = cartoes_validos[idx]
        texto_card = montar_texto_cartao_unitario(card)

        keyboard = [
            [InlineKeyboardButton("✅ Comprar", callback_data=f"buy_card_{card['id']}")],
            [
                InlineKeyboardButton("⬅️ Anterior", callback_data=f"u_nav_{unit_id}_{idx - 1}"),
                InlineKeyboardButton("Próximo ➡️", callback_data=f"u_nav_{unit_id}_{idx + 1}"),
            ],
            [InlineKeyboardButton("❌ Cancelar", callback_data="ver_unitarias")],
        ]

        await query.message.edit_text(texto_card, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

    elif data == "nav_prev" or data == "nav_next":
        cartoes_validos = [c for c in DADOS_CARTOES if not c["vendido"]]
        if cartoes_validos:
            card = random.choice(cartoes_validos)
            texto_card = montar_texto_cartao_unitario(card)
            keyboard = [
                [InlineKeyboardButton("✅ Comprar", callback_data=f"buy_card_{card['id']}")],
                [
                    InlineKeyboardButton("⬅️ Anterior", callback_data="nav_prev"),
                    InlineKeyboardButton("Próximo ➡️", callback_data="nav_next"),
                ],
                [InlineKeyboardButton("❌ Cancelar", callback_data="voltar_cc_full")],
            ]
            await query.message.edit_text(texto_card, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

    elif data.startswith("buy_card_"):
        card_id = data.replace("buy_card_", "")
        card = next((c for c in DADOS_CARTOES if c["id"] == card_id), None)
        if card:
            if card["vendido"]:
                await query.message.reply_text("🔹 <b>CASABLANCA SHOP</b> 🔹\n\n❌ Este cartão já foi vendido!", parse_mode="HTML")
            elif saldo_atual < card["preco"]:
                await query.message.reply_text(
                    f"🔹 <b>CASABLANCA SHOP | SALDO INSUFICIENTE</b> 🔹\n\n"
                    f"Preço do cartão: R$ {card['preco']:,.2f}\n"
                    f"Seu Saldo: R$ {saldo_atual:,.2f}\n\n"
                    f"Adicione saldo digitando: <code>/pix {int(card['preco'])}</code>",
                    parse_mode="HTML",
                )
            else:
                SALDO_USUARIOS[user_id] -= card["preco"]
                card["vendido"] = True
                await query.message.reply_text(
                    f"🎉 <b>COMPRA CONCLUÍDA - CASABLANCA SHOP</b>\n\n"
                    f"<b>Dados do Cartão:</b>\n<code>{card['cc_full']}</code>\n"
                    f"<b>Nome:</b> {card['nome']}\n"
                    f"<b>CPF:</b> {card['cpf']}\n"
                    f"<b>Banco:</b> {card['banco']}\n"
                    f"<b>Nível:</b> {card['nivel_formatado']}\n"
                    f"<b>Bandeira:</b> {card['bandeira']}\n\n"
                    f"Novo Saldo: R$ {SALDO_USUARIOS[user_id]:,.2f}",
                    parse_mode="HTML",
                )

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

telegram_app.add_handler(CommandHandler("add_estoque", add_estoque))
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("pix", comando_pix))
telegram_app.add_handler(InlineQueryHandler(inline_search))
telegram_app.add_handler(CallbackQueryHandler(botao_callback))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, IA_atendimento))

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

            texto_sucesso = (
                f"🔹 <b>CASABLANCA SHOP | PAGAMENTO CONFIRMADO</b> 🔹\n\n"
                f"Foi creditado <b>R$ {value:,.2f}</b> na sua conta."
            ).replace(",", "X").replace(".", ",").replace("X", ".")

            await telegram_app.bot.send_message(chat_id=user_id, text=texto_sucesso, parse_mode="HTML")

        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- REGISTRO DE COMANDOS DO TELEGRAM ---
telegram_app.add_handler(CommandHandler("add_estoque", add_estoque))
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("pix", comando_pix))
telegram_app.add_handler(InlineQueryHandler(inline_search))
telegram_app.add_handler(CallbackQueryHandler(botao_callback))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, IA_atendimento))

@app.get("/")
async def root():
    return {"status": "online"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
