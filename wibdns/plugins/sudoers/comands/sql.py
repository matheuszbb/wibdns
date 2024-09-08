import io
import os
import uuid
import aiocsv
import asyncio
import aiofiles
from sqlite3 import IntegrityError, OperationalError, ProgrammingError
from plugins.decorators.check_sudo import check_sudo
from hydrogram import Client, filters
from hydrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

@Client.on_message(filters.command(["sql"]))
@check_sudo
async def run_sql(client: Client, message: Message):
    try:
        command = message.text.split(maxsplit=1)[1]
    except:
        return await message.reply_text(f"Exemplo: <code>/sql SELECT * FROM bot_configs;</code>.")
    
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="☠ Deletar", callback_data="delete")]
        ]
    )

    try:
        ex = await client.db.cursor.execute(command)
        ret = await ex.fetchall()
        await client.db.conexao.commit()
    except (IntegrityError, OperationalError, ProgrammingError) as e:
        return await message.reply_text(
            f"SQL executado com erro: {e.__class__.__name__}: {e}",
            quote=True,
            reply_markup=kb,
        )

    if ret:
        headers = [name[0] for name in ex.description]
        data = [[str(s) for s in items] for items in ret]
        filename = f'{os.getcwd()}/documentos/consulta_sql_{uuid.uuid4()}.csv'
        await client.bot.write_to_csv(filename, headers, data)
        await message.reply_document(document=filename, file_name="consulta_sql.csv", quote=True, reply_markup=kb)
        await client.bot.async_remove(filename)
    else:
        await message.reply_text(
            "SQL executado com sucesso ou sem retornos.", quote=True, reply_markup=kb
        )

@Client.on_callback_query(filters.regex(r"^delete"))
async def delet(client: Client, query: CallbackQuery):
    try:
        await query.message.delete()
        await query.message.reply_to_message.delete()
    except:pass
