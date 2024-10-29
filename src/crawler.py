import asyncio
import aiohttp
from selectolax.parser import HTMLParser
import re
import logging
from src.database import DatabaseManager
from src.notifier import Notifier
from urllib.parse import urlparse, urlunparse
from typing import List


class Job:
    def __init__(
        self,
        category: str,
        title: str,
        url: str,
        posted_at: str,
        price: str,
        job_type: str,
        duration: str,
        experience_level: str,
        description: str,
    ):
        self.category = category
        self.title = title
        self.url = url
        self.posted_at = posted_at
        self.price = price
        self.job_type = job_type
        self.duration = duration
        self.experience_level = experience_level
        self.description = description

    def to_dict(self):
        return {
            "title": self.title,
            "url": self.url,
            "posted_at": self.posted_at,
            "price": self.price,
            "job_type": self.job_type,
            "duration": self.duration,
            "experience_level": self.experience_level,
            "description": self.description,
        }

    def format_message(self):
        description_arr = self.description.split("\n")
        description = [f">{line.strip()}" for line in description_arr]
        description_str = "\n".join(description)
        message = [
            f"*{self.title} - [{self.category}]*\n",
            f"*{self.experience_level}* - {self.duration}",
            f"*Posted At:* {self.posted_at}",
            f"*Price:* {self.price if self.price else self.job_type}\n",
            "*Description*",
            f">{description_str[:300]}...",
        ]
        return {
            "message": "\n".join(message),
            "button": {
                "text": "View Job",
                "url": self.url,
            },
        }


class Crawler:
    def __init__(
        self,
        remote_host: str,
        notifier: Notifier,
        db_manager: DatabaseManager,
    ):
        self.remote_host = remote_host
        self.notifier = notifier
        self.db_manager = db_manager

    async def get_html(self, session: aiohttp.ClientSession, url: str) -> str:
        headers = {
            "Content-Type": "application/json",
        }
        data = {
            "cmd": "request.get",
            "url": url,
            "maxTimeout": 30000,
        }
        async with session.post(self.remote_host, headers=headers, json=data) as r:
            response = await r.json()

            if response["status"] != "ok" and "Timeout" not in response["message"]:
                await self.notifier.send_notification(
                    ["Error getting HTML", response["message"]]
                )
                raise Exception(f"Error: {response['message']}")
        return response["solution"]["response"]

    async def get_jobs(self, session: aiohttp.ClientSession, item: dict):
        logging.info(f"Processing category: {item['name']}")
        html = await self.get_html(session, item["url"])
        doc = HTMLParser(html)
        articles = doc.css("article")

        for article in articles:
            posted_at = article.css_first(".job-tile-header small").text().strip()
            title = article.css_first(".job-tile-header h2").text().strip()
            title = self.sanitize(title)
            job_url = article.css_first(".job-tile-header h2 a").attributes.get("href")
            job_url = self.complete_url(job_url)
            job_type = article.css_first("[data-test=job-type-label]").text().strip()
            experience_level = article.css_first("[data-test=experience-level]").text()
            duration = article.css_first("[data-test=duration-label]")
            duration = self.sanitize(duration.text().strip()) if duration else None
            description = article.css_first("p.text-body-sm").text().strip()
            price = article.css_first("[data-test=is-fixed-price]")
            price = price.text() if price else None

            if (
                not self.contains_terms_to_avoid(posted_at)
                and self.db_manager.get_job(job_url) is None
            ):
                job = Job(
                    item["name"],
                    title,
                    job_url,
                    posted_at,
                    price,
                    job_type,
                    duration,
                    experience_level,
                    description,
                )
                self.db_manager.save_job(job)

                # Send notification to telegram
                fmt_message = job.format_message()
                await self.notifier.send_notification(
                    fmt_message["message"], fmt_message["button"]
                )

    @staticmethod
    def contains_terms_to_avoid(text: str) -> bool:
        terms_to_avoid = ["last week", "days ago", "weeks ago"]
        return any(term in text.lower() for term in terms_to_avoid)

    @staticmethod
    def sanitize(text: str) -> str:
        cleaned_text = re.sub(r"\n|\t", "", text)
        return re.sub(r"\s+", " ", cleaned_text)

    @staticmethod
    def complete_url(url: str) -> str:
        base_url = "https://www.upwork.com"
        parsed_url = urlparse(base_url + url)
        return urlunparse(parsed_url._replace(query=""))

    async def process_urls(self, urls: List[str]) -> None:
        async with aiohttp.ClientSession() as session:
            tasks = [self.get_jobs(session, url) for url in urls]
            await asyncio.gather(*tasks)
