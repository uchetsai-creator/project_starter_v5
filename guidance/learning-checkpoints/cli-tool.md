# Learning Checkpoints — CLI Tool

Substitute these nouns into `learning-checkpoints-common.md`'s Checkpoint A / B steps.

**Checkpoint A (existing code) — ask about:**
- Which subcommand/file owns this behavior, and how flags get parsed into it
- The exit-code convention and stdin/stdout contract this command follows

**Checkpoint B (new requirement) — ask about:**
- New subcommand/flag shape: name, flags, defaults, exit codes
- Whether this belongs as a new subcommand or a flag on an existing one

**Common unfamiliar-tech hotspots for this type** (candidates for Checkpoint 0):
- The argument-parsing library itself (Click, Typer, argparse) if new to you
- Packaging/distribution mechanics (entry points, versioning)
