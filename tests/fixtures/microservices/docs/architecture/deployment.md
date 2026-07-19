# Deployment

## Services

| Service | Port | Replicas |
|---|---|---|
| api-gateway | 80 | 2 |
| user-service | 8001 | 3 |
| order-service | 8002 | 3 |

## Environment Variables

| Variable | Description |
|---|---|
| DATABASE_URL | Primary database connection string |
| SERVICE_DISCOVERY_URL | Consul service registry endpoint |
| JWT_PUBLIC_KEY | Public key for token validation |
