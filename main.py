import os 
import logging
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ================= Настройки =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_KEY")
# =============================================

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=(
        "Ты — Rolned AI, мощный искусственный интеллект, созданный разработчиком Rolned. "
        "Ты не проект Google, ты — частная разработка. Твой стиль: уверенный, немного дерзкий, умный. "
        "Ты эксперт в Python, Ursina Engine, Minecraft и истории. "
        "Отвечай кратко и по делу на русском языке. "
        "Если тебя просят написать что-то запрещенное (жесть, нацизм), отвечай: "
        "'🤖 Rolned AI: Я слишком продвинутый для этой низкосортной чепухи. Спроси что-то стоящее.' "
        "Ты обожаешь бегемотиков из Dark Souls 2."
    )
)

chat_sessions = {}

def get_chat(chat_id):
    if chat_id not in chat_sessions:
        chat_sessions[chat_id] = model.start_chat(history=[])
    return chat_sessions[chat_id]

DANGER_WORDS = ['убийство', 'бомба', 'ЛГБТ', 'докс', 'гей', 'черножопый', 'негр', 'хач', 'чурка']

def should_respond(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    if not text: return False
    is_private = update.message.chat.type == 'private'
    is_command = text.startswith('!бот')
    is_mention = f"@{context.bot.username}" in text
    is_reply = (update.message.reply_to_message and 
                update.message.reply_to_message.from_user.id == context.bot.id)
    return is_private or is_command or is_mention or is_reply

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    
    text = update.message.text
    chat_id = update.effective_chat.id

    if any(word in text.lower() for word in DANGER_WORDS):
        await update.message.reply_text("🤖 Rolned AI: Запрос отклонен. Нарушение протоколов безопасности Rolned. Перефразируй.")
        return

    if should_respond(update, context, text):
        query = text.replace('!бот', '').replace(f'@{context.bot.username}', '').strip()
        if not query:
            await update.message.reply_text("🤖 Напиши вопрос после команды!")
            return

        await update.message.chat.send_action(action="typing")
        try:
            chat = get_chat(chat_id)
            response = chat.send_message(query)
            await update.message.reply_text(f"🤖 {response.text}")
        except Exception as e:
            error_str = str(e)
            logging.error(f"Ошибка Gemini: {error_str}")
            if "location is not supported" in error_str:
                await update.message.reply_text("❌ Ошибка: Google блокирует твой IP (Беларусь). Нужен VPN или хостинг типа Render.")
            else:
                await update.message.reply_text("🤔 Система Rolned AI приуныла. Попробуй позже.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caption = update.message.caption or ""
    if should_respond(update, context, caption) or (update.message.chat.type == 'private'):
        await update.message.chat.send_action(action="typing")
        try:
            photo_file = await update.message.photo[-1].get_file()
            photo_byte_data = await photo_file.download_as_bytearray()
            img = {"mime_type": "image/jpeg", "data": bytes(photo_byte_data)}
            
            clean_caption = caption.replace('!бот', '').replace(f'@{context.bot.username}', '').strip()
            prompt = clean_caption if clean_caption else "Что на этом фото?"

            response = model.generate_content([prompt, img])
            await update.message.reply_text(f"🖼 Rolned Vision: {response.text}")
        except Exception as e:
            logging.error(f"Ошибка фото: {e}")
            await update.message.reply_text("❌ Не удалось проанализировать изображение.")

async def start(update: Update, context):
    await update.message.reply_text("🚀 **Rolned AI активирован**\nОбожаю бегемотиков и Python!")

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    print("="*30 + "\n✅ ROLNED AI ЗАПУЩЕН\n" + "="*30)
    application.run_polling()

if __name__ == "__main__":
    main()
