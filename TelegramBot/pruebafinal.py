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
avisos_pendientes = {}
avisos_enviados = {}

# Expresión regular para validar avisos (evita avisos falsos)
VALID_AVISO_PATTERN = re.compile(r"(accidente|incendio|robo|fuego|choque|explosión|inundación|sismo|derrumbe|emergencia)", re.IGNORECASE)

# Diccionario para almacenar datos de usuarios verificados
usuarios_verificados = {}

### FUNCIONES BOT IA

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra los comandos disponibles de manera organizada."""
    try:
        menu_message = ( 
            "⚠️ *Bienvenido al Bot de Avisos de Emergencia.*\n\n"
            "🔹 Usa los siguientes comandos:\n\n"
            "✅ /verificar - Registrar tus datos personales para reportar avisos.\n"
            "✅ /aviso - Enviar un aviso de emergencia.\n"
            "✅ /contacto - Ver los números de emergencia en España.\n"
            "✅ /help - Información sobre cómo usar el bot.\n"
            "✅ /stop - Detener el bot.\n\n"
            "⚠️ *Si estás en peligro inmediato, llama al 112.*"
        )

        await update.message.reply_text(menu_message, parse_mode="Markdown")
    except Exception as e:
        print(f"Error en /menu: {e}")
        await update.message.reply_text("❌ Ha ocurrido un error al mostrar el menú.")

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

async def evaluar_gravedad_aviso(aviso_texto):
    """Evalúa la gravedad del aviso y determina si es válido o no."""
    try:
        prompt = (
            f"Analiza el siguiente reporte de emergencia:\n\n"
            f"Aviso: \"{aviso_texto}\"\n\n"
            f"Clasifícalo en una de estas categorías y responde con SOLO UNA PALABRA EXACTA:\n"
            f"- 'grave': Si el incidente pone en riesgo la vida, salud o seguridad de las personas. Ejemplos:\n"
            f"  - Accidentes de tráfico con heridos\n"
            f"  - Incendios, explosiones o derrumbes\n"
            f"  - Robos violentos, peleas con armas, tiroteos\n"
            f"  - Personas inconscientes, infartos, ataques epilépticos\n"
            f"  - Desastres naturales como sismos, inundaciones, tormentas fuertes\n"
            f"  - Suicidios o intentos de suicidio\n\n"
            f"- 'no grave': Si es un problema menor que no requiere respuesta inmediata de emergencia. Ejemplos:\n"
            f"  - Peleas sin armas o sin heridos\n"
            f"  - Molestias leves como ruido o discusiones\n"
            f"  - Objetos perdidos o robos menores sin violencia\n"
            f"  - Enfermedades leves o síntomas menores\n\n"
            f"- 'inválido': Si el mensaje no tiene sentido, es una broma, un error o no es una emergencia. Ejemplos:\n"
            f"  - Spam, bromas o mensajes aleatorios\n"
            f"  - Situaciones que no son urgentes (ej. 'perdí mi celular', 'no tengo internet')\n"
            f"  - Avisos sin información clara\n\n"
            f"Responde con SOLO UNA PALABRA: 'grave', 'no grave' o 'inválido'. No agregues ninguna otra explicación."
        )

        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                system_content,
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,  # Más precisión, menos respuestas aleatorias
            max_tokens=5  # Solo responde con una palabra
        )

        resultado = response.choices[0].message.content.strip().lower()

        if resultado in ["grave", "no grave", "inválido"]:
            return resultado
        else:
            return "error"

    except Exception as e:
        print(f"Error al evaluar la gravedad del aviso: {e}")
        return "error"

async def aviso(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Permite a los usuarios enviar un aviso personalizado y solicita ubicación solo si verificaron sus datos."""
    try:
        user_id = update.message.from_user.id

        # 🔹 Verifica si el usuario ya ha enviado sus datos
        if user_id not in context.user_data or "datos_verificados" not in context.user_data[user_id]:
            await update.message.reply_text(
                "⚠️ *Antes de enviar un aviso, debes verificar tus datos.*\n"
                "Usa el comando `/verificar` para registrarte.",
                parse_mode="Markdown"
            )
            return  # Detiene la ejecución de la función hasta que el usuario verifique sus datos

        # 🔹 Control de spam: Limita a 3 avisos en poco tiempo
        if user_id in avisos_enviados and avisos_enviados[user_id] >= 3:
            await update.message.reply_text("❌ Has enviado demasiados avisos en poco tiempo. Espera antes de enviar otro.")
            return

        # 🔹 Verifica que el usuario haya enviado un aviso con texto
        if not context.args:
            await update.message.reply_text(
                "⚠️ *Formato incorrecto.*\n"
                "Usa el comando así:\n"
                "`/aviso [descripción del incidente]`\n\n"
                "Ejemplo:\n"
                "`/aviso Accidente en la autopista A3, dirección Madrid.`",
                parse_mode="Markdown"
            )
            return

        user_aviso = " ".join(context.args)

        # 🔹 Evaluar la gravedad del aviso con IA
        gravedad = await evaluar_gravedad_aviso(user_aviso)
        
        if gravedad == "grave":
            # Guarda el aviso y aumenta el contador
            avisos_pendientes[user_id] = user_aviso
            avisos_enviados[user_id] = avisos_enviados.get(user_id, 0) + 1

            # Pide ubicación
            keyboard = ReplyKeyboardMarkup(
                [[KeyboardButton("📍 Enviar Ubicación", request_location=True)]],
                one_time_keyboard=True,
                resize_keyboard=True
            )

            await update.message.reply_text(
                "📌 *Por favor, comparte tu ubicación para precisar el aviso.*\n"
                "Pulsa el botón de abajo para enviar tu ubicación exacta.",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        
        elif gravedad == "no grave":
            await update.message.reply_text(
                "❌ *Aviso no aceptado.*\n"
                "El incidente descrito no parece ser una emergencia grave. "
                "Si consideras que es realmente urgente, proporciona más detalles.",
                parse_mode="Markdown"
            )

        else:  # "inválido" o "error"
            await update.message.reply_text(
                "🚫 *Aviso inválido.*\n"
                "Parece que el mensaje no tiene sentido o no es una emergencia real.",
                parse_mode="Markdown"
            )

    except Exception as e:
        print(f"Error en /aviso: {e}")
        await update.message.reply_text("❌ Ha ocurrido un error al procesar tu aviso.")

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
            await update.message.reply_text("❌ No tienes ningún aviso pendiente. Usa /aviso primero.")
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
    application.add_handler(CommandHandler("stop", stop))

    print("✅ El bot está en ejecución. Envía un mensaje en Telegram para probarlo.")
    application.run_polling()
