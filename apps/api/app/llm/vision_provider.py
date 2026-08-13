import httpx
from app.core.config import settings

class VisionProvider:
    """
    Ollama Vision Provider for local image analysis.
    Uses Ollama's /api/generate endpoint with image payloads.
    """

    def __init__(self, base_url: str = None, model: str = None):
        self.base_url = base_url or settings.ollama_base_url
        self.model = model or settings.vision_model
        self._loaded = False

    async def _post_keep_alive(self, keep_alive: str) -> None:
        """Send a minimal generation request to pin or release the model."""
        url = f"{self.base_url}/api/generate"
        payload = {"model": self.model, "prompt": "", "stream": False, "keep_alive": keep_alive}
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=60.0)
            response.raise_for_status()

    async def load(self) -> None:
        """Pin the vision model into memory until explicitly unloaded."""
        if self._loaded:
            return
        await self._post_keep_alive("-1")
        self._loaded = True

    async def unload(self) -> None:
        """Release the vision model from memory immediately."""
        if not self._loaded:
            return
        try:
            await self._post_keep_alive("0")
        finally:
            self._loaded = False

    def is_loaded(self) -> bool:
        return self._loaded

    async def analyze(self, image_b64: str, prompt: str = "Describe this image in detail.") -> str:
        """
        Sends an image to Ollama for analysis and returns the textual description.
        """
        # Clean base64 data prefix if present (e.g. data:image/png;base64,...)
        if "," in image_b64:
            image_b64 = image_b64.split(",", 1)[1]

        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "images": [image_b64],
            "stream": False
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, timeout=60.0)
                response.raise_for_status()
                data = response.json()
                return data.get("response", "").strip()
            except httpx.HTTPError as e:
                raise RuntimeError(f"Error communicating with Ollama Vision model ({self.model}): {e}")
