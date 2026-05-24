from aiogram import Router

from handlers import callbacks, commands, finish_flow, webapp_scan


def setup_routers() -> Router:
    root = Router()
    root.include_router(commands.router)
    root.include_router(callbacks.router)
    root.include_router(finish_flow.router)
    root.include_router(webapp_scan.router)
    return root
