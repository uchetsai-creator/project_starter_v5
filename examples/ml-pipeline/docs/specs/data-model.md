# Data Model

## Schema

@startuml
entity "SubscriberFeature" {
  customer_id: string
  feature_date: date
  tenure_days: int
  plan_tier: string
  monthly_spend_usd: float
  logins_last_30d: int
  support_tickets_last_90d: int
  payment_failures_last_90d: int
}
entity "ChurnScore" {
  customer_id: string
  scored_at: date
  churn_probability: float
  risk_tier: string
  model_version: string
}
SubscriberFeature ||--o{ ChurnScore : scored by production model
@enduml

## Notes

`SubscriberFeature` rows are append-only, partitioned by `feature_date`, and retained
for 180 days to support time-split training. `ChurnScore` is keyed on
`(customer_id, scored_at)` and upserted (not appended) by the weekly scoring job.
