import json
import asyncio
import os
from dotenv import load_dotenv
from src.crawler import Crawler
from src.database import DatabaseManager
from src.notifier import Notifier
import logging

load_dotenv()
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
REMOTE_HOST = os.getenv("FLARESOLVER_ENDPOINT")
NOTIFICATION_ENDPOINT = os.getenv("NOTIFICATION_ENDPOINT")
DB_PATH = os.getenv("DB_PATH", "jobs.db")


async def main():
    if not REMOTE_HOST or not NOTIFICATION_ENDPOINT:
        raise ValueError(
            "FLARESOLVER_ENDPOINT or NOTIFICATION_ENDPOINT are not set in .env file"
        )

    db_manager = DatabaseManager(DB_PATH)
    notification_sender = Notifier(NOTIFICATION_ENDPOINT)
    crawler = Crawler(REMOTE_HOST, notification_sender, db_manager)

    # read urls from urls.json
    with open("urls.json") as f:
        urls = json.load(f)

    await crawler.process_urls(urls)


if __name__ == "__main__":
    asyncio.run(main())
