import asyncio
import telegram
from discord_webhook import DiscordWebhook, DiscordEmbed
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, DISCORD_WEBHOOK_URL
import logging

logger = logging.getLogger(__name__)

class TelegramNotifier:
    def __init__(self):
        logger.debug("Initializing TelegramNotifier")
        self.bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
        logger.debug("TelegramNotifier initialized")

    async def send_message(self, message):
        logger.debug(f"Sending Telegram message: {message}")
        await self.bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.debug("Telegram message sent")

    async def send_file(self, file_path, caption):
        logger.debug(f"Sending Telegram file: {file_path} with caption: {caption}")
        with open(file_path, 'rb') as file:
            await self.bot.send_document(chat_id=TELEGRAM_CHAT_ID, document=file, caption=caption)
        logger.debug("Telegram file sent")

class DiscordNotifier:
    def __init__(self):
        logger.debug("Initializing DiscordNotifier")
        self.webhook_url = DISCORD_WEBHOOK_URL
        logger.debug("DiscordNotifier initialized")

    def send_message(self, message):
        logger.debug(f"Sending Discord message: {message}")
        webhook = DiscordWebhook(url=self.webhook_url, content=message)
        webhook.execute()
        logger.debug("Discord message sent")

    def send_file(self, file_path, caption):
        logger.debug(f"Sending Discord file: {file_path} with caption: {caption}")
        with open(file_path, "rb") as file:
            webhook = DiscordWebhook(url=self.webhook_url, content=caption)
            webhook.add_file(file=file.read(), filename=file_path.split("/")[-1])
            webhook.execute()
        logger.debug("Discord file sent")

class NotificationManager:
    def __init__(self):
        logger.debug("Initializing NotificationManager")
        self.telegram = TelegramNotifier()
        self.discord = DiscordNotifier()
        logger.debug("NotificationManager initialized")

    async def notify(self, message, file_path=None):
        logger.debug(f"Notifying with message: {message}, file_path: {file_path}")
        tasks = [
            asyncio.create_task(self.telegram.send_message(message)),
            asyncio.create_task(asyncio.to_thread(self.discord.send_message, message))
        ]
        if file_path:
            logger.debug("Adding file tasks")
            tasks.extend([
                asyncio.create_task(self.telegram.send_file(file_path, message)),
                asyncio.create_task(asyncio.to_thread(self.discord.send_file, file_path, message))
            ])
        await asyncio.gather(*tasks)
        logger.debug("All notification tasks completed")