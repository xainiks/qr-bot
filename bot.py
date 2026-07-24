@dp.message(F.photo | F.document)
async def scan_qr(message: Message):
    processing_msg = await message.answer("🔍 Получил картинку, ищу QR-код...")

    if message.photo:
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
    else:
        file_info = await bot.get_file(message.document.file_id)
        
    downloaded_file = await bot.download_file(file_info.file_path)
    
    file_bytes = np.asarray(bytearray(downloaded_file.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    
    if img is None:
        await processing_msg.edit_text("❌ Не удалось прочитать файл картинки.")
        return

    val = ""
    detector = cv2.QRCodeDetector()
    
    # Пробуем оригинал, ч/б и инверсию
    variants = [
        img,
        cv2.cvtColor(img, cv2.COLOR_BGR2GRAY),
        cv2.bitwise_not(img)
    ]
    
    for variant in variants:
        v, _, _ = detector.detectAndDecode(variant)
        if v:
            val = v
            break

    if val:
        await processing_msg.edit_text(f"✅ **QR-код успешно расшифрован:**\n\n{val}", parse_mode="Markdown")
    else:
        await processing_msg.edit_text("❌ На этой картинке не удалось найти QR-код. Попробуй обрезать скриншот ближе к самому QR-коду.")
        
