#!/usr/bin/env python3
"""
detect_type.py — Infer project type from code structure and/or requirements text.

Scans file layout, dependency manifests, and optional requirements text.
Outputs a ranked recommendation — including hybrid types (e.g. web-app+llm-app).

Usage:
  python3 detect_type.py                            # scan current directory
  python3 detect_type.py /path/to/project           # scan specific directory
  python3 detect_type.py --requirements "web API"   # text-only (no scan)
  python3 detect_type.py /path --requirements "..."  # both
  python3 detect_type.py --json                      # machine-readable output
  python3 detect_type.py --apply                     # write result to .project-starter.yml

Valid output types: web-app | cli-tool | library | data-pipeline | ml-pipeline
                    microservices | llm-app | iac | mobile-app
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_TYPES = [
    "web-app", "cli-tool", "library", "data-pipeline",
    "ml-pipeline", "microservices", "llm-app", "iac", "mobile-app",
]

# Score at or above this → type is "primary"
PRIMARY_THRESHOLD = 20
# Score at or above this (and ≥40% of top score) → type qualifies for hybrid
HYBRID_THRESHOLD = 10
HYBRID_RATIO = 0.40


# ---------------------------------------------------------------------------
# Signal rules
# ---------------------------------------------------------------------------
# Each rule is: (signal_type, pattern, project_type, weight)
#   signal_type: "file_exists" | "dir_exists" | "file_glob" | "content" | "dep"
#   pattern    : glob / regex / package name depending on signal_type
#   project_type: one of VALID_TYPES
#   weight     : integer points added to that type's score

_FILE_EXISTS_RULES: list[tuple[str, int]] = [
    # IaC
    ("main.tf",            "iac",           25),
    ("terraform.tfvars",   "iac",           20),
    ("terragrunt.hcl",     "iac",           20),
    ("playbook.yml",       "iac",           18),
    ("playbook.yaml",      "iac",           18),
    ("Pulumi.yaml",        "iac",           20),
    ("Pulumi.yml",         "iac",           20),
    ("serverless.yml",     "iac",           15),
    ("serverless.yaml",    "iac",           15),
    ("cdk.json",           "iac",           18),
    # Mobile
    ("pubspec.yaml",       "mobile-app",    30),
    ("android/build.gradle", "mobile-app",  25),
    ("ios/Podfile",        "mobile-app",    25),
    ("metro.config.js",    "mobile-app",    20),
    ("app.json",           "mobile-app",    10),
    # Web / API
    ("next.config.js",     "web-app",       25),
    ("next.config.ts",     "web-app",       25),
    ("nuxt.config.js",     "web-app",       25),
    ("nuxt.config.ts",     "web-app",       25),
    ("vite.config.js",     "web-app",       15),
    ("vite.config.ts",     "web-app",       15),
    ("webpack.config.js",  "web-app",       12),
    ("svelte.config.js",   "web-app",       20),
    ("angular.json",       "web-app",       25),
    # ML
    ("train.py",           "ml-pipeline",   18),
    ("evaluate.py",        "ml-pipeline",   15),
    ("model.py",           "ml-pipeline",   12),
    # Library
    ("setup.py",           "library",       15),
    ("setup.cfg",          "library",       10),
    ("MANIFEST.in",        "library",       12),
    # CLI
    ("__main__.py",        "cli-tool",      15),
]

_DIR_EXISTS_RULES: list[tuple[str, int]] = [
    # IaC
    ("modules",            "iac",           12),
    (".terraform",         "iac",           25),
    ("ansible",            "iac",           15),
    # Mobile
    ("android",            "mobile-app",    18),
    ("ios",                "mobile-app",    18),
    ("lib",                "mobile-app",    8),   # flutter lib/
    # Microservices
    ("services",           "microservices", 18),
    ("k8s",                "microservices", 20),
    ("kubernetes",         "microservices", 20),
    ("helm",               "microservices", 18),
    ("charts",             "microservices", 15),
    # Data pipeline
    ("dags",               "data-pipeline", 25),
    ("pipelines",          "data-pipeline", 12),
    ("etl",                "data-pipeline", 18),
    # ML
    ("notebooks",          "ml-pipeline",   18),
    ("experiments",        "ml-pipeline",   15),
    ("models",             "ml-pipeline",   12),
    ("checkpoints",        "ml-pipeline",   15),
    ("data",               "ml-pipeline",   5),
    # Web
    ("public",             "web-app",       8),
    ("static",             "web-app",       8),
    ("templates",          "web-app",       5),
    ("views",              "web-app",       8),
    ("routes",             "web-app",       12),
    ("controllers",        "web-app",       10),
    ("frontend",           "web-app",       18),
    ("src/pages",          "web-app",       20),
    ("src/components",     "web-app",       18),
    ("pages",              "web-app",       12),
    ("components",         "web-app",       8),
    # LLM
    ("prompts",            "llm-app",       20),
    ("chains",             "llm-app",       18),
    ("agents",             "llm-app",       12),
    ("rag",                "llm-app",       22),
    ("embeddings",         "llm-app",       18),
]

# Python dependencies (requirements.txt / pyproject.toml / setup.py)
_PYTHON_DEP_RULES: list[tuple[str, int]] = [
    # Web
    ("fastapi",            "web-app",       25),
    ("flask",              "web-app",       22),
    ("django",             "web-app",       22),
    ("starlette",          "web-app",       20),
    ("aiohttp",            "web-app",       15),
    ("tornado",            "web-app",       15),
    ("sanic",              "web-app",       18),
    ("litestar",           "web-app",       18),
    # Data pipeline
    ("apache-airflow",     "data-pipeline", 30),
    ("airflow",            "data-pipeline", 28),
    ("prefect",            "data-pipeline", 28),
    ("dagster",            "data-pipeline", 28),
    ("luigi",              "data-pipeline", 25),
    ("dask",               "data-pipeline", 18),
    ("apache-beam",        "data-pipeline", 25),
    ("pyspark",            "data-pipeline", 22),
    ("great-expectations", "data-pipeline", 15),
    ("pandas",             "data-pipeline", 8),
    ("polars",             "data-pipeline", 8),
    # ML
    ("scikit-learn",       "ml-pipeline",   25),
    ("sklearn",            "ml-pipeline",   25),
    ("tensorflow",         "ml-pipeline",   28),
    ("torch",              "ml-pipeline",   28),
    ("pytorch",            "ml-pipeline",   28),
    ("keras",              "ml-pipeline",   25),
    ("xgboost",            "ml-pipeline",   22),
    ("lightgbm",           "ml-pipeline",   22),
    ("catboost",           "ml-pipeline",   20),
    ("mlflow",             "ml-pipeline",   20),
    ("wandb",              "ml-pipeline",   18),
    ("optuna",             "ml-pipeline",   15),
    ("huggingface",        "ml-pipeline",   18),
    ("transformers",       "ml-pipeline",   18),
    # LLM
    ("langchain",          "llm-app",       28),
    ("langgraph",          "llm-app",       28),
    ("openai",             "llm-app",       20),
    ("anthropic",          "llm-app",       20),
    ("llama-index",        "llm-app",       25),
    ("llama_index",        "llm-app",       25),
    ("litellm",            "llm-app",       22),
    ("chromadb",           "llm-app",       20),
    ("pinecone",           "llm-app",       20),
    ("weaviate",           "llm-app",       20),
    ("qdrant",             "llm-app",       20),
    ("semantic-kernel",    "llm-app",       25),
    ("haystack",           "llm-app",       22),
    # CLI
    ("click",              "cli-tool",      22),
    ("typer",              "cli-tool",      22),
    ("argparse",           "cli-tool",      10),
    ("rich",               "cli-tool",      8),
    ("questionary",        "cli-tool",      15),
    ("prompt-toolkit",     "cli-tool",      12),
    # IaC
    ("ansible",            "iac",           25),
    ("pulumi",             "iac",           25),
    ("cdktf",              "iac",           22),
    ("troposphere",        "iac",           20),
    ("boto3",              "iac",           8),
]

# Node.js dependencies (package.json)
_NODE_DEP_RULES: list[tuple[str, int]] = [
    # Web frameworks
    ("express",            "web-app",       25),
    ("fastify",            "web-app",       25),
    ("koa",                "web-app",       22),
    ("hapi",               "web-app",       20),
    ("nestjs",             "web-app",       22),
    ("@nestjs/core",       "web-app",       25),
    ("react",              "web-app",       20),
    ("react-dom",          "web-app",       20),
    ("vue",                "web-app",       20),
    ("@vue/core",          "web-app",       20),
    ("angular",            "web-app",       20),
    ("@angular/core",      "web-app",       25),
    ("svelte",             "web-app",       20),
    ("next",               "web-app",       25),
    ("nuxt",               "web-app",       25),
    ("gatsby",             "web-app",       22),
    ("remix",              "web-app",       22),
    ("astro",              "web-app",       20),
    # Mobile
    ("react-native",       "mobile-app",    30),
    ("expo",               "mobile-app",    28),
    ("@capacitor/core",    "mobile-app",    25),
    ("ionic",              "mobile-app",    22),
    # LLM
    ("langchain",          "llm-app",       25),
    ("@langchain/core",    "llm-app",       25),
    ("openai",             "llm-app",       20),
    ("@anthropic-ai/sdk",  "llm-app",       20),
    ("ai",                 "llm-app",       15),
    # CLI
    ("commander",          "cli-tool",      20),
    ("yargs",              "cli-tool",      20),
    ("inquirer",           "cli-tool",      15),
    ("ink",                "cli-tool",      18),
    # Microservices
    ("grpc",               "microservices", 22),
    ("@grpc/grpc-js",      "microservices", 22),
    ("kafkajs",            "microservices", 20),
    ("amqplib",            "microservices", 18),
    ("bull",               "microservices", 15),
    ("moleculer",          "microservices", 25),
]

# File-glob patterns (match by extension or name pattern in the tree)
_GLOB_RULES: list[tuple[str, int]] = [
    # IaC
    ("**/*.tf",            "iac",           25),
    ("**/*.tfvars",        "iac",           18),
    ("**/*.hcl",           "iac",           15),
    ("**/playbook*.yml",   "iac",           18),
    ("**/playbook*.yaml",  "iac",           18),
    ("**/Pulumi.yaml",     "iac",           20),
    # ML
    ("**/*.ipynb",         "ml-pipeline",   20),
    ("**/train*.py",       "ml-pipeline",   15),
    ("**/model*.py",       "ml-pipeline",   12),
    # Mobile Swift
    ("**/*.swift",         "mobile-app",    18),
    ("**/*.xcodeproj",     "mobile-app",    25),
    ("**/*.xcworkspace",   "mobile-app",    25),
    # Data — narrow patterns to avoid matching 'dagster.py' adapter files
    ("dags/**/*.py",       "data-pipeline", 20),
    ("dags/*.py",          "data-pipeline", 20),
    ("**/pipeline_*.py",   "data-pipeline", 12),
]

# Keyword rules for requirements text (lowercased match)
_KEYWORD_RULES: list[tuple[str, int]] = [
    # web-app
    (r"\bweb\s*app\b",             "web-app",       20),
    (r"\brest\s*api\b",            "web-app",       20),
    (r"\bhttp\s*api\b",            "web-app",       18),
    (r"\brest\s*endpoint",         "web-app",       18),
    (r"\bfrontend\b",              "web-app",       15),
    (r"\bback[\s-]?end\b",         "web-app",       12),
    (r"\bweb\s*server\b",          "web-app",       18),
    (r"\bsingle[\s-]page",         "web-app",       18),
    (r"\bspa\b",                   "web-app",       18),
    (r"\bapi\s*endpoint",          "web-app",       15),
    (r"\bhttp\b",                  "web-app",       8),
    (r"\bwebsite\b",               "web-app",       12),
    (r"\bdashboard\b",             "web-app",       10),
    # cli-tool
    (r"\bcli\b",                   "cli-tool",      22),
    (r"\bcommand[\s-]line\b",      "cli-tool",      22),
    (r"\bterminal\s*tool\b",       "cli-tool",      20),
    (r"\bcommand\s*line\s*tool\b", "cli-tool",      25),
    (r"\bscript\b",                "cli-tool",      8),
    (r"\bshell\s*tool\b",          "cli-tool",      18),
    # library
    (r"\blibrary\b",               "library",       22),
    (r"\bpackage\b",               "library",       15),
    (r"\bsdk\b",                   "library",       20),
    (r"\bopen[\s-]?source\s*lib",  "library",       20),
    (r"\bpypi\b",                  "library",       22),
    (r"\bnpm\s*package\b",         "library",       22),
    (r"\bmodule\b",                "library",       8),
    # data-pipeline
    (r"\betl\b",                   "data-pipeline", 25),
    (r"\bdata\s*pipeline",         "data-pipeline", 25),
    (r"\bbatch\s*(job|process)",   "data-pipeline", 22),
    (r"\bingestion\b",             "data-pipeline", 20),
    (r"\borchestrat",              "data-pipeline", 15),
    (r"\bworkflow\b",              "data-pipeline", 8),
    (r"\bdata\s*warehouse\b",      "data-pipeline", 20),
    (r"\bdata\s*lake\b",           "data-pipeline", 20),
    (r"\bairflow\b",               "data-pipeline", 25),
    (r"\bprefect\b",               "data-pipeline", 25),
    (r"\bdagster\b",               "data-pipeline", 25),
    # ml-pipeline
    (r"\bmachine\s*learning\b",    "ml-pipeline",   25),
    (r"\bml\s*pipeline\b",         "ml-pipeline",   25),
    (r"\bmodel\s*train",           "ml-pipeline",   22),
    (r"\bneural\s*net",            "ml-pipeline",   22),
    (r"\bdeep\s*learning\b",       "ml-pipeline",   25),
    (r"\bml\b",                    "ml-pipeline",   8),
    (r"\bprediction\s*model\b",    "ml-pipeline",   20),
    (r"\bclassif",                 "ml-pipeline",   15),
    (r"\bregression\b",            "ml-pipeline",   12),
    (r"\bfeature\s*engineer",      "ml-pipeline",   18),
    (r"\bmlops\b",                 "ml-pipeline",   22),
    (r"\bexperiment\s*track",      "ml-pipeline",   18),
    # microservices
    (r"\bmicroservice",            "microservices", 25),
    (r"\bservice\s*mesh\b",        "microservices", 22),
    (r"\bkubernetes\b",            "microservices", 18),
    (r"\bk8s\b",                   "microservices", 18),
    (r"\bdocker\s*compose\b",      "microservices", 12),
    (r"\bevent[\s-]driven\b",      "microservices", 15),
    (r"\bmessage\s*queue\b",       "microservices", 15),
    (r"\bkafka\b",                 "microservices", 18),
    (r"\bgraphql\s*gateway\b",     "microservices", 18),
    # llm-app
    (r"\bllm\b",                   "llm-app",       25),
    (r"\bai\s*agent\b",            "llm-app",       22),
    (r"\bchatbot\b",               "llm-app",       20),
    (r"\brag\b",                   "llm-app",       25),
    (r"\bembedding",               "llm-app",       18),
    (r"\bprompt\s*engineer",       "llm-app",       18),
    (r"\blangchain\b",             "llm-app",       22),
    (r"\bgpt\b",                   "llm-app",       18),
    (r"\bclaude\b",                "llm-app",       18),
    (r"\bgenerative\s*ai\b",       "llm-app",       22),
    (r"\bvector\s*db\b",           "llm-app",       20),
    (r"\bvector\s*store\b",        "llm-app",       20),
    (r"\bsemantic\s*search\b",     "llm-app",       20),
    (r"\bfine[\s-]?tun",           "llm-app",       18),
    # iac
    (r"\binfrastructure\s*as\s*code\b", "iac",      25),
    (r"\biac\b",                   "iac",           25),
    (r"\bterraform\b",             "iac",           25),
    (r"\bprovision",               "iac",           15),
    (r"\bcloud\s*infra",           "iac",           18),
    (r"\bansible\b",               "iac",           22),
    (r"\bpulumi\b",                "iac",           22),
    (r"\bhelm\s*chart",            "iac",           18),
    # mobile-app
    (r"\bmobile\s*app\b",          "mobile-app",    25),
    (r"\bios\s*app\b",             "mobile-app",    22),
    (r"\bandroid\s*app\b",         "mobile-app",    22),
    (r"\breact\s*native\b",        "mobile-app",    25),
    (r"\bflutter\b",               "mobile-app",    25),
    (r"\bswiftui\b",               "mobile-app",    25),
    (r"\bxcode\b",                 "mobile-app",    20),
]

# Signals that also identify which verify_spec_code.py adapter applies — a strict
# subset of the rules above (most type signals, e.g. "pandas" or "docker compose",
# have no corresponding adapter). Order is priority within a project type: the first
# matching row wins. Keep the (adapter alias, project type) pairs in sync with
# .githooks/pre-commit's per-type adapter list and ADAPTER_REGISTRY in
# templates/script/validators/verify_spec_code.py.
_ADAPTER_SIGNALS: list[tuple[str, str, str, str]] = [
    # (kind, pattern, adapter alias, project type)
    ("py_dep",   "fastapi",       "fastapi",      "web-app"),
    ("py_dep",   "flask",         "flask",        "web-app"),
    ("py_dep",   "django",        "django",       "web-app"),
    ("node_dep", "express",       "express",      "web-app"),
    ("py_dep",   "click",         "click",        "cli-tool"),
    ("py_dep",   "typer",         "typer",        "cli-tool"),
    ("py_dep",   "apache-airflow","airflow",      "data-pipeline"),
    ("py_dep",   "airflow",       "airflow",      "data-pipeline"),
    ("py_dep",   "dagster",       "dagster",      "data-pipeline"),
    ("py_dep",   "prefect",       "prefect",      "data-pipeline"),
    ("py_dep",   "luigi",         "luigi",        "data-pipeline"),
    ("py_dep",   "langchain",     "langchain",    "llm-app"),
    ("node_dep", "langchain",     "langchain",    "llm-app"),
    ("py_dep",   "ansible",       "ansible",      "iac"),
    ("py_dep",   "pulumi",        "pulumi",       "iac"),
    ("file_glob","**/*.tf",       "terraform",    "iac"),
    ("node_dep", "react-native",  "react_native", "mobile-app"),
    ("file",     "pubspec.yaml",  "flutter",      "mobile-app"),
    ("file_glob","**/*.swift",    "swiftui",      "mobile-app"),
]

# project_type → canonical spec contract path (relative to docs/), mirroring
# document-registry.yaml. hybrid types (e.g. "web-app+llm-app") are intentionally
# not covered — spec_code_adapter is single-valued, so a suggestion is only made
# for a clear, non-hybrid recommendation.
_CANONICAL_SPEC_FILE: dict[str, str] = {
    "web-app":       "docs/specs/api-contract.md",
    "microservices": "docs/specs/api-contract.md",
    "cli-tool":      "docs/specs/cli-contract.md",
    "library":       "docs/specs/public-api.md",
    "data-pipeline": "docs/specs/pipeline-contract.md",
    "ml-pipeline":   "docs/specs/pipeline-contract.md",
    "llm-app":       "docs/specs/llm-contract.md",
    "iac":           "docs/architecture/topology.md",
    "mobile-app":    "docs/specs/mobile-contract.md",
}


# ---------------------------------------------------------------------------
# Scanning helpers
# ---------------------------------------------------------------------------

def _read_dep_names(root: Path) -> tuple[set[str], set[str]]:
    """Return (python_deps, node_deps) as lowercase sets."""
    python_deps: set[str] = set()
    node_deps: set[str] = set()

    # requirements*.txt
    for req_file in root.glob("requirements*.txt"):
        try:
            for line in req_file.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                pkg = re.split(r"[>=<!;]", line)[0].strip().lower()
                if pkg:
                    python_deps.add(pkg)
        except OSError:
            pass

    # pyproject.toml — extract dependency names (best effort)
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        try:
            text = pyproject.read_text(encoding="utf-8", errors="ignore")
            for m in re.finditer(r'"([a-zA-Z0-9_\-\.]+)\s*[>=<!\[]', text):
                python_deps.add(m.group(1).lower())
        except OSError:
            pass

    # setup.py / setup.cfg
    for sfile in (root / "setup.py", root / "setup.cfg"):
        if sfile.exists():
            try:
                text = sfile.read_text(encoding="utf-8", errors="ignore")
                for m in re.finditer(r"['\"]([a-zA-Z0-9_\-\.]+)\s*[>=<!\[]?['\"]", text):
                    python_deps.add(m.group(1).lower())
            except OSError:
                pass

    # package.json
    pkg_json = root / "package.json"
    if pkg_json.exists():
        try:
            data = json.loads(pkg_json.read_text(encoding="utf-8", errors="ignore"))
            for section in ("dependencies", "devDependencies", "peerDependencies"):
                for pkg in data.get(section, {}):
                    node_deps.add(pkg.lower())
        except (OSError, json.JSONDecodeError):
            pass

    return python_deps, node_deps


def _suggest_adapter(root: Path, project_type: str) -> str | None:
    """Return the first verify_spec_code.py adapter alias whose signal is present in
    root and whose project type matches, or None if nothing matched. Reuses
    _read_dep_names — no separate dependency-parsing pass."""
    python_deps, node_deps = _read_dep_names(root)
    for kind, pattern, adapter, ptype in _ADAPTER_SIGNALS:
        if ptype != project_type:
            continue
        if kind == "py_dep" and pattern in python_deps:
            return adapter
        if kind == "node_dep" and pattern in node_deps:
            return adapter
        if kind == "file" and (root / pattern).exists():
            return adapter
        if kind == "file_glob" and next(root.glob(pattern), None) is not None:
            return adapter
    return None


def _guess_src_dir(root: Path) -> str:
    """Best-effort source directory guess — always a guess, never authoritative;
    the caller must mark it as unverified."""
    for candidate in ("src", "app", "lib"):
        if (root / candidate).is_dir():
            return f"{candidate}/"
    return "src/"


def _suggest_spec_code(root: Path, recommendation: str) -> dict[str, str] | None:
    """Suggest spec_code_adapter/spec_code_spec/spec_code_src for a non-hybrid
    recommendation, or None if no adapter signal matched. Never authoritative —
    always presented to the user as a starting guess to verify, not applied silently
    to an existing .project-starter.yml."""
    if "+" in recommendation or recommendation not in _CANONICAL_SPEC_FILE:
        return None
    adapter = _suggest_adapter(root, recommendation)
    if not adapter:
        return None
    return {
        "adapter": adapter,
        "spec": _CANONICAL_SPEC_FILE[recommendation],
        "src": _guess_src_dir(root),
    }


def _score_directory(root: Path) -> dict[str, int]:
    scores: dict[str, int] = {t: 0 for t in VALID_TYPES}

    if not root.is_dir():
        return scores

    # File-exists rules
    for filename, ptype, weight in _FILE_EXISTS_RULES:
        if (root / filename).exists():
            scores[ptype] += weight

    # Dir-exists rules
    for dirname, ptype, weight in _DIR_EXISTS_RULES:
        if (root / dirname).is_dir():
            scores[ptype] += weight

    # Glob rules (limit depth to avoid huge scans)
    for pattern, ptype, weight in _GLOB_RULES:
        matches = list(root.glob(pattern))
        if matches:
            # Count up to 3 matches to avoid over-weighting huge repos
            scores[ptype] += min(len(matches), 3) * weight // 2 + weight // 2

    # Dep rules
    python_deps, node_deps = _read_dep_names(root)
    for pkg, ptype, weight in _PYTHON_DEP_RULES:
        if pkg.lower() in python_deps:
            scores[ptype] += weight
    for pkg, ptype, weight in _NODE_DEP_RULES:
        if pkg.lower() in node_deps:
            scores[ptype] += weight

    # Microservices heuristic: multiple *-service directories
    service_dirs = [d for d in root.iterdir() if d.is_dir() and d.name.endswith(("-service", "_service"))]
    if len(service_dirs) >= 2:
        scores["microservices"] += 20 * min(len(service_dirs), 3)

    return scores


def _score_requirements(text: str) -> dict[str, int]:
    scores: dict[str, int] = {t: 0 for t in VALID_TYPES}
    lowered = text.lower()
    for pattern, ptype, weight in _KEYWORD_RULES:
        if re.search(pattern, lowered):
            scores[ptype] += weight
    return scores


def _merge(a: dict[str, int], b: dict[str, int]) -> dict[str, int]:
    return {t: a[t] + b[t] for t in VALID_TYPES}


def _recommend(scores: dict[str, int]) -> tuple[str, list[tuple[str, int]]]:
    """Return (recommended_type_string, ranked_list_of_(type, score))."""
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    ranked = [(t, s) for t, s in ranked if s > 0]

    if not ranked:
        return "web-app", []  # default fallback

    top_type, top_score = ranked[0]

    if top_score < PRIMARY_THRESHOLD:
        return top_type, ranked

    # Check for hybrid: second type with meaningful score
    hybrid_parts = [top_type]
    for other_type, other_score in ranked[1:]:
        if other_score >= HYBRID_THRESHOLD and other_score >= top_score * HYBRID_RATIO:
            hybrid_parts.append(other_type)
        if len(hybrid_parts) == 2:
            break

    recommendation = "+".join(hybrid_parts)
    return recommendation, ranked


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    # Force UTF-8 stdout/stderr — without this, a non-ASCII character (e.g. "→")
    # crashes print() with UnicodeEncodeError on a non-UTF-8-default Windows console
    # (confirmed in CI on windows-latest; see orchestrator.py's main() and CHANGELOG.md).
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="Infer project type from code structure and/or requirements text.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("Usage:")[1] if "Usage:" in __doc__ else "",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Project directory to scan (default: current directory)",
    )
    parser.add_argument(
        "--requirements", "-r",
        metavar="TEXT",
        help="Requirements description text (supplement or replace directory scan)",
    )
    parser.add_argument(
        "--no-scan",
        action="store_true",
        help="Skip directory scan; use only --requirements text",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output machine-readable JSON",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write detected type into .project-starter.yml (creates it if absent)",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=PRIMARY_THRESHOLD,
        metavar="N",
        help=f"Minimum score for a primary type (default: {PRIMARY_THRESHOLD})",
    )
    args = parser.parse_args()

    root = Path(args.path).resolve()

    # When requirements text is given without an explicit path, skip the scan
    # so the framework repo itself doesn't pollute results.
    path_explicitly_given = args.path != "."
    skip_scan = args.no_scan or (args.requirements and not path_explicitly_given)

    dir_scores: dict[str, int] = {t: 0 for t in VALID_TYPES}
    req_scores: dict[str, int] = {t: 0 for t in VALID_TYPES}

    if not skip_scan:
        if not root.is_dir():
            print(f"[FAIL] Not a directory: {root}", file=sys.stderr)
            sys.exit(1)
        dir_scores = _score_directory(root)

    if args.requirements:
        req_scores = _score_requirements(args.requirements)

    combined = _merge(dir_scores, req_scores)
    recommendation, ranked = _recommend(combined)
    top_score = ranked[0][1] if ranked else 0

    spec_code_suggestion = _suggest_spec_code(root, recommendation) if not skip_scan else None

    if args.json:
        output = {
            "recommendation": recommendation,
            "scores": {t: combined[t] for t in VALID_TYPES},
            "ranked": [{"type": t, "score": s} for t, s in ranked],
            "confidence": "high" if top_score >= 40 else "medium" if top_score >= PRIMARY_THRESHOLD else "low",
            "spec_code_suggestion": spec_code_suggestion,
        }
        print(json.dumps(output, indent=2))
        return

    # Human-readable output
    print(f"\nDetected project type: {recommendation}")
    if "+" in recommendation:
        print("  (hybrid — multiple strong signals detected)")

    confidence = "high" if top_score >= 40 else "medium" if top_score >= PRIMARY_THRESHOLD else "low"
    print(f"Confidence: {confidence}")
    print()

    if ranked:
        print("Score breakdown:")
        for t, s in ranked[:6]:
            bar = "█" * min(s // 5, 20)
            marker = " ←" if t in recommendation.split("+") else ""
            print(f"  {t:<16} {s:>4}  {bar}{marker}")
    else:
        print("No signals detected — defaulting to web-app.")
        print("Tip: run with --requirements to provide a description of your project.")

    if spec_code_suggestion:
        print()
        print("Spec <-> code drift detection looks available for this project (unverified guess):")
        print(f"  spec_code_adapter: {spec_code_suggestion['adapter']}")
        print(f"  spec_code_spec:    {spec_code_suggestion['spec']}")
        print(f"  spec_code_src:     {spec_code_suggestion['src']}")
        print("Verify these three values, then add them to .project-starter.yml (or use --apply")
        print("on a fresh project) to catch spec<->code drift automatically at every commit —")
        print("see README.md -> Spec <-> Code Validator.")

    print()
    if args.apply:
        yml = root / ".project-starter.yml"
        if yml.exists():
            text = yml.read_text(encoding="utf-8")
            new_text = re.sub(
                r"^project_type:.*$",
                f"project_type: {recommendation}",
                text,
                flags=re.MULTILINE,
            )
            yml.write_text(new_text, encoding="utf-8")
            print(f"[OK] Updated project_type in {yml}")
            if spec_code_suggestion:
                print("     spec_code_adapter/spec/src left untouched — this file already exists;")
                print("     see the suggestion above to fill them in by hand.")
        else:
            if spec_code_suggestion:
                yml.write_text(
                    f"# project_starter — project configuration\n"
                    f"project_type: {recommendation}\n"
                    f"docs_path: docs/\n"
                    f"task_type:\n"
                    f"# spec_code_* below is an UNVERIFIED guess from detect_type.py — confirm the\n"
                    f"# adapter, spec path, and src path actually match this project before relying\n"
                    f"# on it; clear all three to disable the gate.\n"
                    f"spec_code_adapter: {spec_code_suggestion['adapter']}\n"
                    f"spec_code_spec: {spec_code_suggestion['spec']}\n"
                    f"spec_code_src: {spec_code_suggestion['src']}\n",
                    encoding="utf-8",
                )
                print(f"[OK] Created {yml} with project_type: {recommendation}")
                print("     spec_code_adapter/spec/src pre-filled with an unverified guess — confirm before relying on it.")
            else:
                yml.write_text(
                    f"# project_starter — project configuration\n"
                    f"project_type: {recommendation}\n"
                    f"docs_path: docs/\n"
                    f"task_type:\n",
                    encoding="utf-8",
                )
                print(f"[OK] Created {yml} with project_type: {recommendation}")
    else:
        print(f"To apply:  python3 detect_type.py {args.path} --apply")
        print(f"To init:   bash setup.sh --init {recommendation} {args.path}")


if __name__ == "__main__":
    main()
