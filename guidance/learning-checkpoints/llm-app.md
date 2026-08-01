# Learning Checkpoints — AI / LLM Application

Substitute these nouns into `learning-checkpoints-common.md`'s Checkpoint A / B steps.

**Checkpoint A (existing code) — ask about:**
- Which prompt/tool owns this behavior, and its current tool schema or retrieval source
- What eval score or known failure mode this piece currently has

**Checkpoint B (new requirement) — ask about:**
- New/changed prompt or tool: parameters, expected output shape, retry strategy
- What eval criteria will judge whether this works (goes in eval-spec.md later)

**Common unfamiliar-tech hotspots for this type** (candidates for Checkpoint 0):
- Prompt engineering patterns (few-shot, chain-of-thought) if new to you
- RAG mechanics: chunking, embeddings, vector store
- LLM-as-judge evaluation methodology
