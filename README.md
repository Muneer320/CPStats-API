---
title: CPStats API
emoji: 🏆
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
license: mit
short_description: Historical competitive programming ratings API
---

# CPStats API

CPStats is a small FastAPI service for looking up public competitive programming profiles on AtCoder, Codeforces, CodeChef and LeetCode. It was built for the SST Lounge Discord community, which is now inactive. SST-Lounge-Bot has an optional `/cp_rating` command that can call this API when both services are configured.

The API works locally with an API key. Its former Hugging Face Space has been unreliable; this README does not claim a live public deployment. Ratings are fetched from third-party sites at request time and can be unavailable when those sites change markup or block automated requests. In particular, CodeChef returned HTTP 403 from the development environment during this update.

## Run locally

Python 3.13 and Docker are supported. Create a `.env` file from `.env.example`, set a long random `API_KEY`, then:

```bash
python -m venv .venv
# Activate .venv for your shell, then:
python -m pip install -r requirements.txt
python main.py
```

Or run the container:

```bash
docker build -t cpstats-api .
docker run --rm -p 7860:7860 -e API_KEY=local-demo-key cpstats-api
```

`GET http://localhost:7860/health` returns 200 when a key is configured. For a live lookup:

```bash
curl -H "Authorization: Bearer local-demo-key" \
  http://localhost:7860/rating/atcoder/tourist
```

For the SST bot, set `CPSTATS_API_URL` to this service's base URL and `CPSTATS_API_KEY` to the same key. Do not expose the key in a client-side application.

## API behavior

| Endpoint | Access | Result |
|---|---|---|
| `GET /`, `GET /platforms` | Public | Service and platform information |
| `GET /health` | Public | 200 with a configured key; 503 without one |
| `GET /rating/{platform}/{username}` | Bearer key | One platform result |
| `POST /rating` | Bearer key | One result from `{"platform":"atcoder","username":"tourist"}` |
| `POST /ratings` | Bearer key | Up to 20 results; each item carries its own status |

Single lookups return 404 for a missing user, 502 for an upstream failure, 400 for an invalid platform, 401 for a missing/wrong key and 429 when the request limit is reached. Batch responses contain item statuses (`success`, `user_not_found`, `upstream_error` and validation errors); `successful_requests` counts only successes. Unrated users can have `rating: null`. Ratings across different platforms are not averaged.

Only successful single lookups enter the in-memory cache (default 15 minutes). `RATE_LIMIT_REQUESTS` and `RATE_LIMIT_WINDOW` set an in-memory limit per client IP and process. This is suitable for a small single-instance demo, not a distributed rate limit. `ALLOWED_ORIGINS` is empty by default; add explicit origins only for browser clients. Server-to-server callers do not need CORS.

## Verify

```bash
python -m pip install pytest httpx
python -m pytest -q
```

The tests use fixed response fixtures, so they work without third-party network access. A weekly GitHub workflow also checks live AtCoder and Codeforces responses with `python -m tests.live_contract`, which may flag upstream changes. The Hugging Face deployment, if restored, must have an `API_KEY` secret and use the Dockerfile in this repository.
