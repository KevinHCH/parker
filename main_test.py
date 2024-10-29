import asyncio
import aiohttp
from dotenv import load_dotenv
import os
from typing import List
from selectolax.parser import HTMLParser
import re
from urllib.parse import urlparse, urlunparse
import hashlib
import json
import logging

load_dotenv()

REMOTE_HOST = os.getenv("FLARESOLVER_ENDPOINT")
NOTIFICATION_ENDPOINT = os.getenv("NOTIFICATION_ENDPOINT")


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


def write_file(file_name: str, data: str) -> None:
    with open(file_name, "w") as f:
        f.write(data)


async def send_notification(message: str, button: dict) -> None:
    data = {"message": message, "button": button, "enqueue": False}
    async with aiohttp.ClientSession() as session:
        headers = {
            "Content-Type": "application/json",
        }
        async with session.post(
            NOTIFICATION_ENDPOINT + "/message", json=data, headers=headers
        ) as r:
            if r.status != 200:
                logging.error(f"Error sending notification: {await r.text()}")
                logging.error(f"Data: {data}")


async def get_html(session: aiohttp.ClientSession, url: str) -> str:
    headers = {
        "Content-Type": "application/json",
    }
    data = {
        "cmd": "request.get",
        "url": url,
        "maxTimeout": 30000,
    }
    async with session.post(REMOTE_HOST, headers=headers, json=data) as r:
        response = await r.json()

        if response["status"] != "ok" and "Timeout" not in response["message"]:
            await send_notification(["Error getting HTML", response["message"]])
            raise Exception(f"Error: {response['message']}")
    return response["solution"]["response"]


async def get_jobs(session: aiohttp.ClientSession, item: dict) -> List[Job]:
    print(f"Processing URL: {item['url']}")
    html = await get_html(session, item["url"])
    job_offers = []
    doc = HTMLParser(html)
    articles = doc.css("article")

    for article in articles:
        posted_at = article.css_first(".job-tile-header small").text().strip()
        title = article.css_first(".job-tile-header h2").text().strip()
        title = sanitize(title)
        job_url = article.css_first(".job-tile-header h2 a").attributes.get("href")
        job_url = complete_url(job_url)
        job_type = article.css_first("[data-test=job-type-label]").text().strip()
        experience_level = article.css_first("[data-test=experience-level]").text()
        duration = article.css_first("[data-test=duration-label]")
        duration = sanitize(duration.text().strip()) if duration else None
        description = article.css_first("p.text-body-sm").text().strip()
        price = article.css_first("[data-test=is-fixed-price]")
        price = price.text() if price else None

        if not contains_terms_to_avoid(posted_at):
            # Create a Job object
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
            job_offers.append(job)

            # Send notification for the job
            fmt_message = job.format_message()
            await send_notification(fmt_message["message"], fmt_message["button"])

    return job_offers


def contains_terms_to_avoid(text: str) -> bool:
    terms_to_avoid = ["last week", "days ago", "weeks ago"]
    return any(term in text.lower() for term in terms_to_avoid)


def sanitize(text: str) -> str:
    cleaned_text = re.sub(r"\n|\t", "", text)
    return re.sub(r"\s+", " ", cleaned_text)


def complete_url(url: str) -> str:
    base_url = "https://www.upwork.com"
    parsed_url = urlparse(base_url + url)
    return urlunparse(parsed_url._replace(query=""))


def hash(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()


async def process_urls(urls: List[str]) -> None:
    async with aiohttp.ClientSession() as session:
        tasks = [get_jobs(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
        # Flatten the results if needed
        all_jobs = [job for sublist in results for job in sublist]
        write_file(
            "jobs.json", json.dumps([job.to_dict() for job in all_jobs], indent=2)
        )


def main() -> None:
    urls = [
        {
            "name": "aws",
            "url": "https://www.upwork.com/nx/search/jobs/?amount=200-&client_hires=1-9,10-&contractor_tier=1,2,3&hourly_rate=35-&location=Northern%20America,Northern%20Europe,South-Eastern%20Asia,Southern%20Europe,Western%20Asia,Western%20Europe&payment_verified=1&proposals=0-4,5-9&q=aws&sort=recency&t=0,1",
        }
    ]
    asyncio.run(process_urls(urls))


if __name__ == "__main__":
    main()
