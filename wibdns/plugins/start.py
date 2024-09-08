import os
from .decorators.check_ban_manutencao import check_ban_manutencao
from datetime import datetime, timedelta
from hydrogram import Client, filters
from hydrogram.types import (
    Message, 
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    )

async def start(client, update, recriar=False, msg_adicional=''):
    user_id = update.from_user.id
    user = await client.db.get_user(user_id)

    if await client.bot.verificar_sudo_dono_admin(user_id):
        btn_adm = [InlineKeyboardButton(await client.bot.manipular_msg("btns.administracao"), callback_data="adm")]
        reply_markup = InlineKeyboardMarkup([btn_adm])
    else:
        btn_adm = []
        reply_markup = None

    msg_principal = await client.bot.manipular_msg(key_path="start", usuario=user)

    msg_principal += msg_adicional

    if recriar:
        if client.bot.configuracoes["foto_bot"]:
            return await client.send_photo(user_id, photo=client.bot.configuracoes["foto_bot"], caption=msg_principal, reply_markup=reply_markup)
        return await client.send_message(user_id, msg_principal, reply_markup=reply_markup)
    elif isinstance(update, Message):
        if client.bot.configuracoes["foto_bot"]:
            return await client.send_photo(user_id, photo=client.bot.configuracoes["foto_bot"], caption=msg_principal, reply_markup=reply_markup)
        return await client.send_message(user_id, msg_principal, reply_markup=reply_markup)
    else:
        return await update.message.edit_text(msg_principal,reply_markup=reply_markup)

@Client.on_message(filters.command(["start"]))
@Client.on_callback_query(filters.regex('^start$'))
@check_ban_manutencao
async def handle_start(client, update):
    await start(client, update)
