from openai import OpenAI, OpenAIError

from app.application.errors import TextToSpeechError


class WebTextToSpeech:
    def __init__(
        self,
        *,
        client: OpenAI,
        model: str = "gpt-4o-mini-tts",
        voice: str = "alloy",
    ):
        self.client = client
        self.model = model
        self.voice = voice

    def synthesize_to_bytes(self, text: str) -> bytes:
        try:
            response = self.client.audio.speech.create(
                model=self.model,
                voice=self.voice,
                input=text,
                response_format="mp3",
            )
            return response.read()
        except OpenAIError as e:
            raise TextToSpeechError(str(e)) from e
