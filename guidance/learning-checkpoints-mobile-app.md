# Learning Checkpoints — Mobile App

Substitute these nouns into `learning-checkpoints-common.md`'s Checkpoint A / B steps.

**Checkpoint A (existing code) — ask about:**
- Which screen owns this behavior, and its navigation/props contract
- What OS permission or lifecycle event this screen depends on

**Checkpoint B (new requirement) — ask about:**
- New/changed screen: props, navigation entry point, permissions required
- Platform-specific behavior differences (iOS vs Android) if cross-platform

**Common unfamiliar-tech hotspots for this type** (candidates for Checkpoint 0):
- The component/state model (React Native, Flutter widgets, SwiftUI views) if new to you
- Platform lifecycle and permission mechanics
