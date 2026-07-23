import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from PIL import Image
import io
import aiohttp

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(F.photo | F.document)
async def scan_qr(message: Message):
    try:
        if message.photo:
            photo = message.photo[-1]
        else:
            if not message.document.mime_type.startswith('image/'):
                await message.answer("Пожалуйста, отправь картинку с QR-кодом.")
                return
            photo = message.document

        file = await bot.get_file(photo.file_id)
        file_bytes = await bot.download_file(file.file_path)
        
        image = Image.open(io.BytesIO(file_bytes.read()))
        
        image_byte_arr = io.BytesIO()
        image.save(image_byte_arr, format='PNG')
        image_byte_arr.seek(0)
        
        async with aiohttp.ClientSession() as session:
            form = aiohttp.FormData()
            form.add_field('file', image_byte_arr.read(), filename='qr.png', content_type='image/png')
            
            async with session.post('http://api.qrserver.com/v1/read-qr-code/', data=form) as response:
                result = await response.json()
                qr_text = result[0]['symbol'][0]['data']
                
                if qr_text:
                    await message.answer(f"Ссылка из QR-кода:\n{qr_text}")
                else:
                    await message.answer("На этой картинке не удалось найти QR-код.")
                    
    except Exception:
        await message.answer("Не удалось распознать QR-код. Убедитесь, что картинка четкая.")

@dp.message(F.text == "/start")
async def start_cmd(message: Message):
    await message.answer("Привет! Отправь мне картинку с QR-кодом, и я вышлю тебе ссылку.")

async def main():
    logging.basicConfig(level=logging.INFO)
    print("Бот запущен и готов к работе!")
    await dp.start_polling(bot)

asyncio.run(main())
