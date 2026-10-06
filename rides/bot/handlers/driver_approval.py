"""
Handlers for driver approval / rejection inline button callbacks.
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery

from ..keyboards import build_resolved_booking_keyboard
from ...services import process_driver_approval

router = Router()


@router.callback_query(F.data.startswith("approve_booking:"))
async def cb_approve_booking(query: CallbackQuery):
    """
    Handle driver clicking 'Approve' button for a booking request.
    Decrements available seats and notifies passenger.
    """
    booking_id = int(query.data.split(":")[1])

    success, msg, data = await process_driver_approval(booking_id, approved=True)
    if not success:
        await query.answer(msg, show_alert=True)
        return

    await query.answer("Booking approved!", show_alert=False)

    # Update driver message UI
    updated_text = (
        query.message.text +
        f"\n\n<b>Decision:</b> ✅ <b>Approved</b>\n"
        f"Remaining seats on this ride: <b>{data['remaining_seats']}</b>"
    )
    await query.message.edit_text(
        updated_text,
        reply_markup=build_resolved_booking_keyboard("APPROVED")
    )

    # Notify passenger
    bot = query.bot
    passenger_notification = (
        f"🎉 <b>Booking Confirmed!</b>\n\n"
        f"Great news! Your booking request for <b>Ride #{data['ride_id']}</b> has been <b>APPROVED</b>.\n\n"
        f"<b>Route:</b> {data['departure']} ➡️ {data['arrival']}\n"
        f"<b>Schedule:</b> {data['date']} at {data['time']}\n"
        f"<b>Status:</b> ✅ Approved\n\n"
        "Please be at the pickup location on time. Have a safe journey!"
    )

    try:
        await bot.send_message(
            chat_id=data['passenger_telegram_id'],
            text=passenger_notification
        )
    except Exception:
        # Best effort notification in case user blocked bot
        pass


@router.callback_query(F.data.startswith("reject_booking:"))
async def cb_reject_booking(query: CallbackQuery):
    """
    Handle driver clicking 'Reject' button for a booking request.
    Marks booking as REJECTED and notifies passenger.
    """
    booking_id = int(query.data.split(":")[1])

    success, msg, data = await process_driver_approval(booking_id, approved=False)
    if not success:
        await query.answer(msg, show_alert=True)
        return

    await query.answer("Booking rejected.", show_alert=False)

    # Update driver message UI
    updated_text = (
        query.message.text +
        "\n\n<b>Decision:</b> ❌ <b>Rejected</b>"
    )
    await query.message.edit_text(
        updated_text,
        reply_markup=build_resolved_booking_keyboard("REJECTED")
    )

    # Notify passenger
    bot = query.bot
    passenger_notification = (
        f"❌ <b>Booking Declined</b>\n\n"
        f"Your booking request for <b>Ride #{data['ride_id']}</b> "
        f"({data['departure']} ➡️ {data['arrival']}) was declined by the driver.\n\n"
        "Feel free to search for other available rides."
    )

    try:
        await bot.send_message(
            chat_id=data['passenger_telegram_id'],
            text=passenger_notification
        )
    except Exception:
        pass


@router.callback_query(F.data == "booking_decision_final")
async def cb_booking_final(query: CallbackQuery):
    """Handle click on already resolved booking button."""
    await query.answer("This booking decision has already been finalized.", show_alert=True)
