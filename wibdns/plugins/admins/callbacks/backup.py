from utils import send_db_backup
from plugins.decorators.check_donos import check_donos
from hydrogram import Client, filters
from hydrogram.types import (
    Message, 
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ForceReply,
    )

@Client.on_callback_query(filters.regex('^backup$'))
@check_donos
async def backup(client, message):
    user_id = message.from_user.id
    try:
        await send_db_backup(client, user_id)
    except:pass