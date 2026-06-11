# Backend API
## Architectur
- Django + DRF (Request handling)
Handles all user-facing operations: authentication, monitor CRUD, serving historical data. Standard synchronous Django.
- Celery + Redis (Async task processing)
The background engine. Celery Beat reads the schedule from Postgres (DatabaseScheduler) and fires ping_monitor tasks into Redis. Celery Worker picks them up and executes them. This layer runs completely independently of the web server — on a separate Render service in production.
The key architectural decision: each Monitor has its own PeriodicTask row, created automatically via Django signals when a monitor is saved. This means each monitor respects its own check interval independently. Pausing a monitor disables its PeriodicTask. Deleting a monitor removes it entirely.
- Django Channels (Real-time push)
After every check, the Celery worker sends a message to a Redis channel group named after the monitor. Channels picks it up and pushes it over WebSocket to every connected client watching that monitor. The worker and web server are on separate machines — Redis acts as the message bus between them.
- Redis database:
Redis serves three completely separate functions in this project:

  - Celery broker — task message queue between Beat and Worker
  - Channel layer — message bus between Worker and Channels
  - Django cache — cached monitor list and detail responses per user, invalidated via signals on every save

## Using the API
### Endpoints
``` Auth
POST   /api/auth/login/
POST   /api/auth/logout/
POST   /api/auth/registration/
POST   /api/auth/token/refresh/

Monitors
GET    /api/monitors/                  list your monitors
POST   /api/monitors/                  create a monitor
GET    /api/monitors/{id}/             retrieve one monitor
PATCH  /api/monitors/{id}/             update a monitor
DELETE /api/monitors/{id}/             delete a monitor
GET    /api/monitors/{id}/results/     last 50 check results
GET    /api/monitors/{id}/incidents/   all incidents

WebSocket
WS     /ws/monitors/{id}/             live check result stream

Docs
GET    /api/schema/                    OpenAPI schema
GET    /api/schema/swagger-ui/         Swagger UI
GET    /api/schema/redoc/              Redoc UI
```

The base URL for all endpoints is:
`https://uptime-tracker-jzoy.onrender.com`
Interactive documentation is available at /api/schema/swagger-ui/ or /api/schema/redoc/ — you can explore and test all endpoints directly from the browser.

### Create an account
```
curl -X POST https://uptime-tracker-jzoy.onrender.com/api/auth/registration/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "yourname",
    "email": "you@example.com",
    "password1": "yourpassword",
    "password2": "yourpassword"
  }'
```
On success you receive a 200 OK. Auth cookies are set automatically.
### Login
```
curl -X POST https://uptime-tracker-jzoy.onrender.com/api/auth/login/ \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{
    "username": "yourname",
    "password": "yourpassword"
  }'
```
`-c cookies.txt` saves your auth cookies locally. Pass `-b cookies.txt` on every subsequent request to authenticate.
### Create a monitor
```
curl -X POST https://uptime-tracker-jzoy.onrender.com/api/monitors/ \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "name": "My API",
    "url": "https://your-api.onrender.com/health/",
    "method": "GET",
    "expected_status_code": 200,
    "check_interval_seconds": 300
  }'
```
| Field | Required | Description | 
| :--- | :---: | ---: |
| name | Yes | A label for this monitor |
| url | Yes | The endpoint to ping |
| method | Yes | GET or POST |
| expected_status_code | Yes | What counts as "up" (e.g. 200) |
| check_interval_seconds | No | How often to check. Minimum 300 (5 min). Default 300 |
| timeout_seconds | No | How long to wait for a response. Default 10 |
| is_active | No | true to start monitoring immediately. Default true |
### List your monitors
```bash
curl https://uptime-tracker-jzoy.onrender.com/api/monitors/ \
  -b cookies.txt
```
### View check results
```bash
curl https://uptime-tracker-jzoy.onrender.com/api/monitors/{id}/results/ \
  -b cookies.txt
```
Returns the last 50 check results for the monitor, ordered by most recent first. Each result includes:
```json
{
  "id": 1,
  "monitor": 1,
  "checked_at": "2026-06-03T14:31:25Z",
  "is_up": true,
  "status_code": 200,
  "response_time_ms": 143,
  "error_message": null
}
```
### View incidents
```
curl https://uptime-tracker-jzoy.onrender.com/api/monitors/{id}/incidents/ \
  -b cookies.txt
```
Each incident represents one downtime event:
```
json{
  "id": 1,
  "monitor": 1,
  "started_at": "2026-06-03T12:00:00Z",
  "resolved_at": "2026-06-03T12:20:00Z",
  "is_resolved": true
}
```
resolved_at is null if the monitor is currently down.

### Pause or resume a monitor
```bash
# pause
curl -X PATCH https://uptime-tracker-jzoy.onrender.com/api/monitors/{id}/ \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"is_active": false}'

# resume
curl -X PATCH https://uptime-tracker-jzoy.onrender.com/api/monitors/{id}/ \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"is_active": true}'
```
Pausing stops checks immediately without deleting any history.

### Real-time updates via WebSocket
Connect to receive live check results the moment they arrive:
```
ws://uptime-tracker-jzoy.onrender.com/ws/monitors/{id}/
```
Requires your access_token cookie to be present in the handshake headers. Each message is a JSON object identical to a check result:
```json
{
  "monitor_id": 1,
  "checked_at": "2026-06-03T14:31:25Z",
  "is_up": true,
  "status_code": 200,
  "response_time_ms": 143,
  "error_message": null
}
```
### Delete a monitor
```bash
curl -X DELETE https://uptime-tracker-jzoy.onrender.com/api/monitors/{id}/ \
  -b cookies.txt
```
Deletes the monitor and all its check results and incidents permanently.

### Logout
```
bashcurl -X POST https://uptime-tracker-jzoy.onrender.com/api/auth/logout/ \
  -b cookies.txt
```
Blacklists the refresh token and clears both auth cookies.
