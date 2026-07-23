import os
import cv2
import numpy as np
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart

TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start_cmd(message: Message):
    await message.answer("Привет! Отправь мне картинку или скриншот с QR-кодом, и я его расшифрую.")

@dp.message(F.photo)
async def scan_qr(message: Message):
    # Берем самое качественное фото из тех, что прислал телеграм
    photo = message.photo[-1]
    file_info = await bot.get_file(photo.file_id)
    
    # Скачиваем файл в байты
    downloaded_file = await bot.download_file(file_info.file_path)
    
    # Превращаем байты в картинку для OpenCV
    file_bytes = np.asarray(bytearray(downloaded_file.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    
    if img is None:
        await message.answer("Не удалось прочитать файл картинки.")
        return

    # Используем встроенный в OpenCV детектор QR-кодов
    detector = cv2.QRCodeDetector()
    val, points, straight_qrcode = detector.detectAndDecode(img)
    
    if val:
        await message.answer(f"✅ **QR-код успешно расшифрован:**\n\n{val}", parse_mode="Markdown")
    else:
        await message.answer("❌ На этой картинке не удалось найти QR-код. Попробуй отправить скриншот целиком или без сжатия (как файл).")

if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))
    
