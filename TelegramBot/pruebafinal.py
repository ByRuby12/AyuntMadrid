import nest_asyncio
import os
from openai import OpenAI
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

nest_asyncio.apply()  # Soluciona problemas de asincronía en Colab

# Recuperar las claves API desde variables de entorno
openai_api_key = os.getenv("OPENAI_API_KEY")
telegram_bot_key = os.getenv("CURAIME_BOT_KEY")

# Configurar OpenAI
MODEL = "gpt-4o-mini"
client = OpenAI(api_key=openai_api_key)

# Mensaje de contexto para OpenAI
system_content_prompt = (
    "Eres un bot de Telegram con una personalidad divertida y amigable. "
    "Responde con un tono de humor, pero siempre con información precisa."
)

system_content = {"role": "system", "content": system_content_prompt}
messages_to_send = [system_content]

# Función para manejar los mensajes del usuario
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    messages_to_send.append({"role": "user", "content": user_message})

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages_to_send,
            temperature=0.7,
            max_tokens=250
        )
        ai_response = response.choices[0].message.content
        messages_to_send.append({"role": "assistant", "content": ai_response})

        await context.bot.send_message(chat_id=update.effective_chat.id, text=ai_response)

    except Exception as e:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Error: {e}")

# Iniciar el bot
if __name__ == '__main__':
    application = ApplicationBuilder().token(telegram_bot_key).build()
    message_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    application.add_handler(message_handler)
    
    print("✅ El bot está en ejecución. Envía un mensaje en Telegram para probarlo.")
    application.run_polling()
