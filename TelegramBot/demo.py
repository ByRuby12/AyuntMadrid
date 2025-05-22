# -----------------------IMPORT LIBRERIAS---------------------------

from diccionarios import AVISOS_PRUEBA, PETICIONES_PRUEBA, WELCOME_MESSAGES, BOT_TEXTS
from claves import OPENAI_API_KEY, CURAIME_BOT_KEY, TELEGRAM_GROUP_ID
from datetime import datetime
from telegram import (Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, Location)
from telegram.ext import (ApplicationBuilder, MessageHandler, filters, ContextTypes, ConversationHandler)
from langdetect import detect

import nest_asyncio
import openai
import json
import os
import requests
import asyncio

# --------------------CONFIGURACIONES PREVIAS-----------------------
nest_asyncio.apply()

# Configuración de claves
if not (TELEGRAM_GROUP_ID and OPENAI_API_KEY and CURAIME_BOT_KEY):
    raise print(f"❌ Error: Faltan claves necesarias para operar el bot. Revisa TELEGRAM_GROUP_ID, OPENAI_API_KEY y CURAIME_BOT_KEY en claves.py.")
os.environ["TELEGRAM_GROUP_ID"] = TELEGRAM_GROUP_ID
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
os.environ["CURAIME_BOT_KEY"] = CURAIME_BOT_KEY
openai.api_key = OPENAI_API_KEY

# Etapas de conversación
ESPERANDO_UBICACION, ESPERANDO_MEDIA = range(2)

# Mensaje de sistema para OpenAI
system_content_prompt = f"""
Eres un asistente del Ayuntamiento de Madrid encargado de clasificar reportes ciudadanos.
Los reportes pueden ser de tipo 'aviso' (problemas o incidencias) o 'petición' (solicitudes de mejora).
Debes analizar un mensaje del usuario e identificar su tipo ('aviso' o 'petición'), una categoría y una subcategoría,
siguiendo estrictamente los valores que aparecen en los diccionarios oficiales del Ayuntamiento.

IMPORTANTE: El mensaje del usuario puede estar en cualquier idioma (español, inglés, francés, alemán, etc). Debes traducirlo internamente si es necesario y responder SIEMPRE en español, usando los nombres de categoría y subcategoría tal como aparecen en los diccionarios.

Cada categoría contiene una lista de subcategorías, y cada subcategoría tiene un campo "nombre" que debes usar como referencia exacta para clasificar.

Aquí tienes el listado completo de categorías y subcategorías válidas:

Categorías y subcategorías para AVISOS:
{json.dumps(AVISOS_PRUEBA, indent=2, ensure_ascii=False)}

Categorías y subcategorías para PETICIONES:
{json.dumps(PETICIONES_PRUEBA, indent=2, ensure_ascii=False)}

🔍 INSTRUCCIONES CRÍTICAS:
- El tipo ('aviso' o 'petición') debe determinarse exclusivamente según en qué diccionario (AVISOS o PETICIONES) se encuentre la categoría y subcategoría.
- NO asumas el tipo por palabras como 'solicito', 'quiero', etc.
- Si una subcategoría solo está en AVISOS, entonces el tipo debe ser 'aviso'.
- Si está solo en PETICIONES, entonces el tipo debe ser 'petición'.

🚫 ERROR COMÚN (NO LO COMETAS):
- Mensaje: 'Solicito cubo de basura' → Subcategoría: 'Nuevo cubo o contenedor' (está en AVISOS) → Tipo correcto: 'aviso' (¡NO 'petición'!).

⚠️ RESPUESTA: Devuelve solo un JSON válido en este formato:
{{"tipo": "aviso", "categoría": "Alumbrado Público", "subcategoría": "Calle Apagada"}}

Si no puedes clasificar el mensaje, responde con un JSON vacío: {{}}
No incluyas ningún texto adicional. Solo el JSON.
"""

# ------------------------FUNCIONES----------------------------------

# Envía el mensaje del usuario a OpenAI para analizarlo. Si detecta que es un aviso o petición con una categoría y subcategoría 
# válidas (según los diccionarios que tienes), devuelve esa información estructurada. Si no es válido, devuelve None.
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

# Recibe el mensaje del usuario y lo analiza con la función anterior. Si es válido, guarda la información en context.user_data, 
# informa al usuario del tipo de reporte detectado y le pide que comparta su ubicación. Si no es válido, le muestra un mensaje 
# explicando qué es un aviso o una petición.
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

# Toma la ubicación enviada por el usuario, completa los datos del reporte (incluyendo nombre, fecha y coordenadas) y los envía a 
# un grupo de Telegram formateados como mensaje. Luego confirma al usuario que el reporte ha sido enviado correctamente.
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

    # Validar ubicación con la API PRE antes de pedir foto/video
    try:
        payload = {
            "service_id": "591b36544e4ea839018b4653",  # Usar la ID de la subcategoría o una por defecto
            "description": datos["descripcion"],
            "position": {
                "lat": datos["latitud"],
                "lng": datos["longitud"]
            },
            "address_string": "Calle Mayor, 12"
        }
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer Yjk1MWRiZWVlN2Y4YmRkNmI2NTNkNjU2OGYyYjNlYTJjNzBiNjg0YzllN2Q1M2Q3N2IzYmY3NjcxZGI4ZGZiOA'
        }
        url = "https://servpubpre.madrid.es/AVSICAPIINT/requests?jurisdiction_id=es.madrid&return_data=false"
        response = requests.post(url, headers=headers, json=payload)
        try:
            response_data = response.json()
        except Exception:
            response_data = {}
        # Si el error es por zona fuera de Madrid, cancelar aquí
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

# Envía el mensaje del usuario al grupo de Telegram con la información del reporte. Si el usuario envía una foto o video, lo adjunta al mensaje.
# Si el usuario decide omitir el archivo, envía el mensaje sin multimedia. Luego confirma al usuario que el reporte ha sido enviado.
# Finalmente, finaliza la conversación.
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

    mensaje_grupo = (
        f"📢 Nuevo {datos['tipo'].upper()} recibido:\n\n"
        f"👤 Usuario: {datos['usuario']}\n"
        f"🗓 Fecha: {datos['fecha']}\n"
        f"📄 Descripción: {datos['descripcion']}\n"
        f"📌 Tipo: {datos['tipo']}\n"
        f"📂 Categoría: {datos['categoria']}\n"
        f"🔖 Subcategoría: {datos['subcategoria']}\n"
        f"📍 Ubicación: https://maps.google.com/?q={datos['latitud']},{datos['longitud']}"
    )

    print(f"―――――――――――――――――――――――――――――――――――――")
    print("📢 Nuevo", datos['tipo'].upper(), "recibido:")
    print("👤 Usuario:", datos['usuario'])
    print("📆 Fecha:", datos['fecha'])
    print("📄 Descripción:", datos['descripcion'])
    print("📌 Tipo:", datos['tipo'])
    print("📂 Categoría:", datos['categoria'])
    print("🔖 Subcategoría:", datos['subcategoria'])
    print("🔖 ID Subcategoría:", datos['id_subcategoria'])
    print("📍 Ubicación: https://maps.google.com/?q=" + str(datos['latitud']) + "," + str(datos['longitud']), "\n")
    print("Enviando mensaje al grupo con" + (" multimedia" if tipo_media != "omitido" else " sin multimedia"))
    print(f"╚―――――――――――――――――――――――――――――――――――――")

    # Enviar a la Plataforma del Ayuntamiento
    try:
        payload = {
            "service_id": "591b36544e4ea839018b4653",  # Usar la ID de la subcategoría
            "description": datos["descripcion"],  # Descripción
            "position": {
               "lat": datos["latitud"],
               "lng": datos["longitud"],
                "location_additional_data": [
                    {
                        "question": "5e49c26b6d4af6ac018b4623",  # TIPO DE VIA
                        "value": "Avenida"
                    },
                    {
                        "question": "5e49c26b6d4af6ac018b4624",  # NOMBRE DE VIA 
                        "value": "Brasil"
                    },
                    {
                        "question": "5e49c26b6d4af6ac018b4625",  # NUMERO DE VIA
                        "value": "5"
                    },
                    {
                        "question": "5e49c26b6d4af6ac018b4627",  # CODIGO POSTAL
                        "value": 28020
                    },
                    {
                        "question": "5e49c26b6d4af6ac018b4628",  # NOMBRE DEL BARRIO
                        "value": "Cuatro Caminos"
                    },
                    {
                        "question": "5e49c26b6d4af6ac018b4629",  # NOMBRE DISTRITO
                        "value": "Tetuan"
                    },
                    {
                        "question": "5e49c26b6d4af6ac018b462a",  # CODIGO DEL DISTRITO
                        "value": 6
                    },
                    {
                        "question": "5e49c26b6d4af6ac018b462b",  # CODIGO DEL BARRIO
                        "value": 2
                    },
                    {
                        "question": "5e49c26b6d4af6ac018b462d",  # COORDENADA DE X DEL NDP
                        "value": 441155.2
                    },
                    {
                        "question": "5e49c26b6d4af6ac018b462e",  # Coordenada Y del NDP
                        "value": 4478434.5
                    },
                    {
                        "question": "5e49c26b6d4af6ac018b4633",  # Id ndp
                        "value": 20011240
                    },
                    {
                        "question": "5e49c26b6d4af6ac018b462f",  # Coordenada X del reporte
                        "value": 441182.22
                    },
                    {
                        "question": "5e49c26b6d4af6ac018b4630",  # Coordenada Y del reporte
                        "value": 4478435.6
                    },
                    {
                        "question": "5e49c26b6d4af6ac018b4632",  # Id de la via
                        "value": 114200
                    },
                    {
                        "question": "5e49c26b6d4af6ac018b4631",  # orientación
                        "value": "Oeste"
                    }
                ]
            },
            "address_string": "Calle Mayor, 12",  # Dirección de ejemplo
            "device_type": "5922cfab4e4ea823178b4568",  # Optional
            "additionalData": [
                {
                    "question": "5e49c26b6d4af6ac018b45d2",  # ¿Cual es el problema?
                    "value": "Malos olores"
                }
            ]
        }

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer 123'
        }

        url = "https://servpubpre.madrid.es/AVSICAPIINT/requests?jurisdiction_id=es.madrid&return_data=false"
        
        response = requests.post(url, headers=headers, json=payload)
        try:
            response_data = response.json()
            service_request_id = response_data.get("service_request_id", "No disponible")
        except json.JSONDecodeError:
            service_request_id = "No disponible"
        print(f"╔――――Respuesta del servidor: {response.text}")
        print(f"╚―――――――――――――――――――――――――――――――――――――")
        # Comprobar si el error es por zona fuera de Madrid
        if (
            isinstance(response_data, dict)
            and response_data.get("error_msg")
            and "Coordinates do not have a valid zones" in response.text
        ):
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            await asyncio.sleep(2)
            await update.message.reply_text(
                textos['out_of_madrid'],
                parse_mode="Markdown"
            )
            return ConversationHandler.END

        # Si todo es correcto, enviar el mensaje al grupo de Telegram
        if tipo_media == "foto":
            await context.bot.send_photo(
                chat_id=TELEGRAM_GROUP_ID,
                photo=archivo,
                caption=mensaje_grupo,
                parse_mode="Markdown"
            )
        elif tipo_media == "video":
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
            descripcion=datos['descripcion']
        )

        await update.message.reply_text(respuesta, parse_mode="Markdown")
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        await asyncio.sleep(3)
        await update.message.reply_text(textos['sent'])

    except Exception as e:
        print(f"❌ Error al enviar a la plataforma del ayuntamiento: {e}")
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        await asyncio.sleep(3)
        await update.message.reply_text(textos['ayto_error'])
    return ConversationHandler.END

# Handler para recordar que debe enviar ubicación
# Si el usuario no envía una ubicación, se le recuerda que debe hacerlo.
# Si el usuario envía un texto, se le recuerda que debe enviar una ubicación o omitirlo.
# Si el usuario envía un archivo multimedia, se le recuerda que debe enviar una ubicación o omitirlo.
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

# Handler para recordar que debe enviar foto/video/omitir
# Si el usuario no envía un archivo multimedia, se le recuerda que debe hacerlo.
# Si el usuario envía un texto, se le recuerda que debe enviar un archivo multimedia o omitirlo.
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

# -------------------------MAIN---------------------------------------

# Inicia el bot y configura el manejador de conversación para recibir mensajes y ubicaciones.
# Cuando el usuario envía un mensaje, se analiza y se le pide la ubicación. Luego, se le pide que envíe una foto o video del problema.
# Finalmente, se envía el reporte al grupo de Telegram y se confirma al usuario que su reporte ha sido enviado.

if __name__ == '__main__':
    app = ApplicationBuilder().token(CURAIME_BOT_KEY).build()    
    conversation_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensaje)],
        states={
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