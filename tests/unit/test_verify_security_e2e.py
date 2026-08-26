"""Real-tool end-to-end tests for verify_security.py's bandit and eslint-plugin-security
paths. test_verify_security.py's tests all monkeypatch _run_bandit/_run_eslint/_run_semgrep
— these instead run the actual tools, to catch exactly the two real bugs found while adding
CI coverage for them (see CHANGELOG.md):

  1. subprocess.run(['eslint', ...]) (bare command name) fails on Windows with
     FileNotFoundError — npm installs eslint as .cmd/.ps1 shims, which Windows
     CreateProcess cannot execute without shell=True. Fixed by passing the fully-resolved
     path from shutil.which() instead of the bare name (applied to bandit/semgrep too,
     for consistency, even though their pip-packaged .exe files happened not to need it).
  2. The original eslint integration assumed the legacy .eslintrc.json config system.
     ESLint 9+ (what `npm install eslint` gets today) removed it entirely in favor of flat
     config (eslint.config.cjs) — confirmed by actually running it, not assumed.

Both are skipped (not failed) when the respective tool isn't installed, matching this
project's convention for real-tool tests (see test_gin_detector.py, test_verify_prose.py).
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_VS_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "templates" / "script" / "validators" / "verify_security.py"
)
_REPO_ROOT = _VS_PATH.parent.parent.parent.parent

_HAS_BANDIT = shutil.which("bandit") is not None


def _eslint_supports_flat_config() -> str | None:
    """--no-config-lookup was only added in ESLint 8.21 — older globally-installed
    eslint binaries (e.g. distro packages, which can lag many major versions behind
    npm's latest) reject it with exit code 2, which would otherwise make this test
    FAIL rather than SKIP on those systems. Returns None if usable, else a skip reason."""
    exe = shutil.which("eslint")
    if exe is None:
        return "eslint not installed"
    try:
        proc = subprocess.run(
            [exe, "--no-config-lookup", "--version"],
            capture_output=True, text=True, timeout=10,
        )
    except OSError:
        return "eslint not installed"
    if proc.returncode != 0:
        return "installed eslint is too old to support --no-config-lookup (needs 8.21+)"
    return None


def _eslint_plugin_security_missing() -> bool:
    """require('eslint-plugin-security') must resolve from _REPO_ROOT (see
    _run_eslint()'s docstring) — it's a devDependency the repo doesn't vendor by
    default, only present after `npm install eslint-plugin-security` there."""
    node = shutil.which("node")
    if node is None:
        return True
    try:
        proc = subprocess.run(
            [node, "-e", "require.resolve('eslint-plugin-security')"],
            capture_output=True, text=True, cwd=str(_REPO_ROOT), timeout=10,
        )
    except OSError:
        return True
    return proc.returncode != 0


_ESLINT_SKIP_REASON = _eslint_supports_flat_config()
if _ESLINT_SKIP_REASON is None and _eslint_plugin_security_missing():
    _ESLINT_SKIP_REASON = "eslint-plugin-security not installed in repo (npm install eslint-plugin-security)"
_HAS_ESLINT = _ESLINT_SKIP_REASON is None


def _run(*args: str, cwd=None) -> subprocess.CompletedProcess:
    import os
    return subprocess.run(
        [sys.executable, str(_VS_PATH), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env={**os.environ, "PYTHONUTF8": "1"}, cwd=cwd,
    )


@pytest.mark.skipif(not _HAS_BANDIT, reason="bandit not installed")
def test_bandit_finds_real_shell_true_issue(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "app.py").write_text(
        "import subprocess\n"
        "def run(user_input):\n"
        "    subprocess.call(user_input, shell=True)\n",
        encoding="utf-8",
    )
    result = _run("--src", str(src), "--json")
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["tools_run"] == ["bandit"]
    rules = {f["rule"] for f in payload["findings"]}
    assert "B602" in rules  # subprocess with shell=True


@pytest.mark.skipif(not _HAS_ESLINT, reason=_ESLINT_SKIP_REASON or "eslint not usable")
def test_eslint_finds_real_eval_and_child_process_issues(tmp_path):
    """The config file must be written inside the repo (where node_modules lives) for
    require('eslint-plugin-security') to resolve — see _run_eslint()'s docstring. This
    test runs verify_security.py with cwd=repo root and --src pointed at a location
    still inside that tree, matching real usage (security_scan_src is always a path
    under the project, never an unrelated external directory)."""
    src = _REPO_ROOT / "tmp_test_eslint_e2e_src"
    src.mkdir(exist_ok=True)
    try:
        (src / "app.js").write_text(
            "const { exec } = require('child_process');\n"
            "function run(userInput) {\n"
            "    eval(userInput);\n"
            "    exec(userInput);\n"
            "}\n",
            encoding="utf-8",
        )
        result = _run("--src", "tmp_test_eslint_e2e_src", "--json", cwd=str(_REPO_ROOT))
        assert result.returncode == 0, result.stdout + result.stderr
        payload = json.loads(result.stdout)
        assert payload["tools_run"] == ["eslint-plugin-security"]
        rules = {f["rule"] for f in payload["findings"]}
        assert "security/detect-eval-with-expression" in rules
        assert "security/detect-child-process" in rules
    finally:
        shutil.rmtree(src, ignore_errors=True)
        # Confirm the throwaway config was actually cleaned up, not just that the test passed.
        leftover = list(_REPO_ROOT.glob(".eslint-security-*.config.cjs"))
        assert leftover == [], f"leftover eslint config file(s) not cleaned up: {leftover}"
