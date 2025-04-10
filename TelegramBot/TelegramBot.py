# -----------------------IMPORT LIBRERIAS---------------------------

from diccionarios import AVISOS, PETICIONES
from claves import OPENAI_API_KEY, CURAIME_BOT_KEY

import nest_asyncio
import asyncio
import json
import os
import time
from datetime import datetime
import re
import openai
from telegram import (Update, ReplyKeyboardMarkup, KeyboardButton)
from telegram.ext import (ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes, ConversationHandler)

#----------------------------------------------------------------------------

# Permite aplicar una solución para manejar múltiples bucles de eventos asyncio 
# dentro de un entorno donde ya hay un bucle de eventos en ejecución.
nest_asyncio.apply()

# Claves API desde variables de entorno
TELEGRAM_GROUP_ID = "-1002545875124"
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
os.environ["CURAIME_BOT_KEY"] = CURAIME_BOT_KEY

# Configurar Modelo OpenAI
MODEL = "gpt-4o-mini"
openai.api_key = OPENAI_API_KEY

# Etapas de la conversación
UBICACION = 1

# Mensaje de contexto para OpenAI
system_content_prompt = (
    "Eres un asistente del Ayuntamiento de Madrid encargado de clasificar reportes ciudadanos. "
    "Los reportes pueden ser de tipo 'aviso' (problemas o incidencias) o 'petición' (solicitudes de mejora). "
    "Debes analizar un mensaje del usuario e identificar su tipo ('aviso' o 'petición'), una categoría y una subcategoría, "
    "siguiendo estrictamente los valores que aparecen en los diccionarios oficiales del Ayuntamiento.\n\n"

    "Aquí tienes el listado completo de categorías y subcategorías válidas:\n\n"

    f"Categorías y subcategorías para AVISOS:\n"
    f"{json.dumps(AVISOS, indent=2, ensure_ascii=False)}\n\n"

    f"Categorías y subcategorías para PETICIONES:\n"
    f"{json.dumps(PETICIONES, indent=2, ensure_ascii=False)}\n\n"

    "🔍 IMPORTANTE:\n"
    "- Aunque el mensaje del usuario no coincida exactamente con las palabras del diccionario, intenta identificar sinónimos o frases similares.\n"
    "- Si el mensaje describe una situación que encaja con alguna subcategoría, devuélvela aunque esté redactada de forma diferente.\n"
    "- Si no puedes identificar claramente ninguna categoría o subcategoría válida, no devuelvas nada.\n\n"

    "Devuelve únicamente subcategorías exactas del diccionario. No inventes nuevas.\n"
)

messages_to_send = [{"role": "system", "content": system_content_prompt}]

#-----------------------------FUNCIONES DEL BOT-----------------------------------------------

# start(update, context): Muestra el mensaje de bienvenida del bot con una lista 
# de los comandos principales disponibles para el usuario, explicando qué hace cada uno. 
# Si ocurre un error, muestra un mensaje de error.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra los comandos disponibles de manera organizada."""
    try:
        start_message = ( 
            "⚠️ *Bienvenido al Bot de Avisos de Emergencia.*\n\n"
            "🔹 Usa los siguientes comandos principales:\n\n"
            "✅ /verificar - Registrar tus datos personales para reportar avisos.\n"
            "✅ /ayuda - Reporta una emergencia.\n"
            "✅ /asistente - Informa de lo que se debería de hacer en X caso.\n"
            "✅ /contacto - Ver los números de emergencia en España.\n"
            "✅ /datos - Ver los datos que has registrado.\n\n"
            "🔸 Para ver todos los comandos disponibles, usa: /comandos"
        )

        await update.message.reply_text(start_message, parse_mode="Markdown")
    except Exception as e:
        print(f"Error en /start: {e}")
        await update.message.reply_text("❌ Ha ocurrido un error al mostrar el menú.")

# como_usar(update, context): Proporciona una explicación detallada sobre cómo utilizar 
# el bot, paso a paso. Incluye instrucciones sobre cómo verificar datos, reportar emergencias, 
# compartir ubicación, enviar fotos/videos, y consultar información relevante como números de emergencia.
async def como_usar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Explica detalladamente cómo usar el bot paso a paso, incluyendo la verificación obligatoria y el envío de fotos/videos."""
    help_text = (
            "⚠️ *Bienvenido al Bot de Avisos de Emergencia* ⚠️\n\n"
            "Este bot está diseñado para proporcionar información en tiempo real sobre emergencias "
            "y alertas importantes en tu zona. Puedes reportar incidentes, recibir avisos de seguridad "
            "y consultar números de emergencia.\n\n"
            
            "🔹 *¿Cómo funciona?*\n"
            "1️⃣ Usa `/verificar` para registrar tus datos antes de enviar un aviso.\n"
            "2️⃣ Usa `/ayuda [descripción]` para reportar una emergencia.\n"
            "3️⃣ Consulta los números de emergencia con `/contacto`.\n"
            "4️⃣ Usa `/datos` para ver los datos que has registrado.\n"
            "5️⃣ Usa `/modificar` para modificar los datos que has registrado.\n"
            "6️⃣ Usa `/asistente [incidente]` para obtener recomendaciones sobre qué hacer en una situación de emergencia.\n"
            "7️⃣ Usa `/informacion` si tienes dudas.\n"
        )
    
    await update.message.reply_text(help_text, parse_mode="Markdown")

# comandos(update, context): Muestra los comandos disponibles para el usuario, 
# listando todas las acciones que el bot puede realizar.
async def comandos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra los comandos disponibles para el usuario."""
    command_text = (
        "📜 *Comandos Disponibles:*\n\n"
        "✅ /start - Muestra el menú de opciones.\n"
        "✅ /verificar - Registra tus datos personales.\n"
        "✅ /ayuda - Reporta una emergencia.\n"
        "✅ /asistente - Informa de lo que se debería de hacer en X caso.\n"
        "✅ /contacto - Muestra los números de emergencia.\n"
        "✅ /datos - Ver los datos que has registrado.\n"
        "✅ /modificar - Modificar los datos que has registrado.\n"
        "✅ /comandos - Muestra todos los comandos disponibles.\n"
        "✅ /informacion - Explicación sobre cómo usar el bot.\n\n"

        "📧 *Soporte técnico:* contacto@empresa.com\n"
        "📞 *Teléfono de atención:* +34 600 123 456"
    )

    await update.message.reply_text(command_text, parse_mode="Markdown")

# verificar(update, context) Solicita los datos personales del usuario 
# (nombre, correo y teléfono) para registrar y verificar su identidad antes 
# de que pueda hacer reportes.
async def verificar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Solicita los datos personales antes de permitir enviar un aviso."""
    user_id = update.message.from_user.id

    # Verifica si el usuario ya envió sus datos
    if user_id in context.user_data and "datos_verificados" in context.user_data[user_id]:
        await update.message.reply_text("✅ Ya has verificado tus datos. Puedes enviar avisos.")
        return

    await update.message.reply_text(
        "📝 *Verificación de identidad requerida.*\n\n"
        "Por favor, envía los siguientes datos en un solo mensaje:\n"
        "1️⃣ Nombre completo\n"
        "2️⃣ Correo electrónico\n"
        "3️⃣ Número de teléfono\n\n"
        "Ejemplo:\n"
        "`Juan Pérez Gómez, juan.perez@email.com, 698767665`",
        parse_mode="Markdown"
    )

    # Marca al usuario como pendiente de verificación
    context.user_data[user_id] = {"verificacion_pendiente": True}

# recibir_datos(update, context): Recibe los datos personales enviados por 
# el usuario, valida su formato (nombre, correo y teléfono) y los guarda si 
# son correctos. Informa al usuario si hay errores de formato.
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

    nombre, correo, telefono = map(str.strip, partes)

    # Validar datos básicos
    if not re.match(r"^[A-Za-zÁÉÍÓÚáéíóúÑñ ]+$", nombre):
        await update.message.reply_text("❌ Nombre inválido. Debe contener solo letras y espacios.")
        return
    if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", correo):
        await update.message.reply_text("❌ Correo electrónico inválido. Usa un formato válido como `correo@dominio.com`.")
        return
    if not re.match(r"^\+?\d{9,15}$", telefono):
        await update.message.reply_text("❌ Teléfono inválido. Usa un formato válido como +34 600123456.")
        return

    # Guardar datos en el usuario
    context.user_data[user_id] = {
        "nombre": nombre,
        "correo": correo,
        "telefono": telefono,
        "datos_verificados": True
    }

    print("―――――――――――――――――――――――――――――――――――――")
    print("✅ Datos del usuario guardados:")
    print(f"👤 Nombre: {nombre}")
    print(f"📧 Correo: {correo}")
    print(f"📞 Teléfono: {telefono}")
    print("―――――――――――――――――――――――――――――――――――――")

    await update.message.reply_text("✅ Datos verificados. Ahora puedes enviar reportes con /ayuda.")

# modificar(update, context): Permite al usuario modificar los datos verificados 
# en caso de haber cometido un error. Inicia de nuevo el proceso de verificación.
async def modificar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Permite al usuario modificar sus datos si se ha equivocado."""
    user_id = update.message.from_user.id

    # Verifica si el usuario ya ha verificado sus datos
    if user_id not in context.user_data or "datos_verificados" not in context.user_data[user_id]:
        await update.message.reply_text("❌ No tienes datos verificados. Usa /verificar primero.")
        return

    # Elimina los datos anteriores para permitir la reingresión
    del context.user_data[user_id]["nombre"]
    del context.user_data[user_id]["correo"]
    del context.user_data[user_id]["telefono"]
    del context.user_data[user_id]["datos_verificados"]

    # Inicia el proceso de verificación de nuevo
    await update.message.reply_text(
        "📝 Modificación de datos\n\n"
        "Por favor, ingresa de nuevo los siguientes datos en un solo mensaje:\n"
        "1️⃣ Nombre completo\n"
        "2️⃣ Correo electrónico\n"
        "3️⃣ Número de teléfono\n\n"
        "Ejemplo:\n"
        "`Juan Pérez Gómez, juan.perez@email.com, 698767665`",
        parse_mode="Markdown"
    )

    # Marca al usuario como pendiente de nueva verificación
    context.user_data[user_id] = {"verificacion_pendiente": True}

# datos(update, context): Muestra los datos verificados del usuario si ya los 
# ha registrado. Si no están verificados, solicita que el usuario use el comando /verificar.
async def datos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra los datos verificados del usuario."""
    user_id = update.message.from_user.id
    
    # Verifica si el usuario tiene datos verificados
    if user_id not in context.user_data or "datos_verificados" not in context.user_data[user_id]:
        await update.message.reply_text("❌ Aún no has verificado tus datos. Usa /verificar para ingresarlos.")
        return
    
    # Recupera los datos del usuario
    nombre = context.user_data[user_id].get("nombre", "No disponible")
    correo = context.user_data[user_id].get("correo", "No disponible")
    telefono = context.user_data[user_id].get("telefono", "No disponible")
    
    # Envía los datos al usuario
    await update.message.reply_text(
        f"📊 Tus datos verificados son:\n\n"
        f"1️⃣ Nombre completo: {nombre}\n"
        f"2️⃣ Correo electrónico: {correo}\n"
        f"3️⃣ Número de teléfono: {telefono}"
    )

# contacto(update, context): Muestra los números de emergencia más importantes en España 
# (como el 112 para emergencias generales, 091 para policía, etc.).
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

# Función para analizar el reporte
def analizar_reporte(mensaje):
    # Llamada a la API de OpenAI para analizar el mensaje
    response = openai.ChatCompletion.create(
        model=MODEL,
        messages=[ 
            {"role": "system", "content": system_content_prompt},
            {"role": "user", "content": f"Clasifica este reporte: {mensaje}"}
        ],
        functions=[ 
            {
                "name": "clasificar_reporte",
                "description": "Clasifica un reporte de aviso o petición en su categoría y subcategoría correspondiente",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "tipo_reporte": {"type": "string", "enum": ["aviso", "petición"]},
                        "categoria": {"type": "string"},
                        "subcategoria": {"type": "string"}
                    },
                    "required": ["tipo_reporte", "categoria", "subcategoria"]
                }
            }
        ],
        function_call="auto"
    )

    # 📌 Extraer los datos de la respuesta
    result = response.get("choices", [{}])[0].get("message", {}).get("function_call", {}).get("arguments", "{}")

    if result:
        result = result.replace("true", "True").replace("false", "False")
        try:
            # Convertir la respuesta a formato JSON
            data = json.loads(result)

            tipo_reporte = data.get("tipo_reporte")
            categoria = data.get("categoria")
            subcategoria = data.get("subcategoria")

            # Verificar si la categoría y subcategoría están en los diccionarios
            if tipo_reporte == "aviso":
                if categoria in AVISOS and subcategoria in AVISOS[categoria]:
                    return data
                else:
                    for cat, subcats in AVISOS.items():
                        if any(subcat.lower() in mensaje.lower() for subcat in subcats):
                            return {"tipo_reporte": "aviso", "categoria": cat, "subcategoria": subcats[0]}

            elif tipo_reporte == "petición":
                if categoria in PETICIONES and subcategoria in PETICIONES[categoria]:
                    return data
                else:
                    for cat, subcats in PETICIONES.items():
                        if any(subcat.lower() in mensaje.lower() for subcat in subcats):
                            return {"tipo_reporte": "petición", "categoria": cat, "subcategoria": subcats[0]}

            return None

        except json.JSONDecodeError as e:
            return None

    return None

# Función para manejar el comando /ayuda
async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.replace("/ayuda", "").strip()
    user_id = update.message.from_user.id

    # Verificar si el usuario está verificado
    if user_id not in context.user_data or "datos_verificados" not in context.user_data[user_id]:
        await update.message.reply_text("⚠️ Necesitas verificar tus datos antes de enviar un reporte.\n"
        "Usa el comando /verificar para iniciar el proceso.")
        return

    # Verificar si el usuario está enviando el comando sin mensaje
    if not user_message:
        await update.message.reply_text(
            "⚠️ Por favor, proporciona un mensaje después de /ayuda. Ejemplos de cómo hacerlo:\n\n"
            "1️⃣ **Aviso** (incidentes como problemas en la vía pública):\n"
            "`/ayuda Farola apagada en la Calle Mayor 12, Madrid`\n"
            "Para reportar problemas como baches, apagones, árboles caídos, etc.\n\n"
            "2️⃣ **Petición** (solicitudes de mejora o nuevas instalaciones):\n"
            "`/ayuda Solicito nueva instalación de área infantil en la Calle del Sol 3, Madrid`\n"
            "Para pedir cosas como instalación de señales, fuentes, mejoras de accesibilidad, etc.\n\n"
            "🔍 **Recuerda el formato correcto de dirección:**\n"
            "- Incluye **tipo de vía**, nombre de la calle, número (si aplica), ciudad y **código postal**.\n"
            "   Ejemplos válidos:\n"
            "   • Calle Alcalá 23, Madrid, 28041\n"
            "   • Avenida de América 12, Madrid, 28028\n"
            "   • Plaza Mayor 1, Madrid\n"
            "   • Carretera M-30 salida 5, Madrid, 28002\n\n"
            "❗ **Evita direcciones vagas** como 'en mi casa', 'por aquí', 'cerca del parque'. Necesitamos direcciones concretas para procesar tu solicitud correctamente.",
            parse_mode="Markdown"
        )
        return

    # Verificar si el mensaje es un reporte válido
    reporte = analizar_reporte(user_message)
    if not reporte:
        await update.message.reply_text("⚠️ No he podido entender tu solicitud.")
        return

    tipo_reporte = reporte["tipo_reporte"]
    categoria = reporte["categoria"]
    subcategoria = reporte["subcategoria"]

    # Guardar la información en context.user_data
    context.user_data["tipo_reporte"] = tipo_reporte
    context.user_data["categoria"] = categoria
    context.user_data["subcategoria"] = subcategoria
    context.user_data["user_message"] = user_message  # Guardar el mensaje también

    # Solicitar la ubicación
    await update.message.reply_text(
        "Por favor, comparte tu ubicación en tiempo real para continuar con el reporte.",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("📍 Compartir ubicación", request_location=True)]],
            one_time_keyboard=True
        )
    )
    return UBICACION

# Función para manejar la ubicación recibida
async def recibir_ubicacion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    # Acceder a los datos almacenados en context.user_data
    tipo_reporte = context.user_data.get("tipo_reporte")
    categoria = context.user_data.get("categoria")
    subcategoria = context.user_data.get("subcategoria")
    user_message = context.user_data.get("user_message")  # Obtener el mensaje del usuario

    # Obtener la ubicación
    location = update.message.location
    if location:
        latitude = location.latitude
        longitude = location.longitude
        cordenadas_ubicacion = f"Lat: {latitude}, Long: {longitude}"

        respuesta = (
            f"📋 Reporte clasificado:\n"
            f"👤 Usuario: `{user_id}`\n"
            f"📌 Tipo: {tipo_reporte.capitalize()}\n"
            f"📂 Categoría: {categoria}\n"
            f"🔖 Subcategoría: {subcategoria}\n"
            f"🗺️ Dirección: {cordenadas_ubicacion}\n"
            f"💬 Descripción: {user_message}"
        )

        await update.message.reply_text(respuesta, parse_mode="Markdown")
        await context.bot.send_message(
            chat_id=TELEGRAM_GROUP_ID,
            text=respuesta
        )
    return ConversationHandler.END

#-----------------------------MANEJADORES DEL BOT-----------------------------------------------

# Este código configura y ejecuta el bot de Telegram, añadiendo manejadores para los comandos y mensajes, 
# y luego inicia el bot en modo "polling" para que empiece a recibir y responder a las interacciones de los usuarios.

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("ayuda", ayuda)],
    states={
        UBICACION: [MessageHandler(filters.LOCATION, recibir_ubicacion)]
    },
    fallbacks=[]
)

if __name__ == '__main__':
    application = ApplicationBuilder().token(CURAIME_BOT_KEY).build()

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("verificar", verificar))
    application.add_handler(CommandHandler("contacto", contacto))
    application.add_handler(CommandHandler("informacion", como_usar))
    application.add_handler(CommandHandler("comandos", comandos))
    application.add_handler(CommandHandler("modificar", modificar))
    application.add_handler(CommandHandler("datos", datos))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_datos))

    print("✅ El bot está en ejecución.")
    application.run_polling()