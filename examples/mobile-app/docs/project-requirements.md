# Project Requirements

## Goals

* Give users a simple way to track daily habits and see their streaks at a glance.
* Send a local reminder notification for each habit at the time the user chooses.
* Work fully offline — no account or network connection required.

---

## Scope

### In Scope
* Creating, editing, and archiving habits (name, icon, frequency, reminder time)
* Marking a habit done for the current day and viewing a streak counter
* A weekly/monthly stats view showing completion rate per habit
* Local push notification reminders

### Out of Scope
* Multi-device sync or cloud backup
* Social features (sharing streaks, friends, leaderboards)
* Habit suggestions or AI coaching

---

## Roles

| Role | Description |
|---|---|
| User | The single local user of the app — no accounts, no server-side identity |

---

## Functional Requirements

* **FR-001**: The app must let a user create a habit with a name, an icon, and a
  frequency (daily, or specific weekdays).
* **FR-002**: The app must let a user mark a habit as done for the current day from the
  Home screen with a single tap.
* **FR-003**: The app must compute and display a current streak (consecutive completed
  days) and a longest streak per habit.
* **FR-004**: The app must schedule a local notification at the user-chosen reminder time
  for each active habit.
* **FR-005**: The app must let a user archive a habit without deleting its history.

---

## Non-Functional Requirements

* **Performance**: Home screen renders the full habit list in under 300ms on a
  mid-range device (e.g. Pixel 6a / iPhone SE 2022).
* **Offline-first**: All core features (create, mark done, view stats) work with the
  device in airplane mode.
* **Storage**: All data is persisted locally in SQLite via `sqflite`; nothing leaves
  the device.
* **Battery**: Reminder notifications use the OS-native scheduler (`flutter_local_notifications`)
  rather than a background polling service.

---

## Edge Cases

### Empty and missing input
* Creating a habit with an empty name is rejected with an inline validation error.

### Permission boundaries
* Not applicable — single-user, no roles.

### Concurrency and race conditions
* Marking the same habit done twice in the same day is idempotent — the second tap
  toggles it back to not-done rather than double-counting the streak.

### External dependency failures
* Notification permission denied by the OS → reminders are silently disabled for that
  habit and a banner on the Habit Detail screen explains how to re-enable them in
  Settings.

### State machine violations
* Marking a habit done for a day before its creation date is not possible — the date
  picker on the Stats screen is bounded to the habit's creation date.

### Data contract violations
* Importing a corrupted local backup file is rejected with an error dialog; the
  existing local database is left untouched.

---

## Acceptance Criteria

* **AC-001**: Given a habit with a 3-day current streak, when the user marks today done,
  then the streak counter shows 4 and the longest streak updates if 4 exceeds it.
* **AC-002**: Given a habit with a reminder time of 8:00 PM, when that time arrives and
  the habit is not yet marked done, then a local notification is delivered.
* **AC-003**: Given an archived habit, when the user views the Home screen, then the
  habit does not appear in the active list but its history remains visible from Stats.

---

## Assumptions

* The app targets a single logged-out user per device install; no backend account system
  exists in v1.
* The device clock/timezone is trusted for computing "day boundaries" for streaks.
