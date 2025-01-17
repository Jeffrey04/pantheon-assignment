import asyncio
import hashlib
import hmac
import time
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from functools import reduce
from itertools import chain
from os import environ

import httpx
import structlog
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI

app = FastAPI()
logger = structlog.get_logger()
load_dotenv()


class Source(Enum):
    UNSPLASH = "Unsplash"
    STORYBLOCKS = "Storyblocks"
    PIXABAY = "Pixabay"


@dataclass
class Image:
    image_id: str  # the ID of the image
    thumbnails: str  # thumbnails url of the image
    preview: str  # preview url of the image
    title: str  # title/description of the image
    source: Source  # which image library you get this image from? [Unsplash, Storyblocks, Pixabay]
    tags: Sequence[str]  # the tag/keywords of the images (if any)


@app.get("/search")
async def search(search_term: str) -> Sequence[Image]:
    tasks = []
    async with httpx.AsyncClient() as client, asyncio.TaskGroup() as tg:
        tasks.append(tg.create_task(_search_unsplash(client, search_term)))
        tasks.append(tg.create_task(_search_pixabay(client, search_term)))
        tasks.append(tg.create_task(_search_storyblocks(client, search_term)))

    return tuple(chain.from_iterable(task.result() for task in tasks))


async def _search_unsplash(
    client: httpx.AsyncClient, search_term: str
) -> Sequence[Image]:
    response = await client.get(
        "https://api.unsplash.com/search/photos",
        headers={
            "Accept-Version": "v1",
            "Authorization": f"Client-ID {environ.get('UNSPLASH_ACCESS', 'TEST-KEY')}",
        },
        params={"query": search_term},
    )

    if response.status_code == 200:
        return reduce(
            lambda current, incoming: current
            + (
                Image(
                    incoming["id"],
                    incoming["urls"]["thumb"],
                    incoming["urls"]["regular"],
                    incoming["description"],
                    Source.UNSPLASH,
                    (),
                ),
            ),
            response.json().get("results", []),
            (),
        )

    else:
        raise Exception("Search failed")


async def _search_pixabay(
    client: httpx.AsyncClient, search_term: str
) -> Sequence[Image]:
    response = await client.get(
        "https://pixabay.com/api/",
        params={"key": environ.get("PIXABAY_KEY", "TEST-KEY"), "q": search_term},
    )

    if response.status_code == 200:
        return reduce(
            lambda current, incoming: current
            + (
                Image(
                    str(incoming["id"]),
                    incoming["previewURL"],
                    incoming["webformatURL"],
                    incoming["tags"],
                    Source.PIXABAY,
                    tuple(tag.strip() for tag in incoming.get("tags", "").split(",")),
                ),
            ),
            response.json().get("hits", []),
            (),
        )

    else:
        raise Exception("Search failed")


async def _search_storyblocks(
    client: httpx.AsyncClient, search_term: str
) -> Sequence[Image]:
    expires = int(time.time()) + 10
    resource = "/api/v2/images/search"

    response = await client.get(
        f"https://api.storyblocks.com{resource}",
        params={
            "APIKEY": environ.get("STORYBLOCKS_PUBLIC", "TEST-PUBLIC"),
            "EXPIRES": expires,
            "HMAC": hmac.new(
                bytearray(
                    environ.get("STORYBLOCKS_PRIVATE", "TEST-PRIVATE") + str(expires),
                    "utf-8",
                ),
                resource.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest(),
            "keywords": search_term,
            "user_id": "PANTHEON_PROJECT:API_USER",
            "project_id": "PANTHEON_PROJECT",
        },
    )

    if response.status_code == 200:
        return reduce(
            lambda current, incoming: current
            + (
                Image(
                    str(incoming["id"]),
                    incoming["thumbnail_url"],
                    incoming["preview_url"],
                    incoming["title"],
                    Source.STORYBLOCKS,
                    (),
                ),
            ),
            response.json().get("results", []),
            (),
        )

    else:
        print(response.read())
        raise Exception("Search failed")


def main() -> None:
    uvicorn.run(app, host="0.0.0.0", port=8081)
