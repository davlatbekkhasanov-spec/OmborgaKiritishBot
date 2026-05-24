from aiogram import Router

from handlers import callbacks, commands, finish_flow


def setup_routers() -> Router:
    root = Router()
    root.include_router(commands.router)
    root.include_router(callbacks.router)
    root.include_router(finish_flow.router)
    return root
