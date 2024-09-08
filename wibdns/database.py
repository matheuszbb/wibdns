import os
import time
import json
import asyncio
import aiosqlite
from random import sample
from datetime import datetime, timedelta

class DB:
    def __init__(self,):
        self.dbpath = "bot.db"
        self.conexao = None
        self.cursor = None

    async def connect(self):
        self.conexao = await aiosqlite.connect(self.dbpath)
        self.conexao.row_factory = aiosqlite.Row
        self.cursor = await self.conexao.cursor()
        await self.cursor.execute("PRAGMA foreign_keys = ON")

    async def close(self):
        await self.conexao.close()

    async def create_tables(self):
        queries = [
            """
CREATE TABLE IF NOT EXISTS usuarios(
    id TEXT PRIMARY KEY,
    nome TEXT,
    sobrenome TEXT,
    username TEXT,
    ban BOOLEAN DEFAULT False
);""",                        
"""
CREATE TABLE IF NOT EXISTS donos(
    id INTEGER PRIMARY KEY AUTOINCREMENT, 
    user_id TEXT UNIQUE REFERENCES usuarios(id) ON DELETE CASCADE
);""", 
"""
CREATE TABLE IF NOT EXISTS admins(
    id INTEGER PRIMARY KEY AUTOINCREMENT, 
    user_id TEXT UNIQUE REFERENCES usuarios(id) ON DELETE CASCADE
);""", 
"""
CREATE TABLE IF NOT EXISTS servidores(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT,
    ip TEXT,
    key TEXT,
    port TEXT
);""",   
"""
CREATE TABLE IF NOT EXISTS dns(
    id INTEGER PRIMARY KEY AUTOINCREMENT, 
    dns TEXT,
    ban BOOLEAN DEFAULT True,
    data_criacao TEXT DEFAULT (datetime('now','localtime')),
    server_id INTEGER REFERENCES servidores(id) ON DELETE CASCADE
);""", 
"""
CREATE TABLE IF NOT EXISTS bot_configs(
    manutencao BOOLEAN DEFAULT True, 
    foto_bot TEXT DEFAULT ''
);""", 
"""
CREATE INDEX IF NOT EXISTS idx_dns_ban ON dns (dns, ban);
""",                           
"""
INSERT INTO bot_configs (manutencao, foto_bot)
SELECT True, ''
WHERE NOT EXISTS (SELECT 1 FROM bot_configs);                                                                                                                                                    
""",
]
        for query in queries:
            await self.cursor.execute(query)
        await self.conexao.commit()

    async def atualizar_valor_bilhete(self, novo_valor_bilhete):
        query = "UPDATE bot_configs SET valor_bilhete = ?"
        params = (novo_valor_bilhete,)
        await self.cursor.execute(query, params)
        await self.conexao.commit()

    async def atualizar_taxa_efi(self, nova_taxa_efi):
        query = "UPDATE bot_configs SET taxa_efi = ?"
        params = (nova_taxa_efi,)
        await self.cursor.execute(query, params)
        await self.conexao.commit()

    async def atualizar_bonus_deposito_btc(self, novo_bonus_deposito_btc):
        query = "UPDATE bot_configs SET bonus_deposito_btc = ?"
        params = (novo_bonus_deposito_btc,)
        await self.cursor.execute(query, params)
        await self.conexao.commit()

    async def criar_evento(self, criador, msgs):
        query = "INSERT INTO eventos (criador, msgs) VALUES (?, ?)"
        params = (criador, msgs)
        await self.cursor.execute(query, params)
        await self.conexao.commit()

    async def copiar_evento(self, evento_id, novo_criador):
        query_select = "SELECT nome, msgs, horas, dias, dias_semana, meses FROM eventos WHERE id = ?"
        params_select = (evento_id,)
        cursor = await self.cursor.execute(query_select, params_select)
        evento = await cursor.fetchone()

        if evento:
            query_insert = """
            INSERT INTO eventos (criador, nome, msgs, horas, dias, dias_semana, meses)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            params_insert = (novo_criador, f"copia {evento['nome']}", evento['msgs'], evento['horas'], evento['dias'], evento['dias_semana'], evento['meses'])
            await self.cursor.execute(query_insert, params_insert)
            await self.conexao.commit()
            
            novo_evento_id = self.cursor.lastrowid
            return novo_evento_id
        else:
            return None

    async def remover_evento(self, id):
        query = "DELETE FROM eventos WHERE id = ?"
        params = (id,)
        await self.cursor.execute(query, params)
        await self.conexao.commit()

    async def atualizar_evento_nome(self, nome, id):
        query = "UPDATE eventos SET nome = ? WHERE id = ?"
        params = (nome,id)
        await self.cursor.execute(query, params)
        await self.conexao.commit()

    async def atualizar_evento_status(self, status, id):
        query = "UPDATE eventos SET status = ? WHERE id = ?"
        params = (status,id)
        await self.cursor.execute(query, params)
        await self.conexao.commit()

    async def atualizar_evento_horas(self, horas, id):
        query = "UPDATE eventos SET horas = ? WHERE id = ?"
        params = (horas,id)
        await self.cursor.execute(query, params)
        await self.conexao.commit()

    async def atualizar_evento_dias(self, dias, id):
        query = "UPDATE eventos SET dias = ? WHERE id = ?"
        params = (dias,id)
        await self.cursor.execute(query, params)
        await self.conexao.commit()

    async def atualizar_evento_dias_semana(self, dias_semana, id):
        query = "UPDATE eventos SET dias_semana = ? WHERE id = ?"
        params = (dias_semana,id)
        await self.cursor.execute(query, params)
        await self.conexao.commit()
    
    async def atualizar_evento_meses(self, meses, id):
        query = "UPDATE eventos SET meses = ? WHERE id = ?"
        params = (meses,id)
        await self.cursor.execute(query, params)
        await self.conexao.commit()

    async def atualizar_evento_msgs(self, msgs, id):
        query = "UPDATE eventos SET msgs = ? WHERE id = ?"
        params = (msgs,id)
        await self.cursor.execute(query, params)
        await self.conexao.commit()

    async def get_evento(self, id):
        query = "SELECT * FROM eventos WHERE id = ?"
        params = (id,)
        await self.cursor.execute(query, params)
        row = await self.cursor.fetchone()
        if row:
            return dict(row)
        else:
            return {}

    async def get_eventos_ativos(self):
        query = "SELECT * FROM eventos WHERE status = 1"
        await self.cursor.execute(query)
        rows = await self.cursor.fetchall()
        if rows:
            return {row['id']: dict(row) for row in rows}
        else:
            return {}

    async def get_eventos(self):
        await self.cursor.execute("SELECT * FROM eventos")
        rows = await self.cursor.fetchall()
        if rows:
            return {row['id']: dict(row) for row in rows}
        else:
            return {}

    async def get_gateways(self):
        query = "SELECT * FROM gateways"
        await self.cursor.execute(query)
        rows = await self.cursor.fetchall()
        if rows:
            return {row['gateway_simbolo']: dict(row) for row in rows}
        else:
            return {}

    async def get_total_usuarios(self):
        query = "SELECT COUNT(*) FROM usuarios"
        await self.cursor.execute(query)
        row = await self.cursor.fetchone()
        return row[0] if row else 0

    async def get_configs(self):
        query = "SELECT * FROM bot_configs"
        await self.cursor.execute(query)
        row = await self.cursor.fetchone()
        return dict(row) if row else {}

    async def add_user(self, user_id, nome, sobrenome, username):
        await self.cursor.execute("SELECT id FROM usuarios WHERE id = ?", (user_id,))
        existing_user = await self.cursor.fetchone()

        if existing_user:
            await self.cursor.execute("UPDATE usuarios SET nome = ?, sobrenome = ?, username = ? WHERE id = ?", (nome, sobrenome, username, user_id))
        else:
            await self.cursor.execute("INSERT INTO usuarios (id, nome, sobrenome, username) VALUES (?, ?, ?, ?)", (user_id, nome, sobrenome, username))

        await self.conexao.commit()

    async def add_dns(self, dns, ban, server_id):
        await self.cursor.execute("SELECT id FROM dns WHERE dns = ? AND server_id = ?", (dns, server_id))
        existing_dns = await self.cursor.fetchone()

        if existing_dns:
            await self.cursor.execute("UPDATE dns SET ban = ? WHERE dns = ? AND server_id = ?", (ban, dns, server_id))
        else:
            await self.cursor.execute("INSERT INTO dns (dns, ban, server_id) VALUES (?, ?, ?)", (dns, ban, server_id))

        await self.conexao.commit()

    async def criar_servidor(self, user, ip, key, port):
        query = "INSERT INTO servidores (user, ip, key, port) VALUES (?, ?, ?, ?)"
        params = (user, ip, key, port)
        await self.cursor.execute(query, params)
        await self.conexao.commit()  

    async def get_all_unbanned_users(self):
        await self.cursor.execute("SELECT * FROM usuarios WHERE ban = False")
        rows = await self.cursor.fetchall()
        return [dict(row) for row in rows] if rows else []
    
    async def get_all_admins(self):
        query = "SELECT usuarios.* FROM admins JOIN usuarios ON admins.user_id = usuarios.id"
        await self.cursor.execute(query)
        rows = await self.cursor.fetchall()
        return [dict(row) for row in rows] if rows else []

    async def get_all_servidores(self):
        query = "SELECT * FROM servidores"
        await self.cursor.execute(query)
        rows = await self.cursor.fetchall()
        return [dict(row) for row in rows] if rows else []

    async def add_admin(self, user_id):
        query = "INSERT INTO admins (user_id) VALUES (?)"
        params = (user_id,)
        await self.cursor.execute(query, params)
        await self.conexao.commit()

    async def remove_admin(self, user_id):
        query = "DELETE FROM admins WHERE user_id = ?"
        params = (user_id,)
        await self.cursor.execute(query, params)
        await self.conexao.commit()

    async def remove_servidor(self, id_servidor):
        query = "DELETE FROM servidores WHERE id = ?"
        params = (id_servidor,)
        await self.cursor.execute(query, params)
        await self.conexao.commit()

    async def get_all_donos(self):
        query = "SELECT usuarios.* FROM donos JOIN usuarios ON donos.user_id = usuarios.id"
        await self.cursor.execute(query)
        rows = await self.cursor.fetchall()
        return [dict(row) for row in rows] if rows else []
    
    async def add_dono(self, user_id):
        query = "INSERT INTO donos (user_id) VALUES (?)"
        await self.cursor.execute(query, (user_id,))
        await self.conexao.commit()

    async def remove_dono(self, user_id):
        query = "DELETE FROM donos WHERE user_id = ?"
        await self.cursor.execute(query, (user_id,))
        await self.conexao.commit()  
    
    async def get_user(self, user_id):
        await self.cursor.execute("SELECT * FROM usuarios WHERE id = ?", (user_id,))
        row = await self.cursor.fetchone()
        return dict(row) if row else None
    
    async def add_remove_saldo(self, user_id, valor):
        query = "UPDATE usuarios SET saldo = saldo + ? WHERE id = ?"
        await self.cursor.execute(query, (valor, user_id))
        await self.conexao.commit()
    
    async def create_deposito(self, valor, id_user, gateway, id_transacao, taxa=0, bonus=0):
        query = "INSERT INTO depositos (valor, dono, gateway, id_transacao, taxa, bonus) VALUES (?, ?, ?, ?, ?, ?)"
        await self.cursor.execute(query, (valor, id_user, gateway, id_transacao, taxa, bonus))
        await self.conexao.commit()

    async def set_manutencao(self, manutencao):
        query = "UPDATE bot_configs SET manutencao = ?"
        await self.cursor.execute(query, (manutencao,))
        await self.conexao.commit()
    
    async def set_ban_user(self, user_id, status=True):
        query = "UPDATE usuarios SET ban = ? WHERE id = ?"
        await self.cursor.execute(query, (status, user_id))
        await self.conexao.commit()

    async def get_plano_proxy(self, id_plano):
        query = "SELECT * FROM plano_proxy WHERE id = ?"
        await self.cursor.execute(query, (id_plano,))
        row = await self.cursor.fetchone()
        return dict(row) if row else None

    async def update_saldo(self, user_id, new_saldo):
        query = "UPDATE usuarios SET saldo = ? WHERE id = ?"
        await self.cursor.execute(query, (new_saldo, user_id))
        await self.conexao.commit()

    async def atualizar_gateway(self, gateway_simbolo, gateway='', access_token='', client_id='', client_secret='', certificate='', chave_pix='', store_id='', api_key=''):
        await self.cursor.execute("SELECT gateway_simbolo FROM gateways WHERE gateway_simbolo = ?", (gateway_simbolo,))
        gateway_existente = await self.cursor.fetchone()
        
        if gateway_existente:
            query = """
                UPDATE gateways
                SET gateway = ?, access_token = ?, client_id = ?, client_secret = ?, certificate = ?, chave_pix = ?, store_id = ?, api_key = ?
                WHERE gateway_simbolo = ?
            """
            params = (gateway, access_token, client_id, client_secret, certificate, chave_pix, store_id, api_key, gateway_simbolo)
        else:
            query = """
                INSERT INTO gateways (gateway_simbolo, gateway, access_token, client_id, client_secret, certificate, chave_pix, store_id, api_key)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (gateway_simbolo, gateway, access_token, client_id, client_secret, certificate, chave_pix, store_id, api_key)
        await self.cursor.execute(query, params)
        await self.conexao.commit()
    
    async def atualizar_gateway_status(self, gateway_simbolo, status = False):
        query = "UPDATE gateways SET status = ? WHERE gateway_simbolo = ?"
        params = (status, gateway_simbolo)
        await self.cursor.execute(query, params)
        await self.conexao.commit()
        
    async def update_grupo_historico(self, new_grupo_historico):
        query = "UPDATE bot_configs SET grupo_historico = ?"
        await self.cursor.execute(query, (new_grupo_historico,))
        await self.conexao.commit()

    async def atualizar_ft_bot(self, foto):
        query = "UPDATE bot_configs SET foto_bot = ?"
        params = (foto,)
        await self.cursor.execute(query, params)
        await self.conexao.commit()

    async def get_all_vendas(self, data):
        if len(data.split("/")) == 3:
            formato_data = '%d/%m/%Y'
        elif len(data.split("/")) == 2:
            formato_data = '%m/%Y'
        else:
            formato_data = '%Y'

        query = f"SELECT * FROM vendas WHERE strftime('{formato_data}', venda_date) = ?"
        params = (data,)
        await self.cursor.execute(query, params)
        rows = await self.cursor.fetchall()
        return [dict(row) for row in rows] if rows else []

    async def get_user_all_vendas(self, dono):
        query = "SELECT * FROM vendas WHERE dono = ?"
        params = (dono,)
        await self.cursor.execute(query, params)
        rows = await self.cursor.fetchall()
        return [dict(row) for row in rows] if rows else []

    async def get_user_all_vendas_numeros_sorteio(self, dono, id_sorteio):
        query = "SELECT * FROM numeros_sorteio WHERE dono = ? AND id_sorteio = ?"
        params = (dono, id_sorteio)
        await self.cursor.execute(query, params)
        rows = await self.cursor.fetchall()
        return [dict(row) for row in rows] if rows else []
    
    async def get_sorteio_all_vendas_numeros_sorteio(self, id_sorteio):
        query = "SELECT * FROM numeros_sorteio WHERE id_sorteio = ?"
        params = (id_sorteio,)
        await self.cursor.execute(query, params)
        rows = await self.cursor.fetchall()
        return [dict(row) for row in rows] if rows else []

    async def create_venda_criar_session(self, dono, session, valor):
        query = "INSERT INTO vendas_criar_session (dono, session, valor) VALUES (?, ?, ?)"
        params = (dono, session, valor)
        await self.cursor.execute(query, params)
        await self.conexao.commit()
    
    async def create_venda(self, dono, produto='', valor=0):
        query = "INSERT INTO vendas (dono, produto, valor) VALUES (?, ?, ?)"
        params = (dono, produto, valor)
        await self.cursor.execute(query, params)
        await self.conexao.commit()

    async def get_soma_vendas(self, data, dono=None):
        if len(data.split("/")) == 3:
            formato_data = '%d/%m/%Y'
        elif len(data.split("/")) == 2:
            formato_data = '%m/%Y'
        else:
            formato_data = '%Y'

        if dono:
            query = f"SELECT SUM(valor) AS total_vendas FROM vendas WHERE dono = ? AND strftime('{formato_data}', venda_date) = ?"
            params = (dono, data)
        else:
            query = f"SELECT SUM(valor) AS total_vendas FROM vendas WHERE strftime('{formato_data}', venda_date) = ?"
            params = (data,)

        await self.cursor.execute(query, params)
        result = await self.cursor.fetchone()
        soma_vendas = result[0] if result and result[0] is not None else 0

        return soma_vendas

    async def get_all_depositos(self, data):
        if len(data.split("/")) == 3:
            formato_data = '%d/%m/%Y'
        elif len(data.split("/")) == 2:
            formato_data = '%m/%Y'
        else:
            formato_data = '%Y'

        query = f"SELECT * FROM depositos WHERE strftime('{formato_data}', add_date) = ?"
        params = (data,)
        await self.cursor.execute(query, params)
        rows = await self.cursor.fetchall()
        return [dict(row) for row in rows] if rows else []
    
    async def get_user_all_depositos(self, dono):
        query = "SELECT * FROM depositos WHERE dono = ?"
        params = (dono,)
        await self.cursor.execute(query, params)
        rows = await self.cursor.fetchall()
        return [dict(row) for row in rows] if rows else []

    async def get_soma_depositos(self, data, gateway=None):
        if len(data.split("/")) == 3:
            formato_data = '%d/%m/%Y'
        elif len(data.split("/")) == 2:
            formato_data = '%m/%Y'
        else:
            formato_data = '%Y'

        if gateway:
            query = f"SELECT SUM(valor) AS total_depositado FROM depositos WHERE gateway = ? AND strftime('{formato_data}', add_date) = ?"
            params = (gateway, data)
        else:
            query = f"SELECT SUM(valor) AS total_depositado FROM depositos WHERE strftime('{formato_data}', add_date) = ?"
            params = (data,)
        await self.cursor.execute(query, params)
        result = await self.cursor.fetchone()
        soma_depositos = result[0] if result and result[0] is not None else 0

        return soma_depositos

    async def get_soma_depositos_descontando_taxas(self, data, gateway=None):
        if len(data.split("/")) == 3:
            formato_data = '%d/%m/%Y'
        elif len(data.split("/")) == 2:
            formato_data = '%m/%Y'
        else:
            formato_data = '%Y'

        if gateway:
            query = f"SELECT SUM(valor - taxa) AS total_depositado FROM depositos WHERE gateway = ? AND strftime('{formato_data}', add_date) = ?"
            params = (gateway, data)
        else:
            query = f"SELECT SUM(valor - taxa) AS total_depositado FROM depositos WHERE strftime('{formato_data}', add_date) = ?"
            params = (data,)

        await self.cursor.execute(query, params)
        result = await self.cursor.fetchone()
        soma_depositos = result[0] if result and result[0] is not None else 0

        return soma_depositos

    async def get_top10saldo(self):
        query = """
            SELECT * FROM usuarios 
            WHERE saldo > 0 
            AND ban = 0 
            AND id NOT IN (SELECT user_id FROM donos) 
            AND id NOT IN (SELECT user_id FROM admins) 
            ORDER BY saldo DESC 
            LIMIT 10
        """
        await self.cursor.execute(query)
        rows = await self.cursor.fetchall()
        return [dict(row) for row in rows] if rows else []
        
    async def get_top10compradores(self):
        query = """
            SELECT dono, COUNT(id) as quantidade, SUM(valor) as total_comprado
            FROM vendas 
            WHERE dono NOT IN (SELECT user_id FROM donos) 
            AND dono NOT IN (SELECT user_id FROM admins) 
            GROUP BY dono 
            ORDER BY quantidade DESC 
            LIMIT 10
        """
        await self.cursor.execute(query)
        rows = await self.cursor.fetchall()
        return [dict(row) for row in rows] if rows else []

    async def get_top10depositantes(self):
        query = """
            SELECT dono, SUM(valor) AS total_depositado 
            FROM depositos 
            WHERE dono NOT IN (SELECT user_id FROM donos) 
            AND dono NOT IN (SELECT user_id FROM admins) 
            GROUP BY dono 
            ORDER BY total_depositado DESC 
            LIMIT 10
        """
        await self.cursor.execute(query)
        rows = await self.cursor.fetchall()
        return [dict(row) for row in rows] if rows else []

    async def get_totais(self, data=None):
        if data:
            if len(data.split("/")) == 3:
                formato_data = '%d/%m/%Y'
            elif len(data.split("/")) == 2:
                formato_data = '%m/%Y'
            else:
                formato_data = '%Y'

            query_total_dns = f"SELECT COUNT(id) AS total FROM dns WHERE strftime('{formato_data}', data_criacao) = ?"
            params = (data,)
            await self.cursor.execute(query_total_dns, params)
        else:
            query_total_dns = "SELECT COUNT(id) AS total FROM dns"
            await self.cursor.execute(query_total_dns)
        
        result_total_dns = await self.cursor.fetchone()
        total_dns = result_total_dns[0] if result_total_dns and result_total_dns[0] is not None else 0

        if data:
            query_total_ativo = f"SELECT COUNT(id) AS total_ativo FROM dns WHERE ban = 0 AND strftime('{formato_data}', data_criacao) = ?"
            await self.cursor.execute(query_total_ativo, params)
        else:
            query_total_ativo = "SELECT COUNT(id) AS total_ativo FROM dns WHERE ban = 0"
            await self.cursor.execute(query_total_ativo)
        
        result_total_ativo = await self.cursor.fetchone()
        total_ativo = result_total_ativo[0] if result_total_ativo and result_total_ativo[0] is not None else 0

        if data:
            query_total_banido = f"SELECT COUNT(id) AS total_banido FROM dns WHERE ban = 1 AND strftime('{formato_data}', data_criacao) = ?"
            await self.cursor.execute(query_total_banido, params)
        else:
            query_total_banido = "SELECT COUNT(id) AS total_banido FROM dns WHERE ban = 1"
            await self.cursor.execute(query_total_banido)
        
        result_total_banido = await self.cursor.fetchone()
        total_banido = result_total_banido[0] if result_total_banido and result_total_banido[0] is not None else 0

        return {
            "total": float(total_dns),
            "total_ativo": float(total_ativo),
            "total_banido": float(total_banido),
        }

    async def get_ano_primeiro_dns(self):
        query = "SELECT MIN(strftime('%Y', data_criacao)) AS ano_primeiro_dns FROM dns"
        await self.cursor.execute(query)
        result = await self.cursor.fetchone()
        ano_primeira_venda = int(result[0]) if result and result[0] is not None else None

        return ano_primeira_venda

    async def get_eventos_status(self):
        query = """
            SELECT 
                COUNT(*) AS quantidade,
                SUM(CASE WHEN status = 1 THEN 1 ELSE 0 END) AS quantidade_on,
                SUM(CASE WHEN status = 0 THEN 1 ELSE 0 END) AS quantidade_off
            FROM eventos
        """
        await self.cursor.execute(query)
        result = await self.cursor.fetchone()
        
        return {
            'quantidade': int(result[0]) if result and result[0] is not None else 0,
            'quantidade_on': int(result[1]) if result and result[1] is not None else 0,
            'quantidade_off': int(result[2]) if result and result[2] is not None else 0,
        }

    async def get_sorteio_mais_recente(self):
        query = """
            SELECT * FROM sorteios WHERE status = "ativo"
            ORDER BY data_criacao DESC
            LIMIT 1
        """
        await self.cursor.execute(query)
        row = await self.cursor.fetchone()
        
        return dict(row) if row else None

    async def criar_sorteio(self, id_criador):
        query = "INSERT INTO sorteios (id_criador) VALUES (?)"
        params = (id_criador,)
        await self.cursor.execute(query, params)
        await self.conexao.commit()
        
        query_id = "SELECT last_insert_rowid()"
        await self.cursor.execute(query_id)
        id_sorteio = await self.cursor.fetchone()
        
        return id_sorteio[0]

    async def gerar_numeros_sorteio(self, id_sorteio):
        query = """
            INSERT INTO numeros_sorteio (id_sorteio, numero, dono, data_compra, valor_pago, sorteado)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        valores = [(id_sorteio, f"{numero:06}", None, None, 0.0, False) for numero in range(1000000)]

        await self.cursor.executemany(query, valores)
        await self.conexao.commit()

    async def get_sorteios(self):
        query = "SELECT * FROM sorteios"
        await self.cursor.execute(query)
        rows = await self.cursor.fetchall()
        if rows:
            return {row['id_sorteio']: dict(row) for row in rows}
        else:
            return {}

    async def get_ultimos_20_sorteios(self, conclidos=False):
        query = "SELECT * FROM sorteios ORDER BY data_criacao DESC LIMIT 20"
        if conclidos: query = "SELECT * FROM sorteios WHERE status != 'pendente' ORDER BY data_criacao DESC LIMIT 20;"
        await self.cursor.execute(query)
        rows = await self.cursor.fetchall()
        if rows:
            return {row['id_sorteio']: dict(row) for row in rows}
        else:
            return {}

    async def get_sorteios_status(self):
        query = """
            SELECT 
                COUNT(*) AS quantidade,
                SUM(CASE WHEN status = 'pendente' THEN 1 ELSE 0 END) AS quantidade_pendente,
                SUM(CASE WHEN status = 'concluido' THEN 1 ELSE 0 END) AS quantidade_concluido,
                SUM(CASE WHEN status = 'cancelado' THEN 1 ELSE 0 END) AS quantidade_cancelado,
                SUM(CASE WHEN status = 'ativo' THEN 1 ELSE 0 END) AS quantidade_ativo
            FROM sorteios
        """
        await self.cursor.execute(query)
        result = await self.cursor.fetchone()
        
        return {
            'quantidade': int(result[0]) if result and result[0] is not None else 0,
            'quantidade_pendente': int(result[1]) if result and result[1] is not None else 0,
            'quantidade_concluido': int(result[2]) if result and result[2] is not None else 0,
            'quantidade_cancelado': int(result[3]) if result and result[3] is not None else 0,
            'quantidade_ativo': int(result[4]) if result and result[3] is not None else 0,
        }

    async def atualizar_sorteio_msg(self, msg, id):
        query = "UPDATE sorteios SET msg = ? WHERE id_sorteio = ?"
        params = (msg,id)
        await self.cursor.execute(query, params)
        await self.conexao.commit()
    
    async def atualizar_ft_sorteio(self, foto, id):
        query = "UPDATE sorteios SET ft_premio = ? WHERE id_sorteio = ?"
        params = (foto,id)
        await self.cursor.execute(query, params)
        await self.conexao.commit()

    async def atualizar_ft_bub_sorteio(self, foto, id):
        query = "UPDATE sorteios SET ft_sub_premio = ? WHERE id_sorteio = ?"
        params = (foto,id)
        await self.cursor.execute(query, params)
        await self.conexao.commit()

    async def get_sorteio(self, id_sorteio):
        query = "SELECT * FROM sorteios WHERE id_sorteio = ?"
        params = (id_sorteio,)
        await self.cursor.execute(query, params)
        row = await self.cursor.fetchone()
        
        if row:
            return dict(row)
        else:
            return {}

    async def get_ultimo_sorteio_concluido(self):
        query = "SELECT * FROM sorteios WHERE status = 'concluido' ORDER BY data_criacao DESC LIMIT 1;"
        await self.cursor.execute(query)
        row = await self.cursor.fetchone()
        
        if row:
            return dict(row)
        else:
            return {}        

    async def remover_sorteio(self, id_sorteio):
        query = "DELETE FROM sorteios WHERE id_sorteio = ?"
        params = (id_sorteio,)
        await self.cursor.execute(query, params)
        await self.conexao.commit()

    async def checagem_sorteio_pre_concluir(self, id_sorteio):
        query = "SELECT 1 FROM numeros_sorteio WHERE status = 'disponivel' AND id_sorteio = ? LIMIT 1"
        params = (id_sorteio,)
        await self.cursor.execute(query, params)
        row = await self.cursor.fetchone()
        return row is not None

    async def checagem_sorteio_pre_delete(self, id_sorteio):
        query = "SELECT 1 FROM numeros_sorteio WHERE status = 'comprado' AND id_sorteio = ? LIMIT 1"
        params = (id_sorteio,)
        await self.cursor.execute(query, params)
        row = await self.cursor.fetchone()
        return row is not None

    async def get_numeros_sorteio_com_dono(self, id_sorteio):
        query = """
            SELECT dono, 
                SUM(valor_pago) AS total_pago, 
                COUNT(numero) AS quantidade_numeros,
                GROUP_CONCAT(numero) AS numeros
            FROM numeros_sorteio
            WHERE dono IS NOT NULL AND id_sorteio = ?
            GROUP BY dono
        """
        params = (id_sorteio,)
        await self.cursor.execute(query, params)
        rows = await self.cursor.fetchall()
        
        resultado = {}
        if rows:
            for row in rows:
                resultado[row['dono']] = {
                    'total_pago': row['total_pago'],
                    'quantidade_numeros': row['quantidade_numeros'],
                    'numeros': row['numeros'].split(',')
                }
        
        return resultado

    async def atualizar_sorteio_status(self, status, id_sorteio):
        query = "UPDATE sorteios SET status = ? WHERE id_sorteio = ?"
        if status == 'cancelado':
            query = "UPDATE sorteios SET status = ?, data_cancelamento = (datetime('now','localtime')) WHERE id_sorteio = ?"
        params = (status, id_sorteio)
        await self.cursor.execute(query, params)
        await self.conexao.commit()

    async def remover_dono_numero_sorteio(self, id_sorteio, dono):
        query_select = "SELECT SUM(valor_pago) as total_valor_pago FROM numeros_sorteio WHERE id_sorteio = ? AND dono = ?"
        params_select = (id_sorteio, dono)
        await self.cursor.execute(query_select, params_select)
        row = await self.cursor.fetchone()

        if row and row['total_valor_pago'] is not None:
            total_valor_pago = row['total_valor_pago']

            query_update_saldo = "UPDATE usuarios SET saldo = saldo + ? WHERE id = ?"
            params_update_saldo = (total_valor_pago, dono)
            await self.cursor.execute(query_update_saldo, params_update_saldo)

            query_update_numero = "UPDATE numeros_sorteio SET status = 'disponivel', dono = '', valor_pago = 0, data_compra = '' WHERE id_sorteio = ? AND dono = ?"
            params_update_numero = (id_sorteio, dono)
            await self.cursor.execute(query_update_numero, params_update_numero)

            await self.conexao.commit()

    async def cancelar_dono_numero_sorteio(self, id_sorteio, dono):
        query_select = "SELECT SUM(valor_pago) as total_valor_pago FROM numeros_sorteio WHERE id_sorteio = ? AND dono = ?"
        params_select = (id_sorteio, dono)
        await self.cursor.execute(query_select, params_select)
        row = await self.cursor.fetchone()

        if row and row['total_valor_pago'] is not None:
            total_valor_pago = row['total_valor_pago']

            query_update_saldo = "UPDATE usuarios SET saldo = saldo + ? WHERE id = ?"
            params_update_saldo = (total_valor_pago, dono)
            await self.cursor.execute(query_update_saldo, params_update_saldo)

            query_update_numero = "UPDATE numeros_sorteio SET status = 'cancelado', data_cancelamento = (datetime('now','localtime')) WHERE id_sorteio = ? AND dono = ?"
            params_update_numero = (id_sorteio, dono)
            await self.cursor.execute(query_update_numero, params_update_numero)

            await self.conexao.commit()

    async def get_estatisticas_consumo_numeros_sorteio(self, id_sorteio):
        query = """
            SELECT 
                COUNT(*) AS total,
                SUM(CASE WHEN status IN ('comprado', 'cancelado') THEN 1 ELSE 0 END) AS comprados,
                SUM(CASE WHEN status = 'disponivel' THEN 1 ELSE 0 END) AS disponiveis,
                COALESCE(SUM(valor_pago), 0) AS lucro
            FROM numeros_sorteio
            WHERE id_sorteio = ?
        """
        params = (id_sorteio,)
        await self.cursor.execute(query, params)
        row = await self.cursor.fetchone()
        
        resultado = {
            "total": row['total'] if row['total'] is not None else 0,
            "comprados": row['comprados'] if row['comprados'] is not None else 0,
            "disponiveis": row['disponiveis'] if row['disponiveis'] is not None else 0,
            "lucro": row['lucro'] if row['lucro'] is not None else 0
        }

        return resultado

    async def get_all_numeros_sorteio(self, id_sorteio):
        query = "SELECT * FROM numeros_sorteio WHERE id_sorteio = ?"
        params = (id_sorteio,)
        await self.cursor.execute(query, params)
        rows = await self.cursor.fetchall()
        
        resultado = {row['numero']: dict(row) for row in rows} if rows else {}
        
        return resultado
    
    async def compra_numeros_sorteio(self, id_sorteio, numeros, dono, valor):
        query = """
            UPDATE numeros_sorteio 
            SET dono = ?, data_compra = (datetime('now','localtime')), valor_pago = ?, status = 'comprado'
            WHERE id_sorteio = ? AND numero = ?
        """
        params = [(dono, valor, id_sorteio, numero) for numero in numeros]
        await self.cursor.executemany(query, params)
        await self.conexao.commit()

    async def create_vendas_numeros_sorteio(self, user_id, lt_numeros_comprados, sorteio_id, valor_bilhete):
        query = "INSERT INTO vendas_numeros_sorteio (dono, numero, id_sorteio, valor) VALUES (?, ?, ?, ?)"
        params = [(user_id, numero, sorteio_id, valor_bilhete) for numero in lt_numeros_comprados]
        await self.cursor.executemany(query, params)
        await self.conexao.commit()

    async def get_all_sorteios(self, data):
        if len(data.split("/")) == 3:
            formato_data = '%d/%m/%Y'
        elif len(data.split("/")) == 2:
            formato_data = '%m/%Y'
        else:
            formato_data = '%Y'

        query = f"SELECT * FROM sorteios WHERE strftime('{formato_data}', data_criacao) = ?"
        params = (data,)
        await self.cursor.execute(query, params)
        rows = await self.cursor.fetchall()
        return [dict(row) for row in rows] if rows else []

    async def atualizar_numero_vencedor(self, id_sorteio, numero):
        query_update = "UPDATE numeros_sorteio SET sorteado = 1 WHERE id_sorteio = ? AND numero = ?"
        params_update = (id_sorteio, numero)
        await self.cursor.execute(query_update, params_update)
        await self.conexao.commit()

        query_select = "SELECT dono FROM numeros_sorteio WHERE id_sorteio = ? AND numero = ? AND sorteado = 1"
        params_select = (id_sorteio, numero)
        await self.cursor.execute(query_select, params_select)
        resultado = await self.cursor.fetchone()
        return resultado[0] if resultado else ''
    
    async def atualizar_sorteio_conclusao(self, id_sorteio, id_mega, dados):
        query = "UPDATE sorteios SET dados = ?, id_sorteio_api = ?, status = 'concluido', data_resultado = (datetime('now','localtime')) WHERE id_sorteio = ?"
        params = (dados, id_mega, id_sorteio)
        await self.cursor.execute(query, params)
        await self.conexao.commit()

    async def atualiza_numeros_sorteio_conclusao(self, id_sorteio):
        query = "UPDATE numeros_sorteio SET data_resultado = (datetime('now','localtime')) WHERE id_sorteio = ?"
        params = (id_sorteio,)
        await self.cursor.execute(query, params)
        await self.conexao.commit()

    async def gerar_sub_premio(self, id_sorteio, quantidade_sub_premio):
        dc_sub_premios = {}

        if quantidade_sub_premio > 0:
            query_count = """
                SELECT COUNT(*) as total_sub_premios FROM numeros_sorteio
                WHERE id_sorteio = ? AND sub_premio = 1
            """
            params_count = (id_sorteio,)
            await self.cursor.execute(query_count, params_count)
            row = await self.cursor.fetchone()

            if row and row['total_sub_premios'] is not None:
                sub_premios_atuais = row['total_sub_premios']

                if sub_premios_atuais < quantidade_sub_premio:
                    query_select = "SELECT id, numero FROM numeros_sorteio WHERE id_sorteio = ?"
                    params_select = (id_sorteio,)
                    await self.cursor.execute(query_select, params_select)
                    ids_disponiveis = await self.cursor.fetchall()

                    ids_para_sub_premio = sample(ids_disponiveis, quantidade_sub_premio - sub_premios_atuais)
                    query_update = "UPDATE numeros_sorteio SET sub_premio = 1 WHERE id = ?"
                    params_update = [(id['id'],) for id in ids_para_sub_premio]
                    await self.cursor.executemany(query_update, params_update)

                    dc_sub_premios = {id['numero']: {"id": "", "numero": id['numero']} for id in ids_para_sub_premio}
                else:
                    query_select = "SELECT id, numero FROM numeros_sorteio WHERE id_sorteio = ? AND sub_premio = 1"
                    params_select = (id_sorteio,)
                    await self.cursor.execute(query_select, params_select)
                    ids_sub_premios_atuais = await self.cursor.fetchall()

                    ids_para_desativar = sample(ids_sub_premios_atuais, sub_premios_atuais - quantidade_sub_premio)
                    query_update = "UPDATE numeros_sorteio SET sub_premio = 0 WHERE id = ?"
                    params_update = [(id['id'],) for id in ids_para_desativar]
                    await self.cursor.executemany(query_update, params_update)

                    dc_sub_premios = {id['numero']: {"id": "", "numero": id['numero'],"data_compra":""} for id in ids_sub_premios_atuais}

            await self.conexao.commit()
        else:
            query = "UPDATE numeros_sorteio SET sub_premio = 0 WHERE id_sorteio = ? AND sub_premio = 1"
            params = (id_sorteio,)
            await self.cursor.execute(query, params)
            await self.conexao.commit()
            dc_sub_premios = {}

        query_select_dados = "SELECT dados FROM sorteios WHERE id_sorteio = ?"
        params_select_dados = (id_sorteio,)
        await self.cursor.execute(query_select_dados, params_select_dados)
        row = await self.cursor.fetchone()

        if row and row['dados']:
            dados_json = json.loads(row['dados'])

            dados_json['sub_vencedores'] = dc_sub_premios

            query_update_dados = "UPDATE sorteios SET dados = ? WHERE id_sorteio = ?"
            params_update_dados = (json.dumps(dados_json), id_sorteio)
            await self.cursor.execute(query_update_dados, params_update_dados)

            await self.conexao.commit()

    async def atualizar_sub_premio(self, id_sorteio, numero_sorteado, user_id):
        query_update_dados = "UPDATE numeros_sorteio SET sub_sorteado = 1 WHERE id_sorteio = ? AND numero = ?"
        params_update_dados = (id_sorteio, numero_sorteado)
        await self.cursor.execute(query_update_dados, params_update_dados)

        await self.conexao.commit()

        query_select_dados = "SELECT dados FROM sorteios WHERE id_sorteio = ?"
        params_select_dados = (id_sorteio,)
        await self.cursor.execute(query_select_dados, params_select_dados)
        row = await self.cursor.fetchone()

        if row and row['dados']:
            dados_json = json.loads(row['dados'])

            dados_json['sub_vencedores'][str(numero_sorteado)]["id"] = str(user_id)
            dados_json['sub_vencedores'][str(numero_sorteado)]["data_compra"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            query_update_dados = "UPDATE sorteios SET dados = ? WHERE id_sorteio = ?"
            params_update_dados = (json.dumps(dados_json), id_sorteio)
            await self.cursor.execute(query_update_dados, params_update_dados)

            await self.conexao.commit()

    # async def count_all_produtos(self):
    #     query = "SELECT COUNT(*) FROM produtos"
    #     await self.cursor.execute(query)
    #     count = await self.cursor.fetchone()
    #     return count[0] if count else 0

    # async def get_precos(self):
    #     query = "SELECT * FROM precos ORDER BY quantidade_minima ASC"
    #     await self.cursor.execute(query)
    #     rows = await self.cursor.fetchall()
    #     return [dict(row) for row in rows] if rows else []
    
    # async def get_preco(self, quantidade):
    #     query = "SELECT valor FROM precos WHERE quantidade_minima <= ? ORDER BY quantidade_minima DESC LIMIT 1"
    #     await self.cursor.execute(query, (quantidade,))
    #     row = await self.cursor.fetchone()
    #     return row[0] if row else None