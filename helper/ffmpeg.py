import time
import os
import asyncio
from PIL import Image
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from pyrogram.types import Message

async def fix_thumb(thumb):
    width = 0
    height = 0
    try:
        if thumb != None:
            parser = createParser(thumb)
            metadata = extractMetadata(parser)
            if metadata.has("width"):
                width = metadata.get("width")
            if metadata.has("height"):
                height = metadata.get("height")
            with Image.open(thumb) as img:
                img.convert("RGB").save(thumb)
                resized_img = img.resize((width, height))
                resized_img.save(thumb, "JPEG")
            parser.close()
    except Exception as e:
        print(e)
        thumb = None 
    return width, height, thumb
    
async def take_screen_shot(video_file, output_directory, ttl):
    os.makedirs(output_directory, exist_ok=True) # FIX
    out_put_file_name = f"{output_directory}/{time.time()}.jpg"
    file_genertor_command = [
        "ffmpeg","-ss",str(ttl),"-i",video_file,"-vframes","1",out_put_file_name
    ]
    process = await asyncio.create_subprocess_exec(*file_genertor_command,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await process.communicate()
    if os.path.lexists(out_put_file_name):
        return out_put_file_name
    return None
    
async def add_metadata(input_path, output_path, metadata, ms):
    try:
        # FIX 1: Create folder if not exists
        os.makedirs(os.path.dirname(output_path) or "Metadata", exist_ok=True)
        os.makedirs("Metadata", exist_ok=True)
        
        await ms.edit("<i>I Found Metadata, Adding Into Your File ⚡</i>")
        # FIX 2: Clean metadata - remove quotes that break ffmpeg
        clean_meta = str(metadata).replace('"','').replace("'",'').strip()
        if not clean_meta:
            clean_meta = "Encoded By @MadflixBotz"

        command = [
            'ffmpeg', '-y', '-i', input_path, '-map', '0', '-c', 'copy',
            '-metadata', f'title={clean_meta}',
            '-metadata', f'author={clean_meta}',
            output_path
        ]
        
        process = await asyncio.create_subprocess_exec(*command,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await process.communicate()
        print(stderr.decode())

        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            await ms.edit("<i>Metadata Added ✅</i>")
            return output_path
        else:
            print(f"FFmpeg failed, using original file")
            return input_path # Fallback to original instead of None
    except Exception as e:
        print(f"Metadata Error: {e}")
        return input_path
