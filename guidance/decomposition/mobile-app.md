# Decomposition — Mobile App

Nouns for `guidance/decomposition/common.md`.

- **Observer:** the app user on a device
- **Entry point:** a screen or a user gesture (tap, swipe, deep link, push notification)
- **Independent Test:** run the flow on a simulator / emulator and check what the screen shows,
  including offline and permission-denied states

## Artifact kinds

| Kind | Prefix | In a mobile app | First failing check |
|---|---|---|---|
| Contract | `CONTRACT` | API client types / models matching `mobile-contract.md` | Decoding test with a recorded response |
| State | `STATE` | Local store / cache schema, persisted settings | Store test: write then read back after restart |
| Logic | `LOGIC` | View model / use case / repository | Unit test on the view model's output state |
| Entry | `ENTRY` | Screen, navigation route, deep-link or push handler | UI test: the gesture shows the expected screen state |
| Guard | `GUARD` | Offline mode, OS permission denied, token expiry, retry UI | UI test: airplane mode → cached data + offline banner |

## Typical Guard cases

- No network → cached data shown with an offline indicator; queued writes sync later
- OS permission denied (camera, location, notifications) → explanation and settings link
- Session expired mid-flow → re-auth without losing the user's input

## Example slice

```
SL-1 (P1)  Last synced data is readable offline
  Independent Test: load once online, switch to airplane mode, reopen → data shown
  Task STATE [SL-1] cache schema for the list                     Covers: FR-002
  Task LOGIC [SL-1] repository reads cache when network fails     Covers: FR-002, AC-003
  Task GUARD [SL-1] offline banner and stale-data timestamp       Covers: AC-004
  Task ENTRY [SL-1] list screen binds to repository state         Covers: AC-003
```
