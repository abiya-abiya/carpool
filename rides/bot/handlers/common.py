"""
Common command handlers: /start, /help, and cancel.
"""

from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from ..keyboards import get_main_menu_keyboard

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Welcome message and main menu."""
    await state.clear()
    user_name = message.from_user.first_name if message.from_user else "there"
    welcome_text = (
        f"👋 Hello, <b>{user_name}</b>!\n\n"
        "Welcome to the <b>Carpool Bot</b> 🚗💨\n\n"
        "Here is what you can do:\n"
        "• <b>Offer a Ride</b>: Share your travel route and take passengers\n"
        "• <b>Search Rides</b>: Find upcoming rides and request a seat\n"
        "• <b>Driver Approvals</b>: Drivers approve or reject passenger booking requests\n\n"
        "Use the menu below or commands like /create_ride and /rides to get started!"
    )
    await message.answer(welcome_text, reply_markup=get_main_menu_keyboard())


@router.message(Command("help"))
@router.message(F.text == "ℹ️ Help")
async def cmd_help(message: Message):
    """Help documentation for users."""
    help_text = (
        "<b>📖 Carpool Bot Help & Commands</b>\n\n"
        "<b>For Drivers:</b>\n"
        "• /create_ride — Start step-by-step ride creation (departure, arrival, time, seats)\n"
        "• You will receive instant notifications when passengers request to book your ride with <b>Approve/Reject</b> buttons.\n\n"
        "<b>For Passengers:</b>\n"
        "• /rides or /search_rides — Browse available rides with clickable inline buttons\n"
        "• Click on a ride to view details and send a booking request to the driver\n"
        "• You will be notified as soon as the driver accepts or rejects your request\n\n"
        "<b>General:</b>\n"
        "• /cancel — Cancel any active multi-step operation at any time\n"
    )
    await message.answer(help_text, reply_markup=get_main_menu_keyboard())


@router.message(Command("cancel"))
@router.message(F.text == "❌ Cancel Operation")
async def cmd_cancel(message: Message, state: FSMContext):
    """Abort current FSM state."""
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("There is no active operation to cancel.", reply_markup=get_main_menu_keyboard())
        return

    await state.clear()
    await message.answer("Action canceled. Returning to main menu.", reply_markup=get_main_menu_keyboard())
