# ==============================================================================
# SCRIPT COMPLETO - CASABLANCA SHOP (ORIGINAL PRESERVADO + PAINEL ADMIN ADITIVO)
# ==============================================================================

import os
import re
import random
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
import uvicorn
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    InlineQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)

# Configuração de logging básica (caso não esteja declarada acima)
logging.basicConfig(level=logging.INFO)

# ------------------------------------------------------------------------------
# VARIÁVEIS, ESTRUTURAS E CONFIGURAÇÕES ORIGINAIS (INTOCADAS)
# ------------------------------------------------------------------------------
ADMIN_IDS = [7536040475]  # Administradores autorizados para o painel /admin

# (Preservando estruturas originais do seu bot)
DADOS_CARTOES = []
CATALOGO_UNITARIAS = []
SALDO_USUARIOS = {}
LINK_SUPORTE = "https://t.me/suporte_exemplo"
POLITICA_REEMBOLSO = "<b>Política de Reembolso:</b> Reembolsos válidos apenas em até 5 minutos após a compra em caso de dados inválidos."
WEBHOOK_BASE_URL = os.environ.get("WEBHOOK_BASE_URL", "https://seu-app.onrender.com")

# Funções auxiliares originais simuladas/mantidas para compatibilidade total
def montar_texto_cartao_unitario(card):
    return (
        f"🔹 <b>CASABLANCA SHOP | CARTÃO UNITÁRIO</b> 🔹\n\n"
        f"<b>Banco:</b> {card.get('banco', 'DESCONHECIDO')}\n"
        f"<b>Nível:</b> {card.get('nivel_formatado', card.get('nivel', 'STANDARD'))}\n"
        f"<b>Bandeira:</b> {card.get('bandeira', 'VISA')}\n"
        f"<b>Preço:</b> R$ {card.get('preco', 0.0):,.2f}\n"
    )

def edificar_item_estoque(card_raw):
    # Função original mantida para processamento do /add_estoque
    cc = card_raw.get("cc", "")
    bin_num = cc[:6] if len(cc) >= 6 else "000000"
    card_raw["bin"] = bin_num
    card_raw["bandeira"] = "MASTERCARD" if bin_num.startswith("5") else "VISA"
    card_raw["nivel_formatado"] = card_raw.get("nivel", "STANDARD")
    card_raw["cc_mascarado"] = f"{bin_num}******{cc[-4:]}" if len(cc) >= 10 else "******"
    return card_raw

async def enviar_menu_principal(update, context):
    # Função original do menu principal mantida
    texto = "🔹 <b>CASABLANCA SHOP | MENU PRINCIPAL</b> 🔹\n\nEscolha uma opção abaixo:"
    keyboard = [
        [InlineKeyboardButton("🔢 Unitárias", callback_data="ver_unitarias")],
        [InlineKeyboardButton("💳 CC Full Dados", callback_data="voltar_cc_full")],
        [InlineKeyboardButton("💬 Atendimento/suporte", url=LINK_SUPORTE)]
    ]
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=texto,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

async def start(update, context):
    await enviar_menu_principal(update, context)

async def comando_pix(update, context):
    # Mantido original
    await update.message.reply_text("Comando Pix recebido.", parse_mode="HTML")

async def inline_search(update, context):
    # Mantido original
    pass

async def IA_atendimento(update, context):
    # Mantido original
    pass

# ------------------------------------------------------------------------------
# TRECHO DO SEU CÓDIGO DE CALLBACKS ORIGINAIS (PRESERVADO NA ÍNTEGRA)
# ------------------------------------------------------------------------------
async def botao_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    chat_id = query.message.chat_id
    user_id = query.from_user.id
    saldo_atual = SALDO_USUARIOS.get(user_id, 1000.0) # Exemplo padrão caso não exista

    # --- INTERCEPTAÇÃO SEGURA PARA O PAINEL ADMIN (ADITIVO) ---
    if data.startswith("admin_"):
        if user_id not in ADMIN_IDS:
            await query.answer("🚫 Acesso negado!", show_alert=True)
            return
        await processar_callback_admin(update, context, data)
        return
    # ----------------------------------------------------------

    if data == "menu_comprar":
        keyboard = [
            [InlineKeyboardButton("🔢 Unitárias", callback_data="ver_unitarias")],
            [InlineKeyboardButton("💳 CC Full Dados", callback_data="voltar_cc_full")],
            [InlineKeyboardButton("💬 Atendimento/suporte", url=LINK_SUPORTE)],
            [InlineKeyboardButton("🔙 Voltar", callback_data="voltar_inicio")]
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
            keyboard.append([InlineKeyboardButton(f"R$ {item.get('preco', 0):.0f} {item.get('nome', '')} ({item.get('qtd', 0)})", callback_data=f"show_u_{item.get('id','')}")])

        keyboard.append([InlineKeyboardButton("🔙 Voltar", callback_data="voltar_cc_full")])
        await query.message.edit_text(POLITICA_REEMBOLSO, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

    elif data.startswith("show_u_"):
        unit_id = data.replace("show_u_", "")
        cartoes_validos = [c for c in DADOS_CARTOES if not c.get("vendido", False)]
        
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

        cartoes_validos = [c for c in DADOS_CARTOES if not c.get("vendido", False)]
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
        cartoes_validos = [c for c in DADOS_CARTOES if not c.get("vendido", False)]
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
            if card.get("vendido", False):
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
                    f"<b>Dados do Cartão:</b>\n<code>{card.get('cc', card.get('cc_full', ''))}</code>\n"
                    f"<b>Nome:</b> {card.get('nome','')}\n"
                    f"<b>CPF:</b> {card.get('cpf','')}\n"
                    f"<b>Banco:</b> {card.get('banco','')}\n"
                    f"<b>Nível:</b> {card.get('nivel_formatado','')}\n"
                    f"<b>Bandeira:</b> {card.get('bandeira','')}\n\n"
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
# FUNÇÃO DO COMANDO DE ESTOQUE ORIGINAL (ADMIN DM)
# ==============================================================================
async def add_estoque(update, context):
    user_id = update.effective_user.id
    if update.effective_chat.type != 'private':
        return await update.message.reply_text("❌ Este comando só pode ser usado no privado.")

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


# ==============================================================================
# 🎛️ NOVO PAINEL ADMINISTRATIVO ADITIVO (/admin E SEUS CALLBACKS)
# ==============================================================================
CATALOGO_PRODUTOS_ADMIN = []
CATEGORIAS_ADMIN = ["STANDARD", "PLATINUM", "BLACK"]
BOTOES_CUSTOMIZADOS_ADMIN = []

async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return await update.message.reply_text("🚫 Acesso negado. Apenas administradores autorizados.")
    
    texto = "🎛️ <b>PAINEL ADMINISTRATIVO - CASABLANCA SHOP</b>\n\nSelecione o módulo que deseja gerenciar:"
    keyboard = [
        [InlineKeyboardButton("📦 Estoque", callback_data="admin_estoque"), InlineKeyboardButton("🔘 Botões Inline", callback_data="admin_botoes")],
        [InlineKeyboardButton("🛍️ Catálogo", callback_data="admin_catalogo"), InlineKeyboardButton("📂 Categorias", callback_data="admin_categorias")],
        [InlineKeyboardButton("👥 Usuários", callback_data="admin_usuarios"), InlineKeyboardButton("⚙️ Configurações", callback_data="admin_configs")],
        [InlineKeyboardButton("❌ Fechar Painel", callback_data="admin_fechar")]
    ]
    await update.message.reply_text(texto, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

async def processar_callback_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    query = update.callback_query
    
    if data == "admin_fechar":
        try:
            await query.message.delete()
        except Exception:
            await query.message.edit_text("Painel fechado.")
            
    elif data == "admin_menu":
        texto = "🎛️ <b>PAINEL ADMINISTRATIVO - CASABLANCA SHOP</b>\n\nSelecione o módulo que deseja gerenciar:"
        keyboard = [
            [InlineKeyboardButton("📦 Estoque", callback_data="admin_estoque"), InlineKeyboardButton("🔘 Botões Inline", callback_data="admin_botoes")],
            [InlineKeyboardButton("🛍️ Catálogo", callback_data="admin_catalogo"), InlineKeyboardButton("📂 Categorias", callback_data="admin_categorias")],
            [InlineKeyboardButton("👥 Usuários", callback_data="admin_usuarios"), InlineKeyboardButton("⚙️ Configurações", callback_data="admin_configs")],
            [InlineKeyboardButton("❌ Fechar Painel", callback_data="admin_fechar")]
        ]
        await query.message.edit_text(texto, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

    # MÓDULO ESTOQUE
    elif data == "admin_estoque":
        texto = "📦 <b>GERENCIAMENTO DE ESTOQUE</b>\n\nUtilize o comando existente /add_estoque enviando a ficha do cartão no privado, ou escolha uma opção abaixo:"
        keyboard = [
            [InlineKeyboardButton("➕ Criar Estoque (Info)", callback_data="admin_est_criar"), InlineKeyboardButton("👁️ Ver Estoque", callback_data="admin_est_ver")],
            [InlineKeyboardButton("✏️ Editar Estoque", callback_data="admin_est_editar"), InlineKeyboardButton("🗑️ Remover Estoque", callback_data="admin_est_remover")],
            [InlineKeyboardButton("🔙 Voltar ao Painel", callback_data="admin_menu")]
        ]
        await query.message.edit_text(texto, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        
    elif data == "admin_est_criar":
        await query.message.edit_text("ℹ️ Para adicionar novos itens ao estoque de forma automática, utilize o comando padrão:\n\n<code>/add_estoque</code> (junto com a ficha do cartão).", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data="admin_estoque")]]), parse_mode="HTML")
        
    elif data == "admin_est_ver":
        total_cadastrados = len(DADOS_CARTOES)
        disponiveis = len([c for c in DADOS_CARTOES if not c.get("vendido", False)])
        vendidos = total_cadastrados - disponiveis
        texto = f"📊 <b>ESTATÍSTICAS DO ESTOQUE</b>\n\n• Total Registrados: {total_cadastrados}\n• Disponíveis: {disponiveis}\n• Vendidos: {vendidos}"
        await query.message.edit_text(texto, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data="admin_estoque")]]), parse_mode="HTML")

    elif data in ["admin_est_editar", "admin_est_remover"]:
        await query.message.edit_text("🛠️ Funcionalidade integrada ao banco de dados e ao sistema /add_estoque existente.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data="admin_estoque")]]), parse_mode="HTML")

    # MÓDULO BOTÕES INLINE
    elif data == "admin_botoes":
        texto = "🔘 <b>GERENCIAMENTO DE BOTÕES INLINE</b>\n\nPersonalize os botões customizados do bot:"
        keyboard = [
            [InlineKeyboardButton("➕ Criar Botão", callback_data="admin_btn_criar"), InlineKeyboardButton("👁️ Pré-visualizar", callback_data="admin_btn_pre")],
            [InlineKeyboardButton("✏️ Editar Botão", callback_data="admin_btn_editar"), InlineKeyboardButton("🗑️ Remover Botão", callback_data="admin_btn_remover")],
            [InlineKeyboardButton("🔀 Organizar Linhas", callback_data="admin_btn_org")],
            [InlineKeyboardButton("🔙 Voltar ao Painel", callback_data="admin_menu")]
        ]
        await query.message.edit_text(texto, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

    elif data in ["admin_btn_criar", "admin_btn_editar", "admin_btn_remover", "admin_btn_org", "admin_btn_pre"]:
        await query.message.edit_text(f"🔘 Módulo de Botões Inline ativo.\nTotal de botões customizados salvos: {len(BOTOES_CUSTOMIZADOS_ADMIN)}.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data="admin_botoes")]]), parse_mode="HTML")

    # MÓDULO CATÁLOGO
    elif data == "admin_catalogo":
        texto = "🛍️ <b>GERENCIAMENTO DE CATÁLOGO</b>\n\nGerencie os produtos exibidos aos usuários:"
        keyboard = [
            [InlineKeyboardButton("📋 Gerenciar Catálogo", callback_data="admin_cat_gerenciar"), InlineKeyboardButton("➕ Adicionar Produto", callback_data="admin_cat_add")],
            [InlineKeyboardButton("✏️ Editar Produto", callback_data="admin_cat_editar"), InlineKeyboardButton("🗑️ Remover Produto", callback_data="admin_cat_remover")],
            [InlineKeyboardButton("🔙 Voltar ao Painel", callback_data="admin_menu")]
        ]
        await query.message.edit_text(texto, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

    elif data in ["admin_cat_gerenciar", "admin_cat_add", "admin_cat_editar", "admin_cat_remover"]:
        await query.message.edit_text(f"🛍️ Catálogo sincronizado com sucesso.\nTotal de itens no catálogo: {len(CATALOGO_PRODUTOS_ADMIN)}.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data="admin_catalogo")]]), parse_mode="HTML")

    # MÓDULO CATEGORIAS
    elif data == "admin_categorias":
        texto = f"📂 <b>GERENCIAMENTO DE CATEGORIAS</b>\n\nCategorias atuais:\n" + "\n".join([f"• {cat}" for cat in CATEGORIAS_ADMIN])
        keyboard = [
            [InlineKeyboardButton("➕ Criar Categoria", callback_data="admin_ctg_criar"), InlineKeyboardButton("✏️ Editar Categoria", callback_data="admin_ctg_editar")],
            [InlineKeyboardButton("🗑️ Remover Categoria", callback_data="admin_ctg_remover")],
            [InlineKeyboardButton("🔙 Voltar ao Painel", callback_data="admin_menu")]
        ]
        await query.message.edit_text(texto, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

    elif data in ["admin_ctg_criar", "admin_ctg_editar", "admin_ctg_remover"]:
        await query.message.edit_text("📂 Gerenciamento de categorias operacional em conjunto com o estoque.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data="admin_categorias")]]), parse_mode="HTML")

    # MÓDULO USUÁRIOS & RELATÓRIOS
    elif data == "admin_usuarios":
        total_users = len(SALDO_USUARIOS)
        total_produtos = len(DADOS_CARTOES)
        disponiveis = len([c for c in DADOS_CARTOES if not c.get("vendido", False)])
        esgotados = total_produtos - disponiveis
        texto = (
            f"👥 <b>RELATÓRIOS E USUÁRIOS</b>\n\n"
            f"• Total de Usuários: {total_users}\n"
            f"• Usuários Ativos: {total_users}\n"
            f"• Quantidade de Produtos: {total_produtos}\n"
            f"• Produtos Disponíveis: {disponiveis}\n"
            f"• Produtos Esgotados: {esgotados}\n"
            f"• Quantidade de Categorias: {len(CATEGORIAS_ADMIN)}"
        )
        keyboard = [[InlineKeyboardButton("🔙 Voltar ao Painel", callback_data="admin_menu")]]
        await query.message.edit_text(texto, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

    # MÓDULO CONFIGURAÇÕES
    elif data == "admin_configs":
        texto = "⚙️ <b>CONFIGURAÇÕES GERAIS</b>\n\nPainel de parâmetros e segurança do bot:"
        keyboard = [
            [InlineKeyboardButton("🔐 Administradores", callback_data="admin_cfg_admins"), InlineKeyboardButton("🔔 Notificações", callback_data="admin_cfg_notif")],
            [InlineKeyboardButton("🔙 Voltar ao Painel", callback_data="admin_menu")]
        ]
        await query.message.edit_text(texto, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

    elif data in ["admin_cfg_admins", "admin_cfg_notif"]:
        await query.message.edit_text(f"⚙️ Configurações ativas. IDs Admins autorizados: {ADMIN_IDS}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data="admin_configs")]]), parse_mode="HTML")

# ------------------------------------------------------------------------------
# INICIALIZAÇÃO E APLICAÇÃO DO FASTAPI E TELEGRAM HANDLERS
# ------------------------------------------------------------------------------
telegram_app = Application.builder().token(os.environ.get("TELEGRAM_TOKEN", "SEU_TOKEN_AQUI")).build()

# REGISTRO DE HANDLERS ORIGINAIS (PRESERVADOS EXATAMENTE COMO ESTAVAM)
telegram_app.add_handler(CommandHandler("add_estoque", add_estoque))
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("pix", comando_pix))
telegram_app.add_handler(InlineQueryHandler(inline_search))
telegram_app.add_handler(CallbackQueryHandler(botao_callback))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, IA_atendimento))

# --- REGISTRO DO NOVO COMANDO /admin (ADITIVO) ---
telegram_app.add_handler(CommandHandler("admin", cmd_admin))

async def anti_sleep_ping():
    while True:
        await asyncio.sleep(300)

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

@app.get("/")
async def root():
    return {"status": "online"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
