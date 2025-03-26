import nest_asyncio
import os
import asyncio
import re
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
            "✅ /help - Información sobre cómo usar el bot.\n"
            "✅ /stop - Detener el bot.\n\n"
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

async def aviso(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Procesa cualquier aviso sin evaluar su gravedad."""
    try:
        user_id = update.message.from_user.id

        # 🔹 Verifica si el usuario está verificado
        if user_id not in context.user_data or "datos_verificados" not in context.user_data[user_id]:
            await update.message.reply_text(
                "⚠️ *Debes verificar tus datos antes de enviar un aviso.*\nUsa `/verificar`.",
                parse_mode="Markdown"
            )
            return

        # 🔹 Extraer el texto del aviso correctamente
        user_aviso = update.message.text.replace("/aviso", "").strip()

        if not user_aviso:
            await update.message.reply_text(
                "⚠️ *Formato incorrecto.*\nUsa:\n`/aviso [descripción detallada del incidente]`",
                parse_mode="Markdown"
            )
            return

        # 🔹 Guarda el aviso sin importar su contenido
        avisos_pendientes[user_id] = (user_aviso, "Ubicación pendiente")

        await update.message.reply_text(
            "✅ *Aviso registrado correctamente.*\nSi es necesario, envía tu ubicación.",
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

async def pendientes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra los avisos pendientes y los ya gestionados."""
    mensaje = "📋 *Estado de los avisos de emergencia:*\n\n"

    # 🔹 Mostrar avisos pendientes
    if avisos_pendientes:
        mensaje += "⏳ *Avisos pendientes:*\n"
        for user_id, (descripcion, ubicacion) in avisos_pendientes.items():
            mensaje += f"🔹 {descripcion}\n📍 Ubicación: {ubicacion}\n\n"
    else:
        mensaje += "✅ No hay avisos pendientes.\n\n"

    # 🔹 Mostrar avisos gestionados
    if avisos_gestionados:
        mensaje += "✅ *Avisos gestionados:*\n"
        for aviso in avisos_gestionados:
            mensaje += f"✔️ {aviso}\n\n"
    else:
        mensaje += "ℹ️ No hay avisos gestionados aún.\n"

    await update.message.reply_text(mensaje, parse_mode="Markdown")

async def recibir_ubicacion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe la ubicación del usuario y la asocia al aviso previo, luego lo envía al grupo."""
    try:
        user_id = update.message.from_user.id
        location = update.message.location

        # 🔹 Depurar si la ubicación se recibe correctamente
        if location is None:
            await update.message.reply_text("❌ No se ha recibido la ubicación. Asegúrate de enviarla correctamente.")
            return

        latitude, longitude = location.latitude, location.longitude

        # 🔹 Verificar si el usuario tiene un aviso pendiente
        if user_id not in avisos_pendientes:
            await update.message.reply_text(
                "⚠️ No tienes un aviso pendiente. Usa /aviso antes de enviar tu ubicación.",
                parse_mode="Markdown"
            )
            return

        user_aviso = avisos_pendientes.pop(user_id)

        # 🔹 Obtener la fecha y hora actual
        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 🔹 Obtener los datos del usuario
        datos_usuario = context.user_data.get(user_id, {})
        nombre = datos_usuario.get("nombre", "Desconocido")
        telefono = datos_usuario.get("telefono", "No proporcionado")
        dni = datos_usuario.get("dni", "No proporcionado")

        # 🔹 Formatear el mensaje para el grupo
        mensaje_grupo = (
            f"🚨 *NUEVO INCIDENTE REPORTADO*\n\n"
            f"📌 *Descripción:* {user_aviso}\n"
            f"📅 *Fecha y Hora:* {fecha_actual}\n"
            f"📍 *Ubicación:* [{latitude}, {longitude}](https://www.google.com/maps?q={latitude},{longitude})\n"
            f"👤 *Reportado por:* {nombre}\n"
            f"🔔 ¡Atención a este incidente!"
        )

        # 🔹 Enviar el aviso al grupo
        await context.bot.send_message(chat_id=TELEGRAM_GROUP_ID, text=mensaje_grupo, parse_mode="Markdown")

        # 🔹 Confirmar al usuario que el aviso fue enviado
        await update.message.reply_text(
            "✅ *Aviso registrado y enviado al grupo de incidentes.*\n"
            "Gracias por reportarlo.",
            parse_mode="Markdown"
        )

        # 🔹 Registrar en consola
        print("―――――――――――――――――――――――――――――――――――――")
        print("📢 NUEVO AVISO RECIBIDO:")
        print(f"👤 Nombre: {nombre}")
        print(f"📅 Fecha y Hora: {fecha_actual}")
        print(f"📞 Teléfono: {telefono}")
        print(f"🆔 DNI: {dni}")
        print(f"📌 Aviso: {user_aviso}")
        print(f"📍 Ubicación: {latitude}, {longitude}")

    except Exception as e:
        print(f"Error en recibir_ubicacion: {e}")
        await update.message.reply_text("❌ Ha ocurrido un error al procesar la ubicación.")

async def unknown_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Responde a mensajes no relacionados con emergencias."""
    await update.message.reply_text(
        "⚠️ *Este bot solo está diseñado para reportar emergencias.*\n\n"
        "Usa `/aviso` para reportar un incidente real o `/menu` para ver las opciones disponibles.",
        parse_mode="Markdown"
    )

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Detiene la ejecución del bot."""
    try:
        await update.message.reply_text("⛔ Apagando el bot...")
        loop = asyncio.get_event_loop()
        loop.stop()
    except Exception as e:
        print(f"Error en /stop: {e}")
        await update.message.reply_text("❌ Error al intentar detener el bot.")

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

### ARRANQUE DEL BOT
if __name__ == '__main__':
    application = ApplicationBuilder().token(telegram_bot_key).build()
    
    application.add_handler(CommandHandler("menu", menu))
    application.add_handler(CommandHandler("verificar", verificar))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_datos))
    application.add_handler(CommandHandler("aviso", aviso))
    application.add_handler(MessageHandler(filters.LOCATION, recibir_ubicacion))
    application.add_handler(CommandHandler("contacto", contacto))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_message))    
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, unknown_message)) ##sd
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("pendientes", pendientes))


    print("✅ El bot está en ejecución. Envía un mensaje en Telegram para probarlo.")
    application.run_polling()
