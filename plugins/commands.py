import os
import logging
import random
import asyncio
from script import script
from pyrogram import client, filters, enums
from pyrogram.errors import chatadminrequired, floodwait
from pyrogram.types import inlinekeyboardbutton, inlinekeyboardmarkup
from database.ia_filterdb import media, get_file_details, unpack_new_file_id
from database.users_chats_db import db
from info import channels, admins, auth_channel, log_channel, pics, batch_file_caption, custom_file_caption, protect_content
from utils import get_settings, get_size, is_subscribed, save_group_settings, temp
from database.connections_mdb import active_connection
import re
import json
import base64
logger = logging.getlogger(__name__)

batch_files = {}

@client.on_message(filters.command("start") & filters.incoming)
async def start(client, message):
    if message.chat.type in [enums.chattype.group, enums.chattype.supergroup]:
        buttons = [
            [
                InlineKeyboardButton('🍿 𝐌𝐎𝐕𝐈𝐄 𝐔𝐏𝐃𝐀𝐓𝐄𝐒', url='https://t.me/ML_LINKS_01')
            ],
            [
                InlineKeyboardButton('💫 𝐇𝐄𝐋𝐏', url=f"https://t.me/{temp.U_NAME}?start=help"),
            ]
            ]
        reply_markup = inlinekeyboardmarkup(buttons)
        await message.reply(script.start_txt.format(message.from_user.mention if message.from_user else message.chat.title, temp.u_name, temp.b_name), reply_markup=reply_markup)
        await asyncio.sleep(2) # 😢 https://github.com/evamariatg/evamaria/blob/master/plugins/p_ttishow.py#l17 😬 wait a bit, before checking.
        if not await db.get_chat(message.chat.id):
            total=await client.get_chat_members_count(message.chat.id)
            await client.send_message(log_channel, script.log_text_g.format(message.chat.title, message.chat.id, total, "unknown"))       
            await db.add_chat(message.chat.id, message.chat.title)
        return 
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)
        await client.send_message(log_channel, script.log_text_p.format(message.from_user.id, message.from_user.mention))
    if len(message.command) != 2:
        buttons = [[
            inlinekeyboardbutton('sᴜʀᴘʀɪsᴇ', callback_data='start')
        ]]
        reply_markup = inlinekeyboardmarkup(buttons)
        m=await message.reply_sticker("caacaguaaxkbaaindml9uwnc3ptj9yntjfu4ygr5dtzwaaieaapbjdexieudbguzybaeba") 
        await asyncio.sleep(1)
        await m.delete()        
        await message.reply_photo(
            photo=random.choice(pics),
            caption=script.sur_txt.format(message.from_user.mention, temp.u_name, temp.b_name),
            reply_markup=reply_markup,
            parse_mode=enums.parsemode.html
        )
        return
    if auth_channel and not await is_subscribed(client, message):
        try:
            invite_link = await client.create_chat_invite_link(int(auth_channel))
        except chatadminrequired:
            logger.error("make sure bot is admin in forcesub channel")
            return
        btn = [
            [
                inlinekeyboardbutton(
                    "🤖 join updates channel", url=invite_link.invite_link
                )
            ]
        ]

        if message.command[1] != "subscribe":
            try:
                kk, file_id = message.command[1].split("_", 1)
                pre = 'checksubp' if kk == 'filep' else 'checksub' 
                btn.append([inlinekeyboardbutton(" 🔄 try again", callback_data=f"{pre}#{file_id}")])
            except (indexerror, valueerror):
                btn.append([inlinekeyboardbutton(" 🔄 try again", url=f"https://t.me/{temp.u_name}?start={message.command[1]}")])
        await client.send_message(
            chat_id=message.from_user.id,
            text="**please join my updates channel to use this bot!**",
            reply_markup=inlinekeyboardmarkup(btn),
            parse_mode=enums.parsemode.markdown
            )
        return
    if len(message.command) == 2 and message.command[1] in ["subscribe", "error", "okay", "help"]:
        buttons = [[
            inlinekeyboardbutton('sᴜʀᴘʀɪsᴇ', callback_data='start')
        ]]
        reply_markup = inlinekeyboardmarkup(buttons)
        await message.reply_photo(
            photo=random.choice(pics),
            caption=script.sur_txt.format(message.from_user.mention, temp.u_name, temp.b_name),
            reply_markup=reply_markup,
            parse_mode=enums.parsemode.html
        )
        return
    data = message.command[1]
    try:
        pre, file_id = data.split('_', 1)
    except:
        file_id = data
        pre = ""
    if data.split("-", 1)[0] == "batch":
        sts = await message.reply("please wait")
        file_id = data.split("-", 1)[1]
        msgs = batch_files.get(file_id)
        if not msgs:
            file = await client.download_media(file_id)
            try: 
                with open(file) as file_data:
                    msgs=json.loads(file_data.read())
            except:
                await sts.edit("failed")
                return await client.send_message(log_channel, "unable to open file.")
            os.remove(file)
            batch_files[file_id] = msgs
        for msg in msgs:
            title = msg.get("title")
            size=get_size(int(msg.get("size", 0)))
            f_caption=msg.get("caption", "")
            if batch_file_caption:
                try:
                    f_caption=batch_file_caption.format(file_name= '' if title is none else title, file_size='' if size is none else size, file_caption='' if f_caption is none else f_caption)
                except exception as e:
                    logger.exception(e)
                    f_caption=f_caption
            if f_caption is none:
                f_caption = f"{title}"
            try:
                await client.send_cached_media(
                    chat_id=message.from_user.id,
                    file_id=msg.get("file_id"),
                    caption=f_caption,
                    protect_content=msg.get('protect', false),
                    )
            except floodwait as e:
                await asyncio.sleep(e.x)
                logger.warning(f"floodwait of {e.x} sec.")
                await client.send_cached_media(
                    chat_id=message.from_user.id,
                    file_id=msg.get("file_id"),
                    caption=f_caption,
                    protect_content=msg.get('protect', false),
                    )
            except exception as e:
                logger.warning(e, exc_info=true)
                continue
            await asyncio.sleep(1) 
        await sts.delete()
        return
    elif data.split("-", 1)[0] == "dstore":
        sts = await message.reply("please wait")
        b_string = data.split("-", 1)[1]
        decoded = (base64.urlsafe_b64decode(b_string + "=" * (-len(b_string) % 4))).decode("ascii")
        try:
            f_msg_id, l_msg_id, f_chat_id, protect = decoded.split("_", 3)
        except:
            f_msg_id, l_msg_id, f_chat_id = decoded.split("_", 2)
            protect = "/pbatch" if protect_content else "batch"
        diff = int(l_msg_id) - int(f_msg_id)
        async for msg in client.iter_messages(int(f_chat_id), int(l_msg_id), int(f_msg_id)):
            if msg.media:
                media = getattr(msg, msg.media)
                if batch_file_caption:
                    try:
                        f_caption=batch_file_caption.format(file_name=getattr(media, 'file_name', ''), file_size=getattr(media, 'file_size', ''), file_caption=getattr(msg, 'caption', ''))
                    except exception as e:
                        logger.exception(e)
                        f_caption = getattr(msg, 'caption', '')
                else:
                    media = getattr(msg, msg.media)
                    file_name = getattr(media, 'file_name', '')
                    f_caption = getattr(msg, 'caption', file_name)
                try:
                    await msg.copy(message.chat.id, caption=f_caption, protect_content=true if protect == "/pbatch" else false)
                except floodwait as e:
                    await asyncio.sleep(e.x)
                    await msg.copy(message.chat.id, caption=f_caption, protect_content=true if protect == "/pbatch" else false)
                except exception as e:
                    logger.exception(e)
                    continue
            elif msg.empty:
                continue
            else:
                try:
                    await msg.copy(message.chat.id, protect_content=true if protect == "/pbatch" else false)
                except floodwait as e:
                    await asyncio.sleep(e.x)
                    await msg.copy(message.chat.id, protect_content=true if protect == "/pbatch" else false)
                except exception as e:
                    logger.exception(e)
                    continue
            await asyncio.sleep(1) 
        return await sts.delete()
        

    files_ = await get_file_details(file_id)           
    if not files_:
        pre, file_id = ((base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))).decode("ascii")).split("_", 1)
        try:
            msg = await client.send_cached_media(
                chat_id=message.from_user.id,
                file_id=file_id,
                protect_content=true if pre == 'filep' else false,
                )
            filetype = msg.media
            file = getattr(msg, filetype)
            title = file.file_name
            size=get_size(file.file_size)
            f_caption = f"<code>{title}</code>"
            if custom_file_caption:
                try:
                    f_caption=custom_file_caption.format(file_name= '' if title is none else title, file_size='' if size is none else size, file_caption='')
                except:
                    return
            await msg.edit_caption(f_caption)
            return
        except:
            pass
        return await message.reply('no such file exist.')
    files = files_[0]
    title = files.file_name
    size=get_size(files.file_size)
    f_caption=files.caption
    if custom_file_caption:
        try:
            f_caption=custom_file_caption.format(file_name= '' if title is none else title, file_size='' if size is none else size, file_caption='' if f_caption is none else f_caption)
        except exception as e:
            logger.exception(e)
            f_caption=f_caption
    if f_caption is none:
        f_caption = f"{files.file_name}"
    await client.send_cached_media(
        chat_id=message.from_user.id,
        file_id=file_id,
        caption=f_caption,
        reply_markup=InlineKeyboardMarkup( [ [ InlineKeyboardButton('🔎 ᴏT‌T‌ M‌ᴏV‌I‌E‌S 🔍', url='https://t.me/ML_LINKS_01')
        ], [
        InlineKeyboardButton('🔎 M‌ᴏV‌I‌E‌S BᴏT 🔍', url='https://t.me/AutofilterV0_bot')
        ] ] ),
        protect_content=True if pre == 'filep' else False,
        )
                    

@client.on_message(filters.command('channel') & filters.user(admins))
async def channel_info(bot, message):
           
    """send basic information of channel"""
    if isinstance(channels, (int, str)):
        channels = [channels]
    elif isinstance(channels, list):
        channels = channels
    else:
        raise valueerror("unexpected type of channels")

    text = '📑 **indexed channels/groups**\n'
    for channel in channels:
        chat = await bot.get_chat(channel)
        if chat.username:
            text += '\n@' + chat.username
        else:
            text += '\n' + chat.title or chat.first_name

    text += f'\n\n**total:** {len(channels)}'

    if len(text) < 4096:
        await message.reply(text)
    else:
        file = 'indexed channels.txt'
        with open(file, 'w') as f:
            f.write(text)
        await message.reply_document(file)
        os.remove(file)


@client.on_message(filters.command('logs') & filters.user(admins))
async def log_file(bot, message):
    """send log file"""
    try:
        await message.reply_document('telegrambot.log')
    except exception as e:
        await message.reply(str(e))

@client.on_message(filters.command('delete') & filters.user(admins))
async def delete(bot, message):
    """delete file from database"""
    reply = message.reply_to_message
    if reply and reply.media:
        msg = await message.reply("processing...⏳", quote=true)
    else:
        await message.reply('reply to file with /delete which you want to delete', quote=true)
        return

    for file_type in ("document", "video", "audio"):
        media = getattr(reply, file_type, none)
        if media is not none:
            break
    else:
        await msg.edit('this is not supported file format')
        return
    
    file_id, file_ref = unpack_new_file_id(media.file_id)

    result = await media.collection.delete_one({
        '_id': file_id,
    })
    if result.deleted_count:
        await msg.edit('file is successfully deleted from database')
    else:
        file_name = re.sub(r"(_|\-|\.|\+)", " ", str(media.file_name))
        result = await media.collection.delete_many({
            'file_name': file_name,
            'file_size': media.file_size,
            'mime_type': media.mime_type
            })
        if result.deleted_count:
            await msg.edit('file is successfully deleted from database')
        else:
            # files indexed before https://github.com/evamariatg/evamaria/commit/f3d2a1bcb155faf44178e5d7a685a1b533e714bf#diff-86b613edf1748372103e94cacff3b578b36b698ef9c16817bb98fe9ef22fb669r39 
            # have original file name.
            result = await media.collection.delete_many({
                'file_name': media.file_name,
                'file_size': media.file_size,
                'mime_type': media.mime_type
            })
            if result.deleted_count:
                await msg.edit('file is successfully deleted from database')
            else:
                await msg.edit('file not found in database')


@client.on_message(filters.command('deleteall') & filters.user(admins))
async def delete_all_index(bot, message):
    await message.reply_text(
        'this will delete all indexed files.\ndo you want to continue??',
        reply_markup=inlinekeyboardmarkup(
            [
                [
                    inlinekeyboardbutton(
                        text="yes", callback_data="autofilter_delete"
                    )
                ],
                [
                    inlinekeyboardbutton(
                        text="cancel", callback_data="close_data"
                    )
                ],
            ]
        ),
        quote=true,
    )


@client.on_callback_query(filters.regex(r'^autofilter_delete'))
async def delete_all_index_confirm(bot, message):
    await media.collection.drop()
    await message.answer('¢ιηємαℓα.¢σм')
    await message.message.edit('succesfully deleted all the indexed files.')


@client.on_message(filters.command('settings'))
async def settings(client, message):
    userid = message.from_user.id if message.from_user else none
    if not userid:
        return await message.reply(f"you are anonymous admin. use /connect {message.chat.id} in pm")
    chat_type = message.chat.type

    if chat_type == enums.chattype.private:
        grpid = await active_connection(str(userid))
        if grpid is not none:
            grp_id = grpid
            try:
                chat = await client.get_chat(grpid)
                title = chat.title
            except:
                await message.reply_text("make sure i'm present in your group!!", quote=true)
                return
        else:
            await message.reply_text("i'm not connected to any groups!", quote=true)
            return

    elif chat_type in [enums.chattype.group, enums.chattype.supergroup]:
        grp_id = message.chat.id
        title = message.chat.title

    else:
        return

    st = await client.get_chat_member(grp_id, userid)
    if (
            st.status != enums.chatmemberstatus.administrator
            and st.status != enums.chatmemberstatus.owner
            and str(userid) not in admins
    ):
        return

    settings = await get_settings(grp_id)

    if settings is not none:
        buttons = [
            [
                inlinekeyboardbutton(
                    'filter button',
                    callback_data=f'setgs#button#{settings["button"]}#{grp_id}',
                ),
                inlinekeyboardbutton(
                    'single' if settings["button"] else 'double',
                    callback_data=f'setgs#button#{settings["button"]}#{grp_id}',
                ),
            ],
            [
                inlinekeyboardbutton(
                    'redirect to',
                    callback_data=f'setgs#botpm#{settings["botpm"]}#{grp_id}',
                ),
                inlinekeyboardbutton(
                    'bot pm' if settings["botpm"] else 'channel',
                    callback_data=f'setgs#botpm#{settings["botpm"]}#{grp_id}',
                ),
            ],
            [
                inlinekeyboardbutton(
                    'file secure',
                    callback_data=f'setgs#file_secure#{settings["file_secure"]}#{grp_id}',
                ),
                inlinekeyboardbutton(
                    '✅ yes' if settings["file_secure"] else '❌ no',
                    callback_data=f'setgs#file_secure#{settings["file_secure"]}#{grp_id}',
                ),
            ],
            [
                inlinekeyboardbutton(
                    'imdb',
                    callback_data=f'setgs#imdb#{settings["imdb"]}#{grp_id}',
                ),
                inlinekeyboardbutton(
                    '✅ yes' if settings["imdb"] else '❌ no',
                    callback_data=f'setgs#imdb#{settings["imdb"]}#{grp_id}',
                ),
            ],
            [
                inlinekeyboardbutton(
                    'spell check',
                    callback_data=f'setgs#spell_check#{settings["spell_check"]}#{grp_id}',
                ),
                inlinekeyboardbutton(
                    '✅ yes' if settings["spell_check"] else '❌ no',
                    callback_data=f'setgs#spell_check#{settings["spell_check"]}#{grp_id}',
                ),
            ],
            [
                inlinekeyboardbutton(
                    'welcome',
                    callback_data=f'setgs#welcome#{settings["welcome"]}#{grp_id}',
                ),
                inlinekeyboardbutton(
                    '✅ yes' if settings["welcome"] else '❌ no',
                    callback_data=f'setgs#welcome#{settings["welcome"]}#{grp_id}',
                ),
            ],
            [
                inlinekeyboardbutton(
                    'auto delete',
                    callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{grp_id}',
                ),
                inlinekeyboardbutton(
                    '10 mins' if settings["auto_delete"] else 'off',
                    callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{grp_id}',
                ),
            ],
        ]

        reply_markup = inlinekeyboardmarkup(buttons)

        await message.reply_text(
            text=f"<b>change your settings for {title} as your wish ⚙</b>",
            reply_markup=reply_markup,
            disable_web_page_preview=true,
            parse_mode=enums.parsemode.html,
            reply_to_message_id=message.id
        )



@client.on_message(filters.command('set_template'))
async def save_template(client, message):
    sts = await message.reply("checking template")
    userid = message.from_user.id if message.from_user else none
    if not userid:
        return await message.reply(f"you are anonymous admin. use /connect {message.chat.id} in pm")
    chat_type = message.chat.type

    if chat_type == enums.chattype.private:
        grpid = await active_connection(str(userid))
        if grpid is not none:
            grp_id = grpid
            try:
                chat = await client.get_chat(grpid)
                title = chat.title
            except:
                await message.reply_text("make sure i'm present in your group!!", quote=true)
                return
        else:
            await message.reply_text("i'm not connected to any groups!", quote=true)
            return

    elif chat_type in [enums.chattype.group, enums.chattype.supergroup]:
        grp_id = message.chat.id
        title = message.chat.title

    else:
        return

    st = await client.get_chat_member(grp_id, userid)
    if (
            st.status != enums.chatmemberstatus.administrator
            and st.status != enums.chatmemberstatus.owner
            and str(userid) not in admins
    ):
        return

    if len(message.command) < 2:
        return await sts.edit("no input!!")
    template = message.text.split(" ", 1)[1]
    await save_group_settings(grp_id, 'template', template)
    await sts.edit(f"successfully changed template for {title} to\n\n{template}") 
