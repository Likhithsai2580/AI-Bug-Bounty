import asyncio
import telegram
from discord_webhook import DiscordWebhook, DiscordEmbed
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, DISCORD_WEBHOOK_URL

class TelegramNotifier:
    def __init__(self):
        self.bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)

    async def send_message(self, message):
        await self.bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

    async def send_file(self, file_path, caption):
        with open(file_path, 'rb') as file:
            await self.bot.send_document(chat_id=TELEGRAM_CHAT_ID, document=file, caption=caption)

class DiscordNotifier:
    def __init__(self):
        self.webhook_url = DISCORD_WEBHOOK_URL

    def send_message(self, message):
        webhook = DiscordWebhook(url=self.webhook_url, content=message)
        webhook.execute()

    def send_file(self, file_path, caption):
        with open(file_path, "rb") as file:
            webhook = DiscordWebhook(url=self.webhook_url, content=caption)
            webhook.add_file(file=file.read(), filename=file_path.split("/")[-1])
            webhook.execute()

class NotificationManager:
    def __init__(self):
        self.telegram = TelegramNotifier()
        self.discord = DiscordNotifier()

    async def notify(self, message, file_path=None):
        tasks = [
            asyncio.create_task(self.telegram.send_message(message)),
            asyncio.create_task(asyncio.to_thread(self.discord.send_message, message))
        ]
        if file_path:
            tasks.extend([
                asyncio.create_task(self.telegram.send_file(file_path, message)),
                asyncio.create_task(asyncio.to_thread(self.discord.send_file, file_path, message))
            ])
        await asyncio.gather(*tasks)