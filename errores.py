import nest_asyncio
import json
import os
import asyncio
import re
import time
from datetime import datetime, timedelta
import openai
from telegram import (Update, KeyboardButton, ReplyKeyboardMarkup)
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

# Diccionario para almacenar avisos pendientes de ubicación
avisos_pendientes = {}  # Clave: user_id, Valor: (descripción, ubicación)
avisos_gestionados = []  # Lista de avisos ya aprobados o atendidos
avisos_enviados = {}  # Para evitar spam de avisos por usuario
usuarios_verificados = {} # almacenar datos de usuarios verificados
last_help_request = {} # almacenar ultima vez que usuario uso comando /ayuda

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

async def iniciar_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "avisos_pendientes" not in context.bot_data:
        context.bot_data["avisos_pendientes"] = []
    if "avisos_gestionados" not in context.bot_data:
        context.bot_data["avisos_gestionados"] = []

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
                "⚠️ *Debes verificar tus datos antes de enviar un aviso.*\nUsa /verificar.",
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
        
        print(f"✅ Ubicación guardada para el aviso: {aviso_encontrado}")  # Depuración
        print("―――――――――――――――――――――――――――――――――――――")

        # Pedir una foto opcional
        await update.message.reply_text(
            "📷📹 *Si es posible, envía una foto o un video del incidente.*\n"
            "Es para poder verificar que el Aviso sea Correcto",
            parse_mode="Markdown"
        )

    except Exception as e:
        print(f"❌ Error en recibir_ubicacion: {e}")
        await update.message.reply_text("❌ Ha ocurrido un error al procesar la ubicación.")

async def recibir_contenido(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe una foto o un video del usuario y lo asocia al aviso pendiente, luego lo envía al grupo."""
    try:
        user_id = update.message.from_user.id

        # Verificar si el mensaje contiene una foto o un video
        file_id = None
        file_type = None

        if update.message.photo:
            file_id = update.message.photo[-1].file_id  # Última imagen = mejor calidad
            file_type = "foto"
        elif update.message.video:
            file_id = update.message.video.file_id
            file_type = "video"
        else:
            await update.message.reply_text("⚠️ No se ha recibido una foto o video válido.")
            return

        print(f"📷📹 Archivo recibido de {user_id}, tipo: {file_type}, file_id: {file_id}")  # Depuración

        if "avisos_pendientes" not in context.bot_data:
            context.bot_data["avisos_pendientes"] = []

        # Buscar el aviso pendiente del usuario
        aviso_encontrado = None
        for aviso in context.bot_data["avisos_pendientes"]:
            if aviso["user_id"] == user_id and aviso.get("archivo") is None:
                aviso["archivo"] = file_id
                aviso["tipo_archivo"] = file_type
                aviso_encontrado = aviso
                break

        if not aviso_encontrado:
            await update.message.reply_text("⚠️ No tienes un aviso pendiente que requiera una foto o video.")
            return

        print(f"✅ {file_type.capitalize()} guardado en el aviso: {aviso_encontrado}")  
        print("―――――――――――――――――――――――――――――――――――――")


        # Obtener los datos del usuario
        datos_usuario = context.user_data.get(user_id, {})
        nombre = datos_usuario.get("nombre", "Desconocido")
        telefono = datos_usuario.get("telefono", "No registrado")

        # Obtener los datos del aviso
        user_aviso = aviso_encontrado["descripcion"]
        latitude, longitude = aviso_encontrado["ubicacion"]

        mensaje_grupo = (
            f"🚨 *NUEVO INCIDENTE REPORTADO*\n\n"
            f"📌 *Descripción:* {user_aviso}\n"
            f"📅 *Fecha y Hora:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"📍 *Ubicación:* [{latitude}, {longitude}](https://www.google.com/maps?q={latitude},{longitude})\n"
            f"👤 *Reportado por:* {nombre}\n"
            f"🔔 ¡Atención a este incidente!"
        )

        # Enviar el archivo al grupo de Telegram
        if file_type == "foto":
            await context.bot.send_photo(
                chat_id=TELEGRAM_GROUP_ID,
                photo=file_id,
                caption=mensaje_grupo,
                parse_mode="Markdown"
            )
        elif file_type == "video":
            await context.bot.send_video(
                chat_id=TELEGRAM_GROUP_ID,
                video=file_id,
                caption=mensaje_grupo,
                parse_mode="Markdown"
            )

        await update.message.reply_text(f"✅ *Aviso registrado y enviado con {file_type}.*", parse_mode="Markdown")
        context.user_data[user_id]["ultimo_aviso"] = time.time()

    except Exception as e:
        print(f"❌ Error en recibir_contenido: {e}")
        await update.message.reply_text("❌ Ha ocurrido un error al procesar el archivo.")

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

def analizar_reporte(mensaje):
    response = openai.ChatCompletion.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "Eres un asistente que clasifica reportes de incidencias en una ciudad."},
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
        # Reemplazamos 'true' y 'false' por True y False para hacer un JSON válido en Python
        result = result.replace("true", "True").replace("false", "False")
        
        try:
            data = json.loads(result)  # Convertir JSON a diccionario
            return data  # Devuelve el diccionario con el reporte clasificado
        except json.JSONDecodeError as e:
            print(f"Error al procesar JSON: {e}")
            return None
    
    return None

def analizar_direccion(mensaje):
    response = openai.ChatCompletion.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "Eres un asistente que detecta direcciones completas en los mensajes."},
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

    # 📌 Extraer los datos de la respuesta
    result = response.get("choices", [{}])[0].get("message", {}).get("function_call", {}).get("arguments", "{}")
    
    if result:
        try:
            data = json.loads(result)  # Convertir JSON a diccionario
            direccion = data.get("direccion")  # Obtener la dirección extraída
            if direccion and validar_direccion(direccion):  # Validar la dirección
                return direccion
            else:
                return "⚠️ La dirección proporcionada parece incorrecta. Por favor, verifica y corrige la dirección."
        except json.JSONDecodeError as e:
            print(f"Error al procesar JSON: {e}")
            return None
    
    return None

def validar_direccion(direccion):
    # Expresión regular que acepta una variedad de direcciones
    patron = re.compile(r"([A-Za-z0-9áéíóúÁÉÍÓÚñÑ\s,]+(?:[\d\s,]+)?)\s*(\d{5})?$")
    if patron.match(direccion):
        return True
    else:
        return False

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
            "⚠️ Por favor, proporciona un mensaje después de /ayuda\n\n"
            "Aquí te dejamos algunos ejemplos para que sepas cómo enviarlo correctamente:\n\n"
            "1️⃣ **Emergencia** (ejemplo de accidente):\n"
            "`/ayuda accidente de coche en la M45 salida 23`\n"
            "Este tipo de mensaje es para situaciones urgentes donde necesitas asistencia inmediata.\n\n"
            "2️⃣ **Reporte general** (ejemplo de aviso de incidente):\n"
            "`/ayuda hay un bache en la calle Mayor 12, Madrid`\n"
            "Utiliza este tipo de mensaje para reportar problemas que no son emergencias, como baches, apagones, etc.\n\n"
            "3️⃣ **Petición de ayuda** (ejemplo de solicitud de recursos):\n"
            "`/ayuda necesito asistencia médica en Avenida de la Paz 10, Madrid, 28010`\n"
            "Usa este mensaje cuando necesites ayuda con recursos específicos, como asistencia médica o bomberos.\n\n"
            "🔍 **Consejos importantes**:\n"
            "- Asegúrate de incluir una descripción clara de lo sucedido.\n"
            "- Si es relevante, proporciona una dirección completa o una ubicación (por ejemplo, Calle del Sol 3, Madrid, 28001).\n"
            "- Si es una emergencia, usa palabras como 'accidente', 'fuego', 'herido', etc.\n\n"
            "📍 **Ejemplo completo de reporte con dirección**:\n"
            "`/ayuda accidente de tráfico en la Calle Mayor 3, Madrid, 28001, con varios coches implicados`",
            parse_mode="Markdown"
        )
        return

    # Verificar si el usuario ha usado el comando recientemente
    current_time = datetime.now()
    if user_id in last_help_request:
        last_request_time = last_help_request[user_id]
        time_difference = current_time - last_request_time

        # Si ha pasado menos de 1 minuto desde la última solicitud, no permitir enviar el comando nuevamente
        if time_difference < timedelta(minutes=1):
            await update.message.reply_text("⚠️ Por favor, espera un minuto antes de enviar otro reporte.")
            return

    # Actualizar el tiempo de la última solicitud del usuario
    last_help_request[user_id] = current_time

    print(f"\n🔹 Nuevo mensaje recibido de {user_id}: {user_message}")

    # 📌 Intentamos clasificarlo como reporte general
    reporte = analizar_reporte(user_message)  # También sin 'await'
    if reporte:
        tipo_reporte = reporte["tipo_reporte"]
        categoria = reporte["categoria"]
        subcategoria = reporte["subcategoria"]

        print(f"✅ Reporte clasificado: Tipo: {tipo_reporte}, Categoría: {categoria}, Subcategoría: {subcategoria}")

        respuesta = (
            f"📋 Reporte clasificado:\n"
            f"👤 Usuario: `{user_id}`\n"
            f"📌 Tipo: {tipo_reporte.capitalize()}\n"
            f"📂 Categoría: {categoria}\n"
            f"🔖 Subcategoría: {subcategoria}"
        )

        # 📌 Intentamos extraer y validar la dirección
        direccion = analizar_direccion(user_message)
        if direccion:
            respuesta += f"\n🗺️ Dirección: {direccion}"

        await update.message.reply_text(respuesta, parse_mode="Markdown")

        # Enviar el reporte al grupo de Telegram
        await context.bot.send_message(
            chat_id=TELEGRAM_GROUP_ID,
            text=respuesta
        )

        return

    # 📌 Si no es ni emergencia ni reporte válido
    print("⚠️ No se pudo clasificar el mensaje.")
    await update.message.reply_text("⚠️ No he podido entender tu solicitud.")

#----------------------------------------------------------------------------

if __name__ == '__main__':
    application = ApplicationBuilder().token(telegram_bot_key).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("verificar", verificar))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_datos))
    application.add_handler(CommandHandler("aviso", aviso))
    application.add_handler(MessageHandler(filters.LOCATION, recibir_ubicacion))
    application.add_handler(CommandHandler("contacto", contacto))
    application.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO, recibir_contenido))
    application.add_handler(CommandHandler("help", como_usar))
    application.add_handler(CommandHandler("comandos", comandos))
    application.add_handler(CommandHandler("pendientes", pendientes))
    application.add_handler(CommandHandler("modificar", modificar))
    application.add_handler(CommandHandler("datos", datos))
    application.add_handler(CommandHandler("ayuda", ayuda))

    print("✅ El bot está en ejecución. Envía un mensaje en Telegram para probarlo.")
    application.run_polling()