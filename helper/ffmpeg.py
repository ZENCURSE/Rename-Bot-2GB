import time
import os
import asyncio
from PIL import Image
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser

async def fix_thumb(thumb):
    width = 320
    height = 320
    try:
        if thumb and os.path.exists(thumb):
            parser = createParser(thumb)
            if parser:
                metadata = extractMetadata(parser)
                if metadata:
                    if metadata.has("width"):
                        try:
                            width = metadata.get("width").value if hasattr(metadata.get("width"), 'value') else int(metadata.get("width"))
                        except:
                            pass
                    if metadata.has("height"):
                        try:
                            height = metadata.get("height").value if hasattr(metadata.get("height"), 'value') else int(metadata.get("height"))
                        except:
                            pass
                parser.close()
            # Resize to max 320 to avoid Telegram error
            with Image.open(thumb) as img:
                img = img.convert("RGB")
                img.thumbnail((320, 320))
                img.save(thumb, "JPEG")
                width, height = img.size
    except Exception as e:
        print(f"fix_thumb error: {e}")
        # don't return None, keep original thumb
    return width, height, thumb
    
async def take_screen_shot(video_file, output_directory, ttl):
    os.makedirs(output_directory, exist_ok=True)
    out_put_file_name = f"{output_directory}/{time.time()}.jpg"
    try:
        file_genertor_command = [
            "ffmpeg","-ss",str(ttl),"-i",video_file,"-vframes","1","-q:v","2", out_put_file_name
        ]
        process = await asyncio.create_subprocess_exec(*file_genertor_command,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await process.communicate()
        e = stderr.decode()
        if os.path.exists(out_put_file_name) and os.path.getsize(out_put_file_name) > 1000:
            return out_put_file_name
        else:
            print(f"Screenshot fail: {e}")
            return None
    except Exception as e:
        print(e)
        return None
    
async def add_metadata(input_path, output_path, metadata_text, ms):
    try:
        os.makedirs(os.path.dirname(output_path) or "Metadata", exist_ok=True)
        if not metadata_text or len(str(metadata_text).strip()) == 0:
            return input_path
            
        await ms.edit("<i>I Found Metadata, Adding Into Your File ⚡</i>")
        
        # Clean but keep spaces
        clean_meta = str(metadata_text).strip().replace('\n',' ').replace('\r','')
        # Escape for ffmpeg - use file method if too long
        # Limit to 200 chars to avoid ffmpeg command too long
        if len(clean_meta) > 200:
            clean_meta = clean_meta[:200]

        # Use -metadata:s:v title and -metadata title both for safety
        command = [
            'ffmpeg', '-y', '-i', input_path,
            '-map', '0', '-c', 'copy',
            '-metadata', f'title={clean_meta}',
            '-metadata', f'comment={clean_meta}',
            output_path
        ]
        
        process = await asyncio.create_subprocess_exec(*command,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await process.communicate()
        err = stderr.decode()
        
        if os.path.exists(output_path) and os.path.getsize(output_path) > 100:
            await ms.edit("<i>Metadata Added ✅</i>")
            return output_path
        else:
            print(f"FFmpeg metadata failed: {err}")
            # fallback to original
            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except:
                    pass
            return input_path
    except Exception as e:
        print(f"Metadata Error: {e}")
        return input_path
