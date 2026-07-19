# Service Contract

## API Contracts

| Method | Path | Consumer | Provider |
|---|---|---|---|
| GET | /users/{id} | order-service | user-service |
| POST | /notifications | order-service | notification-service |

## Events

- Topic: `order.created` -- published by order-service, consumed by notification-service
- Queue: `email.send` -- consumed by notification-service
