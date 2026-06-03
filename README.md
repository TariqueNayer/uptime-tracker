# Uptime-Tracker
*Uptime-Tracker* is a backend project that lets developers register API endpoints and automatically monitors their availability at regular intervals. It detects downtime, tracks response times, logs incidents, and pushes real-time status updates over WebSockets.
Alternative to UptimeRobot or Pingdom. built as a backend API

## Useful for...
- Developers who want to monitor their own deployed APIs
- Teams who want a self-hosted uptime monitoring solution
- Anyone who needs a programmatic record of API availability over time

## Live Demo
- ### API demo:
  - API root link: https://uptime-tracker-jzoy.onrender.com/api/v1/ 
  - API schema link: https://uptime-tracker-jzoy.onrender.com/api/schema/swagger-ui/  
    The demo is deployed on render's free tier, so you first request may take upto 30 seconds to start, it will be normal after that


#### <ins>For API Architecture documentation and user instructions, please read this [Backend/readme](https://github.com/TariqueNayer/uptime-tracker/blob/main/backend/README.md)</ins>


## Core features
- ### Monitor management  
  - Register any HTTP/HTTPS endpoint for monitoring
  - Configure check interval (minimum 5 minutes), timeout, expected status code, and HTTP method
  - Pause and resume monitoring without deleting history
  - Free tier cap of 3 active monitors per user
- ### Automated health checks
  - Celery Beat schedules checks independently per monitor based on its configured interval
  - Each check records status code, response time, and error details
  - Checks run entirely in the background — no user action required after setup
- ### Incident tracking
  - State machine detects UP→DOWN and DOWN→UP transitions
  - Opens a new Incident the moment a monitor first fails
  - Closes the Incident automatically when the monitor recovers
  - Prevents duplicate incidents — one outage event regardless of how many consecutive failures
- ### Real-time updates
  - Django Channels maintains a persistent WebSocket connection per monitor
  - Every check result is pushed instantly to connected clients
  - No polling required — clients receive data the moment it's available
- ### Data retention
  - CheckResults older than 30 days are automatically deleted by a scheduled Celery task
  - Incidents are kept permanently — they're low volume but high value historically
- ### Authentication
  - JWT authentication via httpOnly cookies
  - Access token (15 min) + refresh token (7 days) with rotation and blacklisting
  - Tokens never exposed in response bodies or localStorage
- ### API documentation
  - Full OpenAPI schema auto-generated via drf-spectacular
  - Interactive Swagger UI available at api/schema/swagger-ui/
  - Redoc UI available at api/schema/redoc/

## Tech stack
- Django + DRF — web framework and REST API
- Celery — distributed task queue for background health checks
- Celery Beat — periodic task scheduler with DatabaseScheduler
- Django Channels — WebSocket support via ASGI
- Redis Cloud — Celery broker, Channels layer, Django cache
- Neon Postgres — primary database
- Daphne — ASGI server (HTTP + WebSocket)
- dj-rest-auth + simplejwt — JWT authentication with httpOnly cookies
- drf-spectacular — OpenAPI schema and Swagger docs
- httpx — async-capable HTTP client for health check requests
- Render — demo deployment (two free-tier services)
