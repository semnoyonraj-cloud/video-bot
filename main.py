import os, asyncio, subprocess, threading, random
from telethon import TelegramClient, events
from PIL import Image
from http.server import HTTPServer, BaseHTTPRequestHandler

# Render-এর Health Check (HEAD ও GET দুটোই হ্যান্ডেল করবে)
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is active!")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        return  # ফালতু লগে স্ক্রিন ভর্তি হওয়া বন্ধ রাখবে

def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

# ব্যাকগ্রাউন্ডে হেলথ চেক সার্ভার চালু
threading.Thread(target=run_health_server, daemon=True).start()

# টেলিগ্রাম বোট কনফিগারেশন
API_ID = 39941595
API_HASH = 'af2f3926bc453f96da9ba2e47b4a1a7e'
BOT_TOKEN = '8339320362:AAHX7ZS7s4MOLJgPqS34Wna__oHhHQGgh_A'

bot = TelegramClient('cloud_bot', API_ID, API_HASH)

@bot.on(events.NewMessage)
async def handler(event):
    if event.text and '/start' in event.text:
        await event.respond("✅ **বট অনলাইন আছে!** লোগো পাঠান, তারপর ভিডিও দিন।")
        return

    if event.photo:
        await bot.download_media(event.message, file="logo.png")
        await event.respond("✅ লোগো সেভড!")
        return

    if event.video or (event.text and 'http' in event.text):
        status = await event.respond("⚡ ১০০+ অটো-র্যান্ডম এডিটিং প্রসেস হচ্ছে (লিপসিংক ফিক্সড)...")
        in_f = f"in_{event.id}.mp4"
        out_f = f"out_{event.id}.mp4"
        
        try:
            if event.text and 'http' in event.text:
                url = event.text.split()[0]
                dl_proc = await asyncio.create_subprocess_exec('yt-dlp', '-o', in_f, url)
                await dl_proc.communicate()
            else:
                await bot.download_media(event.message, file=in_f)

            # ডায়নামিক র্যান্ডমাইজেশন
            speed = round(random.uniform(1.04, 1.15), 2)
            brightness = round(random.uniform(-0.04, 0.04), 2)
            contrast = round(random.uniform(0.96, 1.08), 2)
            saturation = round(random.uniform(0.98, 1.15), 2)
            flip = random.choice([True, False])

            # লোগো পজিশন ও সাইজ
            ov = Image.new('RGBA', (1440, 1080), (0,0,0,0))
            if os.path.exists("logo.png"):
                logo_size = random.randint(130, 170)
                logo = Image.open("logo.png").convert("RGBA").resize((logo_size, logo_size))
                positions = [
                    (60, 60),
                    (1440 - logo_size - 60, 60),
                    (60, 1080 - logo_size - 60),
                    (1440 - logo_size - 60, 1080 - logo_size - 60)
                ]
                ov.paste(logo, random.choice(positions))
            ov.save("ov.png")

            # FFmpeg ফিল্টার
            vf_filters = []
            if flip:
                vf_filters.append("hflip")
            vf_filters.append("scale=1440:1080:force_original_aspect_ratio=increase,crop=1440:1080")
            vf_filters.append(f"eq=brightness={brightness}:contrast={contrast}:saturation={saturation}")
            vf_filters.append(f"setpts=PTS/{speed}")

            vf_string = ",".join(vf_filters)
            filter_complex = f"[0:v]{vf_string}[v];[v][1:v]overlay=0:0[outv];[0:a]atempo={speed}[outa]"

            cmd = [
                'ffmpeg', '-y', '-i', in_f, '-i', 'ov.png',
                '-filter_complex', filter_complex,
                '-map', '[outv]', '-map', '[outa]',
                '-map_metadata', '-1',
                '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '28',
                '-c:a', 'aac', '-b:a', '128k', out_f
            ]
            
            proc = await asyncio.create_subprocess_exec(*cmd, stderr=asyncio.subprocess.PIPE)
            await proc.communicate()
            
            if os.path.exists(out_f):
                await status.delete()
                await bot.send_file(event.chat_id, out_f)
        except Exception as e:
            await status.edit(f"❌ প্রসেসিং ভুল হয়েছে: {str(e)}")
        finally:
            if os.path.exists(out_f): os.remove(out_f)
            if os.path.exists(in_f): os.remove(in_f)
            if os.path.exists("ov.png"): os.remove("ov.png")

async def main():
    await bot.start(bot_token=BOT_TOKEN)
    await bot.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
