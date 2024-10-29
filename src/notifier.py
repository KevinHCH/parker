import aiohttp
import logging


class Notifier:
    def __init__(self, notification_endpoint: str):
        self.notification_endpoint = notification_endpoint

    async def send_notification(self, message: str, button: dict) -> None:
        data = {"message": message, "enqueue": False}
        if button:
            data["button"] = button

        async with aiohttp.ClientSession() as session:
            headers = {
                "Content-Type": "application/json",
            }
            async with session.post(
                self.notification_endpoint + "/message", json=data, headers=headers
            ) as r:
                if r.status != 200:
                    logging.error(f"Error sending notification: {await r.text()}")
                    logging.error(f"Data: {data}")
