# Test Plan

## Testing Strategy

We use a layered testing approach with unit tests, widget tests, and end-to-end
integration tests, run via `flutter test` and `flutter drive`.
Unit tests validate the streak-calculation engine and the local database repository
layer in isolation, using an in-memory `sqflite` instance.
Widget tests verify each screen renders correctly given a fake provider state, without
touching the real database or OS notification APIs.
Integration tests drive the full app on a simulator/emulator through the create-habit
to mark-done-and-see-streak user journey.

## Test Scope

- Unit: streak calculation, database repository CRUD, notification-time scheduling logic
- Widget: Home, Habit Detail, Add Habit, Stats screens
- Integration (e2e): onboarding -> create habit -> mark done -> view stats
