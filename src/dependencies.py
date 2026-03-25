import httpx

from config import config
from llama_client import LlamaServerClient
from slot_manager import SlotManager

# Initialize HTTP clients
root_url = config.BACKEND_URL.rsplit("/v1", 1)[0]
root_client = httpx.AsyncClient(base_url=root_url, timeout=600.0, trust_env=False)

llama_client = LlamaServerClient()
slot_manager = SlotManager(llama_client)
