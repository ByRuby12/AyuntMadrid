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