import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from demo import analizar_mensaje_con_openai, recibir_descripcion_foto

class TestDemo(unittest.IsolatedAsyncioTestCase):
    @patch("demo.openai.ChatCompletion.create", new_callable=AsyncMock)
    async def test_analizar_mensaje_con_openai_valido(self, mock_openai):
        # Simular respuesta válida de OpenAI
        mock_openai.return_value = {
            "choices": [{"message": {"content": '{"tipo": "aviso", "categoría": "Alumbrado Público", "subcategoría": "Farola Apagada"}'}}]
        }

        mensaje = "Quiero reportar una farola rota"
        resultado = await analizar_mensaje_con_openai(mensaje)

        # Verificar que el resultado sea correcto
        self.assertIsNotNone(resultado)
        self.assertEqual(resultado["tipo"], "aviso")
        self.assertEqual(resultado["categoría"], "Alumbrado Público")
        self.assertEqual(resultado["subcategoría"], "Farola Apagada")

    @patch("demo.openai.ChatCompletion.create", new_callable=AsyncMock)
    async def test_analizar_mensaje_con_openai_invalido(self, mock_openai):
        # Simular respuesta inválida de OpenAI
        mock_openai.return_value = {
            "choices": [{"message": {"content": '{}'}}]
        }

        mensaje = "Mensaje irrelevante"
        resultado = await analizar_mensaje_con_openai(mensaje)

        # Verificar que el resultado sea None
        self.assertIsNone(resultado)

    @patch("demo.openai.ChatCompletion.create", new_callable=AsyncMock)
    async def test_analizar_mensaje_con_openai_aviso(self, mock_openai):
        # Simular respuesta válida de OpenAI para un aviso
        mock_openai.return_value = {
            "choices": [{"message": {"content": '{"tipo": "aviso", "categoría": "Alumbrado Público", "subcategoría": "Farola Apagada"}'}}]
        }

        mensaje = "Hay una farola apagada en mi calle"
        resultado = await analizar_mensaje_con_openai(mensaje)

        # Verificar que el resultado sea correcto
        self.assertIsNotNone(resultado)
        self.assertEqual(resultado["tipo"], "aviso")
        self.assertEqual(resultado["categoría"], "Alumbrado Público")
        self.assertEqual(resultado["subcategoría"], "Farola Apagada")

    @patch("demo.openai.ChatCompletion.create", new_callable=AsyncMock)
    async def test_analizar_mensaje_con_openai_peticion(self, mock_openai):
        # Simular respuesta válida de OpenAI para una petición
        mock_openai.return_value = {
            "choices": [{"message": {"content": '{"tipo": "petición", "categoría": "Mobiliario Urbano", "subcategoría": "Nueva Instalación"}'}}]
        }

        mensaje = "Quiero solicitar un banco nuevo en el parque"
        resultado = await analizar_mensaje_con_openai(mensaje)

        # Verificar que el resultado sea correcto
        self.assertIsNotNone(resultado)
        self.assertEqual(resultado["tipo"], "petición")
        self.assertEqual(resultado["categoría"], "Mobiliario Urbano")
        self.assertEqual(resultado["subcategoría"], "Nueva Instalación")

class TestFlujoDescripcionFoto(unittest.IsolatedAsyncioTestCase):
    @patch("demo.analizar_imagen_con_openai", new_callable=AsyncMock)
    async def test_insistencia_foto_no_valida(self, mock_analizar_imagen):
        # Simula que OpenAI nunca clasifica la imagen (siempre devuelve None)
        mock_analizar_imagen.return_value = None

        update = MagicMock()
        update.message.photo = [MagicMock()]
        update.message.text = None
        update.message.reply_text = AsyncMock()
        update.message.photo[-1].get_file = AsyncMock(return_value=MagicMock(download_to_drive=AsyncMock()))
        context = MagicMock()
        context.user_data = {"idioma": "es"}

        estado = await recibir_descripcion_foto(update, context)
        self.assertEqual(estado, 1001)
        update.message.reply_text.assert_awaited_with(
            "No he podido reconocer el contenido de la foto. Puedes volver a intentarlo enviando otra foto o describiendo el problema:",
            parse_mode="Markdown"
        )

    @patch("demo.analizar_mensaje_con_openai", new_callable=AsyncMock)
    async def test_insistencia_texto_no_valido(self, mock_analizar_mensaje):
        # Simula que OpenAI nunca clasifica el texto (siempre devuelve None)
        mock_analizar_mensaje.return_value = None

        update = MagicMock()
        update.message.photo = None
        update.message.text = "Hola, esto es un mensaje irrelevante en español"
        update.message.reply_text = AsyncMock()
        context = MagicMock()
        context.user_data = {"idioma": "es"}
        context.bot.send_chat_action = AsyncMock()

        estado = await recibir_descripcion_foto(update, context)
        self.assertEqual(estado, -1)
        update.message.reply_text.assert_awaited_with(
            "🌐 Puedes hablarme en español, inglés, francés, alemán, chino o portugués. El bot detecta automáticamente el idioma y te responderá en ese idioma.",
            parse_mode="Markdown"
        )

class TestTraducirAEspanol(unittest.IsolatedAsyncioTestCase):
    @patch("demo.openai.ChatCompletion.acreate", new_callable=AsyncMock)
    async def test_traducir_a_espanol_ingles(self, mock_acreate):
        from demo import traducir_a_espanol
        mock_acreate.return_value = {
            "choices": [{"message": {"content": "Esto es una prueba."}}]
        }
        texto = "This is a test."
        resultado = await traducir_a_espanol(texto, "en")
        self.assertEqual(resultado, "Esto es una prueba.")

    @patch("demo.openai.ChatCompletion.acreate", new_callable=AsyncMock)
    async def test_traducir_a_espanol_espanol(self, mock_acreate):
        from demo import traducir_a_espanol
        texto = "Esto ya está en español."
        resultado = await traducir_a_espanol(texto, "es")
        self.assertEqual(resultado, texto)

class TestManejarFotoInicial(unittest.IsolatedAsyncioTestCase):
    @patch("demo.analizar_imagen_con_openai", new_callable=AsyncMock)
    async def test_foto_valida_avanza(self, mock_analizar_imagen):
        from demo import manejar_foto_inicial, BOT_TEXTS, ESPERANDO_UBICACION
        mock_analizar_imagen.return_value = {
            "tipo": "aviso",
            "categoría": "Alumbrado Público",
            "subcategoría": "Farola Apagada",
            "descripcion": "Una farola está apagada."
        }
        update = MagicMock()
        update.message.photo = [MagicMock()]
        update.message.reply_text = AsyncMock()
        update.message.photo[-1].get_file = AsyncMock(return_value=MagicMock(download_to_drive=AsyncMock()))
        context = MagicMock()
        context.user_data = {}
        context.bot.send_chat_action = AsyncMock()
        estado = await manejar_foto_inicial(update, context)
        self.assertEqual(estado, ESPERANDO_UBICACION)

    @patch("demo.analizar_imagen_con_openai", new_callable=AsyncMock)
    async def test_foto_invalida_insiste(self, mock_analizar_imagen):
        from demo import manejar_foto_inicial
        mock_analizar_imagen.return_value = None
        update = MagicMock()
        update.message.photo = [MagicMock()]
        update.message.reply_text = AsyncMock()
        update.message.photo[-1].get_file = AsyncMock(return_value=MagicMock(download_to_drive=AsyncMock()))
        context = MagicMock()
        context.user_data = {}
        context.bot.send_chat_action = AsyncMock()  # <-- Añadido para evitar error de await
        estado = await manejar_foto_inicial(update, context)
        self.assertEqual(estado, 1001)
        update.message.reply_text.assert_awaited_with(
            "No he podido reconocer el contenido de la foto. Por favor, describe brevemente el problema para poder clasificarlo:",
            parse_mode="Markdown"
        )

class TestManejarMensaje(unittest.IsolatedAsyncioTestCase):
    @patch("demo.analizar_mensaje_con_openai", new_callable=AsyncMock)
    async def test_manejar_mensaje_no_clasificado(self, mock_analizar):
        from demo import manejar_mensaje, WELCOME_MESSAGES
        mock_analizar.return_value = None
        update = MagicMock()
        update.message.from_user.id = 123
        update.message.text = "Hola, esto es un mensaje irrelevante en español"
        update.message.reply_text = AsyncMock()
        context = MagicMock()
        context.user_data = {"idioma": "es"}
        context.bot.send_chat_action = AsyncMock()
        # El bot debe responder con los mensajes de bienvenida
        await manejar_mensaje(update, context)
        # Comprobar que se han enviado los mensajes de bienvenida (sin la línea de idioma)
        mensajes = [call.args[0] for call in update.message.reply_text.await_args_list]
        for texto in WELCOME_MESSAGES['es']:
            if "idioma del bot" not in texto:
                self.assertIn(texto, mensajes)

    @patch("demo.analizar_mensaje_con_openai", new_callable=AsyncMock)
    async def test_manejar_mensaje_clasificado(self, mock_analizar):
        from demo import manejar_mensaje, BOT_TEXTS, ESPERANDO_UBICACION
        mock_analizar.return_value = {
            "tipo": "aviso",
            "categoría": "Alumbrado Público",
            "subcategoría": "Farola Apagada"
        }
        update = MagicMock()
        update.message.from_user.id = 123
        update.message.text = "Hola, quiero reportar una farola rota en mi calle"
        update.message.reply_text = AsyncMock()
        context = MagicMock()
        context.user_data = {"idioma": "es"}
        context.bot.send_chat_action = AsyncMock()  # <-- Añadido para evitar error de await
        estado = await manejar_mensaje(update, context)
        self.assertEqual(estado, ESPERANDO_UBICACION)
        # Comprobar que se ha pedido ubicación
        # Se comprueba que se haya enviado algún mensaje de tipo 'send_location'
        mensajes = [call.args[0] for call in update.message.reply_text.await_args_list]
        self.assertIn(BOT_TEXTS['es']['send_location'], mensajes)

class TestAnalizarImagenConOpenAI(unittest.IsolatedAsyncioTestCase):
    @patch("builtins.open", new_callable=unittest.mock.mock_open, read_data=b"fakeimage")
    @patch("demo.openai.ChatCompletion.acreate", new_callable=AsyncMock)
    async def test_analizar_imagen_con_openai_valida(self, mock_acreate, mock_open):
        from demo import analizar_imagen_con_openai
        mock_acreate.return_value = {
            "choices": [{"message": {"content": '{"tipo": "aviso", "categoría": "Alumbrado Público", "subcategoría": "Farola Apagada", "descripcion": "Una farola rota"}'}}]
        }
        resultado = await analizar_imagen_con_openai("fakepath.jpg")
        self.assertIsNotNone(resultado)
        self.assertEqual(resultado["tipo"], "aviso")
        self.assertEqual(resultado["categoría"], "Alumbrado Público")
        self.assertEqual(resultado["subcategoría"], "Farola Apagada")
        self.assertEqual(resultado["descripcion"], "Una farola rota")

    @patch("builtins.open", new_callable=unittest.mock.mock_open, read_data=b"fakeimage")
    @patch("demo.openai.ChatCompletion.acreate", new_callable=AsyncMock)
    async def test_analizar_imagen_con_openai_invalida(self, mock_acreate, mock_open):
        from demo import analizar_imagen_con_openai
        mock_acreate.return_value = {
            "choices": [{"message": {"content": '{}'}}]
        }
        resultado = await analizar_imagen_con_openai("fakepath.jpg")
        self.assertIsNone(resultado)

if __name__ == "__main__":
    unittest.main()