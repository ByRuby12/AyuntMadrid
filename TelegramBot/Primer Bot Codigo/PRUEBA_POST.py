# -----------------------IMPORT LIBRERIAS---------------------------

from diccionarios import AVISOS_PRUEBA, PETICIONES_PRUEBA
from claves import OPENAI_API_KEY, CURAIME_BOT_KEY

import nest_asyncio
import requests
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
    f"{json.dumps(AVISOS_PRUEBA, indent=2, ensure_ascii=False)}\n\n"

    f"Categorías y subcategorías para PETICIONES:\n"
    f"{json.dumps(PETICIONES_PRUEBA, indent=2, ensure_ascii=False)}\n\n"

    "🔍 IMPORTANTE:\n"
    "- Aunque el mensaje del usuario no coincida exactamente con las palabras del diccionario, intenta identificar sinónimos o frases similares.\n"
    "- Si el mensaje describe una situación que encaja con alguna subcategoría, devuélvela aunque esté redactada de forma diferente.\n"
    "- Si no puedes identificar claramente ninguna categoría o subcategoría válida, no devuelvas nada.\n\n"

    "Devuelve únicamente subcategorías exactas del diccionario. No inventes nuevas.\n"
)

messages_to_send = [{"role": "system", "content": system_content_prompt}]

#-----------------------------FUNCIONES DEL BOT-----------------------------------------------

# analizar_reporte(mensaje): Envía el mensaje a la API de OpenAI para clasificarlo como 
# aviso o petición y asignar categoría/subcategoría válida.
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
                        "subcategoria": {"type": "string"},
                        "id_subcategoria": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["tipo_reporte", "categoria", "subcategoria", "id_subcategoria"]
                }
            }
        ],
        function_call="auto"
    )

    # 📌 Extraer los datos de la respuesta
    result = response.get("choices", [{}])[0].get("message", {}).get("function_call", {}).get("arguments", "{}")

    print(f"╔―――――――――――――――――――――――――――――――――――――")
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
                if categoria in AVISOS_PRUEBA:
                    for sub in AVISOS_PRUEBA[categoria]:
                        if sub["nombre"].lower() == subcategoria.lower():
                            print(f"╚――――Reporte clasificado correctamente como aviso.")
                            return {
                                "tipo_reporte": "aviso",
                                "categoria": categoria,
                                "subcategoria": subcategoria,
                                "id_subcategoria": sub["id"]
                            }
                    # Intentar asignar la categoría y subcategoría correcta
                    print(f"╠――――Categoría o subcategoría no válida: {categoria} / {subcategoria}")
                    for cat, subcats in AVISOS_PRUEBA.items():
                        for sub in subcats:
                            if sub["nombre"].lower() in mensaje.lower():
                                print(f"Asignando categoría: {cat} y subcategoría: {sub['nombre']}")
                                return {
                                    "tipo_reporte": "aviso",
                                    "categoria": cat,
                                    "subcategoria": sub['nombre'],
                                    "id_subcategoria": sub["id"]
                                }

            elif tipo_reporte == "petición":
                print(f"╠――――Tipo de reporte: {tipo_reporte}, Categoría: {categoria}, Subcategoría: {subcategoria}")
                if categoria in PETICIONES_PRUEBA:
                    for sub in PETICIONES_PRUEBA[categoria]:
                        if sub["nombre"].lower() == subcategoria.lower():
                            print(f"╚――――Reporte clasificado correctamente como petición.")
                            return {
                                "tipo_reporte": "petición",
                                "categoria": categoria,
                                "subcategoria": subcategoria,
                                "id_subcategoria": sub["id"]
                            }
                    # Intentar asignar la categoría y subcategoría correcta
                    print(f"╠――――Categoría o subcategoría no válida para petición: {categoria} / {subcategoria}")
                    for cat, subcats in PETICIONES_PRUEBA.items():
                        for sub in subcats:
                            if sub["nombre"].lower() in mensaje.lower():
                                print(f"╠――――Asignando categoría: {cat} y subcategoría: {sub['nombre']}")
                                return {
                                    "tipo_reporte": "petición",
                                    "categoria": cat,
                                    "subcategoria": sub['nombre'],
                                    "id_subcategoria": sub["id"]
                                }

            print(f"⚠️ Categoría o subcategoría inválida. Rechazando el resultado⚠️")
            return None

        except json.JSONDecodeError as e:
            print(f"Error al procesar JSON: {e}")
            return None

    print(f"No se recibió una respuesta válida del modelo.")
    return None

# ayuda(update, context): Verifica si el usuario está verificado, muestra ejemplos de 
# uso de /ayuda y solicita la ubicación para el reporte.
async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.replace("/ayuda", "").strip()
    user_id = update.message.from_user.id

    # Verificar si el usuario está enviando el comando sin mensaje
    if not user_message:
        await update.message.reply_text(
            "⚠️ Por favor, proporciona un mensaje después de /ayuda. Ejemplos de cómo hacerlo:\n\n"
            "1️⃣ **Aviso** (problemas en la vía pública):\n"
            "`/ayuda Farola apagada en la Calle Mayor 12, Madrid`\n"
            "Descripción detallada del problema y dirección completa.\n\n"
            "2️⃣ **Petición** (solicitudes de mejora):\n"
            "`/ayuda Solicito nueva instalación de área infantil en la Calle del Sol 3, Madrid`\n"
            "Especifica claramente la solicitud y la dirección exacta.\n\n"
            "🔍 **Formato de dirección**: Incluye tipo de vía, nombre de la calle, número (si aplica), ciudad y código postal.\n"
            "Ejemplos válidos:\n"
            "• Calle Alcalá 23, Madrid, 28041\n"
            "• Plaza Mayor 1, Madrid\n\n",
            parse_mode="Markdown"
        )
        return

    # Verificar si el usuario ha enviado un mensaje recientemente (esperar 2 minutos entre mensajes)
    last_message_time = context.user_data.get(user_id, {}).get("last_message_time", 0)
    current_time = time.time()

    # Si no ha pasado 2 minutos desde el último mensaje
    if current_time - last_message_time < 120:
        remaining_time = 120 - (current_time - last_message_time)
        await update.message.reply_text(f"⚠️ Por favor, espera {int(remaining_time)} segundos antes de enviar otro reporte.")
        return

    # Actualizar el tiempo del último mensaje
    if user_id not in context.user_data:
        context.user_data[user_id] = {}
    context.user_data[user_id]["last_message_time"] = current_time

    # Verificar si el mensaje es un reporte válido
    reporte = analizar_reporte(user_message)
    if not reporte:
        await update.message.reply_text("⚠️ No he podido entender tu solicitud.")
        return

    tipo_reporte = reporte["tipo_reporte"]
    categoria = reporte["categoria"]
    subcategoria = reporte["subcategoria"]
    id_subcategoria = reporte["id_subcategoria"]  # Obtener las IDs de la subcategoría

    # Guardar la información en context.user_data
    context.user_data["tipo_reporte"] = tipo_reporte
    context.user_data["categoria"] = categoria
    context.user_data["subcategoria"] = subcategoria
    context.user_data["id_subcategoria"] = id_subcategoria  # Guardar la ID de la subcategoría
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

# recibir_ubicacion(update, context): Recibe la ubicación del usuario, construye un 
# payload con los datos y lo envía a la plataforma del Ayuntamiento de Madrid.
async def recibir_ubicacion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    # Acceder a los datos almacenados en context.user_data
    tipo_reporte = context.user_data.get("tipo_reporte")
    categoria = context.user_data.get("categoria")
    subcategoria = context.user_data.get("subcategoria")
    id_subcategoria = context.user_data.get("id_subcategoria")  # Obtener la ID de la subcategoría
    user_message = context.user_data.get("user_message")  # Obtener el mensaje del usuario

    # Obtener la ubicación
    location = update.message.location
    if location:
        latitude = location.latitude
        longitude = location.longitude

        # Crear el payload para el POST
        payload = {
            "service_id": "591b36544e4ea839018b4653",  # Usar la ID de la subcategoría
            "description": user_message,  # Descripción
            "position": {
                "lat": latitude,  # latitud
                "lng": longitude,  # longitud
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

    respuesta = (
        f"📋 Reporte Seguimiento: {service_request_id}\n"
        f"👤 Usuario: `{user_id}`\n"
        f"📌 Tipo: {tipo_reporte.capitalize()}\n"
        f"📂 Categoría: {categoria}\n"
        f"🔖 Subcategoría: {subcategoria}\n"
        f"🔖 ID Subcategoria: `{id_subcategoria}`\n"
        f"🗺️ Dirección: {latitude} {longitude}\n"
        f"💬 Descripción: {user_message}\n"
    )

    await update.message.reply_text(respuesta, parse_mode="Markdown")
    await context.bot.send_message(
        chat_id=TELEGRAM_GROUP_ID,
        text=respuesta,
        parse_mode="Markdown"
    )

    await update.message.reply_text("✅ Tu reporte ha sido enviado correctamente a la Plataforma del Ayuntamiento de Madrid")

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

    print("✅ El bot está en ejecución.")
    application.run_polling()