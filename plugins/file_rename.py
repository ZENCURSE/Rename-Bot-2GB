from pyrogram import Client, filters
from pyrogram.enums import MessageMediaType
from pyrogram.errors import FloodWait
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from hachoir.metadata import extractMetadata
from helper.ffmpeg import fix_thumb, take_screen_shot, add_metadata
from hachoir.parser import createParser
from helper.utils import progress_for_pyrogram, convert, humanbytes, add_prefix_suffix
from helper.database import jishubotz
from asyncio import sleep
from PIL import Image
import os, time, re, random, asyncio

@Client.on_message(filters.private & (filters.document | filters.audio | filters.video))
async def rename_start(client, message):
    file = getattr(message, message.media.value)
    filename = file.file_name  
    if file.file_size > 2000 * 1024 * 1024:
         return await message.reply_text("Sorry Bro This Bot Doesn't Support Uploading Files Bigger Than 2GB", quote=True)
    try:
        await message.reply_text(
            text=f"**Please Enter New Filename...**\n\n**Old File Name** :- `{filename}`",
	    reply_to_message_id=message.id,  
	    reply_markup=ForceReply(True)
        )       
        await sleep(30)
    except FloodWait as e:
        await sleep(e.value)
        await message.reply_text(
            text=f"**Please Enter New Filename**\n\n**Old File Name** :- `{filename}`",
	    reply_to_message_id=message.id,  
	    reply_markup=ForceReply(True)
        )
    except:
        pass

@Client.on_message(filters.private & filters.reply)
async def refunc(client, message):
    reply_message = message.reply_to_message
    if (reply_message.reply_markup) and isinstance(reply_message.reply_markup, ForceReply):
        new_name = message.text 
        await message.delete() 
        msg = await client.get_messages(message.chat.id, reply_message.id)
        file = msg.reply_to_message
        media = getattr(file, file.media.value)
        if not "." in new_name:
            if "." in media.file_name:
                extn = media.file_name.rsplit('.', 1)[-1]
            else:
                extn = "mkv"
            new_name = new_name + "." + extn
        await reply_message.delete()
        button = [[InlineKeyboardButton("📁 Document",callback_data = "upload_document")]]
        if file.media in [MessageMediaType.VIDEO, MessageMediaType.DOCUMENT]:
            button.append([InlineKeyboardButton("🎥 Video", callback_data = "upload_video")])
        elif file.media == MessageMediaType.AUDIO:
            button.append([InlineKeyboardButton("🎵 Audio", callback_data = "upload_audio")])
        await message.reply(
            text=f"**Select The Output File Type**\n\n**File Name :-** `{new_name}`",
            reply_to_message_id=file.id,
            reply_markup=InlineKeyboardMarkup(button)
        )

@Client.on_callback_query(filters.regex("upload"))
async def doc(bot, update):    
    if not os.path.isdir("Metadata"):
        os.makedirs("Metadata", exist_ok=True)
    if not os.path.isdir("downloads"):
        os.makedirs("downloads", exist_ok=True)
        
    prefix = await jishubotz.get_prefix(update.message.chat.id)
    suffix = await jishubotz.get_suffix(update.message.chat.id)
    new_name = update.message.text
    new_filename_ = new_name.split(":-")[1]

    try:
        new_filename = add_prefix_suffix(new_filename_, prefix, suffix)
    except Exception as e:
        return await update.message.edit(f"Prefix/Suffix Error: `{e}`")
    
    file_path = f"downloads/{update.from_user.id}/{new_filename}"
    os.makedirs(f"downloads/{update.from_user.id}", exist_ok=True)
    file = update.message.reply_to_message
    ms = await update.message.edit("🚀 Try To Download...  ⚡")    
    try:
     	path = await bot.download_media(message=file, file_name=file_path, progress=progress_for_pyrogram,progress_args=("🚀 Try To Downloading...  ⚡", ms, time.time()))                    
    except Exception as e:
     	return await ms.edit(f"`{e}`")

    # --- METADATA FIXED ---
    _bool_metadata = await jishubotz.get_metadata(update.message.chat.id) 
    final_path = path
    if _bool_metadata:
        try:
            metadata_code = await jishubotz.get_metadata_code(update.message.chat.id)
            metadata_path = f"Metadata/{new_filename}"
            new_final = await add_metadata(path, metadata_path, metadata_code, ms)
            if new_final and os.path.exists(new_final):
                final_path = new_final
        except Exception as e:
            print(f"Metadata add failed: {e}")
            final_path = path
    else:
        await ms.edit("⏳ Mode Changing...  ⚡")

    # --- DURATION FIXED ---
    duration = 0
    try:
        parser = createParser(final_path)
        if parser:
            metadata = extractMetadata(parser)
            if metadata and metadata.has("duration"):
               duration = metadata.get('duration').seconds
            parser.close()
    except Exception as e:
        print(f"Duration extract failed: {e}")
        pass
        
    ph_path = None
    media = getattr(file, file.media.value)
    c_caption = await jishubotz.get_caption(update.message.chat.id)
    c_thumb = await jishubotz.get_thumbnail(update.message.chat.id)

    if c_caption:
         try:
             caption = c_caption.format(filename=new_filename, filesize=humanbytes(media.file_size), duration=convert(duration))
         except Exception as e:
             return await ms.edit(text=f"Caption Error: {e}")
    else:
         caption = f"**{new_filename}**"

    if (media.thumbs or c_thumb):
         if c_thumb:
             ph_path = await bot.download_media(c_thumb)
             width, height, ph_path = await fix_thumb(ph_path)
         else:
             try:
                 # FIXED: don't use duration-1 crash
                 ss_time = random.randint(0, duration - 1) if duration > 1 else 1
                 ph_path_ = await take_screen_shot(final_path, os.path.dirname(os.path.abspath(final_path)), ss_time)
                 width, height, ph_path = await fix_thumb(ph_path_)
             except Exception as e:
                 print(e)
                 ph_path = None

    await ms.edit("💠 Try To Upload... ⚡")
    type = update.data.split("_")[1]
    try:
        if type == "document":
            await bot.send_document(update.message.chat.id, document=final_path, thumb=ph_path, caption=caption, progress=progress_for_pyrogram, progress_args=("💠 Try To Uploading... ⚡", ms, time.time()))
        elif type == "video":
            await bot.send_video(update.message.chat.id, video=final_path, caption=caption, thumb=ph_path, duration=duration, progress=progress_for_pyrogram, progress_args=("💠 Try To Uploading... ⚡", ms, time.time()))
        elif type == "audio":
            await bot.send_audio(update.message.chat.id, audio=final_path, caption=caption, thumb=ph_path, duration=duration, progress=progress_for_pyrogram, progress_args=("💠 Try To Uploading... ⚡", ms, time.time()))
    except Exception as e:
        return await ms.edit(f"**Error :** `{e}`")
    finally:
        await ms.delete()
        try:
            if ph_path and os.path.exists(ph_path):
                os.remove(ph_path)
            if final_path and os.path.exists(final_path):
                os.remove(final_path)
            if path != final_path and os.path.exists(path):
                os.remove(path)
        except:
            pass
