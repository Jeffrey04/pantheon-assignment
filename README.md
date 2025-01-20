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

DATABASE=./database.sqlite
CACHE_RESULT=True

JWT_SECRET=<JWT SECRET KEY>
```

### Setting up with Docker

A docker image is made available at `ghcr.io/jeffrey04/pantheon-assignment:dev`, or you can proceed to build with

```
podman build -t jeffrey04/pantheon-assignment:dev ./podman
```

You can refer to the `docker-compose.yml.sample` to create a compose file for your environment. Please note that the database will reset itself on every run.


## Usage Guide

### Authentication

Register yourself through `POST /register` with the following fields passed to the body as JSON serialized object

* `name`: Your user name
* `password`: Your password

In return you will get an object with the following fields

* `name`: Your user name
* `token`: The JWT token you need to pass through the `Authorization` header for search requests


### Search

In order to authenticate yourself, you need to pass an `Authorization` header as follows

`Authorization: Bearer <YOUR TOKEN>`

Please refer to the previous section to register yourself to get a token.

Search is served via the endpoint `GET /search`. The endpoint expects a query string parameter named `search_term` where the value is a string containing the desired query.


## Experiment with 1000 requests

Not trying to fulfill the goal, just tested out of curiosity (the workstation is running on an old CPU wtih spinning disks). Due to the API limit, I cheated by caching the result before running the test. 6 worker processes were spawned for the test.

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
