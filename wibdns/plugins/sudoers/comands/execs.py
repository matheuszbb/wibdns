import html
import io
import re
import traceback
from plugins.decorators.check_sudo import check_sudo
from contextlib import redirect_stdout
from hydrogram import Client, filters
from hydrogram.types import (
    Message, 
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    )


@Client.on_message(filters.command(["exec"]))
@check_sudo
async def execs(client: Client, message: Message):
    try:
        code = message.text.split(maxsplit=1)[1]
    except:
        return await message.reply_text(f"Exemplo: <code>/exec print('Hello, World!')</code>.")
    strio = io.StringIO()
    exec(
        "async def __ex(client, message): " + " ".join("\n " + line for line in code.split("\n"))
    ) 
    with redirect_stdout(strio):
        try:
            await locals()["__ex"](client, message)
        except: 
            return await message.reply_text(html.escape(traceback.format_exc()))

    if strio.getvalue().strip():
        out = f"<code>{html.escape(strio.getvalue())}</code>"
    else:
        out = "Command executed."
    await message.reply_text(out)
