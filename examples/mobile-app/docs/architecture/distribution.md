# Distribution

## Package Details

| Field | Value |
|---|---|
| Package name | com.habitly.app |
| App Store | Apple App Store, Google Play Store |
| Install | Download "Habitly" from the App Store or Play Store |

## Publish

1. Bump the version and build number in `pubspec.yaml`.
2. Build the release artifacts: `flutter build appbundle` (Android) and
   `flutter build ipa` (iOS).
3. Upload the Android App Bundle via `fastlane android deploy` to the Play Console.
4. Upload the iOS build via `fastlane ios release` to App Store Connect.
5. Submit both for review from their respective consoles.
