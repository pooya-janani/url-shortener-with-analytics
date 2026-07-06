# URL Shortener with Analytics

A production-oriented URL shortener API built with FastAPI, PostgreSQL,
Redis, Celery, and Docker.

The project focuses on backend engineering practices including
asynchronous processing, analytics pipelines, database design, and
containerized development.

## Features

### URL Shortening

-   Create short URLs
-   Custom aliases
-   Expiration dates
-   Password-protected links
-   Configurable redirect types

### Analytics Pipeline

Each visit is processed asynchronously through a background analytics
pipeline.

    Client
      |
      v
    FastAPI Redirect Endpoint
      |
      v
    Celery Task
      |
      +--> User-Agent Parsing
      |
      +--> GeoIP Lookup
      |
      +--> IP Anonymization
      |
      v
    PostgreSQL

## Collected Analytics Data

  Field         Description
  ------------- -----------------------------
  timestamp     Precise visit timestamp
  IP            Anonymized IP address
  user_agent    Original browser user-agent
  browser       Extracted browser name
  os            Extracted operating system
  device_type   Desktop / Mobile / Tablet
  referrer      Source of incoming request
  country       GeoIP country information
  city          GeoIP city information

## Architecture

                     +-------------+
                     |   Client    |
                     +------+------+
                            |
                            v
                     +-------------+
                     |   FastAPI   |
                     +------+------+
                            |
                 +----------+----------+
                 |                     |
                 v                     v
           PostgreSQL              Redis
                 |                     |
                 |                     v
                 |              Celery Worker
                 |                     |
                 +----------+----------+
                            |
                            v
                  Visit Analytics Data

## Technology Stack

### Backend

-   Python
-   FastAPI
-   SQLAlchemy
-   PostgreSQL

### Background Processing

-   Celery
-   Redis

### Analytics

-   geoip2
-   MaxMind GeoLite2
-   User-Agent parsing

### Infrastructure

-   Docker
-   Docker Compose

## Database Structure

Current main entities:

    users
     |
     +-- api_keys

    users
     |
     +-- short_links
              |
              +-- visit_analytics

## Running Locally

Clone the repository:

``` bash
git clone <repository-url>
cd url-shortener-analytics
```

Start services:

``` bash
docker compose up --build
```

Services:

  Service      Port
  ------------ ------
  FastAPI      8000
  PostgreSQL   5433
  Redis        6379

## GeoIP Setup

The GeoIP database is not included in the repository.

Download GeoLite2-City.mmdb and place it here:

    geoip/
     └── GeoLite2-City.mmdb

## Development Progress

Completed:

-   [x] URL creation
-   [x] URL redirection
-   [x] Click tracking
-   [x] Redis click buffering
-   [x] Celery background tasks
-   [x] Visit analytics collection
-   [x] IP anonymization
-   [x] Browser/OS/device extraction
-   [x] GeoIP integration

In progress:

-   [ ] Time-series schema optimization 
-   [ ] Analytics reporting APIs
-   [ ] Dashboard
-   [ ] Production deployment

## Future Improvements

-   Alembic database migrations
-   Advanced analytics queries
-   Rate limiting
-   Monitoring and logging
-   Cloud deployment