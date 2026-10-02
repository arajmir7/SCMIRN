# Component inventory (review draft)

| Component | Location / technology | Active role | Evidence / caveat |
|---|---|---|---|
| Citizen frontend | `src/frontend`, React/TypeScript/Vite, Bootstrap/Leaflet/Chart.js/Three.js | Public UI and workspaces | Build and browser tests pass locally; not all outputs are production functions. |
| API | `src/backend/app`, Python/Flask | Public and advanced APIs | 19 unit/integration tests pass; auth/tenant/deployment evidence incomplete. |
| ORM/database | Flask-SQLAlchemy, SQLite by default | Civic/AI/IoT/SRS records | `db.create_all()`; no versioned migration history in baseline. |
| AI/rights engine | `src/backend/app/core/services/ai_engine.py` | Local generated/canned civic and legal responses | No verified source grounding/model evaluation. |
| Geospatial | Leaflet/React, backend geospatial helpers, browser geocoder | Issue map and search | Data provenance/provider and privacy controls require verification. |
| Upload/document functions | Flask upload endpoint, generator services and document table | Issue media and generated draft | Malware, ACL and legal validity evidence absent. |
| Advanced platform workspaces | IoT, blockchain, resilience, twin, city-brain and enterprise API modules | Interactive simulations/demo | Do not present as connected government/asset infrastructure. |
| Source routing feature candidate | Curated source ZIP only; not canonical at baseline | Consent, deterministic triage, versioned source registry, audit/retention | Separate deployment/runtime; integration evidence must be appended. |
| Build/runtime dependencies | `src/frontend/package-lock.json`, `src/backend/requirements.txt`, Docker/Compose | Build and local runtime | Exact release SBOM/scans not available. |

Exclude `.env`, dependency caches, virtual environments, build artifacts, source SQLite case records, and stale scan claims from assessed evidence.
