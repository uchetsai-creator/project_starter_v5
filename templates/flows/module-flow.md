# Module Flow Index

<!--
  This file is the index and rule definition for all module flow documents.
  Each module's cross-module call sequences have their own dedicated file.
  Each flow file must follow the rules and format defined in this document.

  Naming convention: [module-name]-flow.md
  Location: docs/modules/[module-name]/[module-name]-flow.md
  Examples:
    docs/modules/order/order-flow.md
    docs/modules/payment/payment-flow.md
    docs/modules/inventory/inventory-flow.md

  Files matching *-flow.md are automatically included in the PDF.
  After writing a new flow file, run:
  Edit the ```plantuml block in the file, then rebuild PDF
-->

---

## Rules

* This file acts as the index and rule definition.
* Do not put flow content in this file.
* Each module must have its own flow file if it makes cross-module calls.
* Each flow file must follow the rules and format defined in this document.

### Content Rules

* Describe cross-module service call sequences only.
* One flow file per module — multiple processes can be described in the same file.
* Focus on which service calls which service, in what order.
* Business steps and decision branches belong in docs/business/[process-name]-process.md — not here.

### Sequence Diagram Rules

* Every flow file must include a sequence block for each cross-module process.
* After writing, run: `# Edit the ```plantuml block in the flow file, then rebuild PDF`

---

## Flow Files

| Module | File | Processes covered |
|---|---|---|
| [e.g., Order] | `docs/modules/order/order-flow.md` | [e.g., Create Order, Cancel Order] |
| [module] | `docs/modules/[module]/[module]-flow.md` | [processes] |

---

## Flow File Format

Each flow file must follow this format:

```markdown
# [Module Name] Flow

## Process: [Flow Name, e.g., Create Order]

### Text Overview

Cross-module call sequence at a glance:

\`\`\`
[Caller] → [Service A]: [action]
           [Service A] → [Service B]: [action]
           [Service A] ← [Service B]: [response]
[Caller] ← [Service A]: [final response]
\`\`\`

### Sequence Diagram

\`\`\`plantuml
@startuml
title [Flow Name]

"[Client]"    -> "[Service A]" : [method or HTTP call]
"[Service A]" -> "[Service B]" : [method call]
alt success
  "[Service A]" <-- "[Service B]" : [response]
  "[Service A]" -> "[Service C]" : [method call]
  "[Service A]" <-- "[Service C]" : [response]
  "[Client]"    <-- "[Service A]" : [final response]
else error
  "[Service A]" <-- "[Service B]" : [error / exception]
  "[Client]"    <-- "[Service A]" : [error response]
end
@enduml
\`\`\`

---

## Process: [Another Flow Name, e.g., Cancel Order]

### Text Overview

\`\`\`
[Caller] → [Service A]: [action]
           [Service A] → [Service B]: [action]
[Caller] ← [Service A]: [response]
\`\`\`

### Sequence Diagram

\`\`\`plantuml
@startuml
title [Another Flow Name]

"[Client]"    -> "[Service A]" : [method or HTTP call]
"[Service A]" -> "[Service B]" : [method call]
"[Service A]" <-- "[Service B]" : [response]
"[Client]"    <-- "[Service A]" : [final response]
@enduml
\`\`\`
\`\`\`
```
