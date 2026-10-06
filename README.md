# Carpool: Django & aiogram Telegram Bot

A full-featured carpooling backend and Telegram bot built with **Django** and **aiogram 3.x**.

## Project Architecture

```
carpool/
├── manage.py                     # Django management CLI
├── carpool/                      # Core Django project package
│   ├── __init__.py
│   ├── settings.py               # Django configuration & Telegram Bot settings
│   ├── urls.py                   # Master URL routing
│   ├── asgi.py                   # ASGI config
│   └── wsgi.py                   # WSGI config
├── rides/                        # Rides application
│   ├── __init__.py
│   ├── admin.py                  # Django Admin models registration
│   ├── apps.py                   # AppConfig
│   ├── models.py                 # Ride & Booking models
│   ├── services.py               # Async DB layer bridging aiogram with Django ORM
│   ├── urls.py                   # Rides REST/JSON endpoints
│   ├── views.py                  # API endpoints
│   ├── bot/                      # aiogram Telegram Bot implementation
│   │   ├── __init__.py
│   │   ├── bot_instance.py       # Bot & Dispatcher setup with MemoryStorage
│   │   ├── states.py             # FSM States (RideCreationStates, RideSearchStates)
│   │   ├── keyboards.py          # Reply & Inline Keyboards
│   │   ├── handlers/             # Modular routers
│   │   │   ├── __init__.py       # Router aggregator
│   │   │   ├── common.py         # /start, /help, /cancel
│   │   │   ├── ride_creation.py  # FSM handlers: departure, arrival, date, time, seats
│   │   │   ├── search_and_book.py# Search callbacks, inline ride list, booking request
│   │   │   └── driver_approval.py# Driver approval/rejection callbacks
│   │   └── main.py               # Standalone bot entrypoint
│   └── management/
│       └── commands/
│           └── runbot.py         # `python manage.py runbot` command
├── requirements.txt              # Python package dependencies
└── .env.example                  # Environment configuration template
```

## Key Features

1. **Django Models (`rides/models.py`)**:
   - `Ride`: Stores driver info (Django User and/or Telegram account), departure and arrival locations, ride date, departure time, available seats, total seats, status (`ACTIVE`, `FULL`, `COMPLETED`, `CANCELLED`), and timestamps.
   - `Booking`: Links rides and passengers (Django User and/or Telegram account), booked seat count, booking status (`PENDING`, `APPROVED`, `REJECTED`, `CANCELLED`), with atomic `approve()` and `reject()` methods that automatically decrement available seats and mark the ride as `FULL` when capacity is reached.

2. **aiogram Telegram Bot with MemoryStorage (`rides/bot/`)**:
   - Uses `MemoryStorage` for `FSMContext` to track conversational states in memory.
   - **Ride Creation State Machine (`RideCreationStates`)**:
     - `departure`: Prompts and validates departure location.
     - `arrival`: Prompts and validates arrival destination.
     - `date`: Prompts and parses date (`YYYY-MM-DD`, `today`, or `tomorrow`), ensuring it's not in the past.
     - `time`: Prompts and parses departure time (`HH:MM` 24-hour format).
     - `seats`: Validates available passenger seats (1-20), saves `Ride` to the database, and confirms creation.
   - **Passenger Search & Discovery**:
     - Lists active rides as interactive inline buttons (`build_rides_list_keyboard`).
     - Supports route filtering by departure and arrival keywords.
     - Displays comprehensive ride details when an inline button is clicked.
   - **Booking Request Flow & Driver Approval**:
     - Passenger sends booking request via inline button (`book_ride:{ride_id}`).
     - Creates a `Booking` in `PENDING` state and updates passenger UI.
     - Sends a notification to the driver's Telegram chat containing ride details, passenger information, and interactive inline buttons:
       - `Approve ✅` (`callback_data="approve_booking:{booking_id}"`)
       - `Reject ❌` (`callback_data="reject_booking:{booking_id}"`)
     - When the driver clicks **Approve**:
       - Decrements `available_seats` atomically using database transaction.
       - Edits the driver's notification to show approved status.
       - Dispatches an instant confirmation message to the passenger.
     - When the driver clicks **Reject**:
       - Sets booking status to `REJECTED`.
       - Edits the driver's notification to show rejected status.
       - Dispatches a declination notification to the passenger.

## Setup and Running

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Apply Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Configure Telegram Bot Token
Set `TELEGRAM_BOT_TOKEN` in your environment or `.env` file:
```bash
export TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
```

### 4. Run the Telegram Bot
You can run the bot using either the custom Django management command:
```bash
python manage.py runbot
```
Or directly via the bot module:
```bash
python rides/bot/main.py
```

### 5. Run the Django Web / Admin Server
```bash
python manage.py createsuperuser
python manage.py runserver
```
Navigate to `http://127.0.0.1:8000/admin/` to inspect rides and bookings.
