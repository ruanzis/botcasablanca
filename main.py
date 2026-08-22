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
TOKEN = "8956870259:AAGR_gmp5h2pzwdYnqC_QScrigH8imPVoho"
ID_CANAL = -1004302224747
LINK_CANAL = "https://t.me/+qrh5SObhV3xmODhh"
NOME_FOTO = "capa.jpg"
FOTO_CATEGORIAS = "categorias.jpg"

# MISTICPAY CONFIGURAÇÕES
MISTICPAY_API_URL = "https://api.misticpay.com/v1"  # Ajuste conforme a documentação da MisticPay
MISTICPAY_CLIENT_ID = os.getenv("MISTICPAY_CLIENT_ID", "SEU_CLIENT_ID")
MISTICPAY_CLIENT_SECRET = os.getenv("MISTICPAY_CLIENT_SECRET", "SEU_CLIENT_SECRET")
WEBHOOK_BASE_URL = "https://botcasablanca.onrender.com"

POLITICA_REEMBOLSO = (
    "Política de Reembolso\n\n"
    "⚠️ Caso o saldo esteja abaixo do mínimo garantido na pré-compra, "
    "solicite reembolso em até 20 minutos via @haridadenetwork, com vídeo mostrando cartão, valor e erro."
)

# ==================== ESTOQUES DE UNITÁRIAS (CATÁLOGO) ====================
CATALOGO_UNITARIAS = {
    "platinum": {"nome": "PLATINUM", "preco": "R$ 80", "estoque": 565},
    "gold": {"nome": "GOLD", "preco": "R$ 50", "estoque": 176},
    "personal": {"nome": "PERSONAL", "preco": "R$ 50", "estoque": 55},
    "business": {"nome": "BUSINESS", "preco": "R$ 80", "estoque": 162},
    "elo": {"nome": "ELO", "preco": "R$ 50", "estoque": 24},
    "black": {"nome": "BLACK", "preco": "R$ 120", "estoque": 118},
    "personal_plat_charge": {
        "nome": "PERSONAL PLATINUM CHARGE",
        "preco": "R$ 120",
        "estoque": 34,
    },
    "personal_gold_charge": {
        "nome": "PERSONAL GOLD CHARGE",
        "preco": "R$ 120",
        "estoque": 14,
    },
    "signature": {"nome": "SIGNATURE", "preco": "R$ 80", "estoque": 6},
    "nubank_gold": {"nome": "NUBANK GOLD", "preco": "R$ 35", "estoque": 526},
    "nubank_plat": {"nome": "NUBANK PLATINUM", "preco": "R$ 40", "estoque": 441},
    "classic": {"nome": "CLASSIC", "preco": "R$ 30", "estoque": 201},
    "standard": {"nome": "STANDARD", "preco": "R$ 20", "estoque": 104},
    "infinite": {"nome": "INFINITE", "preco": "R$ 90", "estoque": 88},
}

# Base de Dados Completa com Atualização de Estoque por BIN
DADOS_PLATINUM = [
    {
        "cc": "542819******0150",
        "banco": "BANCO GENIAL SA",
        "nome": "CRISTIANO CACHEIRO MAHIA",
        "cpf": "03250698679",
        "serasa": "306",
        "bc": "93",
        "bin": "542819",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": "80,00",
    },
    {
        "cc": "234075******8043",
        "banco": "PICPAY BANK BANCO MULTIPLO S A",
        "nome": "IGOR TIAGO MIRANDA DA SILVA",
        "cpf": "33258607885",
        "serasa": "966",
        "bc": "929",
        "bin": "234075",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": "80,00",
    },
    {
        "cc": "223357******5915",
        "banco": "ITAU UNIBANCO, S.A.",
        "nome": "VERA LUCIA DE FATIMA FANTI DE ALMEIDA",
        "cpf": "30441013104",
        "serasa": "500",
        "bc": "500",
        "bin": "223357",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": "80,00",
    },
    {
        "cc": "537363******9016",
        "banco": "BANCO BRADESCARD, S.A.",
        "nome": "JOELCIO CRUZ PAIVA",
        "cpf": "00033482705",
        "serasa": "500",
        "bc": "500",
        "bin": "537363",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": "80,00",
    },
    {
        "cc": "538164******4290",
        "banco": "BANCO C6 SA",
        "nome": "CRISTINA PALOMA DOS SANTOS",
        "cpf": "00607587164",
        "serasa": "500",
        "bc": "500",
        "bin": "538164",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": "80,00",
    },
    {
        "cc": "223357******7766",
        "banco": "ITAU UNIBANCO, S.A.",
        "nome": "JHULIANA SANTOS SOUSA",
        "cpf": "04365806599",
        "serasa": "500",
        "bc": "500",
        "bin": "223357",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": "80,00",
    },
    {
        "cc": "223357******1054",
        "banco": "ITAU UNIBANCO, S.A.",
        "nome": "CARLOS HEITOR MIRANDA DE FARIA",
        "cpf": "00754048772",
        "serasa": "500",
        "bc": "500",
        "bin": "223357",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": "80,00",
    },
    {
        "cc": "470598******9086",
        "banco": "ITAU UNIBANCO, S.A.",
        "nome": "PERICLES JOSE LUIZ DA SILVA",
        "cpf": "62510029800",
        "serasa": "500",
        "bc": "500",
        "bin": "470598",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": "80,00",
    },
    {
        "cc": "470598******8023",
        "banco": "ITAU UNIBANCO, S.A.",
        "nome": "ALEXANDER BATISTA DOS SANTOS",
        "cpf": "81820585115",
        "serasa": "500",
        "bc": "500",
        "bin": "470598",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": "80,00",
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
        "preco": "80,00",
    },
    {
        "cc": "478308******6554",
        "banco": "ITAU UNIBANCO, S.A.",
        "nome": "NATHALYA MOREIRA DA SILVA FERREIRA",
        "cpf": "05920033452",
        "serasa": "500",
        "bc": "500",
        "bin": "478308",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": "80,00",
    },
    {
        "cc": "489391******5380",
        "banco": "ITAU UNIBANCO, S.A.",
        "nome": "SOLANGE MARIA COSTA BRAGA ABBONDANZA",
        "cpf": "19665342304",
        "serasa": "500",
        "bc": "500",
        "bin": "489391",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": "80,00",
    },
    {
        "cc": "552937******7622",
        "banco": "CAIXA ECONOMICA FEDERAL",
        "nome": "JOAO GLEDSON RIBEIRO MARTINS",
        "cpf": "65471520149",
        "serasa": "500",
        "bc": "500",
        "bin": "552937",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": "80,00",
    },
    {
        "cc": "514945******5094",
        "banco": "ITAU UNIBANCO, S.A.",
        "nome": "ARTHUR ALVARENGA GENZ",
        "cpf": "47044182860",
        "serasa": "500",
        "bc": "500",
        "bin": "514945",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": "80,00",
    },
    {
        "cc": "414506******0191",
        "banco": "ITAU UNIBANCO, S.A.",
        "nome": "EDUARDO COLARES LISBOA",
        "cpf": "94228540597",
        "serasa": "500",
        "bc": "500",
        "bin": "414506",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": "80,00",
    },
    {
        "cc": "531681******1081",
        "banco": "ITAU UNIBANCO, S.A.",
        "nome": "CARLOSNAICK GONCALVES DE SOUZA",
        "cpf": "31280862734",
        "serasa": "500",
        "bc": "500",
        "bin": "531681",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": "80,00",
    },
    {
        "cc": "470598******3596",
        "banco": "ITAU UNIBANCO, S.A.",
        "nome": "PAULO FERNANDO HORMAIN",
        "cpf": "40689662068",
        "serasa": "500",
        "bc": "500",
        "bin": "470598",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": "80,00",
    },
    {
        "cc": "470598******1266",
        "banco": "ITAU UNIBANCO, S.A.",
        "nome": "SERGIO LUIS SIQUEIRA DE SOUZA",
        "cpf": "41585402087",
        "serasa": "500",
        "bc": "500",
        "bin": "470598",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": "80,00",
    },
    {
        "cc": "531681******0678",
        "banco": "ITAU UNIBANCO, S.A.",
        "nome": "JANAINA MAHENDRA CAMARA ESPINDOLA",
        "cpf": "97046159149",
        "serasa": "500",
        "bc": "500",
        "bin": "531681",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": "80,00",
    },
    {
        "cc": "544169******0487",
        "banco": "ITAU UNIBANCO, S.A.",
        "nome": "ALEXANDRE CARVALHO CHANAN",
        "cpf": "18319050006",
        "serasa": "500",
        "bc": "500",
        "bin": "544169",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": "80,00",
    },
    {
        "cc": "514945******0971",
        "banco": "ITAU UNIBANCO, S.A.",
        "nome": "ANDRE FELIPE CANDIDO DA SILVA",
        "cpf": "33660002879",
        "serasa": "500",
        "bc": "500",
        "bin": "514945",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": "80,00",
    },
    {
        "cc": "470598******5141",
        "banco": "ITAU UNIBANCO, S.A.",
        "nome": "ALESSANDRO FERNANDES GOMES PEREIRA",
        "cpf": "11257194780",
        "serasa": "500",
        "bc": "500",
        "bin": "470598",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": "80,00",
    },
    {
        "cc": "498401******6687",
        "banco": "BANCO DO BRASIL, S.A.",
        "nome": "JEFERSON MOURA ALBUQUERQUE",
        "cpf": "02782109537",
        "serasa": "500",
        "bc": "500",
        "bin": "498401",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": "80,00",
    },
    {
        "cc": "498401******6977",
        "banco": "BANCO DO BRASIL, S.A.",
        "nome": "GIOVANI PERDONATE DOS SANTOS",
        "cpf": "05228787763",
        "serasa": "500",
        "bc": "500",
        "bin": "498401",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": "80,00",
    },
    {
        "cc": "530049******3398",
        "banco": "ITAU UNIBANCO, S.A.",
        "nome": "CHRISTIANNE ELIZA CARDINALI DE ASSIS RIBEIRO",
        "cpf": "04434522612",
        "serasa": "500",
        "bc": "500",
        "bin": "530049",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": "80,00",
    },
    {
        "cc": "498401******8835",
        "banco": "BANCO DO BRASIL, S.A.",
        "nome": "JOAO CARLOS GONCALVES",
        "cpf": "83222103887",
        "serasa": "500",
        "bc": "500",
        "bin": "498401",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": "80,00",
    },
    {
        "cc": "514945******3090",
        "banco": "ITAU UNIBANCO, S.A.",
        "nome": "DALMO DE PAULA FREITAS SERPA",
        "cpf": "26145758791",
        "serasa": "500",
        "bc": "500",
        "bin": "514945",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": "80,00",
    },
    {
        "cc": "531681******4646",
        "banco": "ITAU UNIBANCO, S.A.",
        "nome": "REINALDO LIBERO CERON",
        "cpf": "85483010825",
        "serasa": "500",
        "bc": "500",
        "bin": "531681",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": "80,00",
    },
    {
        "cc": "414506******8345",
        "banco": "ITAU UNIBANCO, S.A.",
        "nome": "WAGNER GONCALVES DE SOUZA TRASEL",
        "cpf": "00423225022",
        "serasa": "500",
        "bc": "500",
        "bin": "414506",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": "80,00",
    },
    {
        "cc": "489167******6213",
        "banco": "BANCO COOPERATIVO SICREDI, S.A.",
        "nome": "RICARDO DA SILVA ALVES",
        "cpf": "38223279304",
        "serasa": "500",
        "bc": "500",
        "bin": "489167",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": "80,00",
    },
    {
        "cc": "514895******7810",
        "banco": "BANCO DO BRASIL, S.A.",
        "nome": "RAMONA DE FATIMA RIBEIRO DE OLIVEIRA",
        "cpf": "42075335168",
        "serasa": "500",
        "bc": "500",
        "bin": "514895",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": "80,00",
    },
    {
        "cc": "498401******4560",
        "banco": "BANCO DO BRASIL, S.A.",
        "nome": "ELIANDRO GABRIEL DOS REIS",
        "cpf": "99708213691",
        "serasa": "500",
        "bc": "500",
        "bin": "498401",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": "80,00",
    },
    {
        "cc": "415275******5226",
        "banco": "PORTOSEG S.A.",
        "nome": "EDSON PIZATO",
        "cpf": "03142986901",
        "serasa": "500",
        "bc": "500",
        "bin": "415275",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": "80,00",
    },
    {
        "cc": "415275******5512",
        "banco": "PORTOSEG S.A.",
        "nome": "PAULO RICARDO PEREIRA LAGOS",
        "cpf": "04901539922",
        "serasa": "500",
        "bc": "500",
        "bin": "415275",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": "80,00",
    },
    {
        "cc": "470598******6146",
        "banco": "ITAU UNIBANCO, S.A.",
        "nome": "SHEYLLA KELLY ESTEVAO SOARES",
        "cpf": "93901968172",
        "serasa": "500",
        "bc": "500",
        "bin": "470598",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": "80,00",
    },
    {
        "cc": "470598******1574",
        "banco": "ITAU UNIBANCO, S.A.",
        "nome": "EDSON FERREIRA DE LIMA",
        "cpf": "09705104387",
        "serasa": "500",
        "bc": "500",
        "bin": "470598",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": "80,00",
    },
    {
        "cc": "531681******5482",
        "banco": "ITAU UNIBANCO, S.A.",
        "nome": "CRISTIANE PATRICIA DA SILVA NUNES",
        "cpf": "35550271826",
        "serasa": "500",
        "bc": "500",
        "bin": "531681",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": "80,00",
    },
    {
        "cc": "531681******1774",
        "banco": "ITAU UNIBANCO, S.A.",
        "nome": "GISELE NUNES DOS SANTOS",
        "cpf": "82334692115",
        "serasa": "500",
        "bc": "500",
        "bin": "531681",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": "80,00",
    },
    {
        "cc": "532930******9111",
        "banco": "PORTOSEG S.A.",
        "nome": "MARIA SANTOS DE BRITO",
        "cpf": "02393475958",
        "serasa": "500",
        "bc": "500",
        "bin": "532930",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": "80,00",
    },
    {
        "cc": "498401******5247",
        "banco": "BANCO DO BRASIL, S.A.",
        "nome": "ISABEL NOEMI CAMPOS REIS",
        "cpf": "51412632587",
        "serasa": "500",
        "bc": "500",
        "bin": "498401",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": "80,00",
    },
    {
        "cc": "514945******4857",
        "banco": "ITAU UNIBANCO, S.A.",
        "nome": "ANTONIA R DA SILVA",
        "cpf": "94919127987",
        "serasa": "500",
        "bc": "500",
        "bin": "514945",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": "80,00",
    },
    {
        "cc": "523431******2193",
        "banco": "ITAU UNIBANCO, S.A.",
        "nome": "LUIS EDUARDO TANGER FAGUNDES",
        "cpf": "92066810010",
        "serasa": "500",
        "bc": "500",
        "bin": "523431",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": "80,00",
    },
    {
        "cc": "516291******3785",
        "banco": "ITAU UNIBANCO, S.A.",
        "nome": "EDUARDO MACIEL DE SOUSA NETO",
        "cpf": "81412363268",
        "serasa": "500",
        "bc": "500",
        "bin": "516291",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": "80,00",
    },
    {
        "cc": "498401******8439",
        "banco": "BANCO DO BRASIL, S.A.",
        "nome": "PATRICIA BAPTISTA TEIXEIRA",
        "cpf": "35670274334",
        "serasa": "500",
        "bc": "500",
        "bin": "498401",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": "80,00",
    },
    {
        "cc": "532930******7118",
        "banco": "PORTOSEG S.A.",
        "nome": "MARCOS ALEXANDRE MARTINS GABRIEL",
        "cpf": "52223426204",
        "serasa": "500",
        "bc": "500",
        "bin": "532930",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": "80,00",
    },
    {
        "cc": "554927******1985",
        "banco": "BANCO DO BRASIL, S.A.",
        "nome": "SILVIA SOUZA SANTOS",
        "cpf": "87921740944",
        "serasa": "500",
        "bc": "500",
        "bin": "554927",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": "80,00",
    },
    {
        "cc": "550209******9253",
        "banco": "NUBANK",
        "nome": "PAULO ARTHUR BENDELAK ROCHA",
        "cpf": "51666944220",
        "serasa": "350",
        "bc": "350",
        "bin": "550209",
        "nivel": "GOLD",
        "fornecedor": "Anon",
        "preco": "35,00",
    },
    {
        "cc": "550209******6565",
        "banco": "NUBANK",
        "nome": "TATIANE GONCALVES DE ABREU",
        "cpf": "10767301757",
        "serasa": "350",
        "bc": "350",
        "bin": "550209",
        "nivel": "GOLD",
        "fornecedor": "Anon",
        "preco": "35,00",
    },
    {
        "cc": "550209******8675",
        "banco": "NUBANK",
        "nome": "ANTONIA LIDIANA SILVA DOS SANTOS CRUZ",
        "cpf": "03359473442",
        "serasa": "350",
        "bc": "350",
        "bin": "550209",
        "nivel": "GOLD",
        "fornecedor": "Anon",
        "preco": "35,00",
    },
    {
        "cc": "550209******7960",
        "banco": "NUBANK",
        "nome": "SARA CALISTO ALVES",
        "cpf": "07059943331",
        "serasa": "350",
        "bc": "350",
        "bin": "550209",
        "nivel": "GOLD",
        "fornecedor": "Anon",
        "preco": "35,00",
    },
    {
        "cc": "550209******9403",
        "banco": "NUBANK",
        "nome": "WILIAN SANTOS VELOSO",
        "cpf": "50453606806",
        "serasa": "350",
        "bc": "350",
        "bin": "550209",
        "nivel": "GOLD",
        "fornecedor": "Anon",
        "preco": "35,00",
    },
    {
        "cc": "550209******0542",
        "banco": "NUBANK",
        "nome": "LEVI STROPARO",
        "cpf": "13921920990",
        "serasa": "350",
        "bc": "350",
        "bin": "550209",
        "nivel": "GOLD",
        "fornecedor": "Anon",
        "preco": "35,00",
    },
    {
        "cc": "550209******0857",
        "banco": "NUBANK",
        "nome": "JOAO PEDRO AZEVEDO COSTA SOUZA",
        "cpf": "70644030488",
        "serasa": "350",
        "bc": "350",
        "bin": "550209",
        "nivel": "GOLD",
        "fornecedor": "Anon",
        "preco": "35,00",
    },
    {
        "cc": "550209******6958",
        "banco": "NUBANK",
        "nome": "LUZIA ROSEMIRIA GOMES DE ALCANTARA SOUZA",
        "cpf": "23532319187",
        "serasa": "350",
        "bc": "350",
        "bin": "550209",
        "nivel": "GOLD",
        "fornecedor": "Anon",
        "preco": "35,00",
    },
    {
        "cc": "550209******2536",
        "banco": "NUBANK",
        "nome": "CLARICE MARQUES DE ALMEIDA DE CARVALHO",
        "cpf": "79071430120",
        "serasa": "350",
        "bc": "350",
        "bin": "550209",
        "nivel": "GOLD",
        "fornecedor": "Anon",
        "preco": "35,00",
    },
    {
        "cc": "550209******5534",
        "banco": "NUBANK",
        "nome": "FABIANA LUXEMBURG BARROSO CAVALCANTE",
        "cpf": "61581178204",
        "serasa": "350",
        "bc": "350",
        "bin": "550209",
        "nivel": "GOLD",
        "fornecedor": "Anon",
        "preco": "35,00",
    },
    {
        "cc": "550209******3975",
        "banco": "NUBANK",
        "nome": "REINALDO EMANOEL DA COSTA GAIA",
        "cpf": "30594049253",
        "serasa": "350",
        "bc": "350",
        "bin": "550209",
        "nivel": "GOLD",
        "fornecedor": "Anon",
        "preco": "35,00",
    },
    {
        "cc": "550209******8163",
        "banco": "NUBANK",
        "nome": "KAINAN ALVES ANTUNES BAHIA",
        "cpf": "01857829573",
        "serasa": "350",
        "bc": "350",
        "bin": "550209",
        "nivel": "GOLD",
        "fornecedor": "Anon",
        "preco": "35,00",
    },
    {
        "cc": "550209******2594",
        "banco": "NUBANK",
        "nome": "MARIA JOSE MENDONCA SALES",
        "cpf": "54810124800",
        "serasa": "350",
        "bc": "350",
        "bin": "550209",
        "nivel": "GOLD",
        "fornecedor": "Anon",
        "preco": "35,00",
    },
    {
        "cc": "550209******0082",
        "banco": "NUBANK",
        "nome": "MARIA DA GUIA CARDEAL DOS SANTOS",
        "cpf": "22159292869",
        "serasa": "350",
        "bc": "350",
        "bin": "550209",
        "nivel": "GOLD",
        "fornecedor": "Anon",
        "preco": "35,00",
    },
    {
        "cc": "550209******8526",
        "banco": "NUBANK",
        "nome": "REGINA LAURA CAMPOS BOTELHO",
        "cpf": "63672111953",
        "serasa": "350",
        "bc": "350",
        "bin": "550209",
        "nivel": "GOLD",
        "fornecedor": "Anon",
        "preco": "35,00",
    },
    {
        "cc": "550209******2586",
        "banco": "NUBANK",
        "nome": "MONIQUE TEIXEIRA NASCIMENTO",
        "cpf": "13052023764",
        "serasa": "350",
        "bc": "350",
        "bin": "550209",
        "nivel": "GOLD",
        "fornecedor": "Anon",
        "preco": "35,00",
    },
    {
        "cc": "550209******8171",
        "banco": "NUBANK",
        "nome": "SHEILA CARDOSO PASSOS",
        "cpf": "82615047191",
        "serasa": "350",
        "bc": "350",
        "bin": "550209",
        "nivel": "GOLD",
        "fornecedor": "Anon",
        "preco": "35,00",
    },
    {
        "cc": "550209******0539",
        "banco": "NUBANK",
        "nome": "FABIO MAGALHAES DIAS",
        "cpf": "17731924858",
        "serasa": "350",
        "bc": "350",
        "bin": "550209",
        "nivel": "GOLD",
        "fornecedor": "Anon",
        "preco": "35,00",
    },
    {
        "cc": "550209******1291",
        "banco": "NUBANK",
        "nome": "THAWANY DA ROCHA NUNES",
        "cpf": "13325122400",
        "serasa": "350",
        "bc": "350",
        "bin": "550209",
        "nivel": "GOLD",
        "fornecedor": "Anon",
        "preco": "35,00",
    },
    {
        "cc": "550209******5371",
        "banco": "NUBANK",
        "nome": "SHEILA NUNES DE SOUZA CASTRO",
        "cpf": "96820110600",
        "serasa": "350",
        "bc": "350",
        "bin": "550209",
        "nivel": "GOLD",
        "fornecedor": "Anon",
        "preco": "35,00",
    },
    {
        "cc": "550209******9695",
        "banco": "NUBANK",
        "nome": "BEATRIZ DE OLIVEIRA ARAUJO",
        "cpf": "42444977300",
        "serasa": "350",
        "bc": "350",
        "bin": "550209",
        "nivel": "GOLD",
        "fornecedor": "Anon",
        "preco": "35,00",
    },
    {
        "cc": "550209******8003",
        "banco": "NUBANK",
        "nome": "CLEUZENI DE PAULO FELIX",
        "cpf": "97463094634",
        "serasa": "350",
        "bc": "350",
        "bin": "550209",
        "nivel": "GOLD",
        "fornecedor": "Anon",
        "preco": "35,00",
    },
    {
        "cc": "550209******8975",
        "banco": "NUBANK",
        "nome": "CRISTIAN ANTONIO PALMA PONCE",
        "cpf": "05815386685",
        "serasa": "350",
        "bc": "350",
        "bin": "550209",
        "nivel": "GOLD",
        "fornecedor": "Anon",
        "preco": "35,00",
    },
    {
        "cc": "550209******3432",
        "banco": "NUBANK",
        "nome": "PEDRO VINICIUS DOS SANTOS FERREIRA",
        "cpf": "05789319742",
        "serasa": "350",
        "bc": "350",
        "bin": "550209",
        "nivel": "GOLD",
        "fornecedor": "Anon",
        "preco": "35,00",
    },
    {
        "cc": "550209******8651",
        "banco": "NUBANK",
        "nome": "CRISTIANO RAFAEL PRIEBE",
        "cpf": "02939596921",
        "serasa": "350",
        "bc": "350",
        "bin": "550209",
        "nivel": "GOLD",
        "fornecedor": "Anon",
        "preco": "35,00",
    },
    {
        "cc": "516292******1792",
        "banco": "NUBANK",
        "nome": "ALEXANDRE MAGNO DE CARVALHO SANTOS",
        "cpf": "42901502172",
        "serasa": "400",
        "bc": "400",
        "bin": "516292",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": "40,00",
    },
    {
        "cc": "516292******7103",
        "banco": "NUBANK",
        "nome": "MARIA ERIVAN DE SOUSA FELIPE",
        "cpf": "80324754353",
        "serasa": "400",
        "bc": "400",
        "bin": "516292",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": "40,00",
    },
    {
        "cc": "516292******2050",
        "banco": "NUBANK",
        "nome": "MARIA ELIENE CAVALCANTE GUIMARAES",
        "cpf": "02476984400",
        "serasa": "400",
        "bc": "400",
        "bin": "516292",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": "40,00",
    },
    {
        "cc": "516292******3580",
        "banco": "NUBANK",
        "nome": "IVANA LIVIA DE PAIVA CORREA",
        "cpf": "41472858808",
        "serasa": "400",
        "bc": "400",
        "bin": "516292",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": "40,00",
    },
    {
        "cc": "516292******4144",
        "banco": "NUBANK",
        "nome": "CARLA ADRIANA FERREIRA PEREIRA",
        "cpf": "50119249120",
        "serasa": "400",
        "bc": "400",
        "bin": "516292",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": "40,00",
    },
    {
        "cc": "516292******5221",
        "banco": "NUBANK",
        "nome": "MIRIAM DE JESUS GUEDES DE SOUZA",
        "cpf": "43179053453",
        "serasa": "400",
        "bc": "400",
        "bin": "516292",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": "40,00",
    },
    {
        "cc": "516292******5068",
        "banco": "NUBANK",
        "nome": "RAFAELA GONCALVES PAZZINI VIANNA",
        "cpf": "25220410881",
        "serasa": "400",
        "bc": "400",
        "bin": "516292",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": "40,00",
    },
    {
        "cc": "516292******6643",
        "banco": "NUBANK",
        "nome": "GUSTAVO FERNANDO CARDOSO PINO",
        "cpf": "38387303801",
        "serasa": "400",
        "bc": "400",
        "bin": "516292",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": "40,00",
    },
    {
        "cc": "516292******3285",
        "banco": "NUBANK",
        "nome": "AUGUSTO WEBER ZAMBRANO",
        "cpf": "00682540080",
        "serasa": "400",
        "bc": "400",
        "bin": "516292",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": "40,00",
    },
    {
        "cc": "516292******9612",
        "banco": "NUBANK",
        "nome": "ANGELINA SADOVSKI VAZQUEZ",
        "cpf": "05546870974",
        "serasa": "400",
        "bc": "400",
        "bin": "516292",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": "40,00",
    },
    {
        "cc": "516292******9198",
        "banco": "NUBANK",
        "nome": "FERNANDO CARNEIRO MENEZES",
        "cpf": "83362886604",
        "serasa": "400",
        "bc": "400",
        "bin": "516292",
        "nivel": "PLATINUM",
        "fornecedor": "Anon",
        "preco": "40,00",
    },
]

# Inicialização Global da Aplicação Telegram
telegram_app = Application.builder().token(TOKEN).build()

# ==================== UTILITÁRIOS DA MISTICPAY ====================
def gerar_pix_misticpay(valor: float, telegram_id: int):
    """
    Função para fazer a requisição de pagamento via MisticPay.
    """
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
        if response.status_code == 200 or response.status_code == 201:
            return response.json()
        else:
            logger.error(f"Erro MisticPay: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Falha ao conectar com MisticPay: {e}")
        return None

# Checagem de canal protegida contra travamentos
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


# ==================== PAINEL PRINCIPAL ====================
async def enviar_menu_principal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    primeiro_nome = user.first_name if user else "Cliente"

    texto = (
        f"Olá **{primeiro_nome}**, seja bem-vindo a **CasaBlanca Bot**! 🏛️✨\n\n"
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
        [
            InlineKeyboardButton("💳 Adicionar Saldo", callback_data="add_saldo")
        ],
        [InlineKeyboardButton("📢 Canal Oficial", url=LINK_CANAL)],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        if os.path.exists(NOME_FOTO):
            with open(NOME_FOTO, "rb") as foto:
                if update.callback_query:
                    await update.callback_query.message.reply_photo(
                        photo=foto,
                        caption=texto,
                        reply_markup=reply_markup,
                        parse_mode="Markdown",
                    )
                else:
                    await update.message.reply_photo(
                        photo=foto,
                        caption=texto,
                        reply_markup=reply_markup,
                        parse_mode="Markdown",
                    )
        else:
            if update.callback_query:
                await update.callback_query.message.reply_text(
                    texto, reply_markup=reply_markup, parse_mode="Markdown"
                )
            else:
                await update.message.reply_text(
                    texto, reply_markup=reply_markup, parse_mode="Markdown"
                )
    except Exception as e:
        logger.error(f"Erro ao enviar menu: {e}")


# ==================== RENDERIZAÇÃO DO CARTÃO NO ESTOQUE ====================
async def exibir_cartao_estoque(query, categoria_key: str, indice: int, max_estoque: int):
    cartao = DADOS_PLATINUM[indice % len(DADOS_PLATINUM)]
    cat_info = CATALOGO_UNITARIAS.get(
        categoria_key, {"nome": "PLATINUM", "preco": "R$ 80"}
    )

    texto_detalhes = (
        f"Número do Cartão: `{cartao['cc']}`\n"
        f"Banco: {cartao['banco']}\n"
        f"Categoria: {cartao.get('nivel', cat_info['nome'])}\n"
        f"Tipo: Crédito\n"
        f"Nome: {cartao['nome']}\n"
        f"CPF: `{cartao['cpf']}`\n"
        f"Score Serasa: {cartao['serasa']}\n"
        f"Score BC: {cartao['bc']}\n\n"
        "Saldo mínimo garantido: R$ 1.200,00\n"
        "Se o saldo for menor que isso, você pode solicitar reembolso conforme a Política de Reembolso.\n\n"
        f"Valor da Compra: R$ {cartao['preco']}\n"
        f"Fornecedor: {cartao.get('fornecedor', 'Anon')}\n\n"
        f"Cartão {indice + 1} de {max_estoque}"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "✅ Comprar", callback_data=f"pagar_{categoria_key}_{indice}"
            )
        ],
        [
            InlineKeyboardButton("⬅️ Anterior", callback_data=f"nav_{categoria_key}_{indice-1}"),
            InlineKeyboardButton("Próximo ➡️", callback_data=f"nav_{categoria_key}_{indice+1}"),
        ],
        [InlineKeyboardButton("🔙 Voltar", callback_data="menu_comprar")],
    ]

    await query.edit_message_text(
        text=texto_detalhes,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )

# ==================== HANDLERS TELEGRAM ====================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await enviar_menu_principal(update, context)

async def callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "menu_comprar":
        keyboard = []
        for key, val in CATALOGO_UNITARIAS.items():
            keyboard.append([
                InlineKeyboardButton(f"{val['nome']} - {val['preco']} ({val['estoque']})", callback_data=f"cat_{key}")
            ])
        keyboard.append([InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="main_menu")])
        await query.edit_message_text("Selecione a categoria desejada:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "main_menu":
        await enviar_menu_principal(update, context)

    elif data == "info":
        await query.edit_message_text(POLITICA_REEMBOLSO, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data="main_menu")]]))

    elif data.startswith("cat_"):
        cat_key = data.replace("cat_", "")
        await exibir_cartao_estoque(query, cat_key, 0, len(DADOS_PLATINUM))

    elif data.startswith("nav_"):
        _, cat_key, idx = data.split("_")
        await exibir_cartao_estoque(query, cat_key, int(idx), len(DADOS_PLATINUM))

    elif data == "add_saldo" or data.startswith("pagar_"):
        # Solicita geração de Pix na MisticPay
        user_id = query.from_user.id
        valor = 80.0  # Exemplo de valor fixo ou dinâmico
        
        pix_data = gerar_pix_misticpay(valor, user_id)
        
        if pix_data and "pix_code" in pix_data:
            qr_code = pix_data.get("pix_code", "")
            msg = f" Pix gerado com sucesso!\n\nCopie o código abaixo para pagar:\n\n`{qr_code}`"
        else:
            msg = "⚠️ Não foi possível gerar o código Pix no momento. Tente novamente mais tarde ou contate o suporte."

        keyboard = [[InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="main_menu")]]
        await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))


# ==================== APLICAÇÃO FASTAPI (WEBHOOK MISTICPAY) ====================
@asynccontextmanager
async def lifespan(app_fastapi: FastAPI):
    # Setup Telegram Application
    telegram_app.add_handler(CommandHandler("start", start_command))
    telegram_app.add_handler(CallbackQueryHandler(callback_router))
    
    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.updater.start_polling()
    logger.info("Bot do Telegram e FastAPI iniciados com sucesso.")

    yield

    # Teardown
    await telegram_app.updater.stop()
    await telegram_app.stop()
    await telegram_app.shutdown()

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return {"status": "ok", "message": "Bot CasaBlanca Online"}

@app.post("/misticpay-webhook")
async def misticpay_webhook(request: Request):
    """
    Rota para receber callbacks da MisticPay quando um pagamento for aprovado
    """
    try:
        data = await request.json()
        logger.info(f"Webhook MisticPay Recebido: {data}")

        # Exemplo de verificação do callback conforme retorno da API MisticPay
        status = data.get("status") or data.get("payment_status")
        external_id = data.get("external_id", "")  # Formato enviado: user_12345678
        
        if status in ["paid", "approved", "completed"] and external_id.startswith("user_"):
            telegram_id = int(external_id.replace("user_", ""))
            amount = data.get("amount", 0)

            # Notifica o usuário no Telegram
            await telegram_app.bot.send_message(
                chat_id=telegram_id,
                text=f"✅ *Pagamento Confirmado!*\n\nSeu pagamento de *R$ {amount}* foi processado com sucesso.",
                parse_mode="Markdown"
            )

        return {"status": "success"}
    except Exception as e:
        logger.error(f"Erro ao processar Webhook da MisticPay: {e}")
        raise HTTPException(status_code=400, detail="Webhook error")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
