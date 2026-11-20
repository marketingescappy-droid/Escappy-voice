import json
from collections.abc import Sequence

from openai import APIConnectionError, APIError, APIStatusError, OpenAI

from escappy.config import OpenAISettings
from escappy.integrations import ChatMessage, CreativeNote

INSTRUCTIONS = (
    "Eres el asistente editorial de Instagram de Escappy Travel. Responde en español. "
    "Usa el historial y las pautas relevantes de la memoria para atender la petición. "
    "Cuando apliques una pauta de un estudio, indica el hallazgo y la fuente si constan "
    "en la memoria. Distingue observaciones, preferencias e hipótesis. Si faltan datos, "
    "dilo. Tus capacidades son redactar y revisar contenido en esta conversación."
)


class ChatError(Exception):
    """Mensaje de error que puede mostrarse en la interfaz."""


class OpenAIChatProvider:
    def __init__(self, settings: OpenAISettings):
        self.settings = settings

    def reply(self, history: Sequence[ChatMessage], memory: Sequence[CreativeNote]) -> str:
        messages = []
        if memory:
            notes = [{"tipo": note.kind, "contenido": note.content} for note in memory]
            messages.append({
                "role": "user",
                "content": "Memoria creativa del equipo:\n" + json.dumps(notes, ensure_ascii=False),
            })
        messages.extend({"role": item.role, "content": item.content} for item in history)
        try:
            with OpenAI(api_key=self.settings.api_key, base_url="https://api.openai.com/v1",
                        timeout=60.0, max_retries=0) as client:
                response = client.responses.create(
                    model=self.settings.model, instructions=INSTRUCTIONS,
                    input=messages, store=False,
                )
        except APIConnectionError:
            raise ChatError("No se pudo contactar con OpenAI. Comprueba tu conexión y reintenta.") from None
        except APIStatusError as error:
            details = {
                400: "Revisa el modelo y la longitud de la conversación y la memoria.",
                401: "Revisa la clave OPENAI_API_KEY.",
                403: "Comprueba los permisos del proyecto y del modelo.",
                404: "Comprueba que el modelo configurado está disponible en tu proyecto.",
                429: "Revisa el saldo y los límites de uso de tu proyecto antes de reintentar.",
            }
            advice = details.get(error.status_code, "Vuelve a intentarlo más tarde.")
            raise ChatError(f"OpenAI devolvió el código {error.status_code}. {advice}") from None
        except APIError:
            raise ChatError("La API de OpenAI devolvió una respuesta inesperada.") from None

        text = response.output_text.strip()
        if response.status != "completed" or not text:
            raise ChatError("OpenAI no devolvió una respuesta de texto completa. Puedes reformular la petición.")
        return text
