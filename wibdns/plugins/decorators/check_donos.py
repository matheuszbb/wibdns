import os
from functools import wraps
from hydrogram import Client, filters
from hydrogram.types import (
    Message, 
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    )

def check_donos(func):
    @wraps(func)
    async def wrapper(client, update, *args, **kwargs):
        try:
            user_id = update.from_user.id
            nome = update.from_user.first_name
            sobrenome = update.from_user.last_name or  ''
            username = f"@{update.from_user.username}" if update.from_user.username else ''

            if user_id not in client.bot.usuarios:
                await client.bot.manager_add_user(user_id, nome, sobrenome, username)       
            
            user = client.bot.usuarios.get(user_id).get('user')

            if user.get('nome') != nome or user.get('sobrenome', '') != sobrenome or user.get('username','@') != username:
                await client.bot.manager_add_user(user_id, nome, sobrenome, username)   
                user = client.bot.usuarios.get(user_id).get('user')
        except: return

        if await client.bot.verificar_sudo_dono(user_id) == False: return

        return await func(client, update, *args, **kwargs)
    return wrapper

