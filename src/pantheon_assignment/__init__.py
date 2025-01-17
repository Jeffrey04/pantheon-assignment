import asyncio
import hashlib
import hmac
import os
import pickle
import sqlite3
import time
from ast import literal_eval
from collections.abc import Sequence
from contextlib import asynccontextmanager, suppress
from dataclasses import dataclass
from enum import Enum
from functools import reduce
from itertools import chain
from os import environ
from typing import Annotated, Literal

import httpx
import jwt
import structlog
import uvicorn
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.hash import argon2

DATABASE_DEFAULT = "./database.sqlite"


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

@dataclass
class User:
    name: str
    password: str


@dataclass
class Token:
    name: str
    token: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Resetting table")

    with suppress(FileNotFoundError):
        os.remove(environ.get("DATABASE", DATABASE_DEFAULT))

    conn = await _database_connect()

    logger.info("Resetting database")
    conn.execute(
        """
        CREATE TABLE user (
            name TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE search (
            search_term TEXT NOT NULL UNIQUE,
            result TEXT NOT NULL
        );
        """
    )
    conn.close()
    yield


app = FastAPI(lifespan=lifespan)
logger = structlog.get_logger()
load_dotenv()


async def _database_connect() -> sqlite3.Connection:
    conn = sqlite3.connect(environ.get("DATABASE", DATABASE_DEFAULT))

    if conn.execute("PRAGMA journal_mode=WAL;").fetchone()[0] != "wal":
        raise Exception("Unable to initialize database")

    return conn


async def _get_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(HTTPBearer())],
    conn: Annotated[sqlite3.Connection, Depends(_database_connect)],
) -> str:
    try:
        user = jwt.decode(
            credentials.credentials, environ.get("JWT_SECRET", "JWT-SECRET"), "HS256"
        )
        cur = conn.execute(
            """
            SELECT  password
            FROM    user
            WHERE   name = ?
            """,
            (user["name"],),
        )

        if (data := cur.fetchone()) and argon2.verify(user["password"], data[0]):
            return user["name"]

        else:
            raise Exception("Unable to authenticate user")

    except Exception as e:
        logger.exception(e)

        raise HTTPException(403, "Unable to authenticate user") from e


@app.post("/register")
async def register(
    user: User,
    conn: Annotated[sqlite3.Connection, Depends(_database_connect)],
) -> Token:
    conn.execute(
        """
        INSERT
        INTO    user (name, password)
        VALUES  (?, ?)
        """,
        (user.name, argon2.hash(user.password)),
    )
    conn.commit()

    return Token(
        user.name,
        jwt.encode(
            {"name": user.name, "password": user.password},
            environ.get("JWT_SECRET", "JWT-SECRET"),
            "HS256",
        ),
    )


@app.get("/search")
async def search(
    search_term: str,
    conn: Annotated[sqlite3.Connection, Depends(_database_connect)],
    current_user: Annotated[str, Security(_get_user)],
) -> Sequence[Image]:
    if _check_is_cache_result():
        if result := _search_cache(conn, search_term):
            return result

    tasks = []
    async with httpx.AsyncClient() as client, asyncio.TaskGroup() as tg:
        tasks.append(tg.create_task(_search_unsplash(client, search_term)))
        tasks.append(tg.create_task(_search_pixabay(client, search_term)))
        tasks.append(
            tg.create_task(_search_storyblocks(client, search_term, current_user))
        )

    result = tuple(chain.from_iterable(task.result() for task in tasks))

    if _check_is_cache_result():
        _cache_result(conn, search_term, result)

    conn.commit()

    return result


def _check_is_cache_result() -> bool:
    try:
        return literal_eval(environ.get("CACHE_RESULT", "False"))
    except Exception:
        return False


def _search_cache(
    conn: sqlite3.Connection, search_term: str
) -> Sequence[Image] | Literal[False]:
    logger.info("Fetching result from cache", search_term=search_term)
    cur = conn.execute(
        """
        SELECT  result
        FROM    search
        WHERE   search_term = ?
        """,
        (search_term,),
    )

    if result := cur.fetchone():
        return pickle.loads(result[0])
    else:
        return False


def _cache_result(
    conn: sqlite3.Connection, search_term: str, result: Sequence[Image]
) -> None:
    logger.info("Caching result", search_term=search_term)

    conn.execute(
        """
        INSERT
        INTO    search (search_term, result)
        VALUES  (?, ?)
        """,
        (search_term, pickle.dumps(result)),
    )


async def _search_unsplash(
    client: httpx.AsyncClient, search_term: str
) -> Sequence[Image]:
    logger.info("Fetching result from unsplash", search_term=search_term)

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
    logger.info("Fetching result from pixabay", search_term=search_term)

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
    client: httpx.AsyncClient, search_term: str, current_user: str
) -> Sequence[Image]:
    logger.info("Fetching result from storyblocks", search_term=search_term)

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
            "user_id": f"PANTHEON_PROJECT:{current_user}",
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
