import os
import uuid
from plugins.decorators.check_donos import check_donos
from hydrogram import Client, filters
from hydrogram.types import (
    ListenerTypes,
    Message, 
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ForceReply,
)

async def configuracoes(client, update,recriar=False,msg_adicional=""):
    try:
        user_id = update.from_user.id 
        user = client.bot.usuarios.get(user_id).get('user')
        configuracoes =  client.bot.configuracoes
        btn_manutencao = [InlineKeyboardButton(
            text=await client.bot.manipular_msg(key_path=f"{'btns.manutenca_off' if configuracoes.get('manutencao', False) else'btns.manutenca_on'}"), 
            callback_data=f"{'manutencao_off' if configuracoes.get('manutencao', False) else'manutencao_on'}"
        )]

        reply_markup=InlineKeyboardMarkup(
            [
                btn_manutencao,
                [
                    InlineKeyboardButton(await client.bot.manipular_msg(key_path="btns.atualizar_ft_bot"), callback_data='atualizar_ft_bot'),
                    InlineKeyboardButton(await client.bot.manipular_msg(key_path="btns.remover_ft_bot"), callback_data='remover_ft_bot')
                ],
                [InlineKeyboardButton(await client.bot.manipular_msg(key_path="btns.backup"), callback_data='backup')],
                [InlineKeyboardButton(await client.bot.manipular_msg(key_path="btns.voltar"), callback_data='adm')],
            ]
        )
        msg_criada = await client.bot.manipular_msg(key_path="msg_configuracoes")
        msg_criada += msg_adicional
        if recriar:
            if client.bot.configuracoes["foto_bot"]:
                return await client.send_photo(user_id, photo=client.bot.configuracoes["foto_bot"], caption=msg_criada, reply_markup=reply_markup)
            return await client.send_message(user_id, msg_criada, reply_markup=reply_markup)            
        else:
            await update.message.edit_text(msg_criada,reply_markup=reply_markup)
    except: return

@Client.on_callback_query(filters.regex('^configuracoes$'))
@check_donos
async def handle_configuracoes(client, update):
    await configuracoes(client, update)

@Client.on_callback_query(filters.regex('^manutencao_off$'))
@check_donos
async def manutencao_off(client, update):
    await client.db.set_manutencao(False)
    client.bot.configuracoes["manutencao"]=False
    return await configuracoes(client, update,recriar=False,msg_adicional=f"\n\n{await client.bot.manipular_msg(key_path='msg_operecao_sucesso')}")

@Client.on_callback_query(filters.regex('^manutencao_on$'))
@check_donos
async def manutencao_on(client, update):
    await client.db.set_manutencao(True)
    client.bot.configuracoes["manutencao"]=True
    return await configuracoes(client, update,recriar=False,msg_adicional=f"\n\n{await client.bot.manipular_msg(key_path='msg_operecao_sucesso')}")

@Client.on_callback_query(filters.regex('^atualizar_ft_bot$'))
@check_donos
async def atualizar_ft_bot(client, message):
    try:
        adm_id = message.from_user.id
        adm = client.bot.usuarios.get(adm_id).get('user')
        await client.send_message(adm_id,await client.bot.manipular_msg(key_path="atualizar_ft_bot"))
        msg = await client.listen(filters=filters.incoming,listener_type=ListenerTypes.MESSAGE,timeout=300,chat_id=adm_id)
        foto =  msg.photo.file_id
        await client.db.atualizar_ft_bot(foto)
        client.bot.configuracoes["foto_bot"]=foto
        return await configuracoes(client, message,recriar=True,msg_adicional=f"\n\n{await client.bot.manipular_msg(key_path='msg_operecao_sucesso')}")
    except: return await configuracoes(client, message,recriar=False,msg_adicional=f"\n\n{await client.bot.manipular_msg(key_path='msg_operecao_cancelada')}")

@Client.on_callback_query(filters.regex('^remover_ft_bot$'))
@check_donos
async def remover_ft_bot(client, message):
    try:
        await client.db.atualizar_ft_bot("")
        client.bot.configuracoes["foto_bot"]=""
        return await configuracoes(client, message,recriar=True,msg_adicional=f"\n\n{await client.bot.manipular_msg(key_path='msg_operecao_sucesso')}")
    except: return await configuracoes(client, message,recriar=False,msg_adicional=f"\n\n{await client.bot.manipular_msg(key_path='msg_operecao_cancelada')}")
   















