"""
Keyboards for Carpool Telegram Bot.
"""

from typing import List, Dict, Any
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton
)


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Main menu persistent reply keyboard."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚗 Offer a Ride"), KeyboardButton(text="🔍 Search Rides")],
            [KeyboardButton(text="📋 Available Rides"), KeyboardButton(text="ℹ️ Help")],
        ],
        resize_keyboard=True
    )


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Keyboard shown during FSM flows to easily abort."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Cancel Operation")]
        ],
        resize_keyboard=True
    )


def build_rides_list_keyboard(rides: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """
    Construct inline keyboard listing available rides as clickable buttons.
    """
    buttons = []
    for ride in rides:
        dep = ride['departure_location']
        arr = ride['arrival_location']
        time_str = ride['time'].strftime('%H:%M') if hasattr(ride['time'], 'strftime') else str(ride['time'])
        date_str = ride['date'].strftime('%b %d') if hasattr(ride['date'], 'strftime') else str(ride['date'])
        seats = ride['available_seats']
        btn_text = f"🚗 {dep} ➡️ {arr} | {date_str} {time_str} ({seats} 🪑)"
        buttons.append([
            InlineKeyboardButton(
                text=btn_text,
                callback_data=f"view_ride:{ride['id']}"
            )
        ])

    # Utility buttons
    buttons.append([
        InlineKeyboardButton(text="🔍 Filter by Route", callback_data="filter_rides"),
        InlineKeyboardButton(text="🔄 Refresh", callback_data="show_all_rides")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def build_ride_detail_keyboard(ride_id: int) -> InlineKeyboardMarkup:
    """
    Construct inline keyboard for viewing ride details and requesting booking.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎟️ Request to Book This Ride",
                    callback_data=f"book_ride:{ride_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Back to Available Rides",
                    callback_data="show_all_rides"
                )
            ]
        ]
    )


def build_driver_approval_keyboard(booking_id: int) -> InlineKeyboardMarkup:
    """
    Construct driver approval inline keyboard with Approve and Reject buttons.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Approve ✅",
                    callback_data=f"approve_booking:{booking_id}"
                ),
                InlineKeyboardButton(
                    text="Reject ❌",
                    callback_data=f"reject_booking:{booking_id}"
                )
            ]
        ]
    )


def build_resolved_booking_keyboard(status: str) -> InlineKeyboardMarkup:
    """
    Replaces interactive buttons once driver has made a decision.
    """
    icon = "✅ Approved" if status.upper() == 'APPROVED' else "❌ Rejected"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"Status: {icon}",
                    callback_data="booking_decision_final"
                )
            ]
        ]
    )
