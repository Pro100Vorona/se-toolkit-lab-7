"""Telegram bot entry point with --test mode.

Usage:
    uv run bot.py --test "/start"    # Test mode - prints response to stdout
    uv run bot.py                    # Normal mode - connects to Telegram
"""

import sys
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from handlers.slash.commands import (
    handle_start,
    handle_help,
    handle_health,
    handle_labs,
    handle_scores,
)
from handlers.intent_router import route_intent
from config import load_config


# Command router - maps commands to handler functions
COMMANDS = {
    "/start": handle_start,
    "/help": handle_help,
    "/health": handle_health,
    "/labs": handle_labs,
    "/scores": handle_scores,
}


async def process_command(command: str) -> str:
    """Route a command to the appropriate handler and return the response."""
    # Parse command and arguments
    parts = command.strip().split(maxsplit=1)
    cmd = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""

    if cmd in COMMANDS:
        handler = COMMANDS[cmd]
        return await handler(args)
    elif cmd.startswith("/"):
        return f"Unknown command: {cmd}. Use /help to see available commands."
    else:
        # Not a command - route to LLM intent router
        return await route_intent(command)


def run_test_mode(command: str) -> None:
    """Run a command in test mode - print response to stdout."""
    config = load_config()
    response = asyncio.run(process_command(command))
    print(response)


async def telegram_handler(message: types.Message, command: str = None) -> None:
    """Handle a Telegram message by routing to the appropriate handler."""
    text = message.text or ""
    
    # Check if it's a slash command
    if text.startswith("/"):
        if command:
            # Known command - route to slash handler
            full_command = text
            response = await process_command(full_command)
            
            # Send with keyboard for /start
            if command == "/start":
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="📚 Available Labs", callback_data="labs")],
                    [InlineKeyboardButton(text="🏥 Health Check", callback_data="health")],
                    [InlineKeyboardButton(text="📊 Scores", callback_data="scores")],
                    [InlineKeyboardButton(text="❓ Help", callback_data="help")],
                ])
                await message.answer(response, reply_markup=keyboard)
                return
        else:
            # Unknown command
            response = f"Unknown command: {text}. Use /help to see available commands."
    else:
        # Plain text - route to LLM intent router
        response = await route_intent(text)
    
    await message.answer(response)


async def run_telegram_bot() -> None:
    """Run the Telegram bot."""
    config = load_config()

    if not config["BOT_TOKEN"]:
        print("Error: BOT_TOKEN not found in .env.bot.secret")
        print("Please set BOT_TOKEN in .env.bot.secret to run the bot.")
        sys.exit(1)

    # Set up logging
    logging.basicConfig(level=logging.INFO)

    # Create bot and dispatcher
    bot = Bot(token=config["BOT_TOKEN"])
    dp = Dispatcher()

    # Register command handlers
    dp.message(Command("start"))(lambda msg: telegram_handler(msg, "/start"))
    dp.message(Command("help"))(lambda msg: telegram_handler(msg, "/help"))
    dp.message(Command("health"))(lambda msg: telegram_handler(msg, "/health"))
    dp.message(Command("labs"))(lambda msg: telegram_handler(msg, "/labs"))
    dp.message(Command("scores"))(lambda msg: telegram_handler(msg, "/scores"))
    
    # Register handler for plain text messages (non-commands)
    dp.message()(lambda msg: telegram_handler(msg))

    # Start polling
    print("Bot is running... Press Ctrl+C to stop.")
    await dp.start_polling(bot)


def run_telegram_mode() -> None:
    """Run the bot in Telegram mode - connect to Telegram API."""
    asyncio.run(run_telegram_bot())


def main() -> None:
    """Main entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        if len(sys.argv) < 3:
            print("Usage: uv run bot.py --test '<command>'")
            print("Example: uv run bot.py --test '/start'")
            sys.exit(1)
        command = sys.argv[2]
        run_test_mode(command)
    else:
        run_telegram_mode()


if __name__ == "__main__":
    main()
