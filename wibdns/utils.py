import os
import time
import json
import asyncio
import zipfile
import aiofiles
import subprocess
from itertools import islice
from hydrogram import Client, filters
from hydrogram.types import (
    ListenerTypes,
    Message, 
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ForceReply,
)

async def send_message_based_on_type(client, user, msg):
    async def manipulate_if_needed(content, **kwargs):
        if content and content.strip():
            return await client.bot.manipular_msg(msg=content, usuario=user, **kwargs)
        else:
            return ""

    content = await manipulate_if_needed(msg.get("content"))
    caption = await manipulate_if_needed(msg.get("caption"))

    if msg["type"] == "text":
        await client.send_message(user.get("id"), content, reply_markup=msg.get("reply_markup", None))
    elif msg["type"] == "photo":
        await client.send_photo(user.get("id"), msg["media"], caption=caption, reply_markup=msg.get("reply_markup", None))
    elif msg["type"] == "video":
        await client.send_video(user.get("id"), msg["media"], caption=caption, reply_markup=msg.get("reply_markup", None))
    elif msg["type"] == "audio":
        await client.send_audio(user.get("id"), msg["media"])
    elif msg["type"] == "document":
        await client.send_document(user.get("id"), msg["media"], caption=caption, reply_markup=msg.get("reply_markup", None))
    elif msg["type"] == "voice":
        await client.send_voice(user.get("id"), msg["media"])
    elif msg["type"] == "video_note":
        await client.send_video_note(user.get("id"), msg["media"])
    elif msg["type"] == "animation":
        await client.send_animation(user.get("id"), msg["media"], caption=caption, reply_markup=msg.get("reply_markup", None))
    elif msg["type"] == "sticker":
        await client.send_sticker(user.get("id"), msg["media"], reply_markup=msg.get("reply_markup", None))

async def geter_messages_broadcast(client, message, messages, adm):
    while True:
        if isinstance(message, CallbackQuery):
            msg = await client.listen(filters=filters.incoming,listener_type=ListenerTypes.MESSAGE,timeout=300,chat_id=message.message.chat.id)
        else:
            msg = await client.listen(filters=filters.incoming,listener_type=ListenerTypes.MESSAGE,timeout=300,chat_id=message.chat.id)
        content = None
        if msg.text:
            if msg.text.startswith('/send') or msg.text.startswith('/enviar'):
                break
            if msg.text.startswith('/cancel'):
                messages = []
                break
            content = {"type": "text", "content": msg.text, "reply_markup": msg.reply_markup}
        elif msg.photo:
            content = {"type": "photo", "media": msg.photo.file_id, "caption": msg.caption, "reply_markup": msg.reply_markup}
        elif msg.video:
            content = {"type": "video", "media": msg.video.file_id, "caption": msg.caption, "reply_markup": msg.reply_markup}
        elif msg.audio:
            content = {"type": "audio", "media": msg.audio.file_id}
        elif msg.document:
            content = {"type": "document", "media": msg.document.file_id, "caption": msg.caption, "reply_markup": msg.reply_markup}
        elif msg.voice:
            content = {"type": "voice", "media": msg.voice.file_id}
        elif msg.video_note:
            content = {"type": "video_note", "media": msg.video_note.file_id}
        elif msg.animation:
            content = {"type": "animation", "media": msg.animation.file_id, "caption": msg.caption, "reply_markup": msg.reply_markup}
        elif msg.sticker:
            content = {"type": "sticker", "media": msg.sticker.file_id,"reply_markup": msg.reply_markup}
        if content:
            messages.append(content)
        await msg.reply_text(await client.bot.manipular_msg(key_path="broadcast_add",usuario=adm),quote=True)

async def gerenciador_broadcast(client,all_users,messages):
    count = 0
    senders = 0
    last_time_out = time.time()
    all_users = (x for x in all_users)
    while True:
        users = list(islice(all_users, 5))

        if not users:
            break

        for msg in messages:
            if  count >= 25 and time.time() - last_time_out <= 1:
                await asyncio.sleep(0.4)
                count = 0
                last_time_out = time.time()
            try:
                await asyncio.gather(*[send_message_based_on_type(client, user, msg) for user in users])
            except Exception as e:
                pass
            senders += len(users)
            count += len(users)

async def clear_backup_folder(folder_path):
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)

async def clear_backup_folder(folder_path):
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)

async def split_file_with_7zip(file_path, output_folder, chunk_size='50M'):
    part_filename = os.path.join(output_folder, f"{os.path.basename(file_path)}.zip")
    command = ['ionice', '-c', '3', 'nice', '-n', '19', '7z', 'a', f'-v{chunk_size}', '-mmt=1', '-mx=1', part_filename, file_path]
    subprocess.run(command, check=True)
    created_files = os.listdir(output_folder)
    return created_files

async def send_db_backup(client, user_id):
    backup_folder = os.path.join(os.getcwd(), 'backup')
    os.makedirs(backup_folder, exist_ok=True)
    await clear_backup_folder(backup_folder)
    db_file_path = 'bot.db'
    parts = await split_file_with_7zip(db_file_path, backup_folder)
    for index, part in enumerate(parts, start=1):
        filename = f'{os.getcwd()}/backup/{part}'
        caption = f'backup do banco de dados {index}/{len(parts)}'
        await client.send_document(chat_id=user_id, file_name=os.path.basename(part), document=filename, caption=caption)
        await asyncio.sleep(5)



