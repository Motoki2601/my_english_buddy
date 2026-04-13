import io

from openai import OpenAI, OpenAIError

from app.application.errors import SpeechToTextError


class WebSpeechToText:
    def __init__(
        self,
        *,
        client: OpenAI,
        model: str = "gpt-4o-mini-transcribe",
    ):
        self.client = client
        self.model = model

    def transcribe_bytes(self, audio_bytes: bytes, mime_type: str = "audio/webm") -> str:
        if not audio_bytes:
            return ""

        ext = self._ext_for_mime(mime_type)
        try:
            response = self.client.audio.transcriptions.create(
                file=(f"audio.{ext}", io.BytesIO(audio_bytes)),
                model=self.model,
            )
            return response.text.strip()
        except OpenAIError as e:
            raise SpeechToTextError(str(e)) from e

    @staticmethod
    def _ext_for_mime(mime_type: str) -> str:
        if "webm" in mime_type:
            return "webm"
        if "mp4" in mime_type or "m4a" in mime_type:
            return "mp4"
        if "ogg" in mime_type:
            return "ogg"
        if "wav" in mime_type:
            return "wav"
        return "webm"
