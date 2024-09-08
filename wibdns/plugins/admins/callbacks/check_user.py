import os
import re
from plugins.admins.callbacks.adm import adm
from plugins.decorators.check_adms import check_adms
from hydrogram import Client, filters
from hydrogram.types import (
    Message, 
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ForceReply,
)

async def check_user(client, update):
    adm_id = str(update.from_user.id)
    while True:
        user_id = await update.message.ask(await client.bot.manipular_msg(key_path="msg_check_user_cb",substitutions={'user_id': adm_id}),reply_markup=ForceReply(),)
        try:
            if user_id.text in ['/cancelar','/cancel']:
                return await adm(client,update,recriar=True,msg_adicional=f"\n\n{await client.bot.manipular_msg(key_path='msg_operecao_cancelada')}")
            user_id = int(user_id.text)
            break
        except Exception as e:pass  
    
    try:
        user = await client.db.get_user(user_id)
        return await check_user_cb(client, update,user_id,recriar=True)
    except Exception as e:
        return await adm(client,update,recriar=True,msg_adicional=f"\n\n{await client.bot.manipular_msg(key_path='msg_erro_dados_nao_encontrados')}")

async def check_user_cb(client, update,user_id=None,recriar=False,msg_adicional=""):
    if user_id:
        user_id = user_id
    else:
        user_id = re.search(r'^check_user_cb(\d+)$', update.data).group(1)

    adm_id = str(update.from_user.id)

    try:
        user = await client.db.get_user(user_id)

        btn_ban=[]
        btn_pomover_admin=[]
        btn_pomover_dono=[]

        if user['ban']:
            btn_ban = [InlineKeyboardButton(text=await client.bot.manipular_msg(key_path="btns.unban"), callback_data=f'unban{user_id}')]
        elif user['ban'] == False:
            btn_ban = [InlineKeyboardButton(text=await client.bot.manipular_msg(key_path="btns.ban"), callback_data=f'ban{user_id}')]
        elif await client.bot.verificar_sudo_dono_admin(user_id):
            btn_ban=[]

        if await client.bot.verificar_sudo_dono_admin(user_id) == False:
            if await client.bot.verificar_sudo(adm_id):
                btn_pomover_admin=[InlineKeyboardButton(text=await client.bot.manipular_msg(key_path="btns.promover_admin",), callback_data=f'promover_adm{user_id}')]
                btn_pomover_dono=[InlineKeyboardButton(text=await client.bot.manipular_msg(key_path="btns.promover_dono",), callback_data=f'promover_dono{user_id}')]
            elif await client.bot.verificar_sudo_dono(adm_id) == False:
                btn_pomover_admin=[InlineKeyboardButton(text=await client.bot.manipular_msg(key_path="btns.promover_admin",), callback_data=f'promover_adm{user_id}')]

        btn_enviar_mensagem_user=[InlineKeyboardButton(text=await client.bot.manipular_msg(key_path="btns.broadcast_user",), callback_data=f'enviar_mensagem_user{user_id}')]
        
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            btn_ban,
            btn_pomover_dono,
            btn_pomover_admin,
            btn_enviar_mensagem_user,
        ])

        msg_criada = await client.bot.manipular_msg(key_path="perfil",usuario=user)
        msg_criada += msg_adicional
            
        if recriar:
            return await client.send_message(adm_id, msg_criada, reply_markup=reply_markup)
        else:
            return await update.message.edit_text(msg_criada, reply_markup=reply_markup)

    except Exception as e:
        return await adm(client,update,recriar=True,msg_adicional=f"\n\n{await client.bot.manipular_msg(key_path='msg_erro_dados_nao_encontrados')}")

@Client.on_callback_query(filters.regex(r'^check_user_cb(\d+)$'))
@check_adms
async def handle_check_user_cb(client, update):
    await check_user_cb(client, update)

@Client.on_callback_query(filters.regex('^check_user$'))
@check_adms
async def handle_check_user(client, update):
    await check_user(client, update)
