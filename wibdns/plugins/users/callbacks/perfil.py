import os
import re
import uuid
import aiocsv
import asyncio
import aiofiles
from plugins.admins.callbacks.check_user import check_user_cb
from plugins.decorators.check_ban_manutencao import check_ban_manutencao
from datetime import datetime, timedelta
from hydrogram import Client, filters
from hydrogram.types import (
    Message, 
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)    

@Client.on_callback_query(filters.regex('^exibir_perfil$'))
@check_ban_manutencao
async def exibir_perfil(client, update,user_id=None,recriar=False,msg_adicional=""):
    if user_id:
        user_id = user_id
    else:
        user_id = update.from_user.id
    user = await client.db.get_user(user_id)

    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=await client.bot.manipular_msg(key_path="btns.voltar"), callback_data='start')],
    ])

    msg_criada = await client.bot.manipular_msg(key_path="perfil",usuario=user)
    msg_criada += msg_adicional

    if recriar:
        if client.bot.configuracoes["foto_bot"]:
            return await client.send_photo(user_id, photo=client.bot.configuracoes["foto_bot"], caption=msg_criada, reply_markup=reply_markup)
        return await client.send_message(user_id, msg_criada, reply_markup=reply_markup)          
    else:
        return await update.message.edit_text(msg_criada,reply_markup=reply_markup)
