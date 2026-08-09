# Research

## Technology Decisions

Decision: Build with Flutter instead of React Native.
Rationale: A single Dart codebase with strong first-party tooling for local notifications
and SQLite (`flutter_local_notifications`, `sqflite`) covers 100% of v1's requirements
without needing native modules, and the team already has Flutter experience.

Decision: Use Riverpod instead of Provider or Bloc for state management.
Rationale: Riverpod's compile-time-safe providers catch the "used outside a provider
scope" class of bugs at build time, and its testability (no BuildContext needed to read
state in tests) matters for a habit-streak calculation engine that needs thorough
unit-test coverage.

Decision: Persist locally with `sqflite` instead of `shared_preferences` or `hive`.
Rationale: Streak calculations need to query "completions in the last N days" — a
relational query — which is straightforward in SQL and awkward with a key-value or
document store; `sqflite` also gives a clear migration path if cloud sync is added later.

## Resolved Clarifications

Q: Should habit reminders be delivered even if the app has been force-closed by the OS?
A: Yes — use the OS-native notification scheduler (`flutter_local_notifications`'s
`zonedSchedule`), which registers with the platform's alarm/notification system and
fires independently of whether the Flutter engine is running.
