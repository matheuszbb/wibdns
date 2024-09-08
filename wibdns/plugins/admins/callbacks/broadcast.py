import os
import time
import asyncio
import traceback
from itertools import islice
from datetime import datetime
from plugins.admins.callbacks.adm import adm as adm_callbacks
from plugins.decorators.check_adms import check_adms
from utils import send_message_based_on_type, geter_messages_broadcast
from hydrogram import Client, filters
from hydrogram.types import (
    Message, 
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ForceReply,
)

@Client.on_callback_query(filters.regex('^broadcast$'))
@check_adms
async def broadcast(client: Client, message: Message):
    try:
        adm_id = message.from_user.id
        adm = client.bot.usuarios.get(adm_id).get('user')
        await client.send_message(adm_id,await client.bot.manipular_msg(key_path="broadcast",usuario=adm))
        last_msg = 0
        messages: list[Message] = []
        await geter_messages_broadcast(client, message, messages, adm)

        if not messages:
            return await adm(client,message,recriar=True,msg_adicional=f"\n\n{await client.bot.manipular_msg(key_path='msg_operecao_cancelada')}")
        else:
            sent = await client.send_message(adm_id,await client.bot.manipular_msg(key_path='broadcaster.msg_enviando'))
            all_users = await client.db.get_all_unbanned_users()
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

                if time.time() - last_msg > 3:
                    last_msg = time.time()
                    try:
                        await sent.edit_text(
                            await client.bot.manipular_msg(key_path='broadcaster.msg_enviando_progreco',substitutions={
                                'progreco': f'{(senders / (users_count * len(messages))) * 100:.2f}',
                            })
                        )
                    except:
                        pass
            await sent.edit_text(
                await client.bot.manipular_msg(key_path='broadcaster.msg_enviando_confirmacao',substitutions={
                    'senders': f'{senders}',
                    'users_count': f'{users_count}',
                })
            )
            return await adm_callbacks(client,message,recriar=True,msg_adicional=f"\n\n{await client.bot.manipular_msg(key_path='msg_operecao_sucesso')}")
    except:
        return await adm_callbacks(client,message,recriar=True,msg_adicional=f"\n\n{await client.bot.manipular_msg(key_path='msg_operecao_cancelada')}")