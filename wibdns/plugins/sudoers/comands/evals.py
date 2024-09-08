import os
import re
import uuid
import html
import traceback
from meval import meval
from plugins.decorators.check_sudo import check_sudo
from hydrogram import Client, filters
from hydrogram.types import (
    Message, 
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    )

@Client.on_message(filters.command(['eval']))
@check_sudo
async def evals(client: Client, message: Message):
    user_id = message.from_user.id
    try:
        text = message.text.split(maxsplit=1)[1]
    except IndexError:
        return await message.reply_text(f"Exemplo: <code>/eval 'Hello, World!'</code>.")
    
    try:
        res = await meval(text, globals(), **locals())
    except Exception:
        ev = traceback.format_exc()
        await message.reply_text(f"<code>{html.escape(ev)}</code>")
    else:
        result_str = str(res)
        if len(result_str) > 4096:
            filename = f'{os.getcwd()}/documentos/eval_result{uuid.uuid4()}.txt'
            await client.bot.write_to_txt(filename, result_str)
            await client.send_document(chat_id=user_id,file_name="eval_result.txt",document=filename)
            await client.bot.async_remove(filename)
        else:
            await message.reply_text(f"<code>{html.escape(result_str)}</code>")