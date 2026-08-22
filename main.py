import os, asyncio, subprocess
from telethon import TelegramClient, events
from PIL import Image

API_ID = 39941595
API_HASH = 'af2f3926bc453f96da9ba2e47b4a1a7e'
BOT_TOKEN = '8339320362:AAHX7ZS7s4MOLJgPqS34Wna__oHhHQGgh_A'

async def main():
    bot = TelegramClient('cloud_bot', API_ID, API_HASH)
    await bot.start(bot_token=BOT_TOKEN)

    @bot.on(events.NewMessage)
    async def handler(event):
        if event.photo:
            await bot.download_media(event.message, file="logo.png")
            await event.respond("✅ লোগো সেভড!")
            return

        if event.video or (event.text and 'http' in event.text):
            status = await event.respond("⚡ প্রসেসিং শুরু...")
            in_f = f"in_{event.id}.mp4"
            if event.text:
                subprocess.run(['yt-dlp', '-o', in_f, event.text.split()[0]])
            else:
                await bot.download_media(event.message, file=in_f)
            
            ov = Image.new('RGBA', (1440, 1080), (0,0,0,0))
            if os.path.exists("logo.png"):
                logo = Image.open("logo.png").convert("RGBA").resize((150, 150))
                ov.paste(logo, (60, 60))
            ov.save("ov.png")

            out_f = f"out_{event.id}.mp4"
            cmd = [
                'ffmpeg', '-y', '-i', in_f, '-i', 'ov.png',
                '-filter_complex', '[0:v]hflip,scale=1440:1080:force_original_aspect_ratio=increase,crop=1440:1080,setpts=PTS/1.2[v];[v][1:v]overlay=0:0[outv];[0:a]atempo=1.2[outa]',
                '-map', '[outv]', '-map', '[outa]', '-map_metadata', '-1',
                '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '28', '-c:a', 'aac', '-b:a', '128k', out_f
            ]
            
            proc = await asyncio.create_subprocess_exec(*cmd, stderr=asyncio.subprocess.PIPE)
            await proc.communicate()
            
            if os.path.exists(out_f):
                await status.delete()
                await bot.send_file(event.chat_id, out_f)
                os.remove(out_f)
            if os.path.exists(in_f):
                os.remove(in_f)

    await bot.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
