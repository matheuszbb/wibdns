import os
import time
import json
import uvloop
import asyncio
import platform
import traceback
from bot import MyBot
from database import DB
from itertools import islice
from datetime import datetime, timedelta
from hydrogram import Client, enums, idle
from hydrogram.types import (
    Message, 
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ForceReply,
)

async def main():
    db = DB() 
    sudo_id = str(os.getenv('SUDO_ID', ''))
    await db.connect()
    await db.create_tables()
    bot = MyBot(db,sudo_id)
    client = Client(
        name="my_bot",
        bot_token=os.getenv('BOT_TOKEN', None),
        api_id=os.getenv('API_ID', None),
        api_hash=os.getenv('API_HASH', None),
        parse_mode=enums.ParseMode.HTML,
        workers=30,
        plugins={'root': 'plugins'},
    )
    client.db = db
    client.bot = bot

    await client.start()
    print('Bot rodando...')
    client.me = await client.get_me()
    await idle()    
    await client.stop()
    print('Bot desativando...')

if __name__ == "__main__":
    if platform.system() == 'Linux':
        uvloop.run(main())
    else:
        asyncio.run(main())