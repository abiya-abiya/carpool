"""
FSM States for the Carpool Telegram Bot.
"""

from aiogram.fsm.state import State, StatesGroup


class RideCreationStates(StatesGroup):
    """
    FSM state machine for driver ride creation flow.
    Handles departure, arrival, date, departure time, and seat count.
    """
    departure = State()
    arrival = State()
    date = State()
    time = State()
    seats = State()


class RideSearchStates(StatesGroup):
    """
    FSM state machine for passenger search filtering.
    """
    departure_query = State()
    arrival_query = State()
