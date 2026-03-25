import httpx
from typing import Dict, List, Any, Optional
from config import config

class LlamaServerClient:
    def __init__(self):
        # We need the root URL of llama-server since some endpoints might be at root.
        # However, usually `/slots`, `/tokenize` might be at root or under /v1 depending on llama-server setup.
        # By default llama-server puts them at the root.
        self.base_url = config.BACKEND_URL.rsplit("/v1", 1)[0] if config.BACKEND_URL.endswith("/v1") else config.BACKEND_URL
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=60.0)
        
    async def get_slots(self) -> List[Dict[str, Any]]:
        """Fetch all slots information from llama-server."""
        response = await self.client.get("/slots")
        response.raise_for_status()
        return response.json()
        
    async def save_slot(self, slot_id: int, filename: str) -> bool:
        """Save slot state to a file."""
        response = await self.client.post(f"/slots/{slot_id}?action=save", json={"filename": filename})
        response.raise_for_status()
        return True
        
    async def restore_slot(self, slot_id: int, filename: str) -> bool:
        """Restore slot state from a file."""
        response = await self.client.post(f"/slots/{slot_id}?action=restore", json={"filename": filename})
        response.raise_for_status()
        return True
        
    async def apply_template(self, messages: List[Dict[str, str]]) -> str:
        """Apply chat template to messages to get the prompt string."""
        response = await self.client.post("/apply-template", json={"messages": messages})
        response.raise_for_status()
        return response.json().get("prompt", "")

    async def tokenize(self, content: str) -> List[int]:
        """Tokenize content into an array of tokens."""
        response = await self.client.post("/tokenize", json={"content": content})
        response.raise_for_status()
        return response.json().get("tokens", [])

    async def close(self):
        await self.client.aclose()
