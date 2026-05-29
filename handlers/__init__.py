from aiogram import Router

from handlers import (
    callbacks,
    commands,
    finish_flow,
    hub_test,
    private_worker,
    qr,
    start_flow,
)


def setup_routers() -> Router:
    root = Router()
    root.include_router(qr.router)
    root.include_router(private_worker.router)
    root.include_router(start_flow.router)
    root.include_router(finish_flow.router)
    root.include_router(callbacks.router)
    root.include_router(commands.router)
    root.include_router(hub_test.router)
    return root
