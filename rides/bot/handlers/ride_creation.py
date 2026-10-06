"""
FSM Handlers for driver ride creation flow.
Handles: departure -> arrival -> date -> time -> seats.
"""

from datetime import datetime, date, timedelta
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from ..states import RideCreationStates
from ..keyboards import get_main_menu_keyboard, get_cancel_keyboard
from ...services import create_ride_record

router = Router()


@router.message(Command("create_ride"))
@router.message(F.text == "🚗 Offer a Ride")
async def start_ride_creation(message: Message, state: FSMContext):
    """
    Entry point for ride creation state machine.
    Asks the driver for departure location.
    """
    await state.clear()
    await state.set_state(RideCreationStates.departure)
    await message.answer(
        "🚗 <b>Create a New Ride (Step 1 of 5)</b>\n\n"
        "📍 Please enter your <b>departure location</b> (e.g., <i>Central Station</i> or <i>Downtown Boston</i>):",
        reply_markup=get_cancel_keyboard()
    )


@router.message(RideCreationStates.departure)
async def process_departure(message: Message, state: FSMContext):
    """
    State handler: processes departure location and asks for arrival location.
    """
    departure = message.text.strip()
    if len(departure) < 2 or len(departure) > 100:
        await message.answer("⚠️ Please provide a valid departure location (2 to 100 characters):")
        return

    await state.update_data(departure=departure)
    await state.set_state(RideCreationStates.arrival)
    await message.answer(
        "🏁 <b>Destination (Step 2 of 5)</b>\n\n"
        f"Departure: <b>{departure}</b>\n\n"
        "Now, please enter your <b>arrival destination</b> (e.g., <i>JFK Airport</i> or <i>New York</i>):"
    )


@router.message(RideCreationStates.arrival)
async def process_arrival(message: Message, state: FSMContext):
    """
    State handler: processes arrival location and asks for the ride date.
    """
    arrival = message.text.strip()
    if len(arrival) < 2 or len(arrival) > 100:
        await message.answer("⚠️ Please provide a valid arrival location (2 to 100 characters):")
        return

    data = await state.get_data()
    if arrival.lower() == data.get('departure', '').lower():
        await message.answer("⚠️ Arrival location cannot be identical to departure location. Please re-enter destination:")
        return

    await state.update_data(arrival=arrival)
    await state.set_state(RideCreationStates.date)
    await message.answer(
        "📅 <b>Date of the Ride (Step 3 of 5)</b>\n\n"
        "Please enter the ride date in <b>YYYY-MM-DD</b> format (e.g., <i>2026-10-15</i>),\n"
        "or type <b>today</b> / <b>tomorrow</b>:"
    )


@router.message(RideCreationStates.date)
async def process_date(message: Message, state: FSMContext):
    """
    State handler: processes and validates date, then asks for departure time.
    """
    text = message.text.strip().lower()
    today = date.today()

    parsed_date = None
    if text == "today":
        parsed_date = today
    elif text == "tomorrow":
        parsed_date = today + timedelta(days=1)
    else:
        try:
            parsed_date = datetime.strptime(text, "%Y-%m-%d").date()
        except ValueError:
            await message.answer(
                "⚠️ Invalid date format. Please use <b>YYYY-MM-DD</b> (e.g. <i>2026-10-20</i>) "
                "or enter <i>today</i> / <i>tomorrow</i>:"
            )
            return

    if parsed_date < today:
        await message.answer("⚠️ Ride date cannot be in the past. Please enter a valid upcoming date:")
        return

    await state.update_data(ride_date=parsed_date.isoformat())
    await state.set_state(RideCreationStates.time)
    await message.answer(
        "⏰ <b>Departure Time (Step 4 of 5)</b>\n\n"
        f"Date: <b>{parsed_date.strftime('%A, %B %d, %Y')}</b>\n\n"
        "Please enter the departure time in 24-hour format <b>HH:MM</b> (e.g., <i>08:30</i> or <i>18:00</i>):"
    )


@router.message(RideCreationStates.time)
async def process_time(message: Message, state: FSMContext):
    """
    State handler: processes departure time and asks for seat count.
    """
    text = message.text.strip()
    try:
        parsed_time = datetime.strptime(text, "%H:%M").time()
    except ValueError:
        await message.answer(
            "⚠️ Invalid time format. Please enter time as <b>HH:MM</b> (e.g., <i>09:15</i> or <i>19:30</i>):"
        )
        return

    await state.update_data(ride_time=parsed_time.strftime("%H:%M"))
    await state.set_state(RideCreationStates.seats)
    await message.answer(
        "🪑 <b>Available Seats (Step 5 of 5)</b>\n\n"
        "How many passenger seats are you offering? (Enter a number from 1 to 8):"
    )


@router.message(RideCreationStates.seats)
async def process_seats(message: Message, state: FSMContext):
    """
    State handler: processes seat count, creates the Ride in database, and clears FSMContext.
    """
    text = message.text.strip()
    if not text.isdigit():
        await message.answer("⚠️ Please enter a valid number (e.g. 1, 2, 3, 4):")
        return

    seats = int(text)
    if seats < 1 or seats > 20:
        await message.answer("⚠️ Seat count must be between 1 and 20. Please re-enter:")
        return

    data = await state.get_data()
    departure = data['departure']
    arrival = data['arrival']
    ride_date = datetime.strptime(data['ride_date'], "%Y-%m-%d").date()
    ride_time = datetime.strptime(data['ride_time'], "%H:%M").time()

    driver_id = message.from_user.id
    driver_name = message.from_user.full_name or message.from_user.first_name
    driver_username = message.from_user.username

    # Persist to database
    ride = await create_ride_record(
        driver_telegram_id=driver_id,
        driver_name=driver_name,
        driver_username=driver_username,
        departure=departure,
        arrival=arrival,
        ride_date=ride_date,
        ride_time=ride_time,
        seats=seats
    )

    # Clear FSMContext
    await state.clear()

    summary_text = (
        "🎉 <b>Ride Published Successfully!</b>\n\n"
        f"<b>Ride ID:</b> #{ride.id}\n"
        f"<b>Driver:</b> {driver_name}\n"
        f"<b>Route:</b> {departure} ➡️ {arrival}\n"
        f"<b>Date:</b> {ride_date.strftime('%A, %b %d, %Y')}\n"
        f"<b>Time:</b> {ride_time.strftime('%H:%M')}\n"
        f"<b>Available Seats:</b> {seats}\n\n"
        "Passengers can now search and send you booking requests.\n"
        "You will be notified whenever someone requests a seat!"
    )
    await message.answer(summary_text, reply_markup=get_main_menu_keyboard())
