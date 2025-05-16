# Documentación del Bot de Telegram para el Ayuntamiento de Madrid
Este bot ha sido realizado por ByRuby12 (Tomas Cano) durante las prácticas de Grado Superior de Desarrollo de Aplicaciones Web (DAW) en el Ayuntamiento de Madrid, distrito San Blas (IAM).

## Introducción
Este bot de Telegram está diseñado para facilitar la comunicación entre los ciudadanos y el Ayuntamiento de Madrid. Permite a los usuarios enviar reportes de problemas o solicitudes de mejora, que son clasificados automáticamente y enviados tanto a un grupo de Telegram como a la plataforma del Ayuntamiento.

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

## Conclusión
Este bot automatiza el proceso de reporte de problemas y solicitudes de mejora, facilitando la comunicación entre los ciudadanos y el Ayuntamiento de Madrid. Su diseño modular y manejo de errores lo hacen robusto y fácil de mantener.
