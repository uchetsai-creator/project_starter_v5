# Logging Spec

## Log Output Format

Structured JSON lines written to the device-local debug log (visible via `flutter logs`
in development; stripped from release builds except for `ERROR` level).

## Required Log Points

- Habit created / archived
- Habit marked done / un-marked
- Notification scheduled / notification permission denied
- Local database migration run
