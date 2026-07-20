# CLI Contract

<!--
  For: CLI Tool projects
  Replaces: api-contract.md (CLI tools have no HTTP endpoints)
  Purpose: Documents every subcommand, flag, argument, output format, and exit code.
  Update when: A subcommand is added or changed, flags change, output format changes,
               or exit codes are added.
-->

## Command Structure

```
[tool-name] <subcommand> [flags] [arguments]
```

Global flags (apply to all subcommands):

| Flag | Type | Default | Description |
|---|---|---|---|
| `--help`, `-h` | bool | false | Show help |
| `--version`, `-v` | bool | false | Show version |
| `--config` | string | `~/.toolname.yaml` | Path to config file |

---

## Subcommands

Repeat this block for each subcommand.

---

### `[tool-name] [subcommand]`

**Description:** [One line — what this command does]

**Usage:**
```
[tool-name] [subcommand] [flags] <required-arg> [optional-arg]
```

#### Arguments

| Name | Required | Description |
|---|---|---|
| `<required-arg>` | Yes | [What it is] |
| `[optional-arg]` | No | [What it is, default behaviour if omitted] |

#### Flags

| Flag | Short | Type | Default | Description |
|---|---|---|---|---|
| `--output` | `-o` | string | stdout | Output file path |
| `--format` | `-f` | enum (json\|yaml\|table) | table | Output format |
| `--dry-run` | | bool | false | Preview without writing |

#### Output

**Success (exit 0):**
```
[Example stdout output — use real representative output]
```

**Failure (exit 1):**
```
Error: [example error message]
```

#### Exit Codes

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | General error (see stderr for details) |
| 2 | Invalid arguments or flags |
| [other] | [meaning] |

#### Example

```bash
# [Describe what this example does]
[tool-name] [subcommand] --flag value <arg>
```

---

## Config File Format

If the CLI supports a config file, document its schema here.

```yaml
# [tool-name] config (~/.toolname.yaml or .toolname.yaml in project root)
[key]: [value]
[section]:
  [nested-key]: [value]
```

Config file values are overridden by flags. Flags always take precedence.

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `TOOLNAME_CONFIG` | `~/.toolname.yaml` | Config file path override |
| `TOOLNAME_LOG_LEVEL` | `info` | Log verbosity (debug / info / warn / error) |

---

## Stdin / Stdout / Stderr Contract

| Stream | Content |
|---|---|
| stdin | [Accepted if `--input -` is passed / Not used] |
| stdout | [Machine-readable output — JSON / table / plain text] |
| stderr | [Human-readable progress and error messages only] |

**Rule:** stdout must be safe to pipe. Never mix progress messages into stdout.

---

## Non-Functional Requirements

| Metric | Requirement |
|---|---|
| Startup time | < [e.g., 200ms] for all subcommands |
| Execution time | [subcommand]: < [e.g., 5s] for typical input; < [e.g., 60s] for large input |
| Memory usage | Peak < [e.g., 200MB] for [input size] |
| Exit code reliability | Must always exit with a defined code — never hang |

---

## Edge Cases

| Scenario | Expected behaviour |
|---|---|
| Unknown flag passed | `exit 2`; stderr: `unknown flag: --[flag]` |
| Required argument missing | `exit 2`; stderr shows usage line |
| Config file path given but not found | `exit 1`; stderr: `config file not found: [path]` |
| Config file exists but is malformed YAML/TOML | `exit 1`; stderr: parse error with line number |
| `--input -` (stdin) with no data piped | Read until EOF; treat empty input as zero records (not an error) |
| Output file path exists | [Overwrite silently / fail with `exit 1` unless `--force` is passed] |
| Output directory does not exist | `exit 1` with clear message, or create if `--mkdir` flag is present |
| stdout closed by pipe consumer mid-write | Catch `SIGPIPE`; `exit 0` — do not print a crash error |
| Interrupted with Ctrl-C (`SIGINT`) | Clean up partial output files; `exit 130` |
| Input file is empty (zero bytes / zero rows) | [exit 0 with "0 records processed" / exit 1 — specify per subcommand] |

> *Add subcommand-specific edge cases in each `### subcommand` section.*
