"""API routers."""
from app.routers.pages import router as pages_router
from app.routers.status import router as status_router
from app.routers.stake import router as stake_router
from app.routers.unstake import router as unstake_router
from app.routers.transfer import router as transfer_router
from app.routers.withdraw import router as withdraw_router
from app.routers.tools import router as tools_router

__all__ = [
    "pages_router",
    "status_router",
    "stake_router",
    "unstake_router",
    "transfer_router",
    "withdraw_router",
    "tools_router",
]
