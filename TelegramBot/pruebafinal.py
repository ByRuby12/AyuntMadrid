import nest_asyncio
import os
import asyncio
import re
import time
from datetime import datetime
from openai import OpenAI
from telegram import (
    Update, KeyboardButton, ReplyKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, MessageHandler, CommandHandler,
    filters, ContextTypes
)
#----------------------------------------------------------------------------

nest_asyncio.apply()

TELEGRAM_GROUP_ID = "-1002545875124"

# Claves API desde variables de entorno
openai_api_key = os.getenv("OPENAI_API_KEY")
telegram_bot_key = os.getenv("CURAIME_BOT_KEY")

# Configurar OpenAI
MODEL = "gpt-4o-mini"
client = OpenAI(api_key=openai_api_key)

# Mensaje de contexto para OpenAI
system_content_prompt = (
    "Eres un bot de Telegram especializado en avisos de emergencia. "
    "Proporcionas información clara y rápida sobre incidentes como incendios, accidentes y desastres naturales. "
    "Siempre respondes con un tono profesional y directo, sin causar pánico."
)

system_content = {"role": "system", "content": system_content_prompt}
messages_to_send = [system_content]

# Diccionario para almacenar avisos pendientes de ubicación
avisos_pendientes = {}  # Clave: user_id, Valor: (descripción, ubicación)
avisos_gestionados = []  # Lista de avisos ya aprobados o atendidos
avisos_enviados = {}  # Para evitar spam de avisos por usuario

# Diccionario para almacenar datos de usuarios verificados
usuarios_verificados = {}

### FUNCIONES BOT IA-------------------------------------------------------------------

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra los comandos disponibles de manera organizada."""
    try:
        menu_message = ( 
            "⚠️ *Bienvenido al Bot de Avisos de Emergencia.*\n\n"
            "🔹 Usa los siguientes comandos:\n\n"
            "✅ /verificar - Registrar tus datos personales para reportar avisos.\n"
            "✅ /aviso - Enviar un aviso de emergencia.\n"
            "✅ /pendientes - Ver los avisos pendientes y los gestionados.\n"
            "✅ /contacto - Ver los números de emergencia en España.\n"
            "✅ /help - Información sobre cómo usar el bot.\n\n"
            "⚠️ *Si estás en peligro inmediato, llama al 112.*"
        )

        await update.message.reply_text(menu_message, parse_mode="Markdown")
    except Exception as e:
        print(f"Error en /menu: {e}")
        await update.message.reply_text("❌ Ha ocurrido un error al mostrar el menú.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Explica detalladamente cómo usar el bot paso a paso, incluyendo la verificación obligatoria."""
    help_text = (
        "⚠️ *Bienvenido al Bot de Avisos de Emergencia* ⚠️\n\n"
        "Este bot está diseñado para proporcionar información en tiempo real sobre emergencias "
        "y alertas importantes en tu zona. Puedes reportar incidentes, recibir avisos de seguridad "
        "y consultar números de emergencia.\n\n"
        "🔹 *¿Cómo funciona?*\n"
        "1️⃣ Usa `/verificar` para registrar tus datos antes de enviar un aviso.\n"
        "2️⃣ Usa `/aviso [descripción]` para reportar una emergencia.\n"
        "3️⃣ Comparte tu ubicación cuando se te solicite.\n"
        "4️⃣ Usa `/pendientes` para ver los avisos en espera y los que han sido gestionados.\n"
        "5️⃣ Consulta los números de emergencia con `/contacto`.\n"
        "6️⃣ Usa `/help` si tienes dudas.\n\n"
        "📜 *Comandos Disponibles:*\n"
        "✅ /menu - Muestra el menú de opciones.\n"
        "✅ /verificar - Registra tus datos personales.\n"
        "✅ /aviso - Reporta una emergencia con ubicación.\n"
        "✅ /pendientes - Lista de avisos pendientes y aprobados.\n"
        "✅ /contacto - Muestra los números de emergencia.\n"
        "✅ /help - Explicación sobre cómo usar el bot.\n\n"
        "📧 *Soporte técnico:* contacto@empresa.com\n"
        "📞 *Teléfono de atención:* +34 600 123 456"
    )
    
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def verificar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Solicita los datos personales antes de permitir enviar un aviso."""
    user_id = update.message.from_user.id

    # 🔹 Verifica si el usuario ya envió sus datos
    if user_id in context.user_data and "datos_verificados" in context.user_data[user_id]:
        await update.message.reply_text("✅ Ya has verificado tus datos. Puedes enviar avisos.")
        return

    await update.message.reply_text(
        "📝 *Verificación de identidad requerida.*\n\n"
        "Por favor, envía los siguientes datos en un solo mensaje:\n"
        "1️⃣ Nombre completo\n"
        "2️⃣ Número de teléfono\n"
        "3️⃣ DNI (Documento de Identidad)\n\n"
        "Ejemplo:\n"
        "`Juan Pérez Gómez, +34 600123456, 12345678X`",
        parse_mode="Markdown"
    )

    # 🔹 Marca al usuario como pendiente de verificación
    context.user_data[user_id] = {"verificacion_pendiente": True}

    # 🔹 Muestra los datos en la consola
    print("―――――――――――――――――――――――――――――――――――――")
    print("📢 NUEVO USUARIO REGISTRADO:")
    print(f"👤 Usuario ID: {user_id}")

async def recibir_datos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe y valida los datos personales enviados por el usuario."""
    user_id = update.message.from_user.id

    if user_id not in context.user_data or "verificacion_pendiente" not in context.user_data[user_id]:
        return  # Ignorar si el usuario no está en proceso de verificación

    datos = update.message.text.strip()
    partes = datos.split(",")

    if len(partes) != 3:
        await update.message.reply_text("❌ Formato incorrecto. Envía los datos como en el ejemplo.")
        return

    nombre, telefono, dni = map(str.strip, partes)

    # Validar datos básicos
    if not re.match(r"^[A-Za-zÁÉÍÓÚáéíóúÑñ ]+$", nombre):
        await update.message.reply_text("❌ Nombre inválido. Debe contener solo letras y espacios.")
        return
    if not re.match(r"^\+?\d{9,15}$", telefono):
        await update.message.reply_text("❌ Teléfono inválido. Usa un formato válido como +34 600123456.")
        return
    if not re.match(r"^\d{8}[A-Za-z]$", dni):
        await update.message.reply_text("❌ DNI inválido. Debe tener 8 números seguidos de una letra (Ej: 12345678X).")
        return

    # Guardar datos en el usuario
    context.user_data[user_id] = {
        "nombre": nombre,
        "telefono": telefono,
        "dni": dni,
        "datos_verificados": True
    }

    await update.message.reply_text("✅ Datos verificados. Ahora puedes enviar avisos con /aviso.")

async def iniciar_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "avisos_pendientes" not in context.bot_data:
        context.bot_data["avisos_pendientes"] = []
    if "avisos_gestionados" not in context.bot_data:
        context.bot_data["avisos_gestionados"] = []

async def aviso(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Procesa cualquier aviso y aplica un cooldown de 2 minutos."""
    try:
        user_id = update.message.from_user.id
        ahora = time.time()

        # Asegurar que el usuario tiene una entrada en context.user_data
        if user_id not in context.user_data:
            context.user_data[user_id] = {}

        # Verificar si el usuario ya está verificado
        if "datos_verificados" not in context.user_data[user_id]:
            await update.message.reply_text(
                "⚠️ *Debes verificar tus datos antes de enviar un aviso.*\nUsa `/verificar`.",
                parse_mode="Markdown"
            )
            return

        # Comprobar si el usuario está en cooldown
        if "ultimo_aviso" in context.user_data[user_id] and (ahora - context.user_data[user_id]["ultimo_aviso"]) < 120:
            tiempo_restante = int(120 - (ahora - context.user_data[user_id]["ultimo_aviso"]))
            await update.message.reply_text(
                f"⏳ *Debes esperar {tiempo_restante} segundos antes de enviar otro aviso.*",
                parse_mode="Markdown"
            )
            return

        # Extraer el texto del aviso correctamente
        user_aviso = update.message.text.replace("/aviso", "").strip()

        if not user_aviso:
            await update.message.reply_text(
                "⚠️ *Formato incorrecto.*\nUsa:\n`/aviso [descripción del incidente]`",
                parse_mode="Markdown"
            )
            return

        # Guardar el aviso en avisos_pendientes en context.bot_data
        if "avisos_pendientes" not in context.bot_data:
            context.bot_data["avisos_pendientes"] = []

        context.bot_data["avisos_pendientes"].append({
            "user_id": user_id,
            "descripcion": user_aviso,
            "ubicacion": None
        })

        await update.message.reply_text(
            "📌 *Envía tu ubicación para completar el aviso.*",
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton("📍 Enviar Ubicación", request_location=True)]],
                one_time_keyboard=True,
                resize_keyboard=True
            ),
            parse_mode="Markdown"
        )

    except Exception as e:
        print(f"❌ Error en /aviso: {e}")
        await update.message.reply_text("❌ Ha ocurrido un error al procesar tu aviso.")

async def recibir_ubicacion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe la ubicación del usuario y la asocia al aviso previo, luego pide una foto."""
    try:
        user_id = update.message.from_user.id
        location = update.message.location

        if not location:
            await update.message.reply_text("❌ No se ha recibido la ubicación. Asegúrate de enviarla correctamente.")
            return

        latitude, longitude = location.latitude, location.longitude

        if "avisos_pendientes" not in context.bot_data:
            context.bot_data["avisos_pendientes"] = []

        # Buscar el aviso pendiente del usuario
        aviso_encontrado = None
        for aviso in context.bot_data["avisos_pendientes"]:
            if aviso["user_id"] == user_id and aviso["ubicacion"] is None:
                aviso["ubicacion"] = (latitude, longitude)
                aviso["foto"] = None  # Agregar campo para la foto
                aviso_encontrado = aviso
                break

        if not aviso_encontrado:
            await update.message.reply_text(
                "⚠️ No tienes un aviso pendiente. Usa /aviso antes de enviar tu ubicación.",
                parse_mode="Markdown"
            )
            return
        print("―――――――――――――――――――――――――――――――――――――")
        print(f"✅ Ubicación guardada para el aviso: {aviso_encontrado}")  # Depuración
        print("―――――――――――――――――――――――――――――――――――――")

        # Pedir una foto opcional
        await update.message.reply_text(
            "📷 *Si es posible, envía una foto del incidente.*\n"
            "Si no tienes una foto, simplemente ignora este mensaje.",
            parse_mode="Markdown"
        )

    except Exception as e:
        print(f"❌ Error en recibir_ubicacion: {e}")
        await update.message.reply_text("❌ Ha ocurrido un error al procesar la ubicación.")

async def recibir_foto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe una foto del usuario y la asocia al aviso pendiente, luego la envía al grupo."""
    try:
        user_id = update.message.from_user.id

        if not update.message.photo:
            await update.message.reply_text("⚠️ No se ha recibido una foto válida.")
            return

        photo = update.message.photo[-1]  # La última imagen suele ser la de mejor calidad
        file_id = photo.file_id

        print(f"📷 Foto recibida de {user_id}, file_id: {file_id}")  # Depuración
        print("―――――――――――――――――――――――――――――――――――――")

        if "avisos_pendientes" not in context.bot_data:
            context.bot_data["avisos_pendientes"] = []

        print(f"📋 Lista de avisos pendientes antes de buscar: {context.bot_data['avisos_pendientes']}")  # Depuración
        print("―――――――――――――――――――――――――――――――――――――")

        aviso_encontrado = None
        for aviso in context.bot_data["avisos_pendientes"]:
            if aviso["user_id"] == user_id and aviso.get("foto") is None:
                aviso["foto"] = file_id
                aviso_encontrado = aviso
                break

        if not aviso_encontrado:
            await update.message.reply_text("⚠️ No tienes un aviso pendiente que requiera una foto.")
            return

        print(f"✅ Foto guardada en el aviso: {aviso_encontrado}")  # Depuración
        print("―――――――――――――――――――――――――――――――――――――")

        # Obtener los datos del usuario
        datos_usuario = context.user_data.get(user_id, {})
        nombre = datos_usuario.get("nombre", "Desconocido")
        telefono = datos_usuario.get("telefono", "No registrado")
        dni = datos_usuario.get("dni", "No registrado")

        # Obtener los datos del aviso
        user_aviso = aviso_encontrado["descripcion"]
        latitude, longitude = aviso_encontrado["ubicacion"]
        fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 📌 Imprimir los datos del usuario en la consola

        print("📢 NUEVO AVISO RECIBIDO:")
        print(f"👤 Nombre      : {nombre}")
        print(f"📅 Fecha y Hora: {fecha_actual}")
        print(f"📞 Teléfono    : {telefono}")
        print(f"🆔 DNI         : {dni}")
        print(f"📌 Aviso       : {user_aviso}")
        print(f"📍 Ubicación   : {latitude}, {longitude}")
        print("―――――――――――――――――――――――――――――――――――――")

        mensaje_grupo = (
            f"🚨 *NUEVO INCIDENTE REPORTADO*\n\n"
            f"📌 *Descripción:* {user_aviso}\n"
            f"📅 *Fecha y Hora:* {fecha_actual}\n"
            f"📍 *Ubicación:* [{latitude}, {longitude}](https://www.google.com/maps?q={latitude},{longitude})\n"
            f"👤 *Reportado por:* {nombre}\n"
            f"🔔 ¡Atención a este incidente!"
        )

        # Enviar la foto al grupo de Telegram
        await context.bot.send_photo(
            chat_id=TELEGRAM_GROUP_ID,
            photo=file_id,
            caption=mensaje_grupo,
            parse_mode="Markdown"
        )

        await update.message.reply_text("✅ *Aviso registrado y enviado con foto.*", parse_mode="Markdown")
        context.user_data[user_id]["ultimo_aviso"] = time.time()

    except Exception as e:
        print(f"❌ Error en recibir_foto: {e}")
        await update.message.reply_text("❌ Ha ocurrido un error al procesar la imagen.")

async def pendientes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra los avisos pendientes y los ya gestionados."""
    mensaje = "📋 *Estado de los avisos de emergencia:*\n\n"

    # Asegurar que las listas existen en `bot_data`
    if "avisos_pendientes" not in context.bot_data:
        context.bot_data["avisos_pendientes"] = []
    if "avisos_gestionados" not in context.bot_data:
        context.bot_data["avisos_gestionados"] = []

    # Mostrar avisos pendientes
    if context.bot_data["avisos_pendientes"]:
        mensaje += "⏳ *Avisos pendientes:*\n"
        for aviso in context.bot_data["avisos_pendientes"]:
            ubicacion = f"📍 {aviso['ubicacion'][0]}, {aviso['ubicacion'][1]}" if aviso["ubicacion"] else "📍 Ubicación pendiente"
            mensaje += f"🔹 {aviso['descripcion']}\n{ubicacion}\n\n"
    else:
        mensaje += "✅ No hay avisos pendientes.\n\n"

    # Mostrar avisos gestionados
    if context.bot_data["avisos_gestionados"]:
        mensaje += "✅ *Avisos gestionados:*\n"
        for aviso in context.bot_data["avisos_gestionados"]:
            mensaje += f"✔️ {aviso['descripcion']}\n\n"
    else:
        mensaje += "ℹ️ No hay avisos gestionados aún.\n"

    await update.message.reply_text(mensaje, parse_mode="Markdown")

async def contacto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra los números de emergencia en España."""
    emergency_numbers = (
        "📞 *Números de Emergencia en España:*\n\n"
        "🚑 Emergencias generales: *112*\n"
        "🚔 Policía Nacional: *091*\n"
        "👮‍♂️ Guardia Civil: *062*\n"
        "🚒 Bomberos: *080* / *085*\n"
        "🏥 Emergencias sanitarias: *061*\n"
        "⚠️ Protección Civil: *900 400 012*\n"
        "🚨 Cruz Roja: *900 100 333*\n"
        "🆘 Violencia de género: *016*\n\n"
        "🔹 *Guarda estos números en tu móvil para cualquier emergencia.*"
    )
    await update.message.reply_text(emergency_numbers, parse_mode="Markdown")

### ARRANQUE DEL BOT-------------------------------------------------------------------
if __name__ == '__main__':
    application = ApplicationBuilder().token(telegram_bot_key).build()
    
    application.add_handler(CommandHandler("menu", menu))
    application.add_handler(CommandHandler("verificar", verificar))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_datos))
    application.add_handler(CommandHandler("aviso", aviso))
    application.add_handler(MessageHandler(filters.LOCATION, recibir_ubicacion))
    application.add_handler(CommandHandler("contacto", contacto))
    # application.add_handler(CommandHandler("stop", stop))
    application.add_handler(MessageHandler(filters.PHOTO, recibir_foto))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("pendientes", pendientes))


    print("✅ El bot está en ejecución. Envía un mensaje en Telegram para probarlo.")
    application.run_polling()
