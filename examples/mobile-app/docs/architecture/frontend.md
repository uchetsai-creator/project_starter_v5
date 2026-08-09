# Frontend

## Stack

- Flutter 3.22 (Dart 3.4)
- Riverpod for state management
- `sqflite` for local SQLite persistence
- `flutter_local_notifications` for reminder scheduling
- `go_router` for declarative navigation

## Page / Screen Structure

| Screen | Route | Purpose |
|---|---|---|
| Onboarding | `/onboarding` | First-run welcome + notification permission prompt |
| Home | `/` | List of active habits with one-tap mark-done |
| Habit Detail | `/habit/:id` | Edit habit, view streak, archive |
| Add Habit | `/habit/new` | Create a new habit |
| Stats | `/stats` | Weekly/monthly completion charts across all habits |
| Settings | `/settings` | Notification permissions, backup/export, about |

## Component Strategy

Screens are composed from small, stateless presentation widgets (`HabitCard`,
`StreakBadge`, `WeekdayPicker`) that read from Riverpod providers backed by the local
database repository layer — no widget talks to `sqflite` directly.
