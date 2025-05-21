# Documentación del Bot de Telegram para el Ayuntamiento de Madrid
Este bot ha sido realizado por ByRuby12 (Tomas Cano) durante las prácticas de Grado Superior de Desarrollo de Aplicaciones Web (DAW) en el Ayuntamiento de Madrid, distrito San Blas (IAM).

## Introducción
Este bot de Telegram está diseñado para facilitar la comunicación entre los ciudadanos y el Ayuntamiento de Madrid. Permite a los usuarios enviar reportes de problemas o solicitudes de mejora, que son clasificados automáticamente y enviados tanto a un grupo de Telegram como a la plataforma del Ayuntamiento.

## Características principales

- Multilingüe: responde en español, inglés, francés, alemán, chino o portugués según la preferencia del usuario. El usuario puede cambiar el idioma en cualquier momento enviando el nombre del idioma (por ejemplo, "español", "inglés", etc.).
- Clasificación automática: utiliza OpenAI para clasificar los mensajes como "aviso" (incidencia) o "petición" (solicitud de mejora), y asigna la categoría y subcategoría correspondiente según los diccionarios oficiales del Ayuntamiento.
- Conversación guiada: el bot guía al usuario paso a paso para enviar la ubicación y, opcionalmente, una foto o vídeo del problema.
- Mensajes personalizados: todos los mensajes del flujo (confirmación, solicitud de ubicación, solicitud de foto/vídeo, seguimiento, errores, etc.) se muestran en el idioma seleccionado por el usuario.
- Envío a la plataforma municipal: los reportes se envían tanto a un grupo de Telegram como a la plataforma oficial del Ayuntamiento de Madrid.
- Manejo de errores: mensajes claros si el reporte no se puede clasificar, si la ubicación está fuera de Madrid, o si hay errores en el envío.

## Ejemplo de flujo de usuario

1. El usuario inicia la conversación y puede cambiar el idioma enviando el nombre del idioma.
2. El usuario describe un problema o hace una petición.
3. El bot clasifica el mensaje y responde en el idioma seleccionado, indicando el tipo, categoría y subcategoría detectados.
4. El bot solicita la ubicación del incidente.
5. El bot solicita una foto, vídeo o permite omitir este paso.
6. El bot envía el reporte al grupo de Telegram y a la plataforma municipal, mostrando un mensaje de seguimiento y confirmación en el idioma del usuario.

## Ejemplo de conversación

A continuación se muestra un ejemplo de interacción con el bot en español y en inglés:

**Usuario:** Hola, hay una farola rota en mi calle

**Bot:**
✅ He detectado un aviso en la categoría 'Alumbrado Público' y subcategoría 'Farola Apagada'.
Por favor, envíame la ubicación del incidente:

**Usuario:** (envía ubicación)

**Bot:**
📸 Si quieres, ahora puedes enviar una *foto o video* del problema. Esto puede ayudar a los equipos del Ayuntamiento.
O pulsa 'Omitir' para continuar sin archivo.

**Usuario:** (envía foto o pulsa Omitir)

**Bot:**
📋 Reporte Seguimiento: 123456789
👤 Usuario: `Nombre Apellido`
📌 Tipo: Aviso
📂 Categoría: Alumbrado Público
🔖 Subcategoría: Farola Apagada
🗺️ Dirección: 40.4168 -3.7038
💬 Descripción: Hola, hay una farola rota en mi calle
✅ Tu reporte ha sido enviado correctamente a la Plataforma del Ayuntamiento de Madrid

---

**Usuario:** english

**Bot:**
👋 Hi! I am the official bot of Madrid City Council. I'm here to help you report any issue or suggestion about the city🏛️
... (resto del mensaje de bienvenida en inglés)

**Usuario:** There is a lot of trash in the park

**Bot:**
✅ I have detected a aviso in category 'Limpieza Viaria' and subcategory 'Basura Acumulada.'
Please send me the location of the incident:

**Usuario:** (sends location)

**Bot:**
📸 If you want, you can now send a *photo or video* of the issue. This can help the City Council teams.
Or press 'Skip' to continue without a file.

**Usuario:** (sends photo or presses Skip)

**Bot:**
📋 Report Follow-up: 987654321
👤 User: `John Doe`
📌 Type: Aviso
📂 Category: Limpieza Viaria
🔖 Subcategory: Basura Acumulada
🗺️ Address: 40.4168 -3.7038
💬 Description: There is a lot of trash in the park
✅ Your report has been successfully sent to the Madrid City Council platform

---

El bot adapta todos los mensajes a cualquiera de los idiomas soportados según la preferencia del usuario.

## Diccionarios y clasificación

El bot utiliza diccionarios oficiales (`AVISOS_PRUEBA` y `PETICIONES_PRUEBA`) para validar categorías y subcategorías. La clasificación se realiza mediante la API de OpenAI, que responde siempre en español para garantizar la correspondencia exacta con los diccionarios.

## Multilingüismo y cambio de idioma

- El idioma de la conversación se puede cambiar en cualquier momento enviando el nombre del idioma (por ejemplo, "francés").
- El idioma seleccionado se mantiene durante toda la conversación, y todos los mensajes del bot se adaptan automáticamente.
- Idiomas soportados: español, inglés, francés, alemán, chino, portugués.

## Estructura del Código
El código está dividido en varias secciones principales:

1. **Importación de Librerías y Configuración Inicial**
2. **Definición de Estados y Mensajes del Bot**
3. **Funciones Principales**
4. **Configuración del Manejador de Conversación**
5. **Ejecución del Bot**

### 1. Importación de Librerías y Configuración Inicial
Se importan las librerías necesarias, incluyendo `telegram` y `telegram.ext` para la interacción con la API de Telegram, y otras librerías como `datetime` y `json` para el manejo de datos. También se configuran las claves necesarias para la API de Telegram y OpenAI.

```python
from telegram import (Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, Location)
from telegram.ext import (ApplicationBuilder, MessageHandler, filters, ContextTypes, ConversationHandler)
from datetime import datetime
import json
import os
```

Se definen variables globales como `TELEGRAM_GROUP_ID` para el ID del grupo de Telegram y las etapas de la conversación (`ESPERANDO_UBICACION`, `ESPERANDO_MEDIA`).

### 2. Definición de Estados y Mensajes del Bot
El bot utiliza un manejador de conversación (`ConversationHandler`) para gestionar los diferentes estados de interacción con el usuario:

- **ESPERANDO_UBICACION**: El bot espera que el usuario envíe su ubicación.
- **ESPERANDO_MEDIA**: El bot espera que el usuario envíe una foto, video o elija omitir.

### 3. Funciones Principales

#### 3.1 `analizar_mensaje_con_openai`
Esta función utiliza la API de OpenAI para analizar el mensaje del usuario y clasificarlo como un "aviso" o "petición". También identifica la categoría y subcategoría del reporte.

- **Entrada**: Mensaje del usuario.
- **Salida**: Un diccionario con el tipo, categoría y subcategoría, o `None` si no se puede clasificar.

#### 3.2 `manejar_mensaje`
Recibe el mensaje inicial del usuario, lo analiza con `analizar_mensaje_con_openai` y solicita la ubicación si el mensaje es válido.

- **Entrada**: Mensaje del usuario.
- **Salida**: Solicitud de ubicación o mensaje de error.

#### 3.3 `recibir_ubicacion`
Recibe la ubicación del usuario, completa los datos del reporte y solicita una foto, video o la opción de omitir.

- **Entrada**: Ubicación del usuario.
- **Salida**: Solicitud de foto, video o confirmación de omisión.

#### 3.4 `recibir_media`
Recibe la foto, video o la decisión de omitir del usuario. Luego, envía el reporte al grupo de Telegram y a la plataforma del Ayuntamiento.

- **Entrada**: Foto, video o texto del usuario.
- **Salida**: Confirmación de envío del reporte.

### 4. Configuración del Manejador de Conversación
El manejador de conversación define los puntos de entrada, estados y salidas de la interacción con el bot.

```python
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
```

### 5. Ejecución del Bot
El bot se inicia utilizando `ApplicationBuilder` y se configura para ejecutar el manejador de conversación.

```python
if __name__ == '__main__':
    app = ApplicationBuilder().token(CURAIME_BOT_KEY).build()
    app.add_handler(conversation_handler)
    print("🤖 Bot en funcionamiento...")
    app.run_polling()
    print("🚫 Bot detenido.")
```

## Flujo de Trabajo
1. **Inicio**: El usuario envía un mensaje describiendo un problema o solicitud.
2. **Clasificación**: El mensaje se analiza y clasifica como "aviso" o "petición".
3. **Ubicación**: El bot solicita la ubicación del incidente.
4. **Media**: El bot solicita una foto, video o permite omitir.
5. **Envío**: El reporte se envía al grupo de Telegram y a la plataforma del Ayuntamiento.

## Detalles Técnicos

### Envío a la Plataforma del Ayuntamiento
El reporte se envía a la plataforma del Ayuntamiento mediante una solicitud HTTP POST. El payload incluye información como:

- Descripción del problema.
- Coordenadas de ubicación.
- Categoría y subcategoría del reporte.

```python
payload = {
    "service_id": "591b36544e4ea839018b4653",
    "description": datos["descripcion"],
    "position": {
       "lat": datos["latitud"],
       "lng": datos["longitud"],
        "location_additional_data": [
            {"question": "5e49c26b6d4af6ac018b4623", "value": "Avenida"},
            ...
        ]
    },
    "address_string": "Calle Mayor, 12",
    "device_type": "5922cfab4e4ea823178b4568",
    "additionalData": [
        {"question": "5e49c26b6d4af6ac018b45d2", "value": "Malos olores"}
    ]
}
```

### Manejo de Errores
El bot incluye manejo de errores para:

- Fallos en la clasificación del mensaje.
- Errores al enviar el reporte a la plataforma del Ayuntamiento.

## Pruebas unitarias

El archivo `test_demo.py` incluye pruebas unitarias para la función de clasificación y el flujo principal del bot. Puedes ejecutarlas con:

```bash
python -m unittest test_demo.py
```

## Dependencias

- python-telegram-bot
- openai
- requests
- asyncio
- nest_asyncio

## Notas de seguridad

- Las claves de API deben mantenerse en el archivo `claves.py` y nunca subirse a repositorios públicos.

## Autor

Bot realizado por ByRuby12 (Tomas Cano) durante las prácticas de Grado Superior de Desarrollo de Aplicaciones Web (DAW) en el Ayuntamiento de Madrid, distrito San Blas (IAM).
