import asyncio
import os
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

# ==================== CONFIGURAÇÕES GERAIS ====================
TOKEN = "8956870259:AAGR_gmp5h2pzwdYnqC_QScrigH8imPVoho"
ID_CANAL = -1004302224747
LINK_CANAL = "https://t.me/+qrh5SObhV3xmODhh"
NOME_FOTO = "capa.jpg"
FOTO_CATEGORIAS = "categorias.jpg"

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


# Checagem de canal protegida contra travamentos
async def esta_no_canal(context: ContextTypes.DEFAULT_TYPE, user_id: int):
    try:
        membro = await asyncio.wait_for(
            context.bot.get_chat_member(chat_id=ID_CANAL, user_id=user_id),
            timeout=4.0,
        )
        return membro.status in ["member", "administrator", "creator"]
    except Exception as e:
        print(f"Aviso ao checar canal: {e}")
        return True


# ==================== PAINEL PRINCIPAL ====================
async def enviar_menu_principal(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
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
            InlineKeyboardButton(
                "💳 Adicionar Saldo", callback_data="add_saldo"
            )
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
        print(f"Erro ao enviar menu: {e}")


# ==================== RENDERIZAÇÃO DO CARTÃO NO ESTOQUE ====================
async def exibir_cartao_estoque(
    query, categoria_key: str, indice: int, max_estoque: int
):
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
            InlineKeyboardButton(
                "⏪ Anterior",
                callback_data=f"nav_{categoria_key}_{indice - 1}",
            ),
            InlineKeyboardButton(
                "Próximo ⏩", callback_data=f"nav_{categoria_key}_{indice + 1}"
            ),
        ],
        [
            InlineKeyboardButton(
                "❌ Cancelar", callback_data="sub_categoria_unitarias"
            )
        ],
    ]

    await query.message.edit_text(
        texto_detalhes,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


# ==================== PESQUISA MODO INLINE (@bot query) ====================
async def pesquisar_inline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.strip()

    if not query:
        return

    resultados = []

    for idx, item in enumerate(DADOS_PLATINUM):
        if (
            query.lower() in item.get("bin", "").lower()
            or query.lower() in item["cc"].lower()
            or query.lower() in item["banco"].lower()
            or query.lower() in item["nome"].lower()
        ):

            titulo = f"R$ {item['preco']} - {item['bin']} - {item['banco']}"
            descricao = f"Nível: {item['nivel']} - CPF: {item['cpf']} - Fornecedor: {item['fornecedor']}"

            conteudo = (
                f"📦 **Item Selecionado:**\n\n"
                f"**Cartão:** `{item['cc']}`\n"
                f"**Banco:** {item['banco']}\n"
                f"**Nível:** {item['nivel']}\n"
                f"**Nome:** {item['nome']}\n"
                f"**CPF:** `{item['cpf']}`\n"
                f"**Valor:** R$ {item['preco']}\n"
                f"**Fornecedor:** {item['fornecedor']}"
            )

            resultados.append(
                InlineQueryResultArticle(
                    id=str(idx),
                    title=titulo,
                    description=descricao,
                    input_message_content=InputTextMessageContent(
                        conteudo, parse_mode="Markdown"
                    ),
                )
            )

    await update.inline_query.answer(resultados[:50], cache_time=1)


# ==================== CONTROLE DE COMANDOS E CALLBACKS ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if await esta_no_canal(context, user_id):
        await enviar_menu_principal(update, context)
    else:
        keyboard = [
            [InlineKeyboardButton("📢 Entrar no Canal", url=LINK_CANAL)],
            [
                InlineKeyboardButton(
                    "🔄 Já entrei / Liberar Acesso", callback_data="verificar"
                )
            ],
        ]
        await update.message.reply_text(
            "⚠️ **ACESSO BLOQUEADO!**\n\n"
            "Para acessar nosso bot, você precisa primeiro entrar no canal oficial.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )


async def processar_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data == "verificar":
        if await esta_no_canal(context, user_id):
            await query.message.delete()
            await enviar_menu_principal(update, context)
        else:
            await query.message.reply_text(
                "❌ Você ainda não entrou no canal! Entre e tente novamente."
            )

    elif data == "menu_comprar":
        await query.message.delete()
        keyboard = [
            [
                InlineKeyboardButton(
                    "💳 CC FULL DADOS", callback_data="categoria_full_dados"
                )
            ],
            [
                InlineKeyboardButton(
                    "📱 E-SIM", callback_data="cat_indisponivel"
                ),
                InlineKeyboardButton(
                    "🗂️ CONSULTÁVEL", callback_data="cat_indisponivel"
                ),
            ],
            [
                InlineKeyboardButton(
                    "💳 CC AUXILIAR", callback_data="cat_indisponivel"
                ),
                InlineKeyboardButton(
                    "🛡️ LARAS", callback_data="cat_indisponivel"
                ),
            ],
            [
                InlineKeyboardButton(
                    "🗽 Login's", callback_data="cat_indisponivel"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 Voltar ao Menu", callback_data="voltar_inicio"
                )
            ],
        ]

        texto = (
            "🛒 **SELEÇÃO DE CATEGORIAS**\n\n"
            "Escolha a categoria que deseja explorar:"
        )

        reply_markup = InlineKeyboardMarkup(keyboard)

        if os.path.exists(FOTO_CATEGORIAS):
            with open(FOTO_CATEGORIAS, "rb") as foto:
                await query.message.reply_photo(
                    photo=foto,
                    caption=texto,
                    reply_markup=reply_markup,
                    parse_mode="Markdown",
                )
        else:
            await query.message.reply_text(
                texto, reply_markup=reply_markup, parse_mode="Markdown"
            )

    elif data == "cat_indisponivel":
        await query.answer(
            "⚠️ Categoria temporariamente sem estoque!", show_alert=True
        )

    elif data == "categoria_full_dados":
        await query.message.delete()
        keyboard = [
            [
                InlineKeyboardButton(
                    "📱 Unitárias", callback_data="sub_categoria_unitarias"
                )
            ],
            [
                InlineKeyboardButton(
                    "🌐 Nível", callback_data="sub_categoria_nivel"
                ),
                InlineKeyboardButton(
                    "🔎 Bin", callback_data="solicitar_busca_bin"
                ),
            ],
            [
                InlineKeyboardButton(
                    "🏛️ banco", callback_data="sub_categoria_banco"
                ),
                InlineKeyboardButton(
                    "🇧🇷 Bandeira", callback_data="sub_categoria_bandeira"
                ),
            ],
            [
                InlineKeyboardButton(
                    "📞 Atendimento/suporte", callback_data="suporte"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 Voltar", callback_data="menu_comprar"
                )
            ],
        ]

        texto_painel = "Doctors ❗️\n/menu\n**Informações**\n- Saldo: R$ 0,00"

        await query.message.reply_text(
            texto_painel,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

    elif data == "solicitar_busca_bin":
        context.user_data["aguardando_bin"] = True
        await query.message.reply_text(
            "🔍 **Pesquisa por BIN**\n\nDigite os 6 primeiros dígitos da BIN que deseja procurar:"
        )

    elif data.startswith("ver_cartao_"):
        indice = int(data.split("_")[2])
        await exibir_cartao_estoque(
            query, "platinum", indice, len(DADOS_PLATINUM)
        )

    elif data == "sub_categoria_unitarias":
        await query.message.delete()
        texto_unitarias = (
            f"{POLITICA_REEMBOLSO}\n\n🛒 **ESTOQUE DISPONÍVEL:**\n\n"
        )

        keyboard = []
        for chave, item in CATALOGO_UNITARIAS.items():
            texto_unitarias += (
                f"• {item['preco']} {item['nome']} ({item['estoque']})\n"
            )
            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"{item['preco']} {item['nome']} ({item['estoque']})",
                        callback_data=f"nav_{chave}_0",
                    )
                ]
            )

        keyboard.append(
            [
                InlineKeyboardButton(
                    "🔙 Voltar", callback_data="categoria_full_dados"
                )
            ]
        )

        await query.message.reply_text(
            texto_unitarias,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

    elif data.startswith("nav_"):
        parts = data.split("_")
        cat_key = parts[1]
        indice = int(parts[2])

        max_estoque = CATALOGO_UNITARIAS.get(cat_key, {}).get(
            "estoque", len(DADOS_PLATINUM)
        )

        if indice < 0:
            indice = max_estoque - 1
        elif indice >= max_estoque:
            indice = 0

        await exibir_cartao_estoque(query, cat_key, indice, max_estoque)

    elif data.startswith("pagar_"):
        parts = data.split("_")
        cat_key = parts[1]
        indice = int(parts[2])
        cat_info = CATALOGO_UNITARIAS.get(
            cat_key, {"nome": "ITEM", "preco": "R$ 80"}
        )

        await query.message.reply_text(
            f"⚡ **PAGAMENTO VIA PIX**\n\n"
            f"Item: **{cat_info['nome']}** (Cartão {indice + 1})\n"
            f"Valor: **{cat_info['preco']}**\n\n"
            "Realize o PIX para gerar a entrega imediata no chat.",
            parse_mode="Markdown",
        )

    elif data == "voltar_inicio":
        await query.message.delete()
        await enviar_menu_principal(update, context)


# ==================== PROCESSADOR DE PESQUISA DE BIN POR TEXTO ====================
async def processar_mensagem_texto(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if context.user_data.get("aguardando_bin"):
        termo_bin = update.message.text.strip()
        context.user_data["aguardando_bin"] = False

        resultados = [
            (idx, item)
            for idx, item in enumerate(DADOS_PLATINUM)
            if termo_bin in item.get("bin", "") or termo_bin in item["cc"]
        ]

        if resultados:
            total_encontrados = len(resultados)

            texto_resposta = f"🔍 **{total_encontrados}/{total_encontrados} foram encontrados.**\nClique em uma opção abaixo:"

            keyboard = []
            for idx, item in resultados:
                rotulo = f"R$ {item['preco']} - {item['bin']} - {item['banco']}\nNível: {item['nivel']} - Full: ✅ Fornecedor: {item['fornecedor']}"
                keyboard.append(
                    [
                        InlineKeyboardButton(
                            rotulo, callback_data=f"ver_cartao_{idx}"
                        )
                    ]
                )

            await update.message.reply_text(
                texto_resposta,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown",
            )
        else:
            await update.message.reply_text(
                f"❌ Nenhum cartão foi encontrado para a BIN **{termo_bin}**.",
                parse_mode="Markdown",
            )


# ==================== EXECUÇÃO DO BOT ====================
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler(["start", "menu"], start))
    app.add_handler(CallbackQueryHandler(processar_callback))
    app.add_handler(InlineQueryHandler(pesquisar_inline))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, processar_mensagem_texto)
    )

    print("CasaBlanca Bot rodando com novos cartões adicionados...")
    app.run_polling()


if __name__ == "__main__":
    main()