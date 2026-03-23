"""Command handlers - pure functions that take input and return text.

These handlers don't know about Telegram. They're just functions you can call
from --test mode, from unit tests, or from the Telegram bot.
This is *separation of concerns* - business logic separate from transport layer.
"""

from services.lms_client import LMSClient
from config import load_config


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
    config = load_config()
    client = LMSClient(config["LMS_API_URL"], config["LMS_API_KEY"])
    try:
        result = await client.health_check()
        if result["status"] == "healthy":
            return f"Backend is healthy. {result.get('item_count', 0)} items available."
        else:
            return f"Backend error: {result.get('error', 'Unknown error')}"
    finally:
        await client.close()


async def handle_labs(user_input: str) -> str:
    """Handle /labs command."""
    config = load_config()
    client = LMSClient(config["LMS_API_URL"], config["LMS_API_KEY"])
    try:
        result = await client.get_labs()
        if "error" in result:
            return f"Error fetching labs: {result['error']}"
        labs = result.get("labs", [])
        if not labs:
            return "No labs available."
        return "Available labs:\n" + "\n".join(f"- {lab}" for lab in labs)
    finally:
        await client.close()


async def handle_scores(user_input: str) -> str:
    """Handle /scores command."""
    # user_input is just the arguments (e.g., "lab-04"), not the full command
    lab = user_input.strip()
    if not lab:
        return "Usage: /scores <lab-name>. Example: /scores lab-01"
    
    config = load_config()
    client = LMSClient(config["LMS_API_URL"], config["LMS_API_KEY"])
    try:
        result = await client.get_scores(lab)
        if "error" in result:
            return f"Error fetching scores: {result['error']}"
        scores = result.get("scores", [])
        if not scores:
            return f"No scores found for {lab}"
        
        lines = [f"Pass rates for {lab}:"]
        for score in scores:
            task = score.get("task", "Unknown")
            rate = score.get("pass_rate", 0)
            attempts = score.get("attempts", 0)
            lines.append(f"- {task}: {rate:.1f}% ({attempts} attempts)")
        return "\n".join(lines)
    finally:
        await client.close()
