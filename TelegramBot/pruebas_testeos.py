import nest_asyncio
import json
import os
import asyncio
import re
import time
from datetime import datetime
import openai
from telegram import (Update)
from telegram.ext import (ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes)
#----------------------------------------------------------------------------

nest_asyncio.apply()

# Claves API desde variables de entorno
TELEGRAM_GROUP_ID = "-1002545875124"
openai_api_key = os.getenv("OPENAI_API_KEY")
telegram_bot_key = os.getenv("CURAIME_BOT_KEY")

# Configurar OpenAI
MODEL = "gpt-4o-mini"
openai.api_key = openai_api_key

# Mensaje de contexto para OpenAI
system_content_prompt = (
    "Eres un bot de Telegram especializado en avisos de emergencia. "
    "Proporcionas información clara y rápida sobre incidentes como incendios, accidentes y desastres naturales. "
    "Siempre respondes con un tono profesional y directo, sin causar pánico."
)

messages_to_send = [{"role": "system", "content": system_content_prompt}]

# DICCIONARIO DE AVISOS Y PETICIONES (AYUNTAMIENTO DE MADRID)
AVISOS = {
    "ALUMBRADO PÚBLICO": [
        "Calle apagada", 
        "Calle apagada v2", 
        "Calle apagada v3", 
        "Calle apagada v4", 
        "Farola apagada", 
        "Otras averías de alumbrado"
    ],
    "Aparcamiento regulado": [
        "Aparcamiento regulado"
    ],
    "ÁRBOLES Y PARQUES": [
        "Árbol en mal estado", 
        "Caminos no pavimentados", 
        "Incidencias de riego", 
        "Incidencias en alcorque o hueco", 
        "Plagas", 
        "Poda de árbol", 
        "Quitar maleza", 
        "Sustitución de árbol"
    ],
    "AREAS INFANTILES, ÁREAS DE MAYORES Y CIRCUITOS": [
        "Área de mayores y circuitos", 
        "Área infantil"
    ],
    "CALZADAS Y ACERAS": [
        "Alcantarillado", 
        "Desperfecto en acera", 
        "Desperfecto en calzada", 
        "Hidrantes de bomberos", 
        "Otras incidencias en calzadas y aceras", 
        "Tapas de registro"
    ],
    "CUBOS Y CONTENEDORES": [
        "Cambio de tamaño de cubo", 
        "Cambio de ubicación de cubo o contenedor", 
        "Cubo o contenedor abandonado", 
        "Cubo o contenedor en mal estado", 
        "Horquillas delimitadoras", 
        "Nuevo cubo o contenedor", 
        "Vaciado de aceite", 
        "Vaciado de cubo o contenedor"
    ],
    "FUENTES": [
        "Incidencias en fuentes de beber", 
        "Incidencias en fuentes ornamentales"
    ],
    "LIMPIEZA Y PINTADAS": [
        "Limpieza en solares municipales", 
        "Limpieza en vías públicas", 
        "Limpieza mobiliario urbano o áreas infantiles", 
        "Pintadas y grafitis", 
        "Pintadas y grafitis v2", 
        "Pintadas y grafitis v3"
    ],
    "MOBILIARIO URBANO": [
        "Banco", 
        "Bolardo u horquilla", 
        "Otros", 
        "Vallas"
    ],
    "PAPELERAS": [
        "Falta de bolsas para excrementos caninos", 
        "Mal estado de papelera", 
        "Nueva instalación de papelera", 
        "Vaciado de papelera"
    ],
    "PLAGAS": [
        "Ratas y cucarachas"
    ],
    "RETIRADAS DE ELEMENTOS": [
        "Animales muertos", 
        "Contenedor de ropa no autorizado", 
        "Muebles abandonados en vía pública", 
        "Muebles particulares", 
        "Recogida de saco o contenedor de escombros"
    ],
    "RIO MANZANARES": [
        "Río Manzanares"
    ],
    "SEÑALES Y SEMÁFOROS": [
        "Incidencia en avisador acústico de semáforo", 
        "Incidencia en pulsador", 
        "Incidencia en señal", 
        "Semáforo apagado"
    ],
    "VEHICULOS ABANDONADOS. RETIRADA DE VEHICULO": [
        "Vehículos abandonados. Retirada de vehículo"
    ]
}

PETICIONES = {
    "ALUMBRADO PÚBLICO": [
        "Peticiones alumbrado"
    ],
    "AREAS INFANTILES, ÁREAS DE MAYORES Y CIRCUITOS": [
        "Nueva Instalación"
    ],
    "CALZADAS Y ACERAS": [
        "Mejora de accesibilidad"
    ],
    "FUENTES": [
        "Nueva Instalación de fuente de beber"
    ],
    "MOBILIARIO URBANO": [
        "Nueva Instalación"
    ],
    "SEÑALES Y SEMÁFOROS": [
        "Nueva Señal"
    ]
}

#----------------------------------------------------------------------------

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
        "3️⃣ Comparte tu ubicación cuando se te solicite.\n"
        "4️⃣ Envía una *foto o video* del incidente después de compartir tu ubicación.\n"
        "5️⃣ Usa `/pendientes` para ver los avisos en espera y los que han sido gestionados.\n"
        "6️⃣ Consulta los números de emergencia con `/contacto`.\n"
        "7️⃣ Usa `/datos` para ver los datos que has registrado.\n"
        "8️⃣ Usa `/modificar` para modificar los datos que has registrado.\n"
        "9️⃣ Usa `/asistente [incidente]` para obtener recomendaciones sobre qué hacer en una situación de emergencia.\n"
        "🔟 Usa `/help` si tienes dudas.\n\n"
    )
    
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def comandos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra los comandos disponibles para el usuario."""
    command_text = (
        "📜 *Comandos Disponibles:*\n\n"
        "✅ /start - Muestra el menú de opciones.\n"
        "✅ /verificar - Registra tus datos personales.\n"
        "✅ /ayuda - Reporta una emergencia.\n"
        "✅ /pendientes - Lista de avisos pendientes y aprobados.\n"
        "✅ /asistente - Informa de lo que se debería de hacer en X caso.\n"
        "✅ /contacto - Muestra los números de emergencia.\n"
        "✅ /datos - Ver los datos que has registrado.\n"
        "✅ /modificar - Modificar los datos que has registrado.\n"
        "✅ /comandos - Muestra todos los comandos disponibles.\n"
        "✅ /help - Explicación sobre cómo usar el bot.\n\n"

        "📧 *Soporte técnico:* contacto@empresa.com\n"
        "📞 *Teléfono de atención:* +34 600 123 456"
    )

    await update.message.reply_text(command_text, parse_mode="Markdown")

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

def analizar_reporte(mensaje):
    # Llamada a la API de OpenAI para analizar el mensaje
    response = openai.ChatCompletion.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "Eres un asistente que clasifica reportes de incidencias en una ciudad. Puedes clasificar en base a categorías y subcategorías existentes. Si el mensaje no corresponde a ninguna categoría válida, no devuelvas nada."},
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
    
    print("╔―――――――――――――――――――――――――――――――――――――")
    print("╠――――Respuesta de la IA: {result}")
    
    if result:
        result = result.replace("true", "True").replace("false", "False")
        try:
            # Convertir la respuesta a formato JSON
            data = json.loads(result)
            print("╠――――Datos procesados: {data}")

            tipo_reporte = data.get("tipo_reporte")
            categoria = data.get("categoria")
            subcategoria = data.get("subcategoria")

            # Verificar si la categoría y subcategoría están en los diccionarios
            if tipo_reporte == "aviso":
                print("╠――――Tipo de reporte: {tipo_reporte}, Categoría: {categoria}, Subcategoría: {subcategoria}")
                if categoria in AVISOS and subcategoria in AVISOS[categoria]:
                    print("Reporte clasificado correctamente como aviso.")
                    return data
                else:
                    # Intentar asignar la categoría y subcategoría correcta
                    print(f"╠――――Categoría o subcategoría no válida: {categoria} / {subcategoria}")
                    for cat, subcats in AVISOS.items():
                        if any(subcat.lower() in mensaje.lower() for subcat in subcats):
                            print(f"Asignando categoría: {cat} y subcategoría: {subcats[0]}")
                            return {"tipo_reporte": "aviso", "categoria": cat, "subcategoria": subcats[0]}

            elif tipo_reporte == "petición":
                print(f"╠――――Tipo de reporte: {tipo_reporte}, Categoría: {categoria}, Subcategoría: {subcategoria}")
                if categoria in PETICIONES and subcategoria in PETICIONES[categoria]:
                    print("╠――――Reporte clasificado correctamente como petición.")
                    return data
                else:
                    # Intentar asignar la categoría y subcategoría correcta para las peticiones
                    print(f"╠――――Categoría o subcategoría no válida para petición: {categoria} / {subcategoria}")
                    for cat, subcats in PETICIONES.items():
                        if any(subcat.lower() in mensaje.lower() for subcat in subcats):
                            print("╠――――Asignando categoría: {cat} y subcategoría: {subcats[0]}")
                            print("╚―――――――――――――――――――――――――――――――――――――")
                            return {"tipo_reporte": "petición", "categoria": cat, "subcategoria": subcats[0]}

            print("⚠️ Categoría o subcategoría inválida. Rechazando el resultado.")
            return None

        except json.JSONDecodeError as e:
            print(f"Error al procesar JSON: {e}")
            return None

    print("No se recibió una respuesta válida del modelo.")
    return None

def analizar_direccion(mensaje):
    response = openai.ChatCompletion.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "Eres un asistente que detecta direcciones completas en los mensajes. Solo extrae direcciones reales (calle, avenida, carretera, etc.) con nombre y número o con código postal si es posible. Si no hay dirección clara, indícalo."},
            {"role": "user", "content": f"Extrae la dirección completa de este mensaje: {mensaje}"}
        ],
        functions=[
            {
                "name": "extraer_direccion",
                "description": "Detecta una dirección completa en el mensaje.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "direccion": {"type": "string"}
                    },
                    "required": ["direccion"]
                }
            }
        ],
        function_call="auto"
    )

    # Extraer resultado del JSON
    result = response.get("choices", [{}])[0].get("message", {}).get("function_call", {}).get("arguments", "{}")

    if result:
        try:
            data = json.loads(result)
            direccion = data.get("direccion")

            # Validar dirección
            if direccion and validar_direccion(direccion):
                return direccion
        except json.JSONDecodeError as e:
            print(f"Error al procesar dirección JSON: {e}")
    
    return None

def validar_direccion(direccion):
    """
    Valida direcciones asegurando que contengan una estructura coherente.
    Permite calles, avenidas, carreteras, etc., con número, ciudad y código postal.
    """
    patron = re.compile(
        r"^(Calle|Avenida|Plaza|Paseo|Carretera|Autopista|Camino|Ronda|Travesía|Vía|Urbanización)?\s?"
        r"[A-Za-z0-9áéíóúÁÉÍÓÚñÑ\s]+(\s?\d+)?(,\s?[A-Za-z\s]+)?(,\s?\d{5})?$",
        re.IGNORECASE
    )
    return bool(patron.match(direccion.strip()))

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

    # Verificar si el usuario ha enviado un mensaje recientemente (esperar 1 minuto entre mensajes)
    last_message_time = context.user_data.get(user_id, {}).get("last_message_time", 0)
    current_time = time.time()

    # Si no ha pasado 1 minuto desde el último mensaje
    if current_time - last_message_time < 60:
        remaining_time = 60 - (current_time - last_message_time)
        await update.message.reply_text(f"⚠️ Por favor, espera {int(remaining_time)} segundos antes de enviar otro reporte.")
        return

    # Actualizar el tiempo del último mensaje
    context.user_data[user_id] = context.user_data.get(user_id, {})
    context.user_data[user_id]["last_message_time"] = current_time

    # Verificar si el mensaje es un reporte válido
    reporte = analizar_reporte(user_message)
    if not reporte:
        print("⚠️ No se pudo clasificar el mensaje.")
        await update.message.reply_text("⚠️ No he podido entender tu solicitud.")
        return

    tipo_reporte = reporte["tipo_reporte"]
    categoria = reporte["categoria"]
    subcategoria = reporte["subcategoria"]

    # Validar contra los diccionarios de categorías
    if tipo_reporte == "aviso":
        if categoria not in AVISOS or subcategoria not in AVISOS[categoria]:
            print(f"⚠️ Reporte inválido: {reporte}")
            await update.message.reply_text("⚠️ No he podido entender tu solicitud.")
            return
    elif tipo_reporte == "petición":
        if categoria not in PETICIONES or subcategoria not in PETICIONES[categoria]:
            print(f"⚠️ Reporte inválido: {reporte}")
            await update.message.reply_text("⚠️ No he podido entender tu solicitud.")
            return
    else:
        print("⚠️ Tipo de reporte desconocido.")
        await update.message.reply_text("⚠️ No he podido entender tu solicitud.")
        return

    # Analizar la dirección
    direccion = analizar_direccion(user_message)
    if not direccion:
        print("⚠️ Dirección no válida. Abortando reporte.")
        await update.message.reply_text("⚠️ No he podido entender tu solicitud.")
        return

    respuesta = (
        f"📋 Reporte clasificado:\n"
        f"👤 Usuario: `{user_id}`\n"
        f"📌 Tipo: {tipo_reporte.capitalize()}\n"
        f"📂 Categoría: {categoria}\n"
        f"🔖 Subcategoría: {subcategoria}\n"
        f"🗺️ Dirección: {direccion}\n"
        f"💬 Descripción: {user_message}"
    )

    await update.message.reply_text(respuesta, parse_mode="Markdown")

    # Enviar el reporte al grupo de Telegram
    await context.bot.send_message(
        chat_id=TELEGRAM_GROUP_ID,
        text=respuesta
    )

#----------------------------------------------------------------------------

if __name__ == '__main__':
    application = ApplicationBuilder().token(telegram_bot_key).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("verificar", verificar))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_datos))
    application.add_handler(CommandHandler("contacto", contacto))
    application.add_handler(CommandHandler("help", como_usar))
    application.add_handler(CommandHandler("comandos", comandos))
    application.add_handler(CommandHandler("modificar", modificar))
    application.add_handler(CommandHandler("datos", datos))
    application.add_handler(CommandHandler("ayuda", ayuda))

    print("✅ El bot está en ejecución. Envía un mensaje en Telegram para probarlo.")
    application.run_polling()