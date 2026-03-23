"""Command handlers - pure functions that take input and return text.

These handlers don't know about Telegram. They're just functions you can call
from --test mode, from unit tests, or from the Telegram bot.
This is *separation of concerns* - business logic separate from transport layer.
"""


async def handle_start(user_input: str) -> str:
    """Handle /start command."""
    return "Welcome! I'm your LMS assistant bot. Use /help to see what I can do."


async def handle_help(user_input: str) -> str:
    """Handle /help command."""
    return """Available commands:
/start - Welcome message
/help - Show this help
/health - Check backend status
/labs - List available labs
/scores <lab> - Show scores for a lab"""


async def handle_health(user_input: str) -> str:
    """Handle /health command."""
    return "Backend status: OK (placeholder)"


async def handle_labs(user_input: str) -> str:
    """Handle /labs command."""
    return "Available labs: (placeholder)"


async def handle_scores(user_input: str) -> str:
    """Handle /scores command."""
    return "Scores: (placeholder)"
