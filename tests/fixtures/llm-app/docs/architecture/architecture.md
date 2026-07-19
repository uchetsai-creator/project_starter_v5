# Architecture

## Overview

System architecture overview for the fixture project.

## System Components

@startuml
[API Service] --> [Database]
[API Service] --> [Cache]
[Load Balancer] --> [API Service]
@enduml
