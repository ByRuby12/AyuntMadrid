# -----------------------IMPORT LIBRERIAS---------------------------

from diccionarios import AVISOS_PRUEBA, PETICIONES_PRUEBA
from claves import OPENAI_API_KEY, CURAIME_BOT_KEY
from datetime import datetime
from telegram import (Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, Location)
from telegram.ext import (ApplicationBuilder, MessageHandler, filters, ContextTypes, ConversationHandler)

import nest_asyncio
import openai
import json
import os
import requests
import asyncio
import time
import re

# -------------------------------------------------------------------

nest_asyncio.apply()

# Configuración de claves
TELEGRAM_GROUP_ID = "-1002545875124"
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
os.environ["CURAIME_BOT_KEY"] = CURAIME_BOT_KEY
openai.api_key = OPENAI_API_KEY

# Etapas de conversación
ESPERANDO_UBICACION, ESPERANDO_MEDIA = range(2)

# Mensaje de sistema para OpenAI
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
    
    "⚠️ DEVUELVE SOLO UN JSON VÁLIDO. EL FORMATO DEBE SER EL SIGUIENTE:\n"
    '{"tipo": "aviso", "categoría": "Alumbrado Público", "subcategoría": "Calle Apagada"}\n\n'
    "No incluyas ningún otro texto ni explicación, solo el JSON.\n"
)

# ------------------------FUNCIONES----------------------------------

# Envía el mensaje del usuario a OpenAI para analizarlo. Si detecta que es un aviso o petición con una categoría y subcategoría 
# válidas (según los diccionarios que tienes), devuelve esa información estructurada. Si no es válido, devuelve None.
async def analizar_mensaje_con_openai(mensaje_usuario: str):
    print(f"Analizando mensaje: {mensaje_usuario}")

    prompt = [
        {"role": "system", "content": system_content_prompt},
        {"role": "user", "content": mensaje_usuario}
    ]

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=prompt,
            temperature=0.2
        )
        contenido = response.choices[0].message["content"]
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

            print("Resultado válido, retornando.")
            return resultado
        else:
            print("No se encontraron 'tipo', 'categoría' o 'subcategoría' en la respuesta de OpenAI.")
    except Exception as e:
        print("Error al analizar respuesta de OpenAI:", e)
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

    resultado = await analizar_mensaje_con_openai(mensaje)

    if not resultado or "tipo" not in resultado or "categoría" not in resultado or "subcategoría" not in resultado:
        print("Mensaje no clasificado correctamente. Respondiendo con mensaje genérico.")
        print(f"╚―――――――――――――――――――――――――――――――――――――")
        await update.message.reply_text(
            "👋 Hola, soy el bot del Ayuntamiento de Madrid.\n\n"
            "Estoy aquí para ayudarte a comunicar *avisos* y *peticiones*:\n\n"
            "🔴 *Aviso*: Cuando quieras informar de un problema, daño o incidencia en tu barrio (por ejemplo: una farola rota, ruido molesto, suciedad en la calle...).\n\n"
            "🟢 *Petición*: Cuando desees proponer una mejora o solicitar algo nuevo (por ejemplo: más bancos en un parque, nueva zona deportiva, más papeleras...).\n\n"
            "✍️ Por favor, escribe tu mensaje explicando el problema o la mejora que necesitas. Yo me encargo de clasificarlo y enviarlo al Ayuntamiento.",
            parse_mode="Markdown"
        )
        return ConversationHandler.END

    tipo = resultado["tipo"]
    categoria = resultado["categoría"]
    subcategoria = resultado["subcategoría"]
    print(f"Clasificado como: Tipo='{tipo}', Categoría='{categoria}', Subcategoría='{subcategoria}'")

    # Buscar el ID de subcategoría
    id_subcategoria = None
    fuente = AVISOS_PRUEBA if tipo.lower() == "aviso" else PETICIONES_PRUEBA

    # Verificamos que la categoría esté bien definida en el diccionario
    if categoria in fuente:
        subcategorias = fuente[categoria]
        if isinstance(subcategorias, dict):  # Si es un diccionario de subcategorías
            for subcat_key, subcat_data in subcategorias.items():
                if subcat_key.lower() == subcategoria.lower() or subcat_data["nombre"].lower() == subcategoria.lower():
                    id_subcategoria = subcat_data["id"][0] if subcat_data["id"] else None
                    break
        elif isinstance(subcategorias, list):  # Si es una lista de subcategorías
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

    boton_ubicacion = ReplyKeyboardMarkup(
        [[KeyboardButton("📍 Enviar ubicación", request_location=True)]],
        one_time_keyboard=True,
        resize_keyboard=True
    )

    print("Esperando ubicación del usuario...")

    await update.message.reply_text(
        f"✅ He detectado un {tipo} en la categoría '{categoria}' y subcategoría '{subcategoria}'.\n\n"
        "Por favor, envíame la ubicación del incidente:",
        reply_markup=boton_ubicacion
    )
    return ESPERANDO_UBICACION

# Toma la ubicación enviada por el usuario, completa los datos del reporte (incluyendo nombre, fecha y coordenadas) y los envía a 
# un grupo de Telegram formateados como mensaje. Luego confirma al usuario que el reporte ha sido enviado correctamente.
async def recibir_ubicacion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ubicacion: Location = update.message.location
    datos = context.user_data.get("reporte", {})

    if not datos:
        print("Error: No tengo datos del reporte. Finalizando conversación.")
        await update.message.reply_text("❌ No tengo datos del reporte. Inténtalo de nuevo.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    print(f"Ubicación recibida: Latitud {ubicacion.latitude}, Longitud {ubicacion.longitude}")

    datos["latitud"] = ubicacion.latitude
    datos["longitud"] = ubicacion.longitude
    datos["usuario"] = update.message.from_user.full_name
    datos["fecha"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    await update.message.reply_text(
        "📸 Si quieres, ahora puedes enviar una *foto o video* del problema. "
        "Esto puede ayudar a los equipos del Ayuntamiento.\n\n"
        "O pulsa 'Omitir' para continuar sin archivo.",
        reply_markup=ReplyKeyboardMarkup([["Omitir"]], one_time_keyboard=True, resize_keyboard=True),
        parse_mode="Markdown"
    )

    return ESPERANDO_MEDIA

# Envía el mensaje del usuario al grupo de Telegram con la información del reporte. Si el usuario envía una foto o video, lo adjunta al mensaje.
# Si el usuario decide omitir el archivo, envía el mensaje sin multimedia. Luego confirma al usuario que el reporte ha sido enviado.
# Finalmente, finaliza la conversación.
async def recibir_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    datos = context.user_data.get("reporte", {})

    if not datos:
        await update.message.reply_text("❌ No tengo datos del reporte. Inténtalo de nuevo.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    archivo = None
    tipo_media = None

    if update.message.photo:
        archivo = update.message.photo[-1].file_id  # última = mayor resolución
        tipo_media = "foto"
    elif update.message.video:
        archivo = update.message.video.file_id
        tipo_media = "video"
    elif update.message.text and update.message.text.lower() == "omitir":
        tipo_media = "omitido"
    else:
        await update.message.reply_text("❌ Por favor, envía una foto, un video o pulsa 'Omitir'.")
        return ESPERANDO_MEDIA

    mensaje_grupo = (
        f"📢 Nuevo {datos['tipo'].upper()} recibido:\n\n"
        f"👤 Usuario: {datos['usuario']}\n"
        f"🗓 Fecha: {datos['fecha']}\n"
        f"📄 Descripción: {datos['descripcion']}\n"
        f"📌 Tipo: {datos['tipo']}\n"
        f"📂 Categoría: {datos['categoria']}\n"
        f"🔖 Subcategoría: {datos['subcategoria']}\n"
        f"🔖 ID Subcategoria: `{datos['id_subcategoria']}`\n"
        f"📍 Ubicación: https://maps.google.com/?q={datos['latitud']},{datos['longitud']}"
    )

    print(f"―――――――――――――――――――――――――――――――――――――")
    print("📢 Nuevo", datos['tipo'].upper(), "recibido:\n")
    print("👤 Usuario:", datos['usuario'])
    print("📆 Fecha:", datos['fecha'])
    print("📄 Descripción:", datos['descripcion'])
    print("📌 Tipo:", datos['tipo'])
    print("📂 Categoría:", datos['categoria'])
    print("🔖 Subcategoría:", datos['subcategoria'])
    print("🔖 ID Subcategoría:", datos['id_subcategoria'])
    print("📍 Ubicación: https://maps.google.com/?q=" + str(datos['latitud']) + "," + str(datos['longitud']))
    print(f"―――――――――――――――――――――――――――――――――――――")

    print("Enviando mensaje al grupo con" + (" multimedia" if tipo_media != "omitido" else " sin multimedia"))
    print(f"╚―――――――――――――――――――――――――――――――――――――")

    if tipo_media == "foto":
        await context.bot.send_photo(chat_id=TELEGRAM_GROUP_ID, photo=archivo, caption=mensaje_grupo, parse_mode="Markdown")
    elif tipo_media == "video":
        await context.bot.send_video(chat_id=TELEGRAM_GROUP_ID, video=archivo, caption=mensaje_grupo, parse_mode="Markdown")
    else:
        await context.bot.send_message(chat_id=TELEGRAM_GROUP_ID, text=mensaje_grupo, parse_mode="Markdown")

    await update.message.reply_text(
        "✅ Tu reporte ha sido enviado al Ayuntamiento. ¡Gracias por tu colaboración!",
        reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END

# -------------------------MAIN---------------------------------------

# Inicia el bot y configura el manejador de conversación para recibir mensajes y ubicaciones.
# Cuando el usuario envía un mensaje, se analiza y se le pide la ubicación. Luego, se le pide que envíe una foto o video del problema.
# Finalmente, se envía el reporte al grupo de Telegram y se confirma al usuario que su reporte ha sido enviado.

if __name__ == '__main__':
    app = ApplicationBuilder().token(CURAIME_BOT_KEY).build()

    conversation_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensaje)],
        states={
            ESPERANDO_UBICACION: [MessageHandler(filters.LOCATION, recibir_ubicacion)],
            ESPERANDO_MEDIA: [
                MessageHandler(filters.PHOTO | filters.VIDEO | filters.TEXT, recibir_media)
            ]
        },
        fallbacks=[],
    )

    app.add_handler(conversation_handler)

    print("🤖 Bot en funcionamiento...")
    app.run_polling()
    print("🚫 Bot detenido.")