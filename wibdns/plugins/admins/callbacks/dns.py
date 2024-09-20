import os
import re
import html
import uuid
import pypdf
import aiofiles
import paramiko
from plugins.decorators.check_donos import check_donos
from hydrogram import Client, filters, mime_types
from hydrogram.types import (
    Message, 
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ForceReply,
    )

async def ssh_write_to_file(hostname, port, username, password, remote_file_path, data):
    with paramiko.SSHClient() as client:
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname, port=port, username=username, password=password)

        stdin, stdout, stderr = client.exec_command("cat /etc/os-release")
        os_info = stdout.read().decode()
        
        if "Ubuntu" not in os_info and "Debian" not in os_info:
            raise ValueError("Erro OS Desconhecido")

        full_dns = ""
        for dns in data:
            full_dns += f'local-zone: "{dns}" redirect\n'
            full_dns += f'local-data: "{dns} A 127.0.0.1"\n'
            full_dns += f'local-data: "{dns} AAAA ::1"\n'
        
        escaped_full_dns = full_dns.replace('"', '\\"')
        if "Ubuntu" in os_info:
            command = f"echo \"{password}\" | sudo -S bash -c 'echo \"{escaped_full_dns}\" >> {remote_file_path} && sudo systemctl restart unbound'"
        elif "Debian" in os_info:
            command = f"echo \"{password}\" | su -c 'echo \"{escaped_full_dns}\" >> {remote_file_path} && systemctl restart unbound'"
        
        stdin, stdout, stderr = client.exec_command(command)
        stdout.channel.recv_exit_status()

        output = stdout.read().decode()
        errors = stderr.read().decode()
        
        if errors:
            raise ValueError(f"Erro ao executar o comando: {errors}")

async def ssh_remove_from_file(hostname, port, username, password, remote_file_path, data):
    with paramiko.SSHClient() as client:
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname, port=port, username=username, password=password)

        stdin, stdout, stderr = client.exec_command("cat /etc/os-release")
        os_info = stdout.read().decode()
        
        if "Ubuntu" not in os_info and "Debian" not in os_info:
            raise ValueError("Erro OS Desconhecido")

        for dns in data:
            if "Ubuntu" in os_info:
                command = f"echo \"{password}\" | sudo -S bash -c 'sed -i \"/{dns}/d\" {remote_file_path}'"
            elif "Debian" in os_info:
                command = f"echo \"{password}\" | su -c 'sed -i \"/{dns}/d\" {remote_file_path}'"
            stdin, stdout, stderr = client.exec_command(command)
            stdout.channel.recv_exit_status()

        if "Ubuntu" in os_info:
            command = f"echo \"{password}\" | sudo -S bash -c 'systemctl restart unbound'"
        elif "Debian" in os_info:
            command = f"echo \"{password}\" | su -c 'systemctl restart unbound'"
            
        stdin, stdout, stderr = client.exec_command(command)
        stdout.channel.recv_exit_status()

        output = stdout.read().decode()
        errors = stderr.read().decode()
        
        if errors:
            raise ValueError(f"Erro ao executar o comando: {errors}")

async def gestor_dns(client,message,valid_entries,file_name,user_id):
    if len(valid_entries) == 0: 
        try:
            await client.bot.async_remove(file_name)
        except Exception as e: pass
        return await message.reply(await client.bot.manipular_msg(key_path="dns.msg_cancelar_quantidade_validos_zero"))
    
    servidores = await client.db.get_all_servidores()

    if not servidores: 
        try:
            await client.bot.async_remove(file_name)
        except Exception as e: pass
        return await message.reply(await client.bot.manipular_msg(key_path="dns.msg_cancelar_quantidade_servidores_zero"))

    while True:
        resposta = await message.ask(await client.bot.manipular_msg(key_path="dns.msg_pre_ssh"),reply_markup=ForceReply())
        try:
            if resposta.text in ['/cancelar','/cancel']:
                return await message.reply(await client.bot.manipular_msg(key_path="msg_operecao_cancelada"))
            elif resposta.text in ['/desbloquear','/bloquear']:
                resposta = resposta.text
                break
        except:pass

    for servidor in servidores:
        try:
            if resposta == "/bloquear":
                await message.reply(await client.bot.manipular_msg(key_path="dns.msg_inicio_bloquear",substitutions={"validos": f"{len(valid_entries)}","ip": f"{servidor['ip']}"}))
                await ssh_write_to_file(hostname = servidor['ip'], port = servidor['port'], username = servidor['user'], password = servidor['key'], remote_file_path = "/etc/unbound/unbound.conf.d/blocklist.txt", data = valid_entries)
                await message.reply(await client.bot.manipular_msg(key_path="msg_atualizando_dados"))
                for dns in valid_entries:
                    await client.db.add_dns(dns, True, servidor['id'])
                await message.reply(await client.bot.manipular_msg(key_path="msg_operecao_sucesso"))
            else:
                await message.reply(await client.bot.manipular_msg(key_path="dns.msg_inicio_desbloquear",substitutions={"validos": f"{len(valid_entries)}","ip": f"{servidor['ip']}"}))
                await ssh_remove_from_file(hostname = servidor['ip'], port = servidor['port'], username = servidor['user'], password = servidor['key'], remote_file_path = "/etc/unbound/unbound.conf.d/blocklist.txt", data = valid_entries)
                await message.reply(await client.bot.manipular_msg(key_path="msg_atualizando_dados"))
                for dns in valid_entries:
                    await client.db.add_dns(dns, False, servidor['id'])
                await message.reply(await client.bot.manipular_msg(key_path="msg_operecao_sucesso"))
            try:
                await client.bot.async_remove(file_name)
            except Exception as e: pass
        except Exception as e:
            result_str = str(e) 
            if len(result_str) > 4096:
                filename = f'{os.getcwd()}/documentos/erro_log{uuid.uuid4()}.txt'
                await client.bot.write_to_txt(filename, result_str)
                await client.send_document(chat_id=user_id,file_name="erro_log.txt",document=filename)
                await client.bot.async_remove(filename)
            else:
                await message.reply_text(f"<code>{html.escape(result_str)}</code>")

@Client.on_message(filters.document)
@check_donos
async def handle_txt_pdf_file(client, message):
    user_id = message.from_user.id 
    if message.document.mime_type == "text/plain":
        document = message.document
        file_name_original = document.file_name
        file_name = f'{os.getcwd()}/downloads/lista_dns{uuid.uuid4()}.txt'
        await message.download(file_name)
        await message.reply(await client.bot.manipular_msg(key_path="dns.msg_arquivo_recebido",substitutions={"file_name_original":file_name_original}))

        async with aiofiles.open(file_name, 'r', encoding='utf-8') as file:
            lines = await file.readlines()
        
        dns_pattern = re.compile(r'^(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$')
        ipv4_pattern = re.compile(r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$')
        ipv6_pattern = re.compile(r'^(?:[a-fA-F0-9]{1,4}:){7}[a-fA-F0-9]{1,4}$')

        valid_entries = []
        invalid_entries = []
        for line in lines:
            line = line.strip()
            if dns_pattern.match(line) or ipv4_pattern.match(line) or ipv6_pattern.match(line):
                valid_entries.append(line)
            else:
                invalid_entries.append(line)

        await message.reply(await client.bot.manipular_msg(key_path="dns.msg_dados_recebimento",substitutions={
            "total": f"{len(lines)}",
            "validos": f"{len(valid_entries)}",
            "invalidos": f"{len(invalid_entries)}",
        }))

        if len(invalid_entries) >= 1:
            try:
                filename_invalidos = f'{os.getcwd()}/documentos/lista_dns_invalidos{uuid.uuid4()}.txt'
                await client.bot.write_to_txt(filename_invalidos, invalid_entries)
                await client.send_document(chat_id=user_id,file_name="lista_dns_invalidos.txt",document=filename_invalidos)
                await client.bot.async_remove(filename_invalidos)
            except Exception as e: pass

        await gestor_dns(client,message,valid_entries,file_name,user_id)
    
    elif message.document.mime_type == "application/pdf":
        document = message.document
        file_name_original = document.file_name
        file_name = f'{os.getcwd()}/downloads/lista_dns{uuid.uuid4()}.pdf'
        await message.download(file_name)
        await message.reply(await client.bot.manipular_msg(key_path="dns.msg_arquivo_recebido",substitutions={"file_name_original":file_name_original}))

        leitor_pdf = pypdf.PdfReader(file_name)
        texto = ''
        
        for pagina in range(len(leitor_pdf.pages)):
            pagina_obj = leitor_pdf.pages[pagina]
            texto += pagina_obj.extract_text()
        
        padrao_email = r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
        padrao_dns = r'\b(?:[a-zA-Z0-9-]+\.)+(?!gov\b|gov\.br\b)[a-zA-Z]{2,6}\b'
        ipv4_pattern = r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$'
        ipv6_pattern = r'^(?:[a-fA-F0-9]{1,4}:){7}[a-fA-F0-9]{1,4}$'
        
        texto_sem_emails = re.sub(padrao_email, '', texto)
        dns_encontrados = re.findall(padrao_dns, texto_sem_emails)
        v4 = re.findall(ipv4_pattern, texto_sem_emails)
        v6 = re.findall(ipv6_pattern, texto_sem_emails)

        valid_entries = dns_encontrados+v4+v6
        invalid_entries = []

        await message.reply(await client.bot.manipular_msg(key_path="dns.msg_dados_recebimento",substitutions={
            "total": f"{len(valid_entries)}",
            "validos": f"{len(valid_entries)}",
            "invalidos": f"{len(invalid_entries)}",
        }))

        await gestor_dns(client,message,valid_entries,file_name,user_id)