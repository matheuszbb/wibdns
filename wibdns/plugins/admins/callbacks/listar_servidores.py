import re
from plugins.decorators.check_donos import check_donos
from plugins.admins.callbacks.check_user import check_user_cb
from hydrogram import Client, filters
from hydrogram.types import (
    Message, 
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ForceReply,
    )

@Client.on_callback_query(filters.regex('^listar_servidores (?P<page>\d+)$'))
@check_donos
async def listar_servidores(client, update, recriar=False, msg_adicional=''):
    try:
        user_id = update.from_user.id 
        try:
            page = int(update.matches[0]["page"])
        except: page = 0
        servidores = await client.db.get_all_servidores()
        items_per_page = 6
        start_index = page * items_per_page
        end_index = start_index + items_per_page
        paginated_servidores = servidores[start_index:end_index]

        msg_lista_admins = await client.bot.manipular_msg(key_path="msg_listar_servidores")
        lt_temp = []

        for i in range(0, len(paginated_servidores), 3):
            row = []
            for j in range(3):
                if i + j < len(paginated_servidores):
                    servidor = paginated_servidores[i + j]
                    msg_temp = '\n' + await client.bot.manipular_msg(key_path='servidor', substitutions={
                        'user': f'{servidor.get("user","")}',
                        'ip': f'{servidor.get("ip","")}',
                        'key': f'{servidor.get("key","")}',
                        'port': f'{servidor.get("port","")}',
                        'id': f'{servidor.get("id","")}',
                    }) + '\n'
                    btn = InlineKeyboardButton(text=f'🆔 Id: {servidor.get("id")}', callback_data=f'remover_servidor:{servidor.get("id")}')
                    row.append(btn)
                    msg_lista_admins += msg_temp
            lt_temp.append(row)

        buttons = []

        if start_index > 0:
            buttons.append(InlineKeyboardButton(await client.bot.manipular_msg(key_path="btns.anterior"), callback_data=f'listar_servidores {page-1}'))
        if end_index < len(servidores):
            buttons.append(InlineKeyboardButton(await client.bot.manipular_msg(key_path="btns.proximo"), callback_data=f'listar_servidores {page+1}'))

        lt_temp.append(buttons)
        lt_temp.append([InlineKeyboardButton(text=await client.bot.manipular_msg(key_path='btns.adicionar_servidor'), callback_data='adicionar_servidor')])
        lt_temp.append([InlineKeyboardButton(text=await client.bot.manipular_msg(key_path='btns.voltar'), callback_data='adm')])
        reply_markup = InlineKeyboardMarkup(lt_temp)

        msg_lista_admins += await client.bot.manipular_msg(key_path="msg_listar_servidores_aviso")
        msg_lista_admins += msg_adicional

        if recriar:
            if client.bot.configuracoes["foto_bot"]:
                return await client.send_photo(user_id, photo=client.bot.configuracoes["foto_bot"], caption=msg_lista_admins, reply_markup=reply_markup)
            return await client.send_message(user_id, msg_lista_admins, reply_markup=reply_markup)           
        else:
            await update.message.edit_text(msg_lista_admins, reply_markup=reply_markup)
    except: return

@Client.on_callback_query(filters.regex('^adicionar_servidor$'))
@check_donos
async def adicionar_servidor(client, update):
    try:
        user_id = update.from_user.id 
        
        while True:
            user = await update.message.ask(await client.bot.manipular_msg(key_path="servidores.msg_user"),reply_markup=ForceReply(),)
            try:
                if user.text in ['/cancelar','/cancel']:
                    return await client.send_message(user_id,await client.bot.manipular_msg(key_path="msg_operecao_cancelada"))
                user = user.text
                break
            except Exception as e:pass

        while True:
            ip = await update.message.ask(await client.bot.manipular_msg(key_path="servidores.msg_ip"),reply_markup=ForceReply(),)
            try:
                if ip.text in ['/cancelar','/cancel']:
                    return await client.send_message(user_id,await client.bot.manipular_msg(key_path="msg_operecao_cancelada"))
                elif re.match(r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$', ip.text):
                    ip = ip.text
                    break
            except Exception as e:pass

        while True:
            key = await update.message.ask(await client.bot.manipular_msg(key_path="servidores.msg_key"),reply_markup=ForceReply(),)
            try:
                if key.text in ['/cancelar','/cancel']:
                    return await client.send_message(user_id,await client.bot.manipular_msg(key_path="msg_operecao_cancelada"))
                key = key.text
                break
            except Exception as e:pass  
        
        while True:
            port = await update.message.ask(await client.bot.manipular_msg(key_path="servidores.msg_port"),reply_markup=ForceReply(),)
            try:
                if port.text in ['/cancelar','/cancel']:
                    return await client.send_message(user_id,await client.bot.manipular_msg(key_path="msg_operecao_cancelada"))
                port = int(port.text)
                break
            except Exception as e:pass 

        await client.db.criar_servidor(user, ip, key, port)
        return await listar_servidores(client, update,recriar=True,msg_adicional=f"\n\n{await client.bot.manipular_msg(key_path='msg_operecao_sucesso')}")    
    except Exception as e: 
        return await listar_servidores(client, update,recriar=True,msg_adicional=f"\n\n{await client.bot.manipular_msg(key_path='msg_operecao_cancelada')}")
    
@Client.on_callback_query(filters.regex('^remover_servidor:'))
@check_donos
async def remover_servidor(client, update):
    try:
        id_servidor = update.data.split(":")[1]
        await client.db.remove_servidor(id_servidor)
        return await listar_servidores(client,update,recriar=False,msg_adicional=f"\n\n{await client.bot.manipular_msg(key_path='msg_operecao_sucesso')}")
    except:
        return await listar_servidores(client,update,recriar=False,msg_adicional=f"\n\n{await client.bot.manipular_msg(key_path='msg_erro_dados_nao_encontrados')}")