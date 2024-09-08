import os
import uuid
from plugins.decorators.check_adms import check_adms
from plugins.decorators.check_donos import check_donos
from hydrogram import Client, filters
from hydrogram.types import (
    Message, 
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ForceReply,
    InlineQueryResultArticle,
    InputTextMessageContent,
)

async def adm(client, update,recriar=False,msg_adicional=""):
    try:
        user_id = update.from_user.id 
        user = await client.db.get_user(user_id)
        
        if await client.bot.verificar_sudo(user_id):
            btn_lt_donos = [InlineKeyboardButton(text=await client.bot.manipular_msg(key_path="btns.listar_donos"), callback_data='listar_donos')]
        else:
            btn_lt_donos = []

        if await client.bot.verificar_sudo_dono(user_id):
            msg_admin = "admin"
            btn_configuracoes = [InlineKeyboardButton(text=await client.bot.manipular_msg(key_path="btns.configuracoes"), callback_data='configuracoes')]
            btn_lt_adms = [InlineKeyboardButton(text=await client.bot.manipular_msg(key_path="btns.listar_adms"), callback_data='listar_admins')]
            btn_relatorios = [InlineKeyboardButton(text=await client.bot.manipular_msg(key_path="btns.relatorios"), callback_data=f'relatorios')]
            btn_servidores = [InlineKeyboardButton(text=await client.bot.manipular_msg(key_path="btns.servidores"), callback_data=f'listar_servidores 0')]
        else: 
            msg_admin ="admin_min"
            btn_lt_adms = []
            btn_configuracoes = []
            btn_relatorios=[]
            btn_servidores=[]

        data = await client.db.get_totais(await client.bot.dia())

        substitutions={
            'total': f'{data["total"]:,.0f}',
            'total_ativo': f'{data["total_ativo"]:,.0f}',
            'total_banido': f'{data["total_banido"]:,.0f}',
        }

        reply_markup=InlineKeyboardMarkup(
            [
                btn_configuracoes,
                [InlineKeyboardButton(await client.bot.manipular_msg(key_path="btns.check_user"), callback_data='check_user')],
                [InlineKeyboardButton(await client.bot.manipular_msg(key_path="btns.broadcast"), callback_data='broadcast')],
                btn_servidores,
                btn_relatorios,
                btn_lt_adms,
                btn_lt_donos,
                [InlineKeyboardButton(await client.bot.manipular_msg(key_path="btns.voltar"), callback_data='start')]
            ]
        )
        msg_criada = await client.bot.manipular_msg(key_path=msg_admin,substitutions=substitutions,usuario=user)
        msg_criada += msg_adicional
        if recriar:
            if client.bot.configuracoes["foto_bot"]:
                return await client.send_photo(user_id, photo=client.bot.configuracoes["foto_bot"], caption=msg_criada, reply_markup=reply_markup)
            return await client.send_message(user_id, msg_criada, reply_markup=reply_markup)
        else:
            return await update.message.edit_text(msg_criada,reply_markup=reply_markup)
    except:pass

@Client.on_callback_query(filters.regex('^adm$'))
@check_adms
async def handle_adm(client, update):
    await adm(client, update)