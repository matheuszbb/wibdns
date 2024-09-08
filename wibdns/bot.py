import os
import re
import yaml
import aiocsv
import asyncio
import aiofiles
from functools import wraps
from string import Template
from datetime import datetime, timedelta

class MyBot():
    def __init__(self,db,sudo_id,*args, **kwargs):
        self.db = db
        self.sudo_id = sudo_id
        self.usuarios = {}
        self.mensagem_sorteio_atual = ""
        self.id_sorteio_atual = ""
        self.numeros_sorteio_atual = {}
        self.total_usuarios = 0
        self.numeros_sorteio_atual_disponiveis = 0
        self.configuracoes = {}
        asyncio.create_task(self.initialize_bot())

    async def initialize_bot(self):
        await self.get_bot_configuracoes()

    async def get_bot_configuracoes(self):
        self.configuracoes = await self.db.get_configs()

    async def manager_add_user(self,user_id, first_name, last_name, username):
        await self.db.add_user(user_id, first_name, last_name, username)
        user = await self.db.get_user(user_id)
        await self.add_usuarios(user_id,user)  

    async def add_usuarios(self,user_id,user):   
        if user_id not in self.usuarios:
            self.usuarios[user_id] = {}
            self.usuarios[user_id].update({'user': user})
            self.usuarios[user_id].setdefault('numeros_sorteio', 0)
            self.total_usuarios = f'{await self.db.get_total_usuarios()}'

    async def hora_do_dia(self):
        horario = int(datetime.now().strftime("%H")) 
        if horario >= 18:
            return 'Boa Noite'
        elif horario <= 11:
            return 'Bom Dia'
        else:
            return 'Boa Tarde'

    async def dia_semana(self):
        return datetime.now().weekday()

    async def date_time(self):   
        return datetime.now().strftime("%d/%m/%Y %H:%M:%S")   

    async def dia(self):   
        return datetime.now().strftime("%d/%m/%Y") 
    
    async def mes(self):   
        return datetime.now().strftime("%m/%Y") 
    
    async def ano(self):   
        return datetime.now().strftime("%Y") 

    async def hora(self):  
        return datetime.now().strftime("%H:%M:%S")

    async def hora_minuto(self):  
        return datetime.now().strftime("%H:%M")   

    async def verifica_date_patterns(self,date):
        date_patterns = [
            r"\b(0[1-9]|1[0-9]|2[0-9]|3[01])/(0[1-9]|1[0-2])/([0-9]{4})\b",  # 05/12/2024
            r"\b(0[1-9]|1[0-2])/([0-9]{4})\b",  # 12/2024
            r"\b([0-9]{4})\b"  # 2024
        ]
        if any(re.fullmatch(pattern, date) for pattern in date_patterns):
            return True
        else: return False
    
    def async_cache(func):
        cache = {}
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if args not in cache:
                cache[args] = await func(*args, **kwargs)
            return cache[args]

        return wrapper

    @async_cache
    async def get_yaml(self):
        async with aiofiles.open('yamls/config.yaml', 'r', encoding='utf-8') as file:
            return yaml.safe_load(await file.read())

    async def get_default_substitutions(self, usuario=None,*args,**kwargs):
        data_user = {}
        if usuario:
            data_user = {
                'user_id': usuario.get("id",''),
                'nome': usuario.get("nome",''),
                'sobrenome': usuario.get("sobrenome",''),
                'username': usuario.get("username",''),
                'ban': "🚫 Usuário banido" if usuario.get("ban",0) else "✅ Usuário ativo",
                }
        return {
            'hora_do_dia': await self.hora_do_dia(),
            'date_time': await self.date_time(),
            'dia': await self.dia(),
            'mes': await self.mes(),
            'ano': await self.ano(),
            'hora': await self.hora(),
            'hora_minuto': await self.hora_minuto(),
            'msg_manutencao': "Ativa, Bot bloqueado" if self.configuracoes.get("manutencao") else "Desativada, Bot aberto",
            'grupo_historico': self.configuracoes.get("grupo_historico", ''),
            'total_usuarios': self.total_usuarios,
            **data_user
        }

    async def manipular_msg(self, key_path=None, msg=None, usuario=None, substitutions={}, *args,**kwargs):
        if msg:
            mensagens = msg
        else:
            keys = key_path.split('.')
            mensagens = await self.get_yaml()
            for key in keys:
                mensagens = mensagens[key]
        template = Template(mensagens)
        substitutions = {**await self.get_default_substitutions(usuario), **substitutions}
        return template.safe_substitute(substitutions)  
          
    async def verificar_sudo(self, user_id):
        if str(user_id) in [str(self.sudo_id)]:return True
        else :return False

    async def verificar_dono(self, user_id):
        if str(user_id) in ([user['id'] for user in await self.db.get_all_donos()]):return True
        else :return False

    async def verificar_admin(self, user_id):
        if str(user_id) in ([user['id'] for user in await self.db.get_all_admins()]):return True
        else :return False

    async def verificar_sudo_dono(self, user_id):
        if str(user_id) in ([user['id'] for user in await self.db.get_all_donos()]+[str(self.sudo_id)]):return True
        else :return False

    async def verificar_sudo_dono_admin(self, user_id):
        if str(user_id) in ([user['id'] for user in await self.db.get_all_admins()]+[user['id'] for user in await self.db.get_all_donos()]+[str(self.sudo_id)]):return True
        else :return False

    async def write_to_txt(self, filename, content):
        async with aiofiles.open(filename, mode='w') as txtfile:
            if isinstance(content, list):
                for item in content:
                    await txtfile.write(f"{item}\n")
            else:
                await txtfile.write(content)

    async def write_to_csv(self, filename, headers, data):
        async with aiofiles.open(filename, mode='w', newline='') as csvfile:
            writer = aiocsv.AsyncWriter(csvfile, delimiter=',')
            await writer.writerow(headers)
            for row in data:
                if isinstance(row, dict):
                    values = [f"{value:.2f}".replace('.', ',') if isinstance(value, float) else value for value in row.values()]
                else:
                    values = row
                await writer.writerow(values)

    async def async_remove(self,filename):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, os.remove, filename)
