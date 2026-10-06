"""
Handlers and callbacks for passenger searches, displaying available rides
as inline buttons, and initiating booking requests.
"""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from ..states import RideSearchStates
from ..keyboards import (
    build_rides_list_keyboard,
    build_ride_detail_keyboard,
    build_driver_approval_keyboard,
    get_main_menu_keyboard
)
from ...services import (
    get_available_rides,
    get_ride_details,
    create_booking_request
)

router = Router()


@router.message(Command("rides"))
@router.message(Command("search_rides"))
@router.message(F.text.in_({"🔍 Search Rides", "📋 Available Rides"}))
async def list_available_rides(message: Message, state: FSMContext):
    """
    Search and display available rides as interactive inline buttons.
    """
    await state.clear()
    rides = await get_available_rides()

    if not rides:
        await message.answer(
            "📍 <b>No Available Rides Found</b>\n\n"
            "There are currently no active rides with available seats.\n"
            "Check back later or offer a ride yourself!",
            reply_markup=get_main_menu_keyboard()
        )
        return

    await message.answer(
        f"🚗 <b>Available Rides ({len(rides)} found)</b>\n\n"
        "Click on any ride below to inspect details and request a booking:",
        reply_markup=build_rides_list_keyboard(rides)
    )


@router.callback_query(F.data == "show_all_rides")
async def cb_show_all_rides(query: CallbackQuery):
    """Callback to refresh and display all available rides."""
    await query.answer()
    rides = await get_available_rides()

    if not rides:
        await query.message.edit_text(
            "📍 <b>No Available Rides Found</b>\n\n"
            "There are currently no active rides with available seats.",
            reply_markup=None
        )
        return

    await query.message.edit_text(
        f"🚗 <b>Available Rides ({len(rides)} found)</b>\n\n"
        "Click on any ride below to view details or book:",
        reply_markup=build_rides_list_keyboard(rides)
    )


@router.callback_query(F.data == "filter_rides")
async def cb_filter_rides_prompt(query: CallbackQuery, state: FSMContext):
    """Prompt passenger for search filter keywords."""
    await query.answer()
    await state.set_state(RideSearchStates.departure_query)
    await query.message.answer(
        "🔍 <b>Search Rides by Route</b>\n\n"
        "Enter your desired <b>departure location</b> (or type <i>skip</i> to search any):"
    )


@router.message(RideSearchStates.departure_query)
async def process_search_departure(message: Message, state: FSMContext):
    """Process departure filter and ask for destination filter."""
    text = message.text.strip()
    dep_query = None if text.lower() == 'skip' else text
    await state.update_data(dep_query=dep_query)
    await state.set_state(RideSearchStates.arrival_query)
    await message.answer(
        "🏁 Now enter your desired <b>arrival destination</b> (or type <i>skip</i> to search any):"
    )


@router.message(RideSearchStates.arrival_query)
async def process_search_arrival(message: Message, state: FSMContext):
    """Execute search query and display results as inline buttons."""
    text = message.text.strip()
    arr_query = None if text.lower() == 'skip' else text

    data = await state.get_data()
    dep_query = data.get('dep_query')
    await state.clear()

    rides = await get_available_rides(departure_query=dep_query, arrival_query=arr_query)

    if not rides:
        filter_desc = []
        if dep_query:
            filter_desc.append(f"from '{dep_query}'")
        if arr_query:
            filter_desc.append(f"to '{arr_query}'")
        desc = " ".join(filter_desc) if filter_desc else "matching your criteria"

        await message.answer(
            f"❌ No rides found {desc}.\n"
            "Try a broader search or view all available rides.",
            reply_markup=get_main_menu_keyboard()
        )
        return

    await message.answer(
        f"🎯 Found <b>{len(rides)} matching ride(s)</b>:\n"
        "Select a ride to view details and request a booking:",
        reply_markup=build_rides_list_keyboard(rides)
    )


@router.callback_query(F.data.startswith("view_ride:"))
async def cb_view_ride_details(query: CallbackQuery):
    """
    Display details of selected ride with an inline button to request booking.
    """
    ride_id = int(query.data.split(":")[1])
    ride = await get_ride_details(ride_id)

    if not ride or ride['status'] != 'ACTIVE':
        await query.answer("This ride is no longer active or available.", show_alert=True)
        return

    await query.answer()

    time_str = ride['time'].strftime('%H:%M') if hasattr(ride['time'], 'strftime') else str(ride['time'])
    date_str = ride['date'].strftime('%A, %B %d, %Y') if hasattr(ride['date'], 'strftime') else str(ride['date'])
    driver_handle = f"@{ride['driver_username']}" if ride['driver_username'] else "No username"

    details_text = (
        f"🚗 <b>Ride #{ride['id']} Details</b>\n\n"
        f"<b>Route:</b> {ride['departure_location']} ➡️ {ride['arrival_location']}\n"
        f"<b>Date:</b> {date_str}\n"
        f"<b>Departure Time:</b> {time_str}\n"
        f"<b>Driver:</b> {ride['driver_name']} ({driver_handle})\n"
        f"<b>Available Seats:</b> {ride['available_seats']} of {ride['total_seats']}\n"
        f"<b>Status:</b> {ride['status']}\n\n"
        "Ready to travel? Click below to send a booking request to the driver."
    )

    await query.message.edit_text(
        details_text,
        reply_markup=build_ride_detail_keyboard(ride['id'])
    )


@router.callback_query(F.data.startswith("book_ride:"))
async def cb_book_ride(query: CallbackQuery):
    """
    Process passenger booking request and notify the driver with approval buttons.
    """
    ride_id = int(query.data.split(":")[1])
    passenger_id = query.from_user.id
    passenger_name = query.from_user.full_name or query.from_user.first_name
    passenger_username = query.from_user.username

    success, msg, booking_data = await create_booking_request(
        ride_id=ride_id,
        passenger_telegram_id=passenger_id,
        passenger_name=passenger_name,
        passenger_username=passenger_username,
        seats_booked=1
    )

    if not success:
        await query.answer(msg, show_alert=True)
        return

    await query.answer("Booking request submitted!", show_alert=False)

    # Update passenger UI
    confirmation_text = (
        f"⏳ <b>Booking Request Sent!</b>\n\n"
        f"<b>Booking ID:</b> #{booking_data['id']}\n"
        f"<b>Ride:</b> #{booking_data['ride_id']} ({booking_data['departure']} ➡️ {booking_data['arrival']})\n"
        f"<b>Date:</b> {booking_data['date']} at {booking_data['time']}\n"
        f"<b>Status:</b> 🟡 Pending Driver Approval\n\n"
        "The driver has been notified with your request. You will receive an immediate update once they respond."
    )
    await query.message.edit_text(confirmation_text)

    # Send approval request to driver with inline buttons
    bot = query.bot
    driver_notification = (
        f"🔔 <b>New Passenger Booking Request!</b>\n\n"
        f"<b>Booking ID:</b> #{booking_data['id']}\n"
        f"<b>Passenger:</b> {passenger_name} "
        f"({'@' + passenger_username if passenger_username else '(no username)'})\n"
        f"<b>Ride:</b> #{booking_data['ride_id']} ({booking_data['departure']} ➡️ {booking_data['arrival']})\n"
        f"<b>Schedule:</b> {booking_data['date']} at {booking_data['time']}\n"
        f"<b>Seats Requested:</b> {booking_data['seats_booked']}\n\n"
        "Please accept or decline this passenger's request:"
    )

    try:
        await bot.send_message(
            chat_id=booking_data['driver_telegram_id'],
            text=driver_notification,
            reply_markup=build_driver_approval_keyboard(booking_data['id'])
        )
    except Exception as e:
        # If driver hasn't initiated chat with bot or bot cannot reach them
        pass
