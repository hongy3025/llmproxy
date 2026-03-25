"""
代理服务入口模块。

负责初始化 FastAPI 应用，设置生命周期事件（如启动时初始化依赖，关闭时清理资源），
并注册各业务路由。
"""

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
    """
    FastAPI 生命周期管理函数。

    在应用启动时初始化全局资源（如槽位管理器），在关闭时释放 HTTP 客户端等资源。

    Args:
        app (FastAPI): FastAPI 应用实例。
    """
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
