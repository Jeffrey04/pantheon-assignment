# Pantheon Backend Engineer Assignment

## Setting up

### Configuration

The application expects the following configuration to be made available as environment variables, or through usage of a dotenv (`.env`) file.

```
UNSPLASH_APP_ID=<UNSPLASH APP ID>
UNSPLASH_ACCESS=<UNSPLASH ACCESS CODE>
UNSPLASH_SECRET=<UNSPLASH SECRET CODE>

PIXABAY_KEY=<PIXABAY KEY>

STORYBLOCKS_PUBLIC=<STORYBLOCKS PUBLIC KEY>
STORYBLOCKS_PRIVATE=<STORYBLOCKS PRIVATE KEY>

DATABASE=/app/database/database.sqlite
CACHE_RESULT=True

JWT_SECRET=<JWT SECRET KEY>
```

### Setting up with Docker

A docker image is made available at `ghcr.io/jeffrey04/pantheon-assignment:dev`, or you can proceed to build with

```
podman build -t jeffrey04/pantheon-assignment:dev -f ./podman/Dockerfile .
```

Assuming the environment variables are saved in a dotenv file named `.env`, you can start the server by using (ensure the `DATABASE` environment variable matches the `--volume` mount)

```
podman run jeffrey04/pantheon-assignment:dev --env_file .env --volume=./database:/app/database --publish=0.0.0.0:8081:8081
```

The application should now be accessible at `http://localhost:8081`, check out the API docs at `http://localhost:8081/docs`.

You can refer to the `docker-compose.yml.sample` to create a compose file for your environment. Please note that the database will reset itself on every run.


### Setting up with Python

For this, you will need the project manager [uv](https://github.com/astral-sh/uv).

Once `uv` is installed, install the project by

```
uv sync
```

Then run the project by

```
uv run pantheon-assignment
```

The application should now be accessible at `http://localhost:8081`, check out the API docs at `http://localhost:8081/docs`.


## Usage Guide

### Authentication

Register yourself through `POST /register` with the following fields passed to the body as JSON serialized object

* `name`: Your user name
* `password`: Your password

In return you will get an object with the following fields

* `name`: Your user name
* `token`: The JWT token you need to pass through the `Authorization` header for search requests

#### Example (with httpie-like `xh` client)

```
$ http localhost:8081/register --json name=foo password=bar
HTTP/1.1 200 OK
Content-Length: 148
Content-Type: application/json
Date: Fri, 17 Jan 2025 17:22:52 GMT
Server: uvicorn
{
    "name": "foo",
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoiZm9vIiwicGFzc3dvcmQiOiJiYXIifQ.k0-sVR_MKXEFa9ryAth_qLmV86MY79Gw5VPYy4pvlAU"
}
```


### Search

In order to authenticate yourself, you need to pass an `Authorization` header as follows

`Authorization: Bearer <YOUR TOKEN>`

Please refer to the previous section to register yourself to get a token.

Search is served via the endpoint `GET /search`. The endpoint expects a query string parameter named `search_term` where the value is a string containing the desired query.


#### Example (with httpie-like `xh` client)

```
$ http localhost:8081/search search_term==cat "Authorization:Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoiZm9vIiwicGFzc3dvcmQiOiJiYXIifQ.k0-sVR_MKXEFa9ryAth_qLmV86MY79Gw5VPYy4pvlAU"
HTTP/1.1 200 OK
Content-Length: 31863
Content-Type: application/json
Date: Mon, 20 Jan 2025 09:44:12 GMT
Server: uvicorn

[
    {
        "image_id": "IFxjDdqK_0U",
        "thumbnails": "https://images.unsplash.com/photo-1472491235688-bdc81a63246e?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w2OTgwMzZ8MHwxfHNlYXJjaHwxfHxjYXR8ZW58MHx8fHwxNzM3MzY2MjEzfDA&ixlib=rb-4.0.3&q=80&w=200",
        "preview": "https://images.unsplash.com/photo-1472491235688-bdc81a63246e?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w2OTgwMzZ8MHwxfHNlYXJjaHwxfHxjYXR8ZW58MHx8fHwxNzM3MzY2MjEzfDA&ixlib=rb-4.0.3&q=80&w=1080",
        "title": "Startled blue-eyed cat",
        "source": "Unsplash",
        "tags": []
    },
    {
        "image_id": "9UUoGaaHtNE",
        "thumbnails": "https://images.unsplash.com/photo-1511044568932-338cba0ad803?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w2OTgwMzZ8MHwxfHNlYXJjaHwyfHxjYXR8ZW58MHx8fHwxNzM3MzY2MjEzfDA&ixlib=rb-4.0.3&q=80&w=200",
        "preview": "https://images.unsplash.com/photo-1511044568932-338cba0ad803?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w2OTgwMzZ8MHwxfHNlYXJjaHwyfHxjYXR8ZW58MHx8fHwxNzM3MzY2MjEzfDA&ixlib=rb-4.0.3&q=80&w=1080",
        "title": null,
        "source": "Unsplash",
        "tags": []
    },
... (snipped)
```

## Experiment with 1000 requests

Not trying to fulfill the goal, just tested out of curiosity (the workstation is running on an old CPU with spinning disks). Due to the API limit, I cheated by caching the result before running the test. 6 worker processes were spawned for the test.

```
jeffrey04@nobita-ubuntu:pantheon-assignment on  main [!?] is 📦 v0.1.0 via 🐍 v3.12.6 (pantheon-assignment) [direnv] [▲]  http localhost:8081/register --json name=foo password=bar
HTTP/1.1 200 OK
Content-Length: 148
Content-Type: application/json
Date: Fri, 17 Jan 2025 17:22:52 GMT
Server: uvicorn
{
    "name": "foo",
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoiZm9vIiwicGFzc3dvcmQiOiJiYXIifQ.k0-sVR_MKXEFa9ryAth_qLmV86MY79Gw5VPYy4pvlAU"
}

jeffrey04@nobita-ubuntu:pantheon-assignment on  main [!?] is 📦 v0.1.0 via 🐍 v3.12.6 (pantheon-assignment) [direnv] [I]  http localhost:8081/search search_term==cat "Authorization:Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoiZm9vIiwicGFzc3dvcmQiOiJiYXIifQ.k0-sVR_MKXEFa9ryAth_qLmV86MY79Gw5VPYy4pvlAU"^C
jeffrey04@nobita-ubuntu:pantheon-assignment on  main [!?] is 📦 v0.1.0 via 🐍 v3.12.6 (pantheon-assignment) [direnv] [I]  oha "http://localhost:8081/search?search_term=cat" -n1000 -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoiZm9vIiwicGFzc3dvcmQiOiJiYXIifQ.k0-sVR_MKXEFa9ryAth_qLmV86MY79Gw5VPYy4pvlAU"
Summary:
  Success rate: 100.00%
  Total:        48.0969 secs
  Slowest:      4.7838 secs
  Fastest:      0.2193 secs
  Average:      2.3804 secs
  Requests/sec: 20.7913

  Total data:   29.70 MiB
  Size/request: 30.41 KiB
  Size/sec:     632.31 KiB

Response time histogram:
  0.219 [1]   |
  0.676 [22]  |■
  1.132 [48]  |■■
  1.589 [27]  |■
  2.045 [37]  |■■
  2.502 [549] |■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
  2.958 [204] |■■■■■■■■■■■
  3.414 [55]  |■■■
  3.871 [36]  |■■
  4.327 [11]  |
  4.784 [10]  |

Response time distribution:
  10.00% in 1.8162 secs
  25.00% in 2.2206 secs
  50.00% in 2.3879 secs
  75.00% in 2.6068 secs
  90.00% in 3.1488 secs
  95.00% in 3.6872 secs
  99.00% in 4.3547 secs
  99.90% in 4.7838 secs
  99.99% in 4.7838 secs


Details (average, fastest, slowest):
  DNS+dialup:   0.0009 secs, 0.0001 secs, 0.0018 secs
  DNS-lookup:   0.0000 secs, 0.0000 secs, 0.0001 secs

Status code distribution:
  [200] 1000 responses
```
