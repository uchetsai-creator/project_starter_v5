# Distribution

<!--
  For: Library / SDK and CLI Tool projects
  Replaces: deployment.md (libraries and CLIs are not "deployed" — they are distributed)
  Purpose: Documents how the package is built, published, and installed by end users.
  Update when: Build process changes, a new registry is added or removed,
               installation instructions change, or CI/CD pipeline changes.
-->

## Package Identity

| Property | Value |
|---|---|
| Package name | [e.g., `my-library`, `my-cli`] |
| Registry | [npm / PyPI / crates.io / GitHub Releases / Homebrew / etc.] |
| Registry URL | [Direct link to the package page] |
| Source repository | [GitHub / GitLab URL] |

---

## Build

**Prerequisites:**

```bash
# Install build tools
[command — e.g., npm install / pip install build / cargo build]
```

**Build command:**

```bash
[build command — e.g., npm run build / python -m build / cargo build --release]
```

**Output:**

| Artifact | Path | Description |
|---|---|---|
| [Library bundle / Binary] | `[dist/index.js / dist/*.whl / target/release/binary]` | [What it is] |
| [Type declarations] | `[dist/index.d.ts]` | [TypeScript types — if applicable] |

---

## Publish

**Authentication:**

```bash
# Authenticate with the registry before publishing
[auth command — e.g., npm login / twine upload requires PYPI_TOKEN env var]
```

**Publish command:**

```bash
[publish command — e.g., npm publish / twine upload dist/* / cargo publish]
```

**Required before publishing:**
- Version bumped in `[pyproject.toml / package.json / Cargo.toml]`
- `CHANGELOG.md` updated (see `docs/specs/release-guide.md`)
- All tests passing
- Git tag created and pushed

---

## Installation (end user)

```bash
# npm
npm install [package-name]

# PyPI
pip install [package-name]

# Homebrew (if applicable)
brew install [formula-name]

# Binary download (if applicable)
curl -L [release URL] | tar xz
```

---

## CI/CD Pipeline

| Stage | Trigger | Action |
|---|---|---|
| Test | Every PR and push | Run full test suite |
| Build | Every merge to `main` | Build distributable artifact |
| Publish | Git tag `v*` pushed | Publish to registry |

CI configuration: [`[link to CI config — .github/workflows/*.yml / .gitlab-ci.yml]`]

---

## Release Artifacts

For each GitHub/GitLab release, attach:

| File | Description |
|---|---|
| `[package-name]-[version].tar.gz` | Source archive |
| `[binary-name]-linux-x86_64` | Linux binary (if CLI) |
| `[binary-name]-darwin-arm64` | macOS ARM binary (if CLI) |
| `[binary-name]-windows-x86_64.exe` | Windows binary (if CLI) |

Checksums (`SHA256SUMS`) must be attached alongside binaries.

---

## Mobile App Variant

<!--
  Fill in this section instead of the Library / SDK / CLI sections above
  when project type is Mobile App. Delete the sections above if this is a
  pure mobile project.
-->

### App Identity

| Property | iOS | Android |
|---|---|---|
| Bundle ID | `com.example.myapp` | `com.example.myapp` |
| App Store / Play Store ID | [App Store ID] | [Play Store package name] |
| Version naming | `[major].[minor].[patch]` | `[major].[minor].[patch]` |
| Build number | Auto-incremented by CI | `versionCode` auto-incremented by CI |

---

### Build Pipeline

| Tool | Purpose |
|---|---|
| [Fastlane / Xcode Cloud / Bitrise / GitHub Actions] | CI orchestration |
| [Xcode / Gradle] | Platform build toolchain |
| [EAS Build / Expo] | Cross-platform build service (if using Expo) |

**iOS build command:**

```bash
# Local (ad-hoc / TestFlight)
fastlane ios beta

# Or via Xcode
xcodebuild -workspace [App.xcworkspace] -scheme [App] -configuration Release \
  -archivePath build/App.xcarchive archive
```

**Android build command:**

```bash
# Local APK
./gradlew assembleRelease

# AAB for Play Store
./gradlew bundleRelease
```

---

### Signing Configuration

**iOS:**

| Artifact | Certificate | Profile |
|---|---|---|
| Development | Apple Development | `[Team] Development` |
| TestFlight | Apple Distribution | `[App] App Store` |
| App Store | Apple Distribution | `[App] App Store` |

Certificates and profiles are stored in [Keychain / Match / manual download].
Do NOT commit `.p12` files or provisioning profiles to git.

**Android:**

| Property | Value |
|---|---|
| Keystore file | `upload-keystore.jks` — stored in [secure vault, never in git] |
| Key alias | `[upload]` |
| Credentials source | CI environment variables: `KEYSTORE_BASE64`, `KEY_ALIAS`, `KEY_PASSWORD`, `STORE_PASSWORD` |

---

### Release Checklist

**Before each App Store / Google Play release:**

- [ ] Version and build number bumped in `[package.json / pubspec.yaml / Info.plist / build.gradle]`
- [ ] Release notes written for this version
- [ ] All CI tests passing on `main`
- [ ] Signed build generated and uploaded to TestFlight / Internal Testing track
- [ ] QA sign-off on TestFlight / Internal Testing build
- [ ] App Store / Play Store metadata updated (screenshots, description if changed)
- [ ] Compliance questionnaire answered (IDFA, encryption export)

**Submission:**

```bash
# iOS — upload to App Store Connect
fastlane ios release

# Android — upload AAB to Play Console
fastlane android release
```

---

### CI/CD Pipeline

| Stage | Trigger | Action |
|---|---|---|
| Test | Every PR | Unit + integration tests, lint |
| Build (dev) | Merge to `develop` | Debug build, upload to TestFlight Internal / Play Internal |
| Build (release) | Merge to `main` or git tag `v*` | Release build, upload to TestFlight / Play Store |
| Submit | Manual trigger | Submit to App Review / Production track |

CI configuration: [`[link to CI config]`]
