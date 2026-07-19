# Database

## Database Engine

PostgreSQL 15 running on AWS RDS. Connection pooling via PgBouncer.

## Main Entities

- User: stores authentication credentials and profile data
- Order: represents a purchase with status state machine
- Product: catalogue items with inventory tracking
