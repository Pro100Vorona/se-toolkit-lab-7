"""Inline keyboard definitions for common actions."""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Get the main menu keyboard with common actions."""
    keyboard = [
        [
            InlineKeyboardButton(text="📚 Available Labs", callback_data="labs"),
            InlineKeyboardButton(text="🏥 Health Check", callback_data="health"),
        ],
        [
            InlineKeyboardButton(text="📊 My Scores", callback_data="scores"),
            InlineKeyboardButton(text="🏆 Top Learners", callback_data="top_learners"),
        ],
        [
            InlineKeyboardButton(text="❓ Help", callback_data="help"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_lab_selection_keyboard(labs: list[str]) -> InlineKeyboardMarkup:
    """Get a keyboard with lab selection buttons."""
    keyboard = []
    row = []
    for lab in labs[:10]:  # Limit to 10 buttons
        # Extract lab number from title like "Lab 01 – Products..."
        lab_id = lab.split()[1] if lab.startswith("Lab") else lab
        row.append(InlineKeyboardButton(text=lab_id, callback_data=f"lab_{lab_id}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
