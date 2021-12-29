# Copyright (C) 2021 By Veez Music-Project
# Commit Start Date 20/10/2021
# Finished On 28/10/2021

import re
import asyncio

from config import ASSISTANT_NAME, BOT_USERNAME, IMG_1, IMG_2
from driver.filters import command, other_filters
from driver.queues import QUEUE, add_to_queue
from driver.veez import call_py, user
from driver.utils import bash
from pyrogram import Client
from pyrogram.errors import UserAlreadyParticipant, UserNotParticipant
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from pytgcalls import StreamType
from driver.decorators import authorized_users_only
from pytgcalls.types.input_stream import AudioPiped
from youtubesearchpython import VideosSearch


def ytsearch(query: str):
    try:
        search = VideosSearch(query, limit=1).result()
        data = search["result"][0]
        songname = data["title"]
        url = data["link"]
        duration = data["duration"]
        thumbnail = f"https://i.ytimg.com/vi/{data['id']}/hqdefault.jpg"
        return [songname, url, duration, thumbnail]
    except Exception as e:
        print(e)
        return 0


async def ytdl(format: str, link: str):
    stdout, stderr = await bash(f'youtube-dl -g -f "{format}" {link}')
    if stdout:
        return 1, stdout.split("\n")[0]
    return 0, stderr


@Client.on_message(command(["mplay", f"mplay@{BOT_USERNAME}","پخش"]) & other_filters)
@authorized_users_only
async def play(c: Client, m: Message):
    await m.delete()
    replied = m.reply_to_message
    chat_id = m.chat.id
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(text="• منو", callback_data="cbmenu"),
                InlineKeyboardButton(text="• بستن", callback_data="cls"),
            ]
        ]
    )
    if m.sender_chat:
        return await m.reply_text("شما ادمین ناشناس هستید!\n\n» تیک ناشناس خود را در منو تنظیمات گروه بردارید")
    try:
        aing = await c.get_me()
    except Exception as e:
        return await m.reply_text(f"مشکل:\n\n{e}")
    a = await c.get_chat_member(chat_id, aing.id)
    if a.status != "administrator":
        await m.reply_text(
            f"💡برای استفاده از من، باید یک **مدیر** با **مجوزهای زیر** باشم:\n\n» ❌ __حذف پیام ها__\n» ❌ __افزودن کاربران__\n» ❌ __مدیریت چت ویدیویی__\n\nداده ها * است *بعد از اینکه *من را مدیر کردید** بطور خودکار به روز میشود**"
        )
        return
    if not a.can_manage_voice_chats:
        await m.reply_text(
            "مجوز لازم وجود ندارد:" + "\n\n» ❌ __مدیریت چت ویدیویی__"
        )
        return
    if not a.can_delete_messages:
        await m.reply_text(
            "مجوز لازم وجود ندارد:" + "\n\n» ❌ __حذف پیام__"
        )
        return
    if not a.can_invite_users:
        await m.reply_text("مجوز لازم وجود ندارد:" + "\n\n» ❌ __افزودن کاربران با لینک__")
        return
            
    if replied:
        if replied.audio or replied.voice:
            suhu = await replied.reply("📥 **در حال دانلود موسیقی...**")
            dl = await replied.download()
            link = replied.link
            if replied.audio:
                if replied.audio.title:
                    songname = replied.audio.title[:70]
                else:
                    if replied.audio.file_name:
                        songname = replied.audio.file_name[:70]
                    else:
                        songname = "Audio"
            elif replied.voice:
                songname = "Voice Note"
            if chat_id in QUEUE:
                pos = add_to_queue(chat_id, songname, dl, link, "Audio", 0)
                await suhu.delete()
                await m.reply_photo(
                    photo=f"{IMG_1}",
                    caption=f"💡 **موزیک به لیست اضافه شد »** `{pos}`\n\n🏷 **اسم:** [{songname}]({link})\n💭 **شناسه گروه:** `{chat_id}`\n🎧 **به درخواست:** {m.from_user.mention()}",
                    reply_markup=keyboard,
                )
            else:
             try:
                await suhu.edit("🔄 **درحال اتصال به گفتگوی ویدیویی...**")
                await call_py.join_group_call(
                    chat_id,
                    AudioPiped(
                        dl,
                    ),
                    stream_type=StreamType().local_stream,
                )
                add_to_queue(chat_id, songname, dl, link, "Audio", 0)
                await suhu.delete()
                requester = f"[{m.from_user.first_name}](tg://user?id={m.from_user.id})"
                await m.reply_photo(
                    photo=f"{IMG_2}",
                    caption=f"💡 **پخش موزیک شروع شد**\n\n🏷 **اسم:** [{songname}]({link})\n💭 **شناسه گروه:** `{chat_id}`\n💡 **وضعیت:** `درحال پخش`\n🎧 **به درخواست:** {requester}",
                    reply_markup=keyboard,
                )
             except Exception as e:
                await suhu.delete()
                await m.reply_text(f"🚫 error:\n\n» {e}")
        else:
            if len(m.command) < 2:
                await m.reply(
                    "» به یک **فایل صوتی** ریپلی  کنید.\n یا **چیزی برای جستجو بنویسید.**"
                )
            else:
                suhu = await c.send_message(chat_id, "🔎")
                query = m.text.split(None, 1)[1]
                search = ytsearch(query)
                if search == 0:
                    await suhu.edit("❌ **نتیجه ای پیدا نشد.**")
                else:
                    songname = search[0]
                    url = search[1]
                    duration = search[2]
                    thumbnail = search[3]
                    format = "bestaudio[ext=m4a]"
                    veez, ytlink = await ytdl(format, url)
                    if veez == 0:
                        await suhu.edit(f"❌ مشکلی در وبسرویس پخش آنلاین وجود دارد\n\n» `{ytlink}`")
                    else:
                        if chat_id in QUEUE:
                            pos = add_to_queue(
                                chat_id, songname, ytlink, url, "Audio", 0
                            )
                            await suhu.delete()
                            requester = f"[{m.from_user.first_name}](tg://user?id={m.from_user.id})"
                            await m.reply_photo(
                                photo=thumbnail,
                                caption=f"💡 **موزیک به لیست اضافه شد»** `{pos}`\n\n🏷 **اسم:** [{songname}]({url}) | `موزیک`\n**⏱ زمان:** `{duration}`\n🎧 **به دستور:** {requester}",
                                reply_markup=keyboard,
                            )
                        else:
                            try:
                                await suhu.edit("🔄 **درحال پیوستن به گفتگوی ویدیویی...**")
                                await call_py.join_group_call(
                                    chat_id,
                                    AudioPiped(
                                        ytlink,
                                    ),
                                    stream_type=StreamType().local_stream,
                                )
                                add_to_queue(chat_id, songname, ytlink, url, "Audio", 0)
                                await suhu.delete()
                                requester = f"[{m.from_user.first_name}](tg://user?id={m.from_user.id})"
                                await m.reply_photo(
                                    photo=thumbnail,
                                    caption=f"🏷 **اسم:** [{songname}]({url})\n**⏱ زمان:** `{duration}`\n💡 **وضعیت:** `درحال پخش`\n🎧 **به درخواست:** {requester}\n📹 **نوع پخش:** `موسیقی`",
                                    reply_markup=keyboard,
                                )
                            except Exception as ep:
                                await suhu.delete()
                                await m.reply_text(f"🚫 مشکل: `{ep}`")

    else:
        if len(m.command) < 2:
            await m.reply(
                "» به یک **فایل صوتی** ریپلی  کنید.\n یا **چیزی برای جستجو بنویسید.**"
            )
        else:
            suhu = await c.send_message(chat_id, "🔍")
            query = m.text.split(None, 1)[1]
            search = ytsearch(query)
            if search == 0:
                await suhu.edit("❌ **نتیجه ای پیدا نشد.**")
            else:
                songname = search[0]
                url = search[1]
                duration = search[2]
                thumbnail = search[3]
                format = "bestaudio[ext=m4a]"
                veez, ytlink = await ytdl(format, url)
                if veez == 0:
                    await suhu.edit(f"❌ وبسرویس مشکل پخش انلاین \n\n» `{ytlink}`")
                else:
                    if chat_id in QUEUE:
                        pos = add_to_queue(chat_id, songname, ytlink, url, "Audio", 0)
                        await suhu.delete()
                        requester = (
                            f"[{m.from_user.first_name}](tg://user?id={m.from_user.id})"
                        )
                        await m.reply_photo(
                            photo=thumbnail,
                            caption=f"💡 **موزیک به لیست اضافه شد »** `{pos}`\n\n🏷 **نام:** [{songname}]({url}) | `music`\n**⏱ زمان:** `{duration}`\n🎧 **به درخواست:** {requester}",
                            reply_markup=keyboard,
                        )
                    else:
                        try:
                            await suhu.edit("🔄 **درحال پیوستن...**")
                            await call_py.join_group_call(
                                chat_id,
                                AudioPiped(
                                    ytlink,
                                ),
                                stream_type=StreamType().local_stream,
                            )
                            add_to_queue(chat_id, songname, ytlink, url, "Audio", 0)
                            await suhu.delete()
                            requester = f"[{m.from_user.first_name}](tg://user?id={m.from_user.id})"
                            await m.reply_photo(
                                photo=thumbnail,
                                caption=f"🏷 **اسم:** [{songname}]({url})\n**⏱ زمان:** `{duration}`\n💡 **وضعیت:** `درحال پخش`\n🎧 **به درخواست:** {requester}\n📹 **نوع پخش:** `موسیقی`",
                                reply_markup=keyboard,
                            )
                        except Exception as ep:
                            await suhu.delete()
                            await m.reply_text(f"🚫 مشکل: `{ep}`")
