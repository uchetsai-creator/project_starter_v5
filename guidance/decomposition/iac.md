# Decomposition — IaC / DevOps

Nouns for `guidance/decomposition/common.md`.

- **Observer:** the operator or the workload running on the infrastructure
- **Entry point:** the resulting infrastructure state — a reachable service, an access rule, a
  running environment
- **Independent Test:** apply to a non-production environment and check the state from outside
  (connectivity, access, `plan` shows no drift)

## Artifact kinds

| Kind | Prefix | In IaC | First failing check |
|---|---|---|---|
| Contract | `CONTRACT` | Module inputs / outputs, variables, naming in `topology.md` | `validate` fails until the variable is declared |
| State | `STATE` | Remote state, backends, data stores the module creates | `plan` shows the expected new resource |
| Logic | `LOGIC` | Resources inside the module | `plan` diff matches the expected change only |
| Entry | `ENTRY` | Environment composition — calling the module from staging / prod | Apply to staging; resource reachable |
| Guard | `GUARD` | Policy, security groups, drift detection, rollback | Policy test: public ingress is rejected |

Never combine a staging and a production apply in one task.

## Typical Guard cases

- Rule would open a port to the internet → policy check fails before apply
- Apply fails half-way → documented rollback in `runbook.md`, state stays consistent
- Manual change in the console → drift detected on the next `plan`

## Example slice

```
SL-1 (P1)  Staging database accepts connections only from the private subnet
  Independent Test: connect from inside the VPC → succeeds; from outside → refused
  Task CONTRACT [SL-1] allowed_cidrs variable                      Covers: FR-001
  Task LOGIC    [SL-1] security group rule in the db module        Covers: FR-001, AC-001
  Task GUARD    [SL-1] policy rejects 0.0.0.0/0 on db ports        Covers: AC-002
  Task ENTRY    [SL-1] staging passes the private subnet CIDR      Covers: AC-001
```
