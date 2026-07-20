# Permissions

## Roles

| Role | Description |
|---|---|
| ops | Operations team member — can view and override orders |
| readonly | Support team — view only, no status changes |

## Permission Matrix

| Action | ops | readonly |
|---|---|---|
| GET /api/orders/:id | ✅ | ✅ |
| POST /api/orders | ✅ | ❌ |
| POST /internal/orders/:id/override-status | ✅ | ❌ |
| Export CSV | ✅ | ✅ |
