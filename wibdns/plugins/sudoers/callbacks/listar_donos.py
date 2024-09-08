import re
from plugins.decorators.check_sudo import check_sudo
from plugins.admins.callbacks.check_user import check_user_cb
from hydrogram import Client, filters
from hydrogram.types import (
    Message, 
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ForceReply,
)

@Client.on_callback_query(filters.regex('^listar_donos$'))
@check_sudo
async def listar_donos(client, update,recriar=False,msg_adicional=''):
    user_id = update.from_user.id 
    donos = await client.db.get_all_donos()
    msg_lista_donos = await client.bot.manipular_msg(key_path="msg_listar_donos",substitutions={'user_id': user_id})
    lt_temp = []
    for i in range(0, len(donos), 2):
        row = []
        for j in range(2):
            if i + j < len(donos):
                adm = donos[i + j]
                msg_temp = '\n' + await client.bot.manipular_msg(key_path='perfil_adm',usuario=adm) + '\n'
                btn = InlineKeyboardButton(text=f'🆔 Id: {adm.get("id")}', callback_data=f'remover_dono:{adm.get("id")}')
                row.append(btn)
                msg_lista_donos += msg_temp
        lt_temp.append(row)
    msg_lista_donos += await client.bot.manipular_msg(key_path="msg_listar_donos_aviso")
    lt_temp.append([InlineKeyboardButton(text=await client.bot.manipular_msg(key_path='btns.adicionar_dono'), callback_data='promover_dono')])
    lt_temp.append([InlineKeyboardButton(text=await client.bot.manipular_msg(key_path='btns.voltar'), callback_data='adm')])
    reply_markup = InlineKeyboardMarkup(lt_temp)

    msg_lista_donos += msg_adicional

    if recriar:
        if client.bot.configuracoes["foto_bot"]:
            return await client.send_photo(user_id, photo=client.bot.configuracoes["foto_bot"], caption=msg_lista_donos, reply_markup=reply_markup)
        return await client.send_message(user_id, msg_lista_donos, reply_markup=reply_markup)           
    else:
        await update.message.edit_text(msg_lista_donos,reply_markup=reply_markup)

@Client.on_callback_query(filters.regex(r'^promover_dono(\d+)$|^promover_dono$'))
@check_sudo
async def promover_dono(client, update):
    adm_id = str(update.from_user.id)
    try:
        user_id = re.search(r'^promover_dono(\d+)$', update.data).group(1)

        try:
            await client.db.add_dono(user_id)
            return await check_user_cb(client, update, user_id,recriar=False,msg_adicional=f"\n\n{await client.bot.manipular_msg(key_path='msg_promover_dono_adm_confirmacao')}")
        except Exception as e:
            return await check_user_cb(client, update, user_id,recriar=False,msg_adicional=f"\n\n{await client.bot.manipular_msg(key_path='msg_promover_dono_adm_erro')}")
    except:
        try:
            while True:
                user_id = await update.message.ask(await client.bot.manipular_msg(key_path="msg_check_user_cb",substitutions={'user_id': adm_id}),reply_markup=ForceReply())
                try:
                    if user_id.text in ['/cancelar','/cancel']:
                        return await check_user_cb(client, update, user_id,recriar=True,msg_adicional=f"\n\n{await client.bot.manipular_msg(key_path='msg_operecao_cancelada')}")
                    user_id = int(user_id.text)
                    break
                except:pass

            await client.db.add_dono(user_id)
            return await listar_donos(client,update,recriar=True,msg_adicional=f"\n\n{await client.bot.manipular_msg(key_path='msg_promover_dono_adm_confirmacao')}")
        except Exception as e:
            return await listar_donos(client,update,recriar=True,msg_adicional=f"\n\n{await client.bot.manipular_msg(key_path='msg_promover_dono_adm_erro')}")

@Client.on_callback_query(filters.regex('^remover_dono:'))
@check_sudo
async def remover_dono(client, update):
    try:
        id_admin = update.data.split(":")[1]
        await client.db.remove_dono(id_admin)
        return await listar_donos(client,update,recriar=False,msg_adicional=f"\n\n{await client.bot.manipular_msg(key_path='msg_operecao_sucesso')}")
    except:
        return await listar_donos(client,update,recriar=False,msg_adicional=f"\n\n{await client.bot.manipular_msg(key_path='msg_erro_dados_nao_encontrados')}")