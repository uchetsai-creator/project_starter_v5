# Business Objects Index

<!--
  This file is the index and rule definition for all business object documents.
  Each business entity has its own dedicated file under docs/business/.
  Each object file must follow the rules and format defined in this document.

  Naming convention: [object-name]-object.md
  Location: docs/business/[object-name]-object.md
  Examples:
    docs/business/order-object.md
    docs/business/customer-object.md
    docs/business/product-object.md

  Files matching *-object.md are automatically included in the PDF.
  State diagrams are rendered automatically by build_pdf.py — no separate step needed.
  To regenerate the PDF after writing a new object file, run:
  python3 docs/script/generators/build_pdf.py docs --lang en -o docs/project-documentation-en.pdf
-->

---

## Rules

* This file acts as the index.
* Do not put object content here — each business entity must have its own file.
* Each object file must follow the rules and format defined in this document.

### Content Rules

* Focus on the entity's lifecycle and domain relationships — not which service handles each transition.
* Technical implementation (column names, query patterns) belongs in `docs/specs/data-model.md`.
* State transitions in `*-object.md` are the canonical source of truth — keep `data-model.md` state section in sync with this file, not the other way around.

### State Diagram Rules

* Every object file must include a `plantuml` state diagram block.
* The diagram shows business states and transition conditions only.
* Do not reference database columns, services, or code in the diagram.
* State diagrams are rendered by `build_pdf.py` — no separate script needed.

---

## Relationships

<!--
  Include this section when 3+ objects have non-trivial relationships.
  Remove for simple projects with only 1-2 objects.
-->

| Object | Relates to | Relationship |
|---|---|---|
| [e.g., Order] | [e.g., Customer] | [e.g., N:1 — each order belongs to one customer] |
| [e.g., Order] | [e.g., Product] | [e.g., N:M — each order contains multiple products via line items] |

---

## Object Files

| Object | File | Status field | States |
|---|---|---|---|
| [e.g., Order] | `docs/business/order-object.md` | `status` | [e.g., PENDING → CONFIRMED → SHIPPED → DELIVERED / CANCELLED] |
| [object name] | `docs/business/[object-name]-object.md` | [field] | [states] |

---

## Object File Format

Each object file must follow this format exactly:

```markdown
# [Object Name]

## Business Purpose
[What business entity does this represent? 1–2 sentences describing its role in the domain.]

## Lifecycle States

| State | Meaning | Who sets it |
|---|---|---|
| `[STATUS_A]` | [What this state means in business terms] | [e.g., Customer / System / Ops] |
| `[STATUS_B]` | [What this state means] | [e.g., System after payment confirmation] |
| `[STATUS_C]` | [Terminal state] | [e.g., System] |
| `[STATUS_D]` | [Terminal state — cancelled] | [e.g., Customer or Ops] |

## State Diagram

\`\`\`plantuml
@startuml
hide empty description
title [Object Name] Lifecycle

[*]         --> STATUS_A : [Trigger: e.g., created]
STATUS_A    --> STATUS_B : [Condition: e.g., payment confirmed]
STATUS_A    --> STATUS_D : [Condition: e.g., customer cancels]
STATUS_B    --> STATUS_C : [Condition: e.g., delivered]
STATUS_B    --> STATUS_D : [Condition: e.g., ops cancels]
STATUS_C    --> [*]
STATUS_D    --> [*]
@enduml
\`\`\`

## Relationships

| Related object | Relationship | Notes |
|---|---|---|
| [e.g., Customer] | N:1 — each [object] belongs to one customer | [e.g., FK: customer_id] |
| [e.g., Product] | N:M — each [object] may reference multiple products | [e.g., via order_items join table] |

## Associated Business Rules

| Rule ID | Description |
|---|---|
| [BR-XXX] | [e.g., An order may only be cancelled if status is STATUS_A or STATUS_B] |
| [BR-XXX] | [e.g., A cancelled order cannot be reactivated] |
```
