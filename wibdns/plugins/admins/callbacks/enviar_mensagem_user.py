import os
import re
import time
import asyncio
import traceback
from itertools import islice
from datetime import datetime
from plugins.decorators.check_adms import check_adms
from plugins.admins.callbacks.check_user import check_user_cb
from utils import send_message_based_on_type, geter_messages_broadcast
from hydrogram import Client, filters
from hydrogram.types import (
    Message, 
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ForceReply,
)

@Client.on_callback_query(filters.regex(r'^enviar_mensagem_user(\d+)$'))
@check_adms
async def enviar_mensagem_user(client: Client, message: Message):
    final_id = re.search(r'^enviar_mensagem_user(\d+)$', message.data).group(1)
    adm_id = message.from_user.id
    adm = client.bot.usuarios.get(adm_id).get('user')
    user = await client.db.get_user(adm_id)
    await client.send_message(adm_id,await client.bot.manipular_msg(key_path="broadcast_user",usuario=user))
    messages: list[Message] = []
    await geter_messages_broadcast(client, message, messages, adm)

    if not messages:
        return await check_user_cb(client, message, final_id, recriar=True, msg_adicional=f"\n\n{await client.bot.manipular_msg(key_path='msg_operecao_cancelada')}")  
    else:
        sent = await client.send_message(adm_id,await client.bot.manipular_msg(key_path='broadcaster.msg_enviando'))
        all_users = [await client.db.get_user(final_id)]
        users_count = len(all_users)
        count = 0
        senders = 0
        last_time_out = time.time()
        all_users = (x for x in all_users)
        while True:
            users = list(islice(all_users, 5))

            if not users:
                break

            for msg in messages:
                if  count >= 25 and time.time() - last_time_out <= 1:
                    await asyncio.sleep(0.4)
                    count = 0
                    last_time_out = time.time()
                try:
                    ## se por algum motivo precisar tratar dados usando o db antes de mandar a mensagem nao user o gather
                    ## ele esta fazendo algo errado pois so funciona com primero usuario depois buga entao se precisar use o for normal
                    # for user in users:
                    #     await send_message_based_on_type(client, user, msg)
                    await asyncio.gather(*[send_message_based_on_type(client, user, msg) for user in users])
                except Exception as e:
                    #traceback.print_exc()
                    pass
                senders += len(users)
                count += len(users)
        return await check_user_cb(client, message, final_id, recriar=True, msg_adicional=f"""\n\n{
            await client.bot.manipular_msg(key_path='broadcaster.msg_enviando_confirmacao',
                substitutions={
                    'senders': f'{senders}',
                    'users_count': f'{users_count}',
                })
            }""")