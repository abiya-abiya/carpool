"""
Router aggregation for Carpool Telegram Bot handlers.
"""

from aiogram import Router
from .common import router as common_router
from .ride_creation import router as ride_creation_router
from .search_and_book import router as search_and_book_router
from .driver_approval import router as driver_approval_router


def setup_routers() -> Router:
    """Combines all sub-routers into a master router."""
    master_router = Router()
    master_router.include_router(common_router)
    master_router.include_router(ride_creation_router)
    master_router.include_router(search_and_book_router)
    master_router.include_router(driver_approval_router)
    return master_router
