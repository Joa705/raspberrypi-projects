# Backend Specification

Follow this document exactly when implementing the backend.

# FastAPI Backend Specification (Raspberry Pi Hardware Control)

## Purpose

This document is the **authoritative specification** for implementing a FastAPI backend that runs on a **single Raspberry Pi** and controls multiple hardware modules (camera, heat sensor, light).

The backend exposes a REST API used by a **Svelte frontend**.

This system is **NOT** a distributed microservices architecture.  
All code runs in **one process on one device**.

Follow this document **exactly**.

---

## High-Level Architecture

```text
Svelte Frontend
     ↓
FastAPI Backend (single process)
     ↓
Python Hardware Modules
     ↓
Raspberry Pi Hardware
```

## Architectural Principles
1. FastAPI Backend (Single Process)
FastAPI acts as:
HTTP API for the Svelte frontend
Controller/orchestrator for hardware modules
Security boundary
Constraints:
Single FastAPI application
No database initially
No message brokers
No service discovery
No networking between modules
No business logic tightly coupled to HTTP routes

2. Hardware Modules Are Python Modules (NOT Services)
Each hardware module:
Owns its hardware logic
Exposes a clean Python interface (classes/functions)
Knows nothing about:
FastAPI
HTTP
Svelte
Is imported and used directly by the API layer
Hardware modules must NOT:
Define routes
Return HTTP responses
Depend on FastAPI

3. Separation of Concerns
Layer	Responsibility
API layer	HTTP, validation, routing, responses
Module layer	Hardware control only

```text
backend/
├── main.py              # FastAPI app entrypoint
├── api/                 # HTTP routes only
│   ├── camera.py
│   ├── heat.py
│   └── light.py
│
├── modules/             # Hardware logic only
│   ├── camera/
│   │   ├── controller.py
│   │   └── driver.py
│   ├── heat/
│   │   └── sensor.py
│   └── light/
│       └── relay.py
```

## File Responsibilities
main.py
Creates the FastAPI application
Includes routers from the api/ directory
Performs basic app configuration
Contains no hardware logic

api/*.py
Define FastAPI routes only
Import and use hardware modules
Perform request validation
Return JSON responses suitable for a Svelte frontend
Contain no hardware logic

modules/*
Contain hardware logic only
Use mock or placeholder implementations where real hardware access is not available
Designed so real GPIO / camera code can replace mocks later
Do not depend on FastAPI or HTTP

## Example API Behavior
These are example public endpoints exposed by FastAPI:
POST /light/on
Turns the light module on
POST /light/off
Turns the light module off
GET /heat
Returns current temperature reading
GET /camera/snapshot
Returns a placeholder camera response

## Mocking and Hardware Safety
Use mock implementations for hardware access
Do not assume GPIO libraries are available
Code should be safe to run on non-Raspberry Pi systems
Hardware access should be encapsulated cleanly

## Explicit Constraints (Very Important)
Do NOT introduce:
Databases
Network-based microservices
Message queues
Service discovery
Event buses
Over-abstraction
Dynamic module loading
This is a simple, modular, single-device system.

## Output Expectations
When implementing this backend:
Generate all required files
Provide complete code for each file
Include clear comments explaining responsibilities
Follow the folder structure exactly
Keep the system simple and Raspberry Pi–appropriate