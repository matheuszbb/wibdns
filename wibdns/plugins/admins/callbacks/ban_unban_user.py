import os
import re
from datetime import datetime
from plugins.decorators.check_adms import check_adms
from plugins.admins.callbacks.check_user import check_user_cb
from hydrogram import Client, filters
from hydrogram.types import (
    Message, 
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ForceReply,
    )

@Client.on_callback_query(filters.regex(r'^ban(\d+)$'))
@check_adms
async def ban_user(client, update):
    adm_id = str(update.from_user.id)
    user_id = re.search(r'^ban(\d+)$', update.data).group(1)

    if await client.bot.verificar_sudo_dono_admin(user_id):
        return await check_user_cb(client, update, user_id, recriar=False, msg_adicional=f"\n\n{await client.bot.manipular_msg(key_path='msg_ban_user_cancelado_adm')}")

    try:
        await client.db.set_ban_user(user_id,True)
        if user_id in client.bot.usuarios:
            client.bot.usuarios[user_id]['user']['ban'] = 1
        return await check_user_cb(client, update,user_id=user_id, recriar=False)
    except Exception as e:
        return await check_user_cb(client, update, user_id, recriar=True, msg_adicional=f"\n\n{await client.bot.manipular_msg(key_path='msg_ban_user_erro')}")

@Client.on_callback_query(filters.regex(r'^unban(\d+)$'))
@check_adms
async def unban_user(client, update):
    adm_id = str(update.from_user.id)
    user_id = re.search(r'^unban(\d+)$', update.data).group(1)

    if await client.bot.verificar_sudo_dono_admin(user_id):
        return await check_user_cb(client, update, user_id, recriar=False, msg_adicional=f"\n\n{await client.bot.manipular_msg(key_path='msg_ban_user_cancelado_adm')}")

    try:
        await client.db.set_ban_user(user_id,False)
        if user_id in client.bot.usuarios:
            client.bot.usuarios[user_id]['user']['ban'] = 1
        return await check_user_cb(client, update, user_id, recriar=False)
    except Exception as e:
        return await check_user_cb(client, update, user_id, recriar=True, msg_adicional=f"\n\n{await client.bot.manipular_msg(key_path='msg_unban_user_erro')}")    