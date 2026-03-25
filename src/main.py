from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from config import config
from dependencies import llama_client, root_client, root_url, slot_manager
from logger_setup import setup_logger
from routers import chat

# Initialize logger
setup_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Proxying requests to: {config.BACKEND_URL}")
    logger.info(f"Root proxying to: {root_url}")
    logger.info(f"Listening on: {config.LISTEN_HOST}:{config.LISTEN_PORT}")
    await slot_manager.initialize_slots()
    yield
    await root_client.aclose()
    await llama_client.close()
    logger.info("Proxy server shutting down.")


app = FastAPI(title="OpenAI Proxy Service", lifespan=lifespan)

app.include_router(chat.router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=config.LISTEN_HOST, port=config.LISTEN_PORT)
