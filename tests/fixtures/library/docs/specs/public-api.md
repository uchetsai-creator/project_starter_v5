# Public API

## Functions

### `create_client(api_key: str, timeout: int = 30) -> Client`

Create and return an authenticated API client.

### `def fetch_data(client: Client, resource_id: str) -> dict`

Fetch a resource by ID. Returns the full resource dictionary.

## Classes

```python
class Client:
    def get(self, path: str) -> dict: ...
    def post(self, path: str, data: dict) -> dict: ...
```
