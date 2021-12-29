from cache.admins import admins
from driver.veez import call_py
from pyrogram import Client, filters
from driver.decorators import authorized_users_only
from driver.filters import command, other_filters
from driver.queues import QUEUE, clear_queue
from driver.utils import skip_current_song, skip_item
from config import BOT_USERNAME, GROUP_SUPPORT, IMG_3, UPDATES_CHANNEL
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)


bttn = InlineKeyboardMarkup(
    [[InlineKeyboardButton("🔙 برگشت", callback_data="cbmenu")]]
)


bcl = InlineKeyboardMarkup(
    [[InlineKeyboardButton("🗑 بستن", callback_data="cls")]]
)


@Client.on_message(command(["reload", f"بازنگری"]) & other_filters)
@authorized_users_only
async def update_admin(client, message):
    global admins
    new_admins = []
    new_ads = await client.get_chat_members(message.chat.id, filter="administrators")
    for u in new_ads:
        new_admins.append(u.user.id)
    admins[message.chat.id] = new_admins
    await message.reply_text(
        "✅ ربات **بازنگری شد !**\n✅ **لیست ادمین دریافت شد**\nتمامی کاربرانی که دسترسی به گفتگوی ویدیو دارند اجازه دسترسی به دستورات دارند**\nلیست کاربران مجاز پاکسازی شد."
    )


@Client.on_message(command(["مجاز", f"auth"]) & other_filters)
@authorized_users_only
async def authenticate(client, message):
    global admins
    if not message.reply_to_message:
        return await message.reply("💡 باید برای انجام این عملیات روی کاربر ریپلای کنید !")
    if message.reply_to_message.from_user.id not in admins[message.chat.id]:
        new_admins = admins[message.chat.id]
        new_admins.append(message.reply_to_message.from_user.id)
        admins[message.chat.id] = new_admins
        await message.reply(
            "🟢 کاربر مجاز شد.\n\nاز این به بعد توانایی دسترسی به دستورات ربات را دارد."
        )
    else:
        await message.reply("✅ کاربر از قبل در لیست مجاز بود!")


@Client.on_message(command(["غیرمجاز", f"deauth"]) & other_filters)
@authorized_users_only
async def deautenticate(client, message):
    global admins
    if not message.reply_to_message:
        return await message.reply("💡 💡 باید برای انجام این عملیات روی کاربر ریپلای کنید !")
    if message.reply_to_message.from_user.id in admins[message.chat.id]:
        new_admins = admins[message.chat.id]
        new_admins.remove(message.reply_to_message.from_user.id)
        admins[message.chat.id] = new_admins
        await message.reply(
            "🔴 کاربر غیرمجاز شد.\n\nاز این به بعد این کاربری توانایی دسترسی به دستورات ربات را ندارد !"
        )
    else:
        await message.reply("✅ این بدبخت از اول تو.انایی دسترسی نداشت")



@Client.on_message(command(["skip", f"skip@{BOT_USERNAME}", "بعدی"]) & other_filters)
@authorized_users_only
async def skip(client, m: Message):

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="• منو", callback_data="cbmenu"
                ),
                InlineKeyboardButton(
                    text="• بستن", callback_data="cls"
                ),
            ]
        ]
    )

    chat_id = m.chat.id
    if len(m.command) < 2:
        op = await skip_current_song(chat_id)
        if op == 0:
            await m.reply("❌ چیزی در حال پخش نیست💮")
        elif op == 1:
            await m.reply("✅ __لیست پخش_ **خالی است.**\n\n**• پخش کننده از گفتگوی ویدیویی خارج میشود😎**")
        elif op == 2:
            await m.reply("🗑️ **لیست پخش پاکسازی شد**\n\n**• پخش کننده از ویس چت خارج میشود😎**")
        else:
            await m.reply_photo(
                photo=f"{IMG_3}",
                caption=f"⏭ **آهنگ شما با موفقیت رد شد**\n\n🏷 **اسم:** [{op[0]}]({op[1]})\n💭 **شناسه گروه:** `{chat_id}`\n💡 **وضعیت:** `درحال پخش`\n🎧 **به درخواست:** {m.from_user.mention()}",
                reply_markup=keyboard,
            )
    else:
        skip = m.text.split(None, 1)[1]
        OP = "🗑 **آهنگ از لیست حذف شد.:**"
        if chat_id in QUEUE:
            items = [int(x) for x in skip.split(" ") if x.isdigit()]
            items.sort(reverse=True)
            for x in items:
                if x == 0:
                    pass
                else:
                    hm = await skip_item(chat_id, x)
                    if hm == 0:
                        pass
                    else:
                        OP = OP + "\n" + f"**#{x}** - {hm}"
            await m.reply(OP)


@Client.on_message(
    command(["stop", f"stop@{BOT_USERNAME}", "end", f"end@{BOT_USERNAME}", "توقف پخش"])
    & other_filters
)
@authorized_users_only
async def stop(client, m: Message):
    chat_id = m.chat.id
    if chat_id in QUEUE:
        try:
            await call_py.leave_group_call(chat_id)
            clear_queue(chat_id)
            await m.reply("✅ **پخش موزیک متوقف شد**")
        except Exception as e:
            await m.reply(f"🚫 **مشکل:**\n\n`{e}`")
    else:
        await m.reply("❌ **چیزی در حال پخش نیست💮**")


@Client.on_message(
    command(["pause", f"pause@{BOT_USERNAME}", "مکث"]) & other_filters
)
@authorized_users_only
async def pause(client, m: Message):
    chat_id = m.chat.id
    if chat_id in QUEUE:
        try:
            await call_py.pause_stream(chat_id)
            await m.reply(
                "⏸ **پخش به حالت مکث کوتاه قرار گرفت**\n\n• **جهت ادامه پخش از دستور زیر استفاده کنید**\n» ازسرگیری"
            )
        except Exception as e:
            await m.reply(f"🚫 **مشکل:**\n\n`{e}`")
    else:
        await m.reply("❌ **چیزی در حال پخش نیست💮**")


@Client.on_message(
    command(["resume", f"resume@{BOT_USERNAME}","ازسرگیری","ادامه"]) & other_filters
)
@authorized_users_only
async def resume(client, m: Message):
    chat_id = m.chat.id
    if chat_id in QUEUE:
        try:
            await call_py.resume_stream(chat_id)
            await m.reply(
                "▶️ **ربات در حال پخش قرار گرفت.**\n\n لطفا بصورت طولانی ربات را مکث نکنید و از دستور `توقف پخش` استفاده کنید"
            )
        except Exception as e:
            await m.reply(f"🚫 **مشکل:**\n\n`{e}`")
    else:
        await m.reply("❌ **چیزی در حال پخش نیست💮**")


@Client.on_message(
    command(["mute", f"mute@{BOT_USERNAME}", "بیصدا"]) & other_filters
)
@authorized_users_only
async def mute(client, m: Message):
    chat_id = m.chat.id
    if chat_id in QUEUE:
        try:
            await call_py.mute_stream(chat_id)
            await m.reply(
                "🔇 **پخش کننده بیصدا شد.**\n\n• **جهت باصدا کردن ربات از دستور زیر استفاده کنید**\n» `باصدا`"
            )
        except Exception as e:
            await m.reply(f"🚫 **مشکل:**\n\n`{e}`")
    else:
        await m.reply("❌ **چیزی در حال پخش نیست💮**")


@Client.on_message(
    command(["unmute", f"unmute@{BOT_USERNAME}", "باصدا"]) & other_filters
)
@authorized_users_only
async def unmute(client, m: Message):
    chat_id = m.chat.id
    if chat_id in QUEUE:
        try:
            await call_py.unmute_stream(chat_id)
            await m.reply(
                "🔊 **ربات با صدا شد.**\n\n• از استفاده طولانی در حالت بیصدایی ربات خودداری کنید🚫"
            )
        except Exception as e:
            await m.reply(f"🚫 **مشکل:**\n\n`{e}`")
    else:
        await m.reply("❌ **چیزی در حال پخش نیست💮**")


@Client.on_callback_query(filters.regex("cbpause"))
async def cbpause(_, query: CallbackQuery):
    if query.message.sender_chat:
        return await query.answer("شما ادمین ناشناس هستید!\n\n» تیک ناشناس خود را در منو تنظیمات گروه بردارید")
    a = await _.get_chat_member(query.message.chat.id, query.from_user.id)
    if not a.can_manage_voice_chats:
        return await query.answer("💡 این دکمه ها فقط برای مدیران هست \n دست نکن بچه🤨 !", show_alert=True)
    chat_id = query.message.chat.id
    if chat_id in QUEUE:
        try:
            await call_py.pause_stream(chat_id)
            await query.edit_message_text(
                "⏸ موزیک در حالت مکث کوتاه قرار گرفت", reply_markup=bttn
            )
        except Exception as e:
            await query.edit_message_text(f"🚫 **مشکل:**\n\n`{e}`", reply_markup=bcl)
    else:
        await query.answer("❌ چیزی در‌حال پخش نیست💮", show_alert=True)


@Client.on_callback_query(filters.regex("cbresume"))
async def cbresume(_, query: CallbackQuery):
    if query.message.sender_chat:
        return await query.answer("شما ادمین ناشناس هستید!\n\n» تیک ناشناس خود را در منو تنظیمات گروه بردارید")
    a = await _.get_chat_member(query.message.chat.id, query.from_user.id)
    if not a.can_manage_voice_chats:
        return await query.answer("💡 این دکمه ها فقط برای مدیران هست \n دست نکن بچه🤨 !", show_alert=True)
    chat_id = query.message.chat.id
    if chat_id in QUEUE:
        try:
            await call_py.resume_stream(chat_id)
            await query.edit_message_text(
                "▶️ پخش به حالت عادی بازگشت.", reply_markup=bttn
            )
        except Exception as e:
            await query.edit_message_text(f"🚫 **مشکل:**\n\n`{e}`", reply_markup=bcl)
    else:
        await query.answer("❌ چیزی در‌حال پخش نیست💮", show_alert=True)


@Client.on_callback_query(filters.regex("cbstop"))
async def cbstop(_, query: CallbackQuery):
    if query.message.sender_chat:
        return await query.answer("شما ادمین ناشناس هستید!\n\n» تیک ناشناس خود را در منو تنظیمات گروه بردارید")
    a = await _.get_chat_member(query.message.chat.id, query.from_user.id)
    if not a.can_manage_voice_chats:
        return await query.answer("💡 این دکمه ها فقط برای مدیران هست \n دست نکن بچه🤨 !", show_alert=True)
    chat_id = query.message.chat.id
    if chat_id in QUEUE:
        try:
            await call_py.leave_group_call(chat_id)
            clear_queue(chat_id)
            await query.edit_message_text("✅ **لیست پخش خالی شد\nاز گفتگوی ویدیویی خارج میشوم**", reply_markup=bcl)
        except Exception as e:
            await query.edit_message_text(f"🚫 **مشکل:**\n\n`{e}`", reply_markup=bcl)
    else:
        await query.answer("❌ چیزی در‌حال پخش نیست💮", show_alert=True)


@Client.on_callback_query(filters.regex("cbmute"))
async def cbmute(_, query: CallbackQuery):
    if query.message.sender_chat:
        return await query.answer("شما ادمین ناشناس هستید!\n\n» تیک ناشناس خود را در منو تنظیمات گروه بردارید")
    a = await _.get_chat_member(query.message.chat.id, query.from_user.id)
    if not a.can_manage_voice_chats:
        return await query.answer("💡 این دکمه ها فقط برای مدیران هست \n دست نکن بچه🤨 !", show_alert=True)
    chat_id = query.message.chat.id
    if chat_id in QUEUE:
        try:
            await call_py.mute_stream(chat_id)
            await query.edit_message_text(
                "🔇 با موفقیت بیصدا شدم", reply_markup=bttn
            )
        except Exception as e:
            await query.edit_message_text(f"🚫 **مشکل:**\n\n`{e}`", reply_markup=bcl)
    else:
        await query.answer("❌ چیزی در‌حال پخش نیست💮", show_alert=True)


@Client.on_callback_query(filters.regex("cbunmute"))
async def cbunmute(_, query: CallbackQuery):
    if query.message.sender_chat:
        return await query.answer("شما ادمین ناشناس هستید!\n\n» تیک ناشناس خود را در منو تنظیمات گروه بردارید")
    a = await _.get_chat_member(query.message.chat.id, query.from_user.id)
    if not a.can_manage_voice_chats:
        return await query.answer("💡 این دکمه ها فقط برای مدیران هست \n دست نکن بچه🤨 !", show_alert=True)
    chat_id = query.message.chat.id
    if chat_id in QUEUE:
        try:
            await call_py.unmute_stream(chat_id)
            await query.edit_message_text(
                "🔊 با موفقیت باصدا شدم", reply_markup=bttn
            )
        except Exception as e:
            await query.edit_message_text(f"🚫 **مشکل:**\n\n`{e}`", reply_markup=bcl)
    else:
        await query.answer("❌ چیزی در‌حال پخش نیست💮", show_alert=True)


@Client.on_message(
    command(["volume", f"volume@{BOT_USERNAME}", "vol","صدا"]) & other_filters
)
@authorized_users_only
async def change_volume(client, m: Message):
    range = m.command[1]
    chat_id = m.chat.id
    if chat_id in QUEUE:
        try:
            await call_py.change_volume_call(chat_id, volume=int(range))
            await m.reply(
                f"✅ **حجم صدا تنظیم شد* `{range}`%"
            )
        except Exception as e:
            await m.reply(f"🚫 **مشکل:**\n\n`{e}`")
    else:
        await m.reply("❌ **چیزی در حال پخش نیست💮**")