import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parent.parent.parent / "templates/script/validators"),
)
from verify_index_coverage import audit  # noqa: E402


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# No index files present — nothing to check (N/A project type)
# ---------------------------------------------------------------------------

def test_no_index_files_returns_empty(tmp_path):
    assert audit(str(tmp_path)) == []


# ---------------------------------------------------------------------------
# business-objects.md
# ---------------------------------------------------------------------------

def test_business_objects_missing_file_is_flagged(tmp_path):
    _write(tmp_path / "business" / "business-objects.md", """
## Object Files

| Object | File | Status field | States |
|---|---|---|---|
| Order | `docs/business/order-object.md` | `status` | PENDING -> SHIPPED |
""")
    results = audit(str(tmp_path))
    assert len(results) == 1
    r = results[0]
    assert r["name"] == "business-objects"
    assert r["missing_files"] == ["business/order-object.md"]
    assert r["orphan_files"] == []


def test_business_objects_existing_file_is_not_flagged(tmp_path):
    _write(tmp_path / "business" / "business-objects.md", """
## Object Files

| Object | File | Status field | States |
|---|---|---|---|
| Order | `docs/business/order-object.md` | `status` | PENDING -> SHIPPED |
""")
    _write(tmp_path / "business" / "order-object.md", "# Order\n")
    r = audit(str(tmp_path))[0]
    assert r["missing_files"] == []


def test_business_objects_orphan_file_is_flagged(tmp_path):
    _write(tmp_path / "business" / "business-objects.md", """
## Object Files

| Object | File | Status field | States |
|---|---|---|---|
| Order | `docs/business/order-object.md` | `status` | PENDING -> SHIPPED |
""")
    _write(tmp_path / "business" / "order-object.md", "# Order\n")
    _write(tmp_path / "business" / "payment-object.md", "# Payment\n")
    r = audit(str(tmp_path))[0]
    assert r["orphan_files"] == ["payment-object.md"]


def test_business_objects_placeholder_row_is_skipped(tmp_path):
    _write(tmp_path / "business" / "business-objects.md", """
## Object Files

| Object | File | Status field | States |
|---|---|---|---|
| [e.g., Order] | `docs/business/[object-name]-object.md` | [field] | [states] |
""")
    r = audit(str(tmp_path))[0]
    assert r["declared_count"] == 0
    assert r["missing_files"] == []


# ---------------------------------------------------------------------------
# business-process.md — same shape, different suffix
# ---------------------------------------------------------------------------

def test_business_process_missing_file_is_flagged(tmp_path):
    _write(tmp_path / "business" / "business-process.md", """
## Process Files

| Process | File | Owner |
|---|---|---|
| Create Order | `docs/business/order-create-process.md` | Customer |
""")
    r = audit(str(tmp_path))[0]
    assert r["name"] == "business-process"
    assert r["missing_files"] == ["business/order-create-process.md"]


def test_index_file_itself_is_never_flagged_as_orphan_of_itself(tmp_path):
    # business-process.md itself ends in '-process.md' — the same suffix as its own
    # per-item files (found via a real bootstrapped project during manual testing).
    _write(tmp_path / "business" / "business-process.md", """
## Process Files

| Process | File | Owner |
|---|---|---|
| Create Order | `docs/business/order-create-process.md` | Customer |
""")
    _write(tmp_path / "business" / "order-create-process.md", "# Create Order\n")
    r = audit(str(tmp_path))[0]
    assert r["missing_files"] == []
    assert r["orphan_files"] == []


# ---------------------------------------------------------------------------
# prompt-library.md — File column not in position 1, and relative to specs/
# ---------------------------------------------------------------------------

def test_prompt_library_missing_file_is_flagged(tmp_path):
    _write(tmp_path / "specs" / "prompt-library.md", """
## Active Prompts

| Prompt ID | Current version | Purpose | File |
|---|---|---|---|
| financial-advice | v1 | gives advice | `prompts/financial-advice-prompt.md` |
""")
    r = audit(str(tmp_path))[0]
    assert r["name"] == "prompt-library"
    assert r["missing_files"] == ["prompts/financial-advice-prompt.md"]


def test_prompt_library_existing_file_is_not_flagged(tmp_path):
    _write(tmp_path / "specs" / "prompt-library.md", """
## Active Prompts

| Prompt ID | Current version | Purpose | File |
|---|---|---|---|
| financial-advice | v1 | gives advice | `prompts/financial-advice-prompt.md` |
""")
    _write(tmp_path / "specs" / "prompts" / "financial-advice-prompt.md", "# Financial Advice\n")
    r = audit(str(tmp_path))[0]
    assert r["missing_files"] == []


def test_retired_prompts_table_is_not_checked_for_coverage(tmp_path):
    _write(tmp_path / "specs" / "prompt-library.md", """
## Active Prompts

| Prompt ID | Current version | Purpose | File |
|---|---|---|---|

## Retired Prompts

| Prompt ID | Last version | Retired date | Replaced by | Reason |
|---|---|---|---|---|
| old-prompt | v1 | 2026-01-01 | financial-advice | rewrite |
""")
    r = audit(str(tmp_path))[0]
    assert r["declared_count"] == 0
    assert r["missing_files"] == []
