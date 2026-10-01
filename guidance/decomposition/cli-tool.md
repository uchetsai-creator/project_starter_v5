# Decomposition — CLI Tool

Nouns for `guidance/decomposition/common.md`.

- **Observer:** the person or script running the command
- **Entry point:** a command / subcommand with its flags, stdin, stdout, stderr, exit code
- **Independent Test:** run the command with fixed input and check exit code, stdout and any
  file written

## Artifact kinds

| Kind | Prefix | In a CLI tool | First failing check |
|---|---|---|---|
| Contract | `CONTRACT` | Command name, flags, defaults, exit codes in `cli-contract.md` | `--help` test lists the new flag with its default |
| State | `STATE` | Config file format, cache / state file on disk | Test: config written then read back |
| Logic | `LOGIC` | Core function the command calls (no argument parsing inside) | Unit test on the function's return value |
| Entry | `ENTRY` | Wiring the parsed arguments to the core function, output formatting | CLI runner test: exit 0 and expected stdout |
| Guard | `GUARD` | Bad arguments, missing files, partial failure, Ctrl-C | CLI runner test: exit code 2 and message on stderr |

Keep Logic free of argument parsing so it is testable without invoking the CLI.

## Typical Guard cases

- Unknown flag value / missing required argument → usage error, exit code 2
- Input file missing or unreadable → clear message on stderr, non-zero exit, nothing written
- Interrupted mid-write → no half-written output file left behind

## Example slice

```
SL-1 (P1)  `tool export --format csv` writes CSV to stdout
  Independent Test: run it on the fixture → exit 0, first line is the header row
  Task CONTRACT [SL-1] --format flag and accepted values          Covers: FR-001
  Task LOGIC    [SL-1] CSV serialiser                             Covers: FR-001, AC-001
  Task GUARD    [SL-1] unsupported format → exit 2                Covers: AC-002
  Task ENTRY    [SL-1] export command calls serialiser            Covers: AC-001
```
