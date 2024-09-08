import os
import uuid
from plugins.decorators.check_donos import check_donos
from hydrogram import Client, filters
from hydrogram.types import (
    Message, 
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ForceReply,
)

@Client.on_callback_query(filters.regex('^relatorios$'))
@check_donos
async def relatorios(client, update,recriar=False,msg_adicional=""):
    try:
        user_id = update.from_user.id 
        user = client.bot.usuarios.get(user_id).get('user')
        data = await client.db.get_totais()

        substitutions={
            'total': f'{data["total"]:,.0f}',
            'total_ativo': f'{data["total_ativo"]:,.0f}',
            'total_banido': f'{data["total_banido"]:,.0f}',
        }
        
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton(await client.bot.manipular_msg(key_path="btns.relatorios_detalhados"), callback_data=f'relatorios_detalhados {await client.bot.ano()}')],
                [InlineKeyboardButton(await client.bot.manipular_msg(key_path="btns.voltar"), callback_data='adm')],
            ]
        )

        msg_criada = await client.bot.manipular_msg(key_path="relatorios",usuario=user,substitutions=substitutions)
        msg_criada += msg_adicional

        if recriar:
            if client.bot.configuracoes["foto_bot"]:
                return await client.send_photo(user_id, photo=client.bot.configuracoes["foto_bot"], caption=msg_criada, reply_markup=reply_markup)
            return await client.send_message(user_id, msg_criada, reply_markup=reply_markup)             
        else:
            await update.message.edit_text(msg_criada,reply_markup=reply_markup)
    except: return

@Client.on_callback_query(filters.regex(r'^relatorios_detalhados (?P<ano>\d+)'))
@check_donos
async def relatorios_detalhados(client, update,recriar=False,msg_adicional=""):
    try:
        ano_buscado = int(update.matches[0]["ano"])
        user_id = update.from_user.id 
        user = client.bot.usuarios.get(user_id).get('user')
        ano_atual = int(await client.bot.ano())
        ano_primeiro_dns = await client.db.get_ano_primeiro_dns()
        if not ano_primeiro_dns:
            ano_primeiro_dns = ano_atual
        
        lt_anos = list(set(range(ano_primeiro_dns, ano_atual + 1)))

        msg_principal = await client.bot.manipular_msg(key_path="relatorio_detalhado",substitutions={'ano_buscado':ano_buscado})

        for mes in range (1,13):
            if mes < 10:
                data = await client.db.get_totais(f"0{mes}/{ano_buscado}")
            else:
               data = await client.db.get_totais(f"{mes}/{ano_buscado}") 

            substitutions={
                'mes': mes,
                'total': f'{data["total"]:,.0f}',
                'total_ativo': f'{data["total_ativo"]:,.0f}',
                'total_banido': f'{data["total_banido"]:,.0f}',
            }

            msg_principal += f'\n{await client.bot.manipular_msg(key_path="relatorio_detalhes",substitutions=substitutions)}\n'
        

        botoes_anos = [
            InlineKeyboardButton(f"{ano} {await client.bot.manipular_msg(key_path=('btns.status_ativo' if ano == ano_buscado else 'btns.status_desativado'))}", callback_data=f'relatorios_detalhados {ano}')
            for ano in lt_anos
        ]

        botoes_anos_linhas = [botoes_anos[i:i + 3] for i in range(0, len(botoes_anos), 3)]

        botoes_anos_linhas.append(
            [InlineKeyboardButton(await client.bot.manipular_msg(key_path="btns.voltar"), callback_data='relatorios')]
        )

        reply_markup = InlineKeyboardMarkup(botoes_anos_linhas)
        
        msg_principal += msg_adicional

        if recriar:
            return await client.send_message(user_id, msg_principal,reply_markup=reply_markup)
        else:
            if isinstance(update.message, Message) and update.message.photo:
                return await client.send_message(user_id, msg_principal, reply_markup=reply_markup) 
            return await update.message.edit_text(msg_principal,reply_markup=reply_markup)
    except: pass
