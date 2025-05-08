# ESTO SON VARIABLES Y FUNCIONES QUE NO SE ESTAN USANDO ACTUALMENTE
# ESTÁN AQUI POR SI SE NECESITAN COGER IDEAS EN UN FUTURO

# --------------------------------------------------------------

# Diccionario para almacenar avisos pendientes de ubicación
avisos_pendientes = {}  # Clave: user_id, Valor: (descripción, ubicación)
avisos_gestionados = []  # Lista de avisos ya aprobados o atendidos
avisos_enviados = {}  # Para evitar spam de avisos por usuario
usuarios_verificados = {} # almacenar datos de usuarios verificados
last_help_request = {} # almacenar ultima vez que usuario uso comando /ayuda

# -----------------------FUNCIONES BOT---------------------------

# Inicializa dos listas en context.bot_data para almacenar los avisos pendientes y gestionados.
async def iniciar_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "avisos_pendientes" not in context.bot_data:
        context.bot_data["avisos_pendientes"] = []
    if "avisos_gestionados" not in context.bot_data:
        context.bot_data["avisos_gestionados"] = []

# Procesa un aviso enviado por el usuario. Verifica si el usuario está verificado y si está dentro del 
# tiempo de cooldown (2 minutos). Si todo es correcto, solicita la ubicación del usuario para completar el aviso.
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

# Recibe la ubicación enviada por el usuario y la asocia al aviso pendiente. Luego, solicita una foto o video como parte del aviso.
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

# Recibe una foto o video del usuario y lo asocia al aviso pendiente. Luego, envía los detalles del aviso 
# (incluyendo la ubicación, descripción, etc.) al grupo de Telegram, junto con el archivo multimedia.
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

# Muestra el estado actual de los avisos de emergencia en el bot, incluyendo tanto los avisos pendientes como los ya gestionados
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

# -----------------------FUNCIONES BOT---------------------------

# analizar_reporte(mensaje): Utiliza la API de OpenAI para analizar el mensaje y 
# clasificarlo en un tipo de reporte (aviso o petición) con su categoría y subcategoría 
# correspondiente. Si el mensaje no se clasifica correctamente, intenta asignar 
# una categoría y subcategoría adecuadas.
def analizar_reporte(mensaje):
    # Llamada a la API de OpenAI para analizar el mensaje
    response = openai.ChatCompletion.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_content_prompt},  # El prompt que te puse arriba
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
    print(f"╠――――Respuesta de la IA: {result}")
    
    if result:
        result = result.replace("true", "True").replace("false", "False")
        try:
            # Convertir la respuesta a formato JSON
            data = json.loads(result)
            print(f"╠――――Datos procesados: {data}")

            tipo_reporte = data.get("tipo_reporte")
            categoria = data.get("categoria")
            subcategoria = data.get("subcategoria")

            # Verificar si la categoría y subcategoría están en los diccionarios
            if tipo_reporte == "aviso":
                print(f"╠――――Tipo de reporte: {tipo_reporte}, Categoría: {categoria}, Subcategoría: {subcategoria}")
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
                            print(f"╠――――Asignando categoría: {cat} y subcategoría: {subcats[0]}")
                            print("╚―――――――――――――――――――――――――――――――――――――")
                            return {"tipo_reporte": "petición", "categoria": cat, "subcategoria": subcats[0]}

            print("⚠️ Categoría o subcategoría inválida. Rechazando el resultado.")
            return None

        except json.JSONDecodeError as e:
            print(f"Error al procesar JSON: {e}")
            return None

    print("No se recibió una respuesta válida del modelo.")
    return None

 # analizar_direccion(mensaje): Utiliza la API de OpenAI para extraer una dirección

# analizar_direccion(mensaje): Utiliza la API de OpenAI para extraer una dirección 
# completa (calle, avenida, etc.) del mensaje del usuario. Si la dirección no es 
# clara o válida, devuelve None.
def analizar_direccion(mensaje):
    # Solicitar la dirección de manera más directa y específica
    response = openai.ChatCompletion.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "Eres un asistente que detecta direcciones completas en los mensajes. Extrae solo las direcciones completas (calle, avenida, carretera, con nombre y número) y descarta cualquier otro tipo de información."},
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

            # Validar la dirección si es correcta
            if direccion and validar_direccion(direccion):
                return direccion
        except json.JSONDecodeError as e:
            print(f"Error al procesar dirección JSON: {e}")
    
    return None


# validar_direccion(direccion): Valida que una dirección tenga una estructura 
# coherente, aceptando calles, avenidas, carreteras, con número y código postal si es posible.
def validar_direccion(direccion):
    """
    Valida direcciones asegurando que contengan una estructura coherente.
    Permite calles, avenidas, carreteras, etc., con número, ciudad y código postal.
    """
    patron = re.compile(
        r"^(Calle|Avenida|Plaza|Paseo|Carretera|Autopista|Camino|Ronda|Travesía|Vía|Urbanización)?\s?"+
        r"[A-Za-z0-9áéíóúÁÉÍÓÚñÑ\s]+(\s?\d+)?(,\s?[A-Za-z\s]+)?(,\s?\d{5})?$",
        re.IGNORECASE
    )
    return bool(patron.match(direccion.strip()))

# ayuda(update, context): Permite a los usuarios reportar una emergencia. 
# Verifica si el usuario ha verificado sus datos, solicita el formato correcto de dirección 
# si el mensaje está vacío o tiene un formato incorrecto, y valida el tipo de reporte (aviso o petición). 
# Si todo es correcto, clasifica el reporte y lo envía al grupo de Telegram.
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

    # Analizar la direcciónn
    direccion = analizar_direccion(user_message)
    print(f"Dirección extraída: {direccion}")
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

#------------------------------------------------------------------------------------------------

AVISOS = {
    "Alumbrado Público": [
        "Calle Apagada",
        "Calle Apagada v2",
        "Calle Apagada v4",
        "Farola Apagada",
        "Luces de Navidad",
        "Otras Averías de Alumbrado"
    ],
    "Aparcamiento Regulado": [
        "Aplicación Móvil",
        "Aviso de Denuncia",
        "No Imprime tique o no valida Pin",
        "No permite anulación de denuncia",
        "Parquímetro",
        "Tarjeta Crédito atascada"
    ],
    "Arboles y Parques": [
        "Árbol en mal estado",
        "Caminos no pavimentados",
        "Incidencias de riesgo",
        "Incidencias en alcorque o hueco",
        "Plagas",
        "Poda de Árbol",
        "Quitar maleza",
        "Sustitución de Árbol"
    ],
    "Áreas Infantiles, Áreas de Mayores y circuitos": [
        "Área de Mayores y circuitos",
        "Área Infantil"
    ],
    "Calzadas y Aceras": [
        "Alcantarillado",
        "Desperfecto en acera",
        "Desperfecto en calzada",
        "Hidrantes de bomberos",
        "Otras incidencias en calzadas y aceras",
        "Tapas de registro",
        "Tapa de Agua Isabel II"
    ],
    "Cubos y Contenedores": [
        "Cambio de tamaño de cubo",
        "Cambio de ubicación de cubo o contenedor",
        "Cubo o contenedor abandonado",
        "Cubo o contenedor en mal estado",
        "Horquillas delimitadoras",
        "Nuevo cubo o contenedor",
        "Vaciado de aceite",
        "Vaciado de cubo o contenedor"
    ],
    "Fuentes": [
        "Incidencias en fuentes de Beber",
        "Incidencias en fuentes ornamentales"
    ],
    "Limpiezas y Pintadas": [
        "Limpieza en solares municipales",
        "Limpieza en vías públicas",
        "Limpieza mobiliario urbano o áreas infantiles",
        "Limpieza en zonas verdes",
        "Pintadas y Grafitis",
        "SELUR"
    ],
    "Mobiliario Urbano": [
        "Banco",
        "Bolardo u horquilla",
        "Otros",
        "Vallas"
    ],
    "Papeleras": [
        "Falta de bolsas para excrementos caninos",
        "Mal estado de papelera",
        "Nueva Instalación de Papelera",
        "Vaciado de Papelera"
    ],
    "Plagas": [
        "Ratas y Cucarachas"
    ],
    "Retirada de Elementos": [
        "Animales muertos",
        "Contenedor de ropa no autorizada",
        "Muebles abandonados en vía pública",
        "Muebles Particulares",
        "Recogida de saco o contenedor de escombros"
    ],
    "Señales y Semáforos": [
        "Incidencia en avisador acústico de semáforo",
        "Incidencia en Pulsador",
        "Incidencia en Señal",
        "Semáforo Apagado"
    ],
    "Vehículos Abandonados. Retirada de vehículo": [
        "Vehículos Abandonados. Retirada de vehículo"
    ]
}

PETICIONES = {
    "Áreas Infantiles, Áreas de Mayores y circuitos": [
        "Nueva Instalación"
    ],
    "Calzadas y Aceras": [
        "Mejora de Accesibilidad"
    ],
    "Fuentes": [
        "Nueva Instalación de fuente de beber"
    ],
    "Mobiliario Urbano": [
        "Nueva Instalación"
    ],
    "Señales y Semáforos": [
        "Nueva Señal"
    ]
}
