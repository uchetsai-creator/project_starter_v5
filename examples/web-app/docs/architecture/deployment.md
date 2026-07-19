# Deployment

## Services

| Service | Port | Description |
|---|---|---|
| api-server | 8000 | FastAPI application server |
| worker | - | Background task processor |
| nginx | 80 | Reverse proxy and static file server |

## Environment Variables

| Variable | Description |
|---|---|
| DATABASE_URL | PostgreSQL connection string |
| SECRET_KEY | JWT signing key |
| REDIS_URL | Cache connection string |
