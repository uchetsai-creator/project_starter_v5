# Mobile Contract

## Screens

| Screen | Route | Entry point |
|---|---|---|
| Onboarding | `/onboarding` | First app launch only |
| Home | `/` | App launch (after onboarding) |
| Habit Detail | `/habit/:id` | Tap a habit card on Home |
| Add Habit | `/habit/new` | Tap the "+" FAB on Home |
| Stats | `/stats` | Bottom nav bar |
| Settings | `/settings` | Bottom nav bar |

## Navigation

Habitly uses a bottom navigation bar with three tabs — Home, Stats, Settings — plus a
stack navigator pushed on top for Habit Detail and Add Habit. Onboarding is a one-time
full-screen route shown before the bottom nav is mounted, on first launch only.

```
Onboarding (one-time)
  -> Home (tab 1, root of bottom nav)
       -> Add Habit (stack push, modal-style)
       -> Habit Detail (stack push)
  -> Stats (tab 2)
  -> Settings (tab 3)
```

Back navigation from Habit Detail or Add Habit returns to Home; the Android hardware
back button and iOS edge-swipe both follow the same stack.

## OS Permissions

| Permission | Platform | Why | Requested when |
|---|---|---|---|
| Notifications | iOS + Android | Deliver habit reminders | End of onboarding |
| Exact alarm scheduling | Android 12+ | Reminders fire at the precise chosen time | First reminder scheduled |

## Push Notification Schemas

Reminders are local (device-scheduled) notifications, not server push, but follow a
fixed payload shape so the same handler code processes them:

```json
{
  "id": "habit-<habit_id>-reminder",
  "title": "Time for: <habit name>",
  "body": "Tap to mark it done for today.",
  "data": { "habit_id": "<uuid>", "action": "open_habit_detail" }
}
```

Tapping the notification deep-links to `/habit/:id` via `go_router`'s notification
launch handler.

## Deep Linking

`habitly://habit/<id>` opens the Habit Detail screen directly; used by both the
notification tap handler and (for future use) home-screen widget taps.
