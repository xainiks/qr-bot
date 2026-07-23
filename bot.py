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
    photo = message.photo[-1]
    file_info = await bot.get_file(photo.file_id)
    downloaded_file = await bot.download_file(file_info.file_path)
    
    file_bytes = np.asarray(bytearray(downloaded_file.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    
    if img is None:
        await message.answer("Не удалось прочитать файл картинки.")
        return

    detector = cv2.QRCodeDetector()
    
    # Пробуем найти в оригинале
    val, points, straight_qrcode = detector.detectAndDecode(img)
    
    # Если не нашли, инвертируем цвета (для белых QR-кодов на цветном фоне)
    if not val:
        inverted_img = cv2.bitwise_not(img)
        val, points, straight_qrcode = detector.detectAndDecode(inverted_img)
    
    if val:
        await message.answer(f"✅ **QR-код успешно расшифрован:**\n\n{val}", parse_mode="Markdown")
    else:
        await message.answer("❌ На этой картинке не удалось найти QR-код.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))
    
