# Data Model

## Entities

@startuml
entity "User" {
  id: UUID
  email: string
}
entity "Order" {
  id: UUID
  status: string
}
User ||--o{ Order : places
@enduml
