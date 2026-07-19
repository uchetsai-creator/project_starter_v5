# Topology

## Infrastructure Topology

@startuml
cloud "AWS" {
  node "VPC" {
    server "EC2 App Server"
    database "RDS PostgreSQL"
    storage "S3 Data Bucket"
  }
}
@enduml
