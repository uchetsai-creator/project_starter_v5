# Data Model

## Schema

@startuml
entity "RawEvent" {
  event_id: string
  timestamp: datetime
}
entity "CleanedEvent" {
  event_id: string
  value: float
}
RawEvent ||--|| CleanedEvent : transforms
@enduml
