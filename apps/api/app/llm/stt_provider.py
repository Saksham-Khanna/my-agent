import asyncio
import io
import logging
from typing import Optional

from faster_whisper import WhisperModel
from app.core.config import settings

logger = logging.getLogger(__name__)

class STTProvider:
    """faster-whisper speech-to-text. Runs on CPU (see ADR-010)."""

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.stt_model
        self._model: Optional[WhisperModel] = None
        self._model_lock = asyncio.Lock()
        self._loaded = False

    @property
    def loaded(self) -> bool:
        return self._loaded

    async def load(self) -> WhisperModel:
        if self._model is not None:
            self._loaded = True
            return self._model
        async with self._model_lock:
            if self._model is None:
                logger.info(f"Loading faster-whisper model '{self.model_name}' on CPU...")
                # Run loading in thread to avoid blocking event loop
                self._model = await asyncio.to_thread(
                    WhisperModel,
                    self.model_name,
                    device="cpu",
                    compute_type="int8"
                )
        self._loaded = True
        return self._model

    async def unload(self) -> None:
        async with self._model_lock:
            self._model = None
            self._loaded = False

    def is_loaded(self) -> bool:
        return self._loaded

    async def transcribe(self, audio_bytes: bytes) -> str:
        """
        Transcribes audio bytes (e.g. from a WebM or WAV blob) to text.
        """
        model = await self.load()

        def _run_transcription():
            audio_io = io.BytesIO(audio_bytes)
            # faster-whisper can decode binary file-like objects using PyAV
            segments, info = model.transcribe(audio_io, beam_size=1)
            text = "".join(segment.text for segment in segments)
            return text.strip()

        try:
            text = await asyncio.to_thread(_run_transcription)
            return text
        except Exception as e:
            logger.error(f"STT transcription failed: {e}")
            raise
