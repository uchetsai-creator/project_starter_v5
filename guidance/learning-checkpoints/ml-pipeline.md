# Learning Checkpoints — ML Pipeline

Substitute these nouns into `learning-checkpoints-common.md`'s Checkpoint A / B steps.

**Checkpoint A (existing code) — ask about:**
- Which stage (train / eval / serve) owns this behavior, and the model contract it follows
- What retraining or threshold policy this stage's output feeds into

**Checkpoint B (new requirement) — ask about:**
- Model input/output schema and production threshold for a new/changed stage
- What experiment/hypothesis this change is testing (goes in experiment-log.md later)

**Common unfamiliar-tech hotspots for this type** (candidates for Checkpoint 0):
- The ML framework itself (scikit-learn, PyTorch, etc.) if new to you
- The evaluation metric or methodology being used
