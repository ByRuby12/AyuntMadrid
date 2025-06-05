# -----------------------IMPORT LIBRERIAS---------------------------
from diccionarios import AVISOS_PRUEBA, PETICIONES_PRUEBA, WELCOME_MESSAGES, BOT_TEXTS, system_content_prompt
from claves import OPENAI_API_KEY, CURAIME_BOT_KEY, TELEGRAM_GROUP_ID, AUTHORIZATION_TOKEN
from datetime import datetime
from telegram import (Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, Location, InputFile)
from telegram.ext import (ApplicationBuilder, MessageHandler, filters, ContextTypes, ConversationHandler)
from langdetect import detect

import nest_asyncio
import openai
import json
import os
import requests
import asyncio
import base64
# --------------------CONFIGURACIONES PREVIAS-----------------------
nest_asyncio.apply()

# Configuración de claves
if not (TELEGRAM_GROUP_ID and OPENAI_API_KEY and CURAIME_BOT_KEY and AUTHORIZATION_TOKEN):
    raise print(f"❌ Error: Faltan claves necesarias para operar el bot. Revisa TELEGRAM_GROUP_ID, OPENAI_API_KEY, CURAIME_BOT_KEY, AUTHORIZATION_TOKEN en claves.py.")
os.environ["TELEGRAM_GROUP_ID"] = TELEGRAM_GROUP_ID
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
os.environ["CURAIME_BOT_KEY"] = CURAIME_BOT_KEY
os.environ["AUTHORIZATION_TOKEN"] = AUTHORIZATION_TOKEN
openai.api_key = OPENAI_API_KEY

# Etapas de conversación
ESPERANDO_UBICACION, ESPERANDO_MEDIA = range(2)

# ------------------------FUNCIONES----------------------------------

# 1.Traduce un texto a español si es necesario
async def traducir_a_espanol(texto, idioma_origen):
    if idioma_origen == 'es':
        return texto
    prompt = [
        {"role": "system", "content": "Eres un traductor profesional. Traduce el siguiente texto al español de España de forma natural y fiel al significado original. Devuelve solo el texto traducido, sin explicaciones ni formato extra."},
        {"role": "user", "content": texto}
    ]
    try:
        response = await openai.ChatCompletion.acreate(
            model="gpt-4o-mini",
            messages=prompt,
            temperature=0.2
        )
        traduccion = response["choices"][0]["message"]["content"].strip()
        return traduccion
    except Exception as e:
        print(f"Error traduciendo a español: {e}")
        return texto  # Si falla, devuelve el original

# ------------------------PRIMERA OPCION-----------------------------

# 1.1.Procesa el mensaje del usuario y pide ubicación si es válido
async def manejar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    mensaje = update.message.text
    print(f"╔―――――――――――――――――――――――――――――――――――――")
    print(f"Mensaje recibido de {user_id}: {mensaje}")

    idiomas_map = {
        'es': 'es', 'en': 'en', 'fr': 'fr', 'de': 'de', 'zh': 'zh', 'pt': 'pt',
        'it': 'it', 'ar': 'ar', 'ru': 'ru', 'hi': 'hi'
    }

    # Mejorar la detección de idioma: priorizar saludos sobre langdetect
    saludos = {
        'en': ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening'],
        'es': ['hola', 'buenas', 'buenos días', 'buenas tardes', 'buenas noches'],
        'fr': ['bonjour', 'salut', 'bonsoir'],
        'de': ['hallo', 'guten tag', 'guten morgen', 'guten abend'],
        'zh': ['你好', '您好', '早上好', '晚上好'],
        'pt': ['olá', 'ola', 'bom dia', 'boa tarde', 'boa noite'],
        'it': ['ciao', 'buongiorno', 'buonasera', 'salve'],
        'ar': ['مرحبا', 'أهلاً', 'صباح الخير', 'مساء الخير'],
        'ru': ['привет', 'здравствуйте', 'доброе утро', 'добрый день', 'добрый вечер'],
        'hi': ['नमस्ते', 'हैलो', 'सुप्रभात', 'शुभ संध्या', 'शुभ रात्रि']
    }
    
    mensaje_limpio = mensaje.strip().lower()
    idioma = None
    # 1. Buscar primero si es un saludo conocido
    for lang, palabras in saludos.items():
        if any(palabra in mensaje_limpio for palabra in palabras):
            idioma = lang
            print(f"Idioma forzado por palabra clave: {idioma}")
            break
    # 2. Si no es saludo, usar langdetect si está en la lista
    if not idioma:
        try:
            detected_lang = detect(mensaje)
            print(f"Idioma detectado: {detected_lang}")
            idioma = idiomas_map.get(detected_lang)
        except Exception as e:
            print(f"No se pudo detectar el idioma, usando español por defecto. Error: {e}")
            idioma = 'es'
    # 3. Si sigue sin idioma, poner español por defecto
    if not idioma:
        idioma = 'es'
    context.user_data["idioma"] = idioma

    resultado = await analizar_mensaje_con_openai(mensaje)

    if not resultado or "tipo" not in resultado or "categoría" not in resultado or "subcategoría" not in resultado:
        print("Mensaje no clasificado correctamente. Respondiendo con mensajes fluidos.")
        print(f"╚―――――――――――――――――――――――――――――――――――――")
        # Mostrar solo los mensajes de bienvenida sin la línea de cambio de idioma
        for texto in WELCOME_MESSAGES[idioma]:
            if "idioma del bot" in texto:
                continue  # Omitir la línea de cambio de idioma
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            await asyncio.sleep(3)
            await update.message.reply_text(texto, parse_mode="Markdown")
        return ConversationHandler.END

    tipo = resultado["tipo"]
    categoria = resultado["categoría"]
    subcategoria = resultado["subcategoría"]
    print(f"Clasificado como: Tipo='{tipo}', Categoría='{categoria}', Subcategoría='{subcategoria}'")

    # Buscar el ID de subcategoría
    id_subcategoria = None
    fuente = AVISOS_PRUEBA if tipo.lower() == "aviso" else PETICIONES_PRUEBA

    if categoria in fuente:
        subcategorias = fuente[categoria]
        if isinstance(subcategorias, dict):
            for subcat_key, subcat_data in subcategorias.items():
                if subcat_key.lower() == subcategoria.lower() or subcat_data["nombre"].lower() == subcategoria.lower():
                    id_subcategoria = subcat_data["id"][0] if subcat_data["id"] else None
                    break
        elif isinstance(subcategorias, list):
            for subcat_data in subcategorias:
                if subcat_data["nombre"].lower() == subcategoria.lower():
                    id_subcategoria = subcat_data["id"][0] if subcat_data["id"] else None
                    break
    else:
        print(f"Categoría '{categoria}' no encontrada en el diccionario.")

    context.user_data["reporte"] = {
        "tipo": tipo,
        "categoria": categoria,
        "subcategoria": subcategoria,
        "id_subcategoria": id_subcategoria,
        "descripcion": mensaje
    }

    textos = BOT_TEXTS.get(idioma, BOT_TEXTS['es'])

    boton_ubicacion = ReplyKeyboardMarkup(
        [[KeyboardButton("📍 Enviar ubicación", request_location=True)]],
        one_time_keyboard=True,
        resize_keyboard=True
    )

    print("Esperando ubicación del usuario...")

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    await asyncio.sleep(3)
    await update.message.reply_text(
        textos['detected'].format(tipo=tipo, categoria=categoria, subcategoria=subcategoria),
        parse_mode="Markdown"
    )
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    await asyncio.sleep(3)
    await update.message.reply_text(
        textos['send_location'],
        reply_markup=boton_ubicacion
    )
    return ESPERANDO_UBICACION

# 1.2.Clasifica un mensaje de texto usando OpenAI
async def analizar_mensaje_con_openai(mensaje_usuario: str):
    print(f"Analizando mensaje: {mensaje_usuario}")

    prompt = [
        {"role": "system", "content": system_content_prompt},
        {"role": "user", "content": mensaje_usuario}
    ]

    contenido = None  # Inicializar la variable para evitar errores

    try:
        response = await openai.ChatCompletion.acreate(
            model="gpt-4o-mini",
            messages=prompt,
            temperature=0.2
        )
        contenido = response["choices"][0]["message"]["content"]  # Acceso correcto al contenido de la respuesta
        print(f"Respuesta de OpenAI: {contenido}")

        resultado = json.loads(contenido)

        # Verificar si el resultado corresponde con una categoría y subcategoría válidas
        if "tipo" in resultado and "categoría" in resultado and "subcategoría" in resultado:
            tipo = resultado["tipo"]
            categoria = resultado["categoría"]
            subcategoria = resultado["subcategoría"]
            print(f"Tipo: {tipo}, Categoría: {categoria}, Subcategoría: {subcategoria}")

            # Verificamos si el tipo, categoría y subcategoría son válidos
            fuente = AVISOS_PRUEBA if tipo.lower() == "aviso" else PETICIONES_PRUEBA
            if categoria in fuente:
                subcategorias = fuente[categoria]
                if isinstance(subcategorias, dict):  # Si es un diccionario de subcategorías
                    if subcategoria not in subcategorias:
                        print(f"Subcategoría '{subcategoria}' no válida en la categoría '{categoria}'.")
                        return None  # Si la subcategoría no es válida, devolvemos None
                elif isinstance(subcategorias, list):  # Si es una lista de subcategorías
                    if not any(subcat["nombre"].lower() == subcategoria.lower() for subcat in subcategorias):
                        print(f"Subcategoría '{subcategoria}' no válida en la categoría '{categoria}'.")
                        return None  # Si la subcategoría no es válida, devolvemos None
            else:
                print(f"Categoría '{categoria}' no válida para el tipo '{tipo}'.")
                return None  # Si la categoría no es válida, devolvemos None
            return resultado
        else:
            print("No se encontraron 'tipo', 'categoría' o 'subcategoría' en la respuesta de OpenAI.")
    except Exception as e:
        print("Error al analizar respuesta de OpenAI:", e)
        if contenido:
            print("Contenido recibido:", contenido)

    return None

# ------------------------SEGUNDA OPCION-----------------------------

# 1.1Procesa la foto inicial enviada por el usuario
async def manejar_foto_inicial(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    idioma = 'es'  # Puedes mejorar esto detectando idioma por preferencia previa
    textos = BOT_TEXTS.get(idioma, BOT_TEXTS['es'])
    print(f"╔―――――――――――――――――――――――――――――――――――――")
    print(f"Foto recibida de {user_id}")
    # Descargar la foto
    photo_file = await update.message.photo[-1].get_file()
    file_path = f"temp_{user_id}.jpg"
    await photo_file.download_to_drive(file_path)
    # Clasificar imagen
    resultado = await analizar_imagen_con_openai(file_path)
    # Eliminar archivo temporal
    try:
        os.remove(file_path)
    except Exception:
        pass
    # Validación reforzada: no avanzar si algún campo está vacío
    if (
        not resultado or
        not resultado.get("tipo") or not resultado.get("categoría") or not resultado.get("subcategoría")
    ):
        print("Imagen no clasificada correctamente. Pidiendo descripción al usuario.")
        await update.message.reply_text(
            "No he podido reconocer el contenido de la foto. Por favor, describe brevemente el problema para poder clasificarlo:",
            parse_mode="Markdown"
        )
        context.user_data["esperando_descripcion_foto"] = True
        return 1001  # Estado especial para descripción tras foto
    tipo = resultado["tipo"]
    categoria = resultado["categoría"]
    subcategoria = resultado["subcategoría"]
    descripcion = resultado.get("descripcion", "[Reporte iniciado por imagen]")
    print(f"Clasificado como: Tipo='{tipo}', Categoría='{categoria}', Subcategoría='{subcategoria}'")
    id_subcategoria = None
    fuente = AVISOS_PRUEBA if tipo.lower() == "aviso" else PETICIONES_PRUEBA
    if categoria in fuente:
        subcategorias = fuente[categoria]
        if isinstance(subcategorias, dict):
            for subcat_key, subcat_data in subcategorias.items():
                if subcat_key.lower() == subcategoria.lower() or subcat_data["nombre"].lower() == subcategoria.lower():
                    id_subcategoria = subcat_data["id"][0] if subcat_data["id"] else None
                    break
        elif isinstance(subcategorias, list):
            for subcat_data in subcategorias:
                if subcat_data["nombre"].lower() == subcategoria.lower():
                    id_subcategoria = subcat_data["id"][0] if subcat_data["id"] else None
                    break
    context.user_data["reporte"] = {
        "tipo": tipo,
        "categoria": categoria,
        "subcategoria": subcategoria,
        "id_subcategoria": id_subcategoria,
        "descripcion": descripcion,
        "foto_inicial": update.message.photo[-1].file_id  # Guardar la foto para no pedirla de nuevo
    }
    print("Esperando ubicación del usuario...")
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    await asyncio.sleep(3)
    await update.message.reply_text(
        textos['detected'].format(tipo=tipo, categoria=categoria, subcategoria=subcategoria),
        parse_mode="Markdown"
    )
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    await asyncio.sleep(3)
    boton_ubicacion = ReplyKeyboardMarkup(
        [[KeyboardButton("📍 Enviar ubicación", request_location=True)]],
        one_time_keyboard=True,
        resize_keyboard=True
    )
    await update.message.reply_text(
        textos['send_location'],
        reply_markup=boton_ubicacion
    )
    return ESPERANDO_UBICACION

# 1.2.Clasifica una imagen y genera una descripción visual usando OpenAI
async def analizar_imagen_con_openai(file_path: str):
    """
    Envía una imagen a OpenAI Vision y clasifica según los diccionarios de avisos/peticiones.
    Devuelve un dict con tipo, categoría y subcategoría, y una descripción visual generada, o None si no se puede clasificar.
    """
    try:
        with open(file_path, "rb") as image_file:
            image_bytes = image_file.read()
            image_b64 = base64.b64encode(image_bytes).decode("utf-8")
            image_data_url = f"data:image/jpeg;base64,{image_b64}"
        # Primer paso: pedir clasificación y descripción visual en la misma llamada
        prompt = [
            {"role": "system", "content": system_content_prompt},
            {"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": image_data_url}},
                {"type": "text", "text": "Por favor, además de clasificar la imagen según las instrucciones, genera una breve descripción visual en español de lo que se observa en la imagen, en un campo 'descripcion'. Si no puedes describirla, deja 'descripcion' como cadena vacía. Devuelve un JSON con los campos: tipo, categoría, subcategoría y descripcion."}
            ]}
        ]
        response = await openai.ChatCompletion.acreate(
            model="gpt-4o",
            messages=prompt,
            temperature=0.2
        )
        contenido = response["choices"][0]["message"]["content"]
        resultado = json.loads(contenido)
        if (
            "tipo" in resultado and "categoría" in resultado and "subcategoría" in resultado
            and "descripcion" in resultado
        ):
            return resultado
    except Exception as e:
        print("Error al analizar imagen con OpenAI:", e)
    return None

# ------------------------PASOS FINALES------------------------------

# 2.Nuevo handler para recibir la descripción tras foto no detectada
async def recibir_descripcion_foto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Si el usuario envía una foto, volver a intentar clasificarla
    if update.message.photo:
        user_id = update.message.from_user.id
        idioma = context.user_data.get("idioma", "es")
        textos = BOT_TEXTS.get(idioma, BOT_TEXTS['es'])
        print(f"Nueva foto recibida tras fallo de clasificación anterior de {user_id}")
        photo_file = await update.message.photo[-1].get_file()
        file_path = f"temp_{user_id}.jpg"
        await photo_file.download_to_drive(file_path)
        resultado = await analizar_imagen_con_openai(file_path)
        try:
            os.remove(file_path)
        except Exception:
            pass
        if not resultado or "tipo" not in resultado or "categoría" not in resultado or "subcategoría" not in resultado:
            print("Imagen no clasificada correctamente. Volver a pedir descripción o nueva foto.")
            await update.message.reply_text(
                "No he podido reconocer el contenido de la foto. Puedes volver a intentarlo enviando otra foto o describiendo el problema:",
                parse_mode="Markdown"
            )
            return 1001
        tipo = resultado["tipo"]
        categoria = resultado["categoría"]
        subcategoria = resultado["subcategoría"]
        descripcion = resultado.get("descripcion", "[Reporte iniciado por imagen]")
        print(f"Clasificado como: Tipo='{tipo}', Categoría='{categoria}', Subcategoría='{subcategoria}'")
        id_subcategoria = None
        fuente = AVISOS_PRUEBA if tipo.lower() == "aviso" else PETICIONES_PRUEBA
        if categoria in fuente:
            subcategorias = fuente[categoria]
            if isinstance(subcategorias, dict):
                for subcat_key, subcat_data in subcategorias.items():
                    if subcat_key.lower() == subcategoria.lower() or subcat_data["nombre"].lower() == subcategoria.lower():
                        id_subcategoria = subcat_data["id"][0] if subcat_data["id"] else None
                        break
            elif isinstance(subcategorias, list):
                for subcat_data in subcategorias:
                    if subcat_data["nombre"].lower() == subcategoria.lower():
                        id_subcategoria = subcat_data["id"][0] if subcat_data["id"] else None
                        break
        context.user_data["reporte"] = {
            "tipo": tipo,
            "categoria": categoria,
            "subcategoria": subcategoria,
            "id_subcategoria": id_subcategoria,
            "descripcion": descripcion,
            "foto_inicial": update.message.photo[-1].file_id
        }
        print("Esperando ubicación del usuario...")
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        await asyncio.sleep(3)
        await update.message.reply_text(
            textos['detected'].format(tipo=tipo, categoria=categoria, subcategoria=subcategoria),
            parse_mode="Markdown"
        )
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        await asyncio.sleep(3)
        boton_ubicacion = ReplyKeyboardMarkup(
            [[KeyboardButton("📍 Enviar ubicación", request_location=True)]],
            one_time_keyboard=True,
            resize_keyboard=True
        )
        await update.message.reply_text(
            textos['send_location'],
            reply_markup=boton_ubicacion
        )
        return ESPERANDO_UBICACION
    # Si es texto, flujo normal: eliminar foto_inicial si existe (para que tras ubicación pida foto/video)
    # Si es texto, flujo normal: eliminar foto_inicial si existe (para que tras ubicación pida foto/video)
    context.user_data.pop("foto_inicial", None)
    context.user_data.pop("esperando_descripcion_foto", None)
    return await manejar_mensaje(update, context)

# 3.Procesa la ubicación enviada por el usuario y pide foto/video si procede
async def recibir_ubicacion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ubicacion: Location = update.message.location
    datos = context.user_data.get("reporte", {})
    idioma = context.user_data.get("idioma", "es")
    textos = BOT_TEXTS.get(idioma, BOT_TEXTS['es'])

    if not datos:
        print("Error: No tengo datos del reporte. Finalizando conversación.")
        await update.message.reply_text(textos['no_report'], reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    print(f"Ubicación recibida: Latitud {ubicacion.latitude}, Longitud {ubicacion.longitude}")

    datos["latitud"] = ubicacion.latitude
    datos["longitud"] = ubicacion.longitude
    datos["usuario"] = update.message.from_user.full_name
    datos["fecha"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    descripcion_original = datos["descripcion"]
    descripcion_es = await traducir_a_espanol(descripcion_original, idioma)
    datos["descripcion_es"] = descripcion_es

    # Validar ubicación con la API PRE antes de pedir foto/video
    try:
        payload = {
            "service_id": "591b36544e4ea839018b4653", 
            "description": descripcion_es,
            "position": {
                "lat": datos["latitud"],
                "lng": datos["longitud"]
            },
            "address_string": "Calle Mayor, 12"
        }
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + AUTHORIZATION_TOKEN,
        }
        url = "https://servpubpre.madrid.es/AVSICAPIINT/requests?jurisdiction_id=es.madrid&return_data=false"
        response = requests.post(url, headers=headers, json=payload)
        try:
            response_data = response.json()
        except Exception:
            response_data = {}
        if (
            isinstance(response_data, dict)
            and response_data.get("error_msg")
            and "Coordinates do not have a valid zones" in response.text
        ):
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            await asyncio.sleep(2)
            await update.message.reply_text(
                textos['out_of_madrid'],
                parse_mode="Markdown",
                reply_markup=ReplyKeyboardRemove()
            )
            print(f"La ubicación está fuera de Madrid. Cancelando.")
            print(f"╚―――――――――――――――――――――――――――――――――――――")
            context.user_data.clear()
            return ConversationHandler.END
    except Exception as e:
        print(f"Error validando ubicación con la API PRE: {e}")
        await update.message.reply_text(textos['ayto_error'], reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    print(f"DESCRIPCIÓN EN ESPAÑOL: {descripcion_es}")

    # --- FLUJO INTELIGENTE FOTO/TEXTO ---
    if datos.get("foto_inicial"):
        # Si ya hay una foto válida, hacer POST y enviar al grupo directamente
        archivo = datos["foto_inicial"]
        return await enviar_reporte_final(datos, textos, descripcion_es, descripcion_original, context, update, tipo_media="foto", archivo=archivo)
    else:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        await asyncio.sleep(3)
        await update.message.reply_text(
            textos['send_media'],
            parse_mode="Markdown"
        )
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        await asyncio.sleep(3)
        skip_text = textos.get('skip_button', 'Omitir')
        await update.message.reply_text(
            textos['skip_media'],
            reply_markup=ReplyKeyboardMarkup([[skip_text]], one_time_keyboard=True, resize_keyboard=True),
            parse_mode="Markdown"
        )
        return ESPERANDO_MEDIA

# 4.Procesa la foto o video enviado por el usuario
async def recibir_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    datos = context.user_data.get("reporte", {})
    idioma = context.user_data.get("idioma", "es")
    textos = BOT_TEXTS.get(idioma, BOT_TEXTS['es'])

    if not datos:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        await asyncio.sleep(3)
        await update.message.reply_text(textos['no_report'], reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    archivo = None
    tipo_media = None
    skip_text = textos.get('skip_button', 'Omitir')

    if update.message.photo:
        archivo = update.message.photo[-1].file_id
        tipo_media = "foto"
    elif update.message.video:
        archivo = update.message.video.file_id
        tipo_media = "video"
    elif update.message.text and update.message.text.lower() == skip_text.lower():
        tipo_media = "omitido"
    else:
        if not (update.message.photo or update.message.video):
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            await asyncio.sleep(1)
            await update.message.reply_text(textos['media_error'])
            return ESPERANDO_MEDIA

    descripcion_es = datos.get("descripcion_es", datos.get("descripcion", ""))
    descripcion_original = datos.get("descripcion", "")
    return await enviar_reporte_final(datos, textos, descripcion_es, descripcion_original, context, update, tipo_media=tipo_media, archivo=archivo)

# 5.Envía el reporte a la API municipal y al grupo de Telegram
async def enviar_reporte_final(datos, textos, descripcion_es, descripcion_original, context, update, tipo_media=None, archivo=None):

    try:
        print("―――――――――――――――――――――――――――――――――――――\n")
        print("📢 Nuevo", datos['tipo'].upper(), "recibido:")
        print("👤 Usuario:", datos['usuario'])
        print("📆 Fecha:", datos['fecha'])
        print("📄 Descripción:", descripcion_es)
        print("📌 Tipo:", datos['tipo'])
        print("📂 Categoría:", datos['categoria'])
        print("🔖 Subcategoría:", datos['subcategoria'])
        print("🔖 ID Subcategoría:", datos.get('id_subcategoria'))
        print("📍 Ubicación: https://maps.google.com/?q=" + str(datos['latitud']) + "," + str(datos['longitud']), "\n")
        if tipo_media == "foto":
            print("Enviando mensaje al grupo con multimedia (foto inicial)")
        elif tipo_media == "video":
            print("Enviando mensaje al grupo con multimedia (video)")
        else:
            print("Enviando mensaje al grupo sin multimedia")
        print(f"╚―――――――――――――――――――――――――――――――――――――")
        
        # Payload completo si hay datos extendidos, si no, el simple
        if 'latitud' in datos and 'longitud' in datos and 'usuario' in datos and 'fecha' in datos:
            payload = {
                "service_id": "591b36544e4ea839018b4653",
                "description": descripcion_es,
                "position": {
                    "lat": datos["latitud"],
                    "lng": datos["longitud"],
                    "location_additional_data": [
                        {
                            "question": "5e49c26b6d4af6ac018b4623",
                            "value": "Avenida"
                        },
                        {
                            "question": "5e49c26b6d4af6ac018b4624",
                            "value": "Brasil"
                        },
                        {
                            "question": "5e49c26b6d4af6ac018b4625",
                            "value": "5"
                        },
                        {
                            "question": "5e49c26b6d4af6ac018b4627",
                            "value": 28020
                        },
                        {
                            "question": "5e49c26b6d4af6ac018b4628",
                            "value": "Cuatro Caminos"
                        },
                        {
                            "question": "5e49c26b6d4af6ac018b4629",
                            "value": "Tetuan"
                        },
                        {
                            "question": "5e49c26b6d4af6ac018b462a",
                            "value": 6
                        },
                        {
                            "question": "5e49c26b6d4af6ac018b462b",
                            "value": 2
                        },
                        {
                            "question": "5e49c26b6d4af6ac018b462d",
                            "value": 441155.2
                        },
                        {
                            "question": "5e49c26b6d4af6ac018b462e",
                            "value": 4478434.5
                        },
                        {
                            "question": "5e49c26b6d4af6ac018b4633",
                            "value": 20011240
                        },
                        {
                            "question": "5e49c26b6d4af6ac018b462f",
                            "value": 441182.22
                        },
                        {
                            "question": "5e49c26b6d4af6ac018b4630",
                            "value": 4478435.6
                        },
                        {
                            "question": "5e49c26b6d4af6ac018b4632",
                            "value": 114200
                        },
                        {
                            "question": "5e49c26b6d4af6ac018b4631",
                            "value": "Oeste"
                        }
                    ]
                },
                "address_string": "Calle Mayor, 12",
                "device_type": "5922cfab4e4ea823178b4568",
                "additionalData": [
                    {
                        "question": "5e49c26b6d4af6ac018b45d2",
                        "value": "Malos olores"
                    }
                ]
            }
        else:
            payload = {
                "service_id": "591b36544e4ea839018b4653",
                "description": descripcion_es,
                "position": {
                    "lat": datos["latitud"],
                    "lng": datos["longitud"]
                },
                "address_string": "Calle Mayor, 12"
            }
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + AUTHORIZATION_TOKEN
        }
        url = "https://servpubpre.madrid.es/AVSICAPIINT/requests?jurisdiction_id=es.madrid&return_data=false"
        response = requests.post(url, headers=headers, json=payload)
        
        try:
            response_data = response.json()
            service_request_id = response_data.get("service_request_id", "No disponible")
        except Exception:
            service_request_id = "No disponible"
        print(f"╔――――Respuesta del servidor: {response.text}")
        print(f"╚―――――――――――――――――――――――――――――――――――――")
        
        mensaje_grupo = (
            f"📢 Nuevo {datos['tipo'].upper()} recibido:\n\n"
            f"👤 Usuario: {datos['usuario']}\n"
            f"🗓 Fecha: {datos['fecha']}\n"
            f"📄 Descripción: {descripcion_es}\n"
            f"📌 Tipo: {datos['tipo']}\n"
            f"📂 Categoría: {datos['categoria']}\n"
            f"🔖 Subcategoría: {datos['subcategoria']}\n"
            f"📍 Ubicación: https://maps.google.com/?q={datos['latitud']},{datos['longitud']}"
        )
        if tipo_media == "foto" and archivo:
            await context.bot.send_photo(
                chat_id=TELEGRAM_GROUP_ID,
                photo=archivo,
                caption=mensaje_grupo,
                parse_mode="Markdown"
            )
        elif tipo_media == "video" and archivo:
            await context.bot.send_video(
                chat_id=TELEGRAM_GROUP_ID,
                video=archivo,
                caption=mensaje_grupo,
                parse_mode="Markdown"
            )
        else:
            await context.bot.send_message(
                chat_id=TELEGRAM_GROUP_ID,
                text=mensaje_grupo,
                parse_mode="Markdown"
            )
        respuesta = textos['followup'].format(
            service_request_id=service_request_id,
            usuario=datos['usuario'],
            tipo=datos['tipo'].capitalize(),
            categoria=datos['categoria'],
            subcategoria=datos['subcategoria'],
            latitud=datos['latitud'],
            longitud=datos['longitud'],
            descripcion=descripcion_original
        )
        await update.message.reply_text(respuesta, parse_mode="Markdown")
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        await asyncio.sleep(3)
        await update.message.reply_text(textos['sent'])
    except Exception as e:
        print(f"❌ Error al enviar reporte final: {e}")
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        await asyncio.sleep(3)
        await update.message.reply_text(textos['ayto_error'])
    return ConversationHandler.END

# ------------------------RECORDATORIO USUARIO PASOS-----------------

# 6.Recuerda al usuario que debe enviar ubicación
async def recordar_ubicacion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    idioma = context.user_data.get("idioma", "es")
    textos = BOT_TEXTS.get(idioma, BOT_TEXTS['es'])
    await update.message.reply_text(
        textos['location_error'],
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("📍 Enviar ubicación", request_location=True)]],
            one_time_keyboard=True,
            resize_keyboard=True
        )
    )
    return ESPERANDO_UBICACION

# 7.Recuerda al usuario que debe enviar foto/video o puede omitir
async def recordar_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    idioma = context.user_data.get("idioma", "es")
    textos = BOT_TEXTS.get(idioma, BOT_TEXTS['es'])
    skip_text = textos.get('skip_button', 'Omitir')
    await update.message.reply_text(
        textos['media_error'],
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton(skip_text)]],
            one_time_keyboard=True,
            resize_keyboard=True
        )
    )
    return ESPERANDO_MEDIA

# -------------------------MANEJADOR MAIN----------------------------

# Inicia el bot y configura el manejador de conversación
if __name__ == '__main__':
    app = ApplicationBuilder().token(CURAIME_BOT_KEY).build()    
    conversation_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensaje),
            MessageHandler(filters.PHOTO, manejar_foto_inicial)
        ],
        states={
            1001: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_descripcion_foto),
                MessageHandler(filters.PHOTO, recibir_descripcion_foto)
            ],
            ESPERANDO_UBICACION: [
                MessageHandler(filters.LOCATION, recibir_ubicacion),
                MessageHandler(filters.ALL & ~filters.LOCATION, recordar_ubicacion)
            ],            ESPERANDO_MEDIA: [
                MessageHandler(filters.PHOTO | filters.VIDEO, recibir_media),
                MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_media),
                MessageHandler(filters.ALL & ~(filters.PHOTO | filters.VIDEO | (filters.TEXT & ~filters.COMMAND)), recordar_media)
            ]
        },
        fallbacks=[],
    )
    app.add_handler(conversation_handler)
    print("🤖 Bot en funcionamiento...")
    app.run_polling()
    print("🚫 Bot detenido.")