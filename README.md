# URL Shortener with Analytics

A FastAPI-based URL shortener with Redis caching, background click processing, rate limiting, and visit analytics.

The goal of this project is to demonstrate practical backend implementation.
---

## Project Summary

The system allows users to create short URLs and track analytics about visits. It uses PostgreSQL for persistent data, Redis for caching/rate limiting/counters, and Celery for asynchronous background processing.

Main capabilities implemented so far:

- User and API key based access
- Short URL creation and redirect flow
- Redis cache-aside lookup for redirects
- Redis-backed click counters
- Celery-based click flushing to PostgreSQL
- Layered rate limiting
- Visit analytics collection
- IP anonymization
- User-Agent parsing
- GeoIP enrichment
- Time-series-style analytics indexing
- Dashboard-oriented analytics API endpoints

Some public API features from the final phase are still pending and are documented below.

---

## Current Project Status

| Area | Status | Notes |
|---|---:|---|
| Phase 1: Core URL shortener | Done | Users, API keys, short links, redirects |
| Phase 2: Redis, caching, click tracking, rate limiting | Done | Cache-aside, Redis counters, Celery flush, layered rate limits |
| Phase 3: Analytics collection and processing | Done | Visit analytics, IP anonymization, User-Agent parsing, GeoIP, time-series index |
| Phase 4: Analytics dashboard API | Done | Daily visits, country breakdown, top referrers, top browsers, multi-link comparison |
| Phase 4: Public API refinements | Partially done | OpenAPI and `/api/v1/` are done; response envelope, cursor pagination, and webhooks are pending |

---

## Architecture

```text
Client / Browser / API Consumer
        |
        v
FastAPI API
        |
        +-----------------------------+
        |                             |
        v                             v
PostgreSQL                         Redis
(users, api keys,                  (redirect cache,
short links, analytics)             rate limits,
                                    click counters,
                                    Celery broker)
                                      |
                                      v
                                 Celery Worker
                                      |
                     +----------------+----------------+
                     |                                 |
                     v                                 v
              Flush click counts              Process visit analytics
              Redis -> PostgreSQL             GeoIP, User-Agent, IP masking
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| API | FastAPI |
| Validation | Pydantic |
| ORM | SQLAlchemy |
| Database | PostgreSQL |
| Cache / counters / rate limit state | Redis |
| Background jobs | Celery |
| GeoIP | `geoip2` + MaxMind GeoLite2 City database |
| User-Agent parsing | `user-agents` |
| Local environment | Docker Compose |

---

## Project Phases and Implementation Details

## Phase 1 — Core URL Shortener

### Goal

Build the basic URL shortener API with users, API keys, short link creation, and redirect handling.

### Implemented

- User model
- API key model
- Short link model
- Pydantic schemas for request/response validation
- Repository layer for database operations
- API key authentication dependency
- Short link creation endpoint
- Redirect endpoint
- Dockerized FastAPI + PostgreSQL setup

### Main endpoints

```http
POST /api/v1/users/
POST /api/v1/users/{user_id}/api-keys
POST /api/v1/links/
GET  /api/v1/links/{short_code}
```

### Implementation choice

The project uses API keys instead of a full login/session flow.

Reason:

- It keeps the authentication flow simple for an API-focused backend.
- It is common for developer-facing APIs.
- It keeps the project focused on URL shortening and analytics.

---

## Phase 2 — Redis, Caching, Click Tracking, and Rate Limiting

### Goal

Improve redirect performance and avoid writing to PostgreSQL on every click.

### Implemented

### 1. Redis cache-aside for redirects

The redirect endpoint first checks Redis for the original URL.

```text
Request short_code
      |
      v
Check Redis
      |
      +-- cache hit -> redirect
      |
      +-- cache miss -> query PostgreSQL -> store in Redis -> redirect
```

Reason:

- Redirects are read-heavy.
- Redis is faster than PostgreSQL for repeated short code lookups.
- Cache-aside keeps the database as the source of truth.

### 2. Hot-link TTL extension

Frequently accessed links can have their Redis TTL refreshed.

Reason:

- Popular links should remain cached longer.
- This reduces database load for high-traffic links.

### 3. Redis click counters

Instead of updating `short_links.click_count` on every redirect, the app increments a Redis counter:

```text
clicks:<short_code>
```

Reason:

- Redis increments are fast.
- PostgreSQL writes are reduced.
- This is a common buffering pattern for high-frequency counters.

### 4. Celery click flush

A Celery task flushes the Redis click count to PostgreSQL.

Reason:

- Keeps redirect response time low.
- Moves database write work to the background.
- Reduces direct write pressure on PostgreSQL.

### 5. Layered rate limiting

Rate limiting uses Redis counters.

Unauthenticated users:

```text
rate:ip:<ip_address>
```

Authenticated users:

```text
rate:user:<user_id>
```

Reason:

- Anonymous traffic can be limited by IP.
- Authenticated users can receive a higher limit.
- Redis expiration naturally supports time-window rate limiting.

---

## Phase 3 — Analytics Collection and Processing

### Goal

Collect useful visit analytics without slowing down the redirect flow.

### Implemented analytics fields

| Field | Description |
|---|---|
| `timestamp` | Precise visit time |
| `ip` | Anonymized IP address |
| `user_agent` | Raw User-Agent string |
| `browser` | Parsed browser name |
| `os` | Parsed operating system |
| `device_type` | Desktop / Mobile / Tablet / Other |
| `referrer` | Source page if available |
| `country` | GeoIP country |
| `city` | GeoIP city |

### Analytics processing flow

```text
Redirect endpoint
      |
      v
Send Celery task
      |
      +-- GeoIP lookup
      +-- IP anonymization
      +-- User-Agent parsing
      |
      v
Insert row into visit_analytics
```

### Implementation choices

### 1. Why analytics processing is asynchronous

The redirect endpoint should stay fast. Analytics enrichment is useful, but it should not block the user.

So the API sends a Celery task and returns the redirect quickly.

### 2. Why raw IP is passed to Celery but not stored

GeoIP lookup needs the real IP address.

However, before storing the IP in PostgreSQL, the app anonymizes it.

Example:

```text
172.20.0.1 -> 172.20.0.xxx
```

Reason:

- GeoIP lookup still works for public IPs.
- The database does not store the full raw IP.

### 3. Why local MaxMind GeoIP database was selected

Possible options:

| Option | Pros | Cons |
|---|---|---|
| External GeoIP API | Easy to start | Adds network dependency, rate limits, slower |
| Local `.mmdb` database | Fast and offline | Requires local file setup |

Selected:

```text
geoip2 + local MaxMind GeoLite2-City.mmdb
```

Reason:

- Avoids external API calls during redirects/analytics.
- Works offline.
- More realistic for backend infrastructure.

### 4. Why User-Agent parsing happens in Celery

User-Agent parsing is enrichment work, not critical redirect work.

Reason:

- Keeps redirect logic lightweight.
- Keeps analytics-related work in the analytics pipeline.

### 5. Time-series schema choice

The `visit_analytics` table stores one row per visit. This is event-style time-series data.

Common query pattern:

```sql
WHERE short_link_id = ?
AND timestamp BETWEEN ? AND ?
```

Implemented index:

```python
Index("idx_visit_link_time", "short_link_id", "timestamp")
```

Reason:

- Most dashboard queries ask for visits for a specific link over time.
- The composite index helps PostgreSQL filter by link and time range efficiently.
- A dedicated time-series database was not necessary for the scope of this assessment.

---

## Phase 4 — Analytics Dashboard API

### Goal

Expose aggregated analytics endpoints that can support dashboard charts and tables.

### Implemented dashboard requirements

| Dashboard requirement | Endpoint | What it returns |
|---|---|---|
| Line chart: visits over last 7 / 30 / 90 days | `GET /api/v1/analytics/{short_code}/daily` | Daily visit counts for one short link |
| Geographic breakdown | `GET /api/v1/analytics/{short_code}/by-country` | Visit counts grouped by country |
| Top referrers | `GET /api/v1/analytics/{short_code}/by-referrer` | Visit counts grouped by referrer |
| Top browsers | `GET /api/v1/analytics/{short_code}/by-browser` | Visit counts grouped by browser |
| Multi-link comparison | `GET /api/v1/analytics/multi?short_codes=a,b,c` | Total visit counts across multiple links |

### Example daily response

```json
{
  "short_code": "H6DI6G0",
  "daily_visits": [
    {
      "date": "2026-07-08",
      "count": 6
    },
    {
      "date": "2026-07-07",
      "count": 4
    }
  ]
}
```

### Example country response

```json
{
  "short_code": "H6DI6G0",
  "visits_by_country": [
    {
      "country": "United States",
      "count": 8
    },
    {
      "country": null,
      "count": 21
    }
  ]
}
```

`country: null` can appear during local Docker testing because private Docker IPs are not mapped in public GeoIP databases.

---

## Phase 4 — Public API Requirements

This part is partially complete.

| Requirement | Status | Explanation |
|---|---:|---|
| Full OpenAPI / Swagger documentation | Done | FastAPI automatically exposes `/docs` and `/openapi.json` |
| URL versioning: `/api/v1/` | Done | Current routers are mounted under `/api/v1/` |
| Consistent response envelope: `{ data, meta, errors }` | Pending | Current endpoints return plain JSON responses |
| Cursor-based pagination for link listings | Pending | A paginated list-links endpoint still needs to be added |
| Webhook support for click threshold events | Pending | Webhook model/config and trigger logic still need to be implemented |

### Why these are pending

The main redirect, caching, analytics, and dashboard features were prioritized first because they represent the core system behavior. The remaining public API refinements are still important, but they are mostly API consistency and integration improvements.

---

## Database Overview

```text
users
 |
 +-- api_keys

users
 |
 +-- short_links
          |
          +-- visit_analytics
```

### `users`

Stores user records.

### `api_keys`

Stores API keys related to users.

### `short_links`

Stores each shortened URL.

Important fields include:

- `original_url`
- `short_code`
- `expires_at`
- `redirect_type`
- `is_active`
- `click_count`
- `last_clicked_at`

### `visit_analytics`

Stores one row per visit.

Important fields include:

- `short_link_id`
- `timestamp`
- `ip`
- `user_agent`
- `browser`
- `os`
- `device_type`
- `referrer`
- `country`
- `city`

Indexes include:

- `short_link_id`
- `timestamp`
- composite index: `(short_link_id, timestamp)`

---

## How to Run the Project

### 1. Clone the repository

```bash
git clone https://github.com/pooya-janani/url-shortener-with-analytics.git
cd url-shortener-with-analytics
```

### 2. Create environment file

```bash
cp .env.example .env
```

Update `.env` based on your local setup.

### 3. Start services

```bash
docker compose up --build
```

Or detached:

```bash
docker compose up --build -d
```

### 4. Open Swagger

```text
http://localhost:8000/docs
```

### 5. Access PostgreSQL

```bash
docker compose exec db psql -U postgres -d url_shortener_db
```

### 6. Access Redis

```bash
docker compose exec redis redis-cli
```

### 7. View logs

API logs:

```bash
docker compose logs -f api
```

Celery logs:

```bash
docker compose logs -f celery_worker
```

---

## GeoIP Setup

The GeoIP database file is not included in Git.

Download the MaxMind GeoLite2 City database and place it here:

```text
geoip/
└── GeoLite2-City.mmdb
```

The folder is kept in Git with:

```text
geoip/.gitkeep
```

The database file is ignored by `.gitignore`:

```text
geoip/*.mmdb
```

Reason:

- The file is external data.
- It may be large.
- It may require license/update management.
- It should not be committed to source control.

---

## How to Use the API

### 1. Create a user

Use Swagger:

```text
POST /api/v1/users/
```

### 2. Create an API key

```text
POST /api/v1/users/{user_id}/api-keys
```

Use the returned API key when creating links.

### 3. Create a short link

```http
POST /api/v1/links/
```

Example body:

```json
{
  "original_url": "https://google.com/",
  "custom_alias": null,
  "expires_at": "2026-07-05T16:22:59.709Z",
  "password": "optional-password",
  "redirect_type": 302
}
```

### 4. Visit a short link

```http
GET /api/v1/links/{short_code}
```

Example:

```bash
curl -v http://localhost:8000/api/v1/links/H6DI6G0
```

### 5. View analytics

Daily visits:

```http
GET /api/v1/analytics/H6DI6G0/daily
```

Country breakdown:

```http
GET /api/v1/analytics/H6DI6G0/by-country
```

Top browsers:

```http
GET /api/v1/analytics/H6DI6G0/by-browser
```

Top referrers:

```http
GET /api/v1/analytics/H6DI6G0/by-referrer
```

Multi-link comparison:

```http
GET /api/v1/analytics/multi?short_codes=H6DI6G0,niusha
```

---

## Useful Test Commands

### Test GeoIP lookup

```bash
docker compose exec api python
```

```python
from app.services.geoip import get_location

print(get_location("8.8.8.8"))
```

Expected:

```python
{"country": "United States", "city": None}
```

### Simulate a public IP during local testing

```bash
curl -H "X-Forwarded-For: 8.8.8.8" http://localhost:8000/api/v1/links/H6DI6G0
```

### Check recent analytics rows

```sql
SELECT id, short_link_id, timestamp, ip, country, city, browser, os, device_type
FROM visit_analytics
ORDER BY id DESC
LIMIT 5;
```

### Check daily aggregation manually

```sql
SELECT DATE(timestamp) AS visit_date, COUNT(*) AS visits_count
FROM visit_analytics
WHERE short_link_id = 9
GROUP BY DATE(timestamp)
ORDER BY visit_date DESC;
```

---

## Local Development Notes

### Browser autocomplete and prefetch behavior

During local testing, a browser may send extra requests when:

- the address bar autocompletes a previously visited URL
- the browser preloads a suggested page
- the user clicks a suggested URL after the browser has already made a request

This can make analytics counts increase more than expected during manual browser testing.

This behavior was confirmed through request logging.

A direct `curl` request usually records one visit.

This is not caused by PostgreSQL, Celery, Redis, or GeoIP. It is browser behavior.

A possible future improvement is short-window Redis deduplication, for example:

```text
recent_visit:<ip>:<short_code>
```

That was not added yet because it introduces a trade-off: very fast repeated real visits could be skipped.

### Local/private IPs and GeoIP

Local Docker requests often use private IPs like:

```text
172.x.x.x
10.x.x.x
192.168.x.x
```

Public GeoIP databases do not map these private IPs to countries or cities, so local analytics may show:

```json
{
  "country": null
}
```

When using a public IP, GeoIP returns real country data.

---

## What Is Done and What Is Left

### Done

- Core URL shortener
- API key authentication
- Redis caching
- Redis click counters
- Celery click flushing
- Layered rate limiting
- Visit analytics
- IP anonymization
- User-Agent parsing
- GeoIP enrichment
- Time-series composite index
- Dashboard analytics endpoints
- Swagger documentation through FastAPI
- `/api/v1/` versioning

### Still left

- Consistent response envelope
- Cursor-based pagination for link listings
- Webhook support for click threshold events
- Alembic migrations
- Automated test suite
- Deployment setup
- Optional dashboard frontend
- Optional analytics deduplication strategy

---

## Notes on Production Readiness

This project demonstrates backend architecture and implementation patterns, but it should not be treated as fully production-ready yet.

Before using it in a real production environment, the following should be added:

- Alembic migrations instead of relying on `create_all`
- automated tests
- stricter error handling
- structured logging configuration
- deployment configuration
- secret management
- webhook retry policy
- pagination and response envelope consistency
- monitoring and alerting

---

## Repository Hygiene

The repository intentionally excludes:

```text
.env
geoip/*.mmdb
__pycache__/
*.pyc
.venv/
venv/
postgres_data/
*.log
```

The repository includes:

```text
.env.example
geoip/.gitkeep
```

This allows other developers to set up the project without committing secrets or external data files.

---

## Version

Current milestone:

```text
v0.1.0
```

This tag represents the completed core shortener flow, caching/click tracking, analytics processing, time-series indexing, and dashboard analytics endpoints.