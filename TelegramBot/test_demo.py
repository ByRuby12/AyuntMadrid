import unittest
from unittest.mock import AsyncMock, patch
from demo import analizar_mensaje_con_openai

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

if __name__ == "__main__":
    unittest.main()