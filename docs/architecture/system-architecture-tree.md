# SCMIRN — System Architecture Tree

**For technical interviews & campus placements**

This document presents SCMIRN (Smart Civic Micro-Infrastructure Resilience Network) as a **clean, hierarchical system architecture** you can walk through in 5–10 minutes with an interview panel.

---

## 1. Executive Summary

| Item | Description |
|------|-------------|
| **System** | AI-powered civic intelligence platform (citizen–governance bridge) |
| **Style** | Multi-tier, modular monolith + microservices (AI service) |
| **Backend** | Flask (Python), REST APIs, CQRS/DDD-inspired core |
| **Frontend** | React 18, TypeScript, Vite |
| **Data** | SQLite/PostgreSQL, Redis (cache), Elasticsearch (search) |
| **AI/ML** | Dedicated AI service (NLP, intent classification, document generation) |

---

## 2. Deployment View (What Runs Where)

```
SCMIRN Deployment
│
├── Client Tier
│   └── Browser / PWA
│       └── React SPA (Vite build) — src/frontend
│
├── Application Tier
│   ├── Backend API (Flask)
│   │   └── src/backend — REST, web UI, mobile UI, AI chat UI
│   └── AI Service (Python)
│       └── src/ai-service — NLP, intent classification, document generation
│
├── Data Tier
│   ├── Primary DB — SQLAlchemy (SQLite dev / PostgreSQL prod)
│   ├── Cache — Redis (sessions, rate limit, cache)
│   └── Search — Elasticsearch (issue index)
│
├── Messaging (optional)
│   └── RabbitMQ — event bus, async tasks
│
└── External Services
    ├── Google Maps API — heatmap, proximity
    ├── SMS / Email — notifications
    ├── Legal data API — citations, acts
    └── Payment gateway — integrations
```

---

## 3. Logical Architecture (Layered View)

High-level layers and where they map in the codebase.

```
SCMIRN Logical Architecture
│
├── 1. Presentation Layer
│   ├── Web UI (React)
│   │   └── src/frontend/src
│   │       ├── App.tsx, main.tsx
│   │       ├── components/ (atoms, etc.)
│   │       └── features/ (documents: api, components, hooks)
│   │
│   ├── Backend-served UIs (Flask templates)
│   │   └── src/backend/app
│   │       ├── web/ (templates, static — main web UI)
│   │       └── core_platform/interfaces/http/blueprints/
│   │           ├── web_ui/
│   │           ├── mobile_ui/
│   │           └── ai_chat/ (chat widget, static JS)
│   │
│   └── API contract
│       └── REST (JSON) — consumed by React and mobile
│
├── 2. Application / API Layer
│   └── src/backend/app
│       ├── api/v1/                    # REST entry points
│       │   ├── routes.py (health)
│       │   ├── issues.py
│       │   ├── documents.py
│       │   ├── heatmap.py
│       │   ├── ai.py, ai_chat.py
│       │   └── auth.py
│       │
│       ├── application/               # Use cases (CQRS-style)
│       │   ├── commands/ (generate_document, report_issue)
│       │   ├── queries/ (get_issues, search_offices)
│       │   └── dto/
│       │
│       └── core_platform/application/
│           ├── commands/ (create_document, report_issue)
│           ├── queries/ (get_nearby_issues, get_user_documents, search_offices)
│           ├── handlers/ (document_created, issue_reported)
│           └── dto/
│
├── 3. Domain Layer
│   └── src/backend/app
│       ├── core/
│       │   ├── entities/ (document, issue, user)
│       │   ├── repositories/ (base, issue, user)
│       │   ├── services/ (issue_service, ai_engine, document_service, geospatial_service)
│       │   └── value_objects.py
│       │
│       └── core_platform/domain/
│           ├── entities/ (document, issue, user, value_objects)
│           ├── repositories/ (issue, user)
│           ├── services/ (issue, notification, office, user, workflow_engine)
│           └── exceptions.py
│
├── 4. Infrastructure Layer
│   └── src/backend/app
│       ├── infrastructure/
│       │   ├── database/ (connection, database, models, repositories)
│       │   ├── cache/ (redis_client)
│       │   ├── external/
│       │   │   ├── api_gateway/ (config, auth_middleware, rate_limiter, routes)
│       │   │   ├── maps_client, openai_client, sms_service
│       │   └── ml/
│       │
│       └── core_platform/infrastructure/
│           ├── persistence/
│           │   ├── sqlalchemy/ (models, repositories, migrations)
│           │   ├── redis/ (cache_client)
│           │   └── elasticsearch/ (issue_index)
│           ├── messaging/ (event_bus, rabbitmq_client)
│           ├── external/ (email_service, legal_data_api, payment_gateway, sms_provider)
│           ├── security/ (audit_logger, password_hasher, token_manager)
│           └── observability/ (metrics)
│
├── 5. AI Service (Separate Process)
│   └── src/ai-service/app
│       ├── api/routes.py
│       ├── core/config.py
│       ├── engine/
│       │   ├── intent_classifier.py
│       │   ├── nlp_processor.py
│       │   └── response_generator.py
│       ├── document_generator.py
│       └── nlp_engine.py
│
└── 6. Cross-Cutting
    └── src/backend/app
        ├── config.py
        ├── extensions.py (db, migrate, jwt, cache, limiter)
        ├── utils/ (constants, exceptions, security, validators)
        └── deps (api/deps.py — shared dependencies)
```

---

## 4. Directory-to-Layer Mapping (Quick Reference)

| Layer | Primary paths | Purpose |
|-------|----------------|---------|
| **Presentation** | `src/frontend/`, `app/web/`, `core_platform/.../blueprints/*_ui/`, `.../ai_chat/` | UI, templates, static assets |
| **API** | `app/api/v1/*.py` | REST endpoints, request/response |
| **Application** | `app/application/`, `core_platform/application/` | Commands, queries, handlers, DTOs |
| **Domain** | `app/core/entities|repositories|services/`, `core_platform/domain/` | Business rules, entities, domain services |
| **Infrastructure** | `app/infrastructure/`, `core_platform/infrastructure/` | DB, cache, external APIs, messaging, security |
| **AI microservice** | `src/ai-service/app/` | NLP, intent, document generation |

---

## 5. Data Flow (Request Path)

```
User → Browser (React / or Flask-rendered UI)
         → Backend API (Flask)
               → Application (command/query)
                     → Domain (entity + domain service)
                           → Infrastructure (repository / external API / AI service)
         ← JSON / HTML
```

Example: **Report issue**  
`POST /api/issues` → `issues.py` → command/handler → `Issue` entity + `IssueService` → `IssueRepository` (DB) + optional event → `RabbitMQ` / handlers.

---

## 6. Key Design Patterns (For Interviews)

| Pattern | Where it appears |
|---------|-------------------|
| **Application factory** | `create_app()` in `app/__init__.py` |
| **Blueprint (modular routes)** | `api/v1/*.py`, `web/routes.py`, `core_platform/.../blueprints/` |
| **Repository** | `core/repositories/`, `core_platform/domain/repositories/`, infrastructure implementations |
| **CQRS-style** | Commands vs queries in `application/`, `core_platform/application/` |
| **Domain entities & value objects** | `core/entities/`, `core_platform/domain/entities/` |
| **DTO** | `application/dto/`, `core_platform/application/dto/` |
| **Event handlers** | `core_platform/application/handlers/`, `core/events/` |
| **External service abstraction** | `infrastructure/external/`, `core_platform/infrastructure/external/` |

---

## 7. Tech Stack Summary

| Concern | Technology |
|---------|------------|
| Frontend | React 18, TypeScript, Vite |
| Backend | Flask, Flask-SQLAlchemy, Flask-JWT, Flask-Caching, Flask-Limiter, Marshmallow |
| AI service | Python (NLP engine, intent classifier, document generator) |
| Database | SQLAlchemy (SQLite / PostgreSQL) |
| Cache | Redis |
| Search | Elasticsearch (issue index) |
| Messaging | RabbitMQ (event bus) |
| Maps | Google Maps API (heatmap, proximity) |
| DevOps | Docker, GitHub Actions (CI/CD), Makefile, scripts in `scripts/` |

---

## 8. One-Minute Pitch (Placement / Interview)

> “SCMIRN is an **AI-powered civic intelligence platform** that connects citizens with governance.  
> The system is **multi-tier**: a **React + TypeScript** frontend, a **Flask** backend with **REST APIs**, and a separate **Python AI microservice** for NLP and document generation.  
> The backend is structured in **layers**: **presentation** (web/mobile/chat UIs), **application** (commands and queries), **domain** (entities and business logic), and **infrastructure** (database, Redis, Elasticsearch, external APIs, messaging).  
> We use **repository pattern**, **CQRS-style** use cases, and **event-driven** handlers where needed. Data flows from API → application → domain → infrastructure, keeping business logic in the domain and I/O in infrastructure.”

---

## 9. File Tree (Condensed)

```
SCMIRN/
├── .github/workflows/          # CI/CD, CodeQL
├── docs/
│   ├── architecture/           # This doc, api-design, database-schema, system-design
│   └── setup/                  # deployment, local-development
├── infrastructure/
│   └── docker-compose.yml
├── scripts/                    # deploy, seed_data, setup
├── src/
│   ├── frontend/               # React, Vite, TS — Presentation
│   ├── backend/                # Flask app — API, Domain, Infrastructure
│   │   ├── app/
│   │   │   ├── api/v1/         # REST
│   │   │   ├── application/    # Commands, queries, DTOs
│   │   │   ├── core/           # Entities, repos, domain services
│   │   │   ├── core_platform/  # DDD-style: domain, application, infrastructure, interfaces
│   │   │   ├── infrastructure/# DB, cache, external
│   │   │   ├── web/            # Web UI (templates, static)
│   │   │   ├── config.py, extensions.py, main.py
│   │   │   └── utils/
│   │   └── tests/
│   └── ai-service/             # NLP, intent, document generation
├── Makefile, README.md, .env.example
```

Use this tree to answer “Where is X?” and “How is the project organized?” in technical interviews and campus placements.
