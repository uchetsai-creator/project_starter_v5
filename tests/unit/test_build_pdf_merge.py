"""Unit tests for build_pdf.py merge behaviour: allowlist dedupe, registry from docs_dir,
status-emoji substitution outside code fences. Rendering (WeasyPrint/PlantUML) is not run."""
import importlib.util
from pathlib import Path

import pytest

from tests.conftest import REPO_ROOT

pytest.importorskip("weasyprint")
pytest.importorskip("cairosvg")
pytest.importorskip("markdown")

_BUILD_PDF = REPO_ROOT / "templates/script/generators/build_pdf.py"


@pytest.fixture(scope="module")
def build_pdf():
    spec = importlib.util.spec_from_file_location("build_pdf_under_test", _BUILD_PDF)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_REGISTRY_YAML = """\
documents:
  project-requirements:
    file: project-requirements.md
    path: project-requirements.md
    required_for: [web-app]
    optional_for: []
    context_priority: high
    task_types: [feature]
    purpose: "requirements"
    used_by: [pdf]
    related: []
    pdf: true
    pdf_chapter: plan
"""


def test_registry_in_docs_dir_wins_over_static_entry_and_is_listed_once(build_pdf, tmp_path):
    """project-requirements.md is declared in the registry (plan) and in the static scaffold
    (introduction). It must be merged once, under the registry chapter."""
    (tmp_path / "document-registry.yaml").write_text(_REGISTRY_YAML, encoding="utf-8")
    (tmp_path / "project-requirements.md").write_text("# Requirements\n", encoding="utf-8")

    allowlist = build_pdf.get_pdf_allowlist(str(tmp_path))
    entries = [e for e in allowlist if e[1] == "project-requirements.md"]
    assert len(entries) == 1
    assert entries[0][0] == "plan"


def test_find_allowed_files_skips_duplicate_paths(build_pdf, tmp_path):
    (tmp_path / "a.md").write_text("# A\n", encoding="utf-8")
    strings = build_pdf.STRINGS["en"]
    allowlist = [
        ("introduction", "a.md", frozenset({"web-app"})),
        ("plan", "a.md", frozenset({"web-app"})),
    ]
    files = build_pdf.find_allowed_files(str(tmp_path), strings, project_type=frozenset({"web-app"}),
                                         allowlist=allowlist)
    assert [rel for rel, _, _ in files] == ["a.md"]


def test_status_emoji_replaced_outside_code_fences_only(build_pdf):
    md = "状态 🔴 高风险\n\n```\n🔴 stays in code\n```\n\n🟢 done"
    out = build_pdf._status_emoji_to_text(md)
    assert '<span style="color:#dc2626">●</span> 高风险' in out
    assert '<span style="color:#16a34a">●</span> done' in out
    assert "🔴 stays in code" in out  # fenced code is left untouched


def test_disable_color_emoji_font_writes_conf_and_sets_env(build_pdf, monkeypatch, tmp_path):
    if not Path("/etc/fonts/fonts.conf").exists():
        pytest.skip("no system fontconfig")
    monkeypatch.delenv("FONTCONFIG_FILE", raising=False)
    conf = build_pdf._disable_color_emoji_font()
    try:
        assert conf and Path(conf).exists()
        text = Path(conf).read_text(encoding="utf-8")
        assert "NotoColorEmoji" in text and "rejectfont" in text
    finally:
        monkeypatch.delenv("FONTCONFIG_FILE", raising=False)
        if conf and Path(conf).exists():
            Path(conf).unlink()


def test_filter_sections_keeps_whole_file_when_no_heading_matches(build_pdf, capsys):
    """A Chinese-headed file must not be silently emptied by English PDF_SECTION_FILTER keys."""
    md = "# 標題\n\n## 模組地圖\n\n內容 A\n\n## 主要流程\n\n內容 B\n"
    out = build_pdf.filter_sections(md, ["## Flow Files"])
    assert "內容 A" in out and "內容 B" in out
    assert "keeping the whole file" in capsys.readouterr().out


def test_filter_sections_still_trims_when_heading_matches(build_pdf):
    md = "# T\n\n## Keep\n\nkeep me\n\n## Drop\n\ndrop me\n"
    out = build_pdf.filter_sections(md, ["## Keep"])
    assert "keep me" in out and "drop me" not in out


def test_find_duplicate_content_groups_identical_files_under_different_names(build_pdf, tmp_path):
    (tmp_path / "a.md").write_text("# Same\n", encoding="utf-8")
    (tmp_path / "b.md").write_text("# Same\n", encoding="utf-8")
    (tmp_path / "c.md").write_text("# Other\n", encoding="utf-8")
    files = [("a.md", str(tmp_path / "a.md"), "1"),
             ("b.md", str(tmp_path / "b.md"), "1"),
             ("c.md", str(tmp_path / "c.md"), "1")]
    groups = build_pdf.find_duplicate_content(files)
    assert groups == [["a.md", "b.md"]]


def test_list_mode_exits_nonzero_on_duplicate_content(build_pdf, tmp_path, monkeypatch, capsys):
    """--list must report duplicates with exit status 1 and must not render."""
    (tmp_path / "document-registry.yaml").write_text(_REGISTRY_YAML, encoding="utf-8")
    (tmp_path / "project-requirements.md").write_text("# Same\n", encoding="utf-8")
    (tmp_path / "copy.md").write_text("# Same\n", encoding="utf-8")
    static = build_pdf._STATIC_PDF_ENTRIES + [("introduction", "copy.md", frozenset({"web-app"}))]
    monkeypatch.setattr(build_pdf, "_STATIC_PDF_ENTRIES", static)
    monkeypatch.setattr(build_pdf.sys, "argv", ["build_pdf.py", str(tmp_path), "--list",
                                                "--project-type", "web-app"])
    with pytest.raises(SystemExit) as exc:
        build_pdf.main()
    assert exc.value.code == 1
    out = capsys.readouterr().out
    assert "Duplicate content:" in out and "copy.md" in out
