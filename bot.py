# (c) @jnsbot (git)

import os
import asyncio
import traceback
from pyrogram import Client, filters
from pyrogram.errors import UserNotParticipant
from pyrogram.errors import FloodWait
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from configs import Config
from mo_tech_yt.check_user_status import handle_user_status
from mo_tech_yt.force_sub_handler import handle_force_sub
from mo_tech_yt.broadcast_handlers import main_broadcast_handler
from mo_tech_yt.database import Database

db = Database(Config.DATABASE_URL, Config.BOT_USERNAME)
Bot = Client(Config.BOT_USERNAME, bot_token=Config.BOT_TOKEN, api_id=Config.API_ID, api_hash=Config.API_HASH)


@Bot.on_message(filters.private)
async def _(bot: Client, cmd: Message):
    await handle_user_status(bot, cmd)


@Bot.on_message(filters.command("start") & filters.private)
async def start(bot: Client, cmd: Message):
    if cmd.from_user.id in Config.BANNED_USERS:
        await cmd.reply_text("Sorry, You are banned.")
        return
    usr_cmd = cmd.text.split("_")[-1]
    if usr_cmd == "/start":
        chat_id = cmd.from_user.id
        if not await db.is_user_exist(chat_id):
            await db.add_user(chat_id)
            await bot.send_message(
                Config.LOG_CHANNEL,
                f"#NEW_USER: \n\nNew User [{cmd.from_user.first_name}](tg://user?id={cmd.from_user.id}) started @{Config.BOT_USERNAME} !!"
            )
        if Config.UPDATES_CHANNEL is not None:
            back = await handle_force_sub(bot, cmd)
            if back == 400:
                return
            else:
                pass
        await cmd.reply_text(
            Config.HOME_TEXT.format(cmd.from_user.first_name, cmd.from_user.id),
            parse_mode="Markdown",
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("👩‍👩‍👦‍👦Group", url="https://t.me/jns_fc_bots"),
                        InlineKeyboardButton("🔊Channel", url="https://t.me/jns_bots")
                    ],
                    [
                        InlineKeyboardButton("💾 MOVIES 💾", url="https://t.me/FCfilmcornerfc")
                    ],
                    [
                        InlineKeyboardButton("🤖About Bot", callback_data="aboutbot"),
                        InlineKeyboardButton("👨‍💼About Me", callback_data="aboutdevs")
                    ]
                ]
            )
        )
    else:
        if Config.UPDATES_CHANNEL is not None:
            back = await handle_force_sub(bot, cmd)
            if back == 400:
                return
            else:
                pass
        try:
            file_id = int(usr_cmd)
            send_stored_file = None
            if Config.FORWARD_AS_COPY is True:
                send_stored_file = await bot.copy_message(chat_id=cmd.from_user.id, from_chat_id=Config.DB_CHANNEL,
                                                          message_id=file_id)
            elif Config.FORWARD_AS_COPY is False:
                send_stored_file = await bot.forward_messages(chat_id=cmd.from_user.id, from_chat_id=Config.DB_CHANNEL,
                                                              message_ids=file_id)
            await send_stored_file.reply_text(
                f"**Here is Sharable Link of this file:** https://telegram.me/share/url?url=https://t.me/{Config.BOT_USERNAME}?start=JNS_BOTS_{file_id}\n\n__To Retrive the Stored File, just open the link!__",
                disable_web_page_preview=True, quote=True)
        except Exception as err:
            await cmd.reply_text(f"Something went wrong!\n\n**Error:** `{err}`")


@Bot.on_message((filters.document | filters.video | filters.audio) & ~filters.edited)
async def main(bot: Client, message: Message):
    if message.chat.type == "private":
        chat_id = message.from_user.id
        if not await db.is_user_exist(chat_id):
            await db.add_user(chat_id)
            await bot.send_message(
                Config.LOG_CHANNEL,
                f"#NEW_USER: \n\nNew User [{message.from_user.first_name}](tg://user?id={message.from_user.id}) started @{Config.BOT_USERNAME} !!"
            )
        if Config.UPDATES_CHANNEL is not None:
            back = await handle_force_sub(bot, message)
            if back == 400:
                return
            else:
                pass
        if message.from_user.id in Config.BANNED_USERS:
            await message.reply_text("Sorry, You are banned!\n\nContact [Support Group](https://t.me/jns_fc_bots)",
                                     disable_web_page_preview=True)
            return
        if Config.OTHER_USERS_CAN_SAVE_FILE is False:
            return
        editable = await message.reply_text("Please wait ...")
        try:
            forwarded_msg = await message.forward(Config.DB_CHANNEL)
            file_er_id = forwarded_msg.message_id
            await forwarded_msg.reply_text(
                f"#PRIVATE_FILE:\n\n[{message.from_user.first_name}](tg://user?id={message.from_user.id}) Got File Link!",
                parse_mode="Markdown", disable_web_page_preview=True)
            share_link = f"https://telegram.me/share/url?url=https://t.me/{Config.BOT_USERNAME}?start=JNS_BOTS_{file_er_id}"
            await editable.edit(
                f"**Your File Stored in my Database!**\n\nHere is the Permanent Link of your file: https://t.me/{Config.BOT_USERNAME}?start=JNS_BOTS_{file_er_id} \n\nJust Click the link to get your file! \n **Share to friends** ⬇️",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("♻️SHARE LINK♻️", url=share_link)],
                     [InlineKeyboardButton("🔊Channel", url="https://t.me/jns_bots"),
                      InlineKeyboardButton("👨‍💼Group", url="https://t.me/jns_fc_bots")]]
                ),
                disable_web_page_preview=True
            )
        except FloodWait as sl:
            await asyncio.sleep(sl.x)
            await bot.send_message(
                chat_id=Config.LOG_CHANNEL,
                text=f"#FloodWait:\nGot FloodWait of `{str(sl.x)}s` from `{str(message.chat.id)}` !!",
                parse_mode="Markdown",
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton("Ban User", callback_data=f"ban_user_{str(message.chat.id)}")]
                    ]
                )
            )
        except Exception as err:
            await editable.edit(f"Something Went Wrong!\n\n**Error:** `{err}`")
            await bot.send_message(
                chat_id=Config.LOG_CHANNEL,
                text=f"#ERROR_TRACEBACK:\nGot Error from `{str(message.chat.id)}` !!\n\n**Traceback:** `{err}`",
                parse_mode="Markdown",
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton("Ban User", callback_data=f"ban_user_{str(message.chat.id)}")]
                    ]
                )
            )
    elif message.chat.type == "channel":
        if (message.chat.id == Config.LOG_CHANNEL) or (message.chat.id == int(Config.UPDATES_CHANNEL)) or message.forward_from_chat or message.forward_from:
            return
        elif int(message.chat.id) in Config.BANNED_CHAT_IDS:
            await bot.leave_chat(message.chat.id)
            return
        else:
            pass
        try:
            forwarded_msg = await message.forward(Config.DB_CHANNEL)
            file_er_id = forwarded_msg.message_id
            share_link = f"https://t.me/{Config.BOT_USERNAME}?start=JNS_BOTS_{file_er_id}"
            CH_edit = await bot.edit_message_reply_markup(message.chat.id, message.message_id,
                                                          reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(
                                                              "Get Sharable Stored Link", url=share_link)]]))
            if message.chat.username:
                await forwarded_msg.reply_text(
                    f"#CHANNEL_BUTTON:\n\n[{message.chat.title}](https://t.me/{message.chat.username}/{CH_edit.message_id}) Channel's Broadcasted File's Button Added!")
            else:
                private_ch = str(message.chat.id)[4:]
                await forwarded_msg.reply_text(
                    f"#CHANNEL_BUTTON:\n\n[{message.chat.title}](https://t.me/c/{private_ch}/{CH_edit.message_id}) Channel's Broadcasted File's Button Added!")
        except FloodWait as sl:
            await asyncio.sleep(sl.x)
            await bot.send_message(
                chat_id=Config.LOG_CHANNEL,
                text=f"#FloodWait:\nGot FloodWait of `{str(sl.x)}s` from `{str(message.chat.id)}` !!",
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
        except Exception as err:
            await bot.send_message(
                chat_id=Config.LOG_CHANNEL,
                text=f"#ERROR_TRACEBACK:\nGot Error from `{str(message.chat.id)}` !!\n\n**Traceback:** `{err}`",
                parse_mode="Markdown",
                disable_web_page_preview=True
            )



@Bot.on_callback_query()
async def button(bot: Client, cmd: CallbackQuery):
    cb_data = cmd.data
    if "aboutbot" in cb_data:
        await cmd.message.edit(
            Config.ABOUT_BOT_TEXT,
            parse_mode="Markdown",
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("MOVIES",
                                             url="https://t.me/FCfilmcornerfc")
                    ],
                    [
                        InlineKeyboardButton("Go Home", callback_data="gotohome"),
                        InlineKeyboardButton("About Me", callback_data="aboutdevs")
                    ]
                ]
            )
        )
    elif "aboutdevs" in cb_data:
        await cmd.message.edit(
            Config.ABOUT_DEV_TEXT,
            parse_mode="Markdown",
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("MOVIES",
                                             url="https://t.me/FCfilmcornerfc")
                    ],
                    [
                        InlineKeyboardButton("About Bot", callback_data="aboutbot"),
                        InlineKeyboardButton("Go Home", callback_data="gotohome")
                    ]
                ]
            )
        )
    elif "gotohome" in cb_data:
        await cmd.message.edit(
            Config.HOME_TEXT.format(cmd.message.chat.first_name, cmd.message.chat.id),
            parse_mode="Markdown",
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("👩‍👩‍👦‍👦Group", url="https://t.me/jns_fc_bots"),
                        InlineKeyboardButton("🔊Channel", url="https://t.me/jns_bots")
                    ],
                    [
                        InlineKeyboardButton("💾Movies💾", url="https://t.me/FCfilmcornerfc")
                    ],
                    [
                        InlineKeyboardButton("🤖About Bot", callback_data="aboutbot"),
                        InlineKeyboardButton("👨‍💼About Me", callback_data="aboutdevs")
                    ]
                ]
            )
        )
    elif "refreshmeh" in cb_data:
        if Config.UPDATES_CHANNEL:
            invite_link = await bot.create_chat_invite_link(int(Config.UPDATES_CHANNEL))
            try:
                user = await bot.get_chat_member(int(Config.UPDATES_CHANNEL), cmd.message.chat.id)
                if user.status == "kicked":
                    await cmd.message.edit(
                        text="Sorry Sir, You are Banned to use me. Contact my [Support Group](https://t.me/jns_fc_bots).",
                        parse_mode="markdown",
                        disable_web_page_preview=True
                    )
                    return
            except UserNotParticipant:
                await cmd.message.edit(
                    text="**You Still Didn't Join ☹️, Please Join My Updates Channel to use this Bot!**\n\nDue to Overload, Only Channel Subscribers can use the Bot!",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton("🤖 Join Updates Channel", url=invite_link.invite_link)
                            ],
                            [
                                InlineKeyboardButton("🔄 Refresh 🔄", callback_data="refreshmeh")
                            ]
                        ]
                    ),
                    parse_mode="markdown"
                )
                return
            except Exception:
                await cmd.message.edit(
                    text="Something went Wrong. Contact my [Support Group](https://t.me/jns_fc_bots).",
                    parse_mode="markdown",
                    disable_web_page_preview=True
                )
                return
        await cmd.message.edit(
            text=Config.HOME_TEXT.format(cmd.message.chat.first_name, cmd.message.chat.id),
            parse_mode="Markdown",
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("👩‍👩‍👦‍👦Group", url="https://t.me/jns_fc_bots"),
                        InlineKeyboardButton("🔊Channel", url="https://t.me/jns_bots")
                    ],
                    [
                        InlineKeyboardButton("💾 MOVIES💾", url="https://t.me/FCfilmcornerfc")
                    ],
                    [
                        InlineKeyboardButton("🤖About Bot", callback_data="aboutbot"),
                        InlineKeyboardButton("👨‍💼About Me", callback_data="aboutdevs")
                    ]
                ]
            )
        )
    elif cb_data.startswith("ban_user_"):
        user_id = cb_data.split("_", 2)[-1]
        if Config.UPDATES_CHANNEL is None:
            await cmd.answer("Sorry Sir, You didn't Set any Updates Channel!", show_alert=True)
            return
        if not int(cmd.from_user.id) == Config.BOT_OWNER:
            await cmd.answer("You are not allowed to do that!", show_alert=True)
            return
        try:
            await bot.kick_chat_member(chat_id=int(Config.UPDATES_CHANNEL), user_id=int(user_id))
            await cmd.answer("User Banned from Updates Channel!", show_alert=True)
        except Exception as e:
            await cmd.answer(f"Can't Ban Him!\n\nError: {e}", show_alert=True)


Bot.run()
