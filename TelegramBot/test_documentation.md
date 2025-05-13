# Documentación de Pruebas Unitarias

Este documento describe las pruebas unitarias realizadas para el archivo `demo.py` del bot de Telegram del Ayuntamiento de Madrid. Las pruebas verifican la funcionalidad de la función `analizar_mensaje_con_openai`, que clasifica mensajes de usuarios en **avisos** o **peticiones** basándose en los diccionarios proporcionados.

## Objetivo de las Pruebas

El objetivo principal de las pruebas es garantizar que:

1. La función `analizar_mensaje_con_openai` clasifique correctamente los mensajes en **avisos** o **peticiones**.
2. Las categorías y subcategorías sean validadas según los diccionarios `AVISOS_PRUEBA` y `PETICIONES_PRUEBA`.
3. La función maneje adecuadamente casos válidos e inválidos.
4. Las respuestas simuladas de OpenAI sean procesadas correctamente.

## Estructura de las Pruebas

Las pruebas están implementadas en el archivo `test_demo.py` utilizando el módulo `unittest` de Python. Se utiliza `AsyncMock` para simular las respuestas de OpenAI.

### Pruebas Implementadas

#### 1. `test_analizar_mensaje_con_openai_valido`
- **Descripción**: Verifica que la función clasifique correctamente un mensaje válido como un **aviso**.
- **Simulación**: Respuesta de OpenAI con tipo `aviso`, categoría `Alumbrado Público` y subcategoría `Farola Apagada`.
- **Entrada**: `"Quiero reportar una farola rota"`
- **Validaciones**:
  - El resultado no es `None`.
  - El tipo es `aviso`.
  - La categoría es `Alumbrado Público`.
  - La subcategoría es `Farola Apagada`.

#### 2. `test_analizar_mensaje_con_openai_invalido`
- **Descripción**: Verifica que la función maneje correctamente un mensaje irrelevante.
- **Simulación**: Respuesta vacía de OpenAI (`{}`).
- **Entrada**: `"Mensaje irrelevante"`
- **Validaciones**:
  - El resultado es `None`.

#### 3. `test_analizar_mensaje_con_openai_aviso`
- **Descripción**: Verifica que la función clasifique correctamente un mensaje como un **aviso**.
- **Simulación**: Respuesta de OpenAI con tipo `aviso`, categoría `Alumbrado Público` y subcategoría `Farola Apagada`.
- **Entrada**: `"Hay una farola apagada en mi calle"`
- **Validaciones**:
  - El resultado no es `None`.
  - El tipo es `aviso`.
  - La categoría es `Alumbrado Público`.
  - La subcategoría es `Farola Apagada`.

#### 4. `test_analizar_mensaje_con_openai_peticion`
- **Descripción**: Verifica que la función clasifique correctamente un mensaje como una **petición**.
- **Simulación**: Respuesta de OpenAI con tipo `petición`, categoría `Mobiliario Urbano` y subcategoría `Nueva Instalación`.
- **Entrada**: `"Quiero solicitar un banco nuevo en el parque"`
- **Validaciones**:
  - El resultado no es `None`.
  - El tipo es `petición`.
  - La categoría es `Mobiliario Urbano`.
  - La subcategoría es `Nueva Instalación`.

## Ejecución de las Pruebas

Para ejecutar las pruebas, utiliza el siguiente comando en la terminal:

```bash
python -m unittest test_demo.py
```

## Resultados Esperados

Todas las pruebas deben pasar sin errores, indicando que la función `analizar_mensaje_con_openai` funciona correctamente para los casos probados.

## Conclusión

Las pruebas unitarias garantizan que la función `analizar_mensaje_con_openai` clasifique correctamente los mensajes de los usuarios y maneje adecuadamente los casos válidos e inválidos. Esto asegura la calidad y confiabilidad del bot de Telegram.
