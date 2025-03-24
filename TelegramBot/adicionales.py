#-------------------------TRADUCTOR AUTOMATICO---------------------------------------------------

async def translate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = " ".join(context.args)  # Captura lo que viene después del comando
    if not user_text:
        await update.message.reply_text("❌ Escribe el texto que quieres traducir. Ejemplo: `/traduce Hello world`")
        return
    
    messages_to_send.append({"role": "user", "content": f"Traduce esto al español: {user_text}"})
    
    response = client.chat.completions.create(
        model=MODEL, messages=messages_to_send, temperature=0.7, max_tokens=250
    )
    translation = response.choices[0].message.content
    
    await update.message.reply_text(f"📝 Traducción: {translation}")

# Agregar el comando /traduce al bot
application.add_handler(CommandHandler("traduce", translate))

#-------------------------DICCIONARIO PARA ALMACENAR DATOS CHAT---------------------------------------------------

user_conversations = {}  # Diccionario para almacenar el historial de cada usuario

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    user_message = update.message.text

    # Si el usuario no tiene historial, crearlo
    if user_id not in user_conversations:
        user_conversations[user_id] = [system_content]
    
    # Agregar el mensaje del usuario al historial
    user_conversations[user_id].append({"role": "user", "content": user_message})

    # Enviar la conversación a OpenAI
    response = client.chat.completions.create(
        model=MODEL, messages=user_conversations[user_id], temperature=0.7, max_tokens=250
    )

    ai_response = response.choices[0].message.content
    user_conversations[user_id].append({"role": "assistant", "content": ai_response})

    await context.bot.send_message(chat_id=user_id, text=ai_response)

#----------------------generar imagenes ia------------------------------------------------------

#primero paso
!pip install pillow
#segundo paso
from telegram import InputFile

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.photo[-1].get_file()
    file_path = file.file_path
    
    # Descargar imagen
    image_file = "photo.jpg"
    file.download(image_file)

    # Enviar la imagen a OpenAI Vision (GPT-4o admite imágenes)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Describe la imagen de manera detallada."},
            {"role": "user", "content": [{"type": "image_url", "image_url": file_path}]}
        ]
    )

    ai_response = response.choices[0].message.content
    await update.message.reply_text(f"📷 Análisis de imagen: {ai_response}")

application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

#problema que tiene un limite de generar imagenes 8cobran por imagenes)