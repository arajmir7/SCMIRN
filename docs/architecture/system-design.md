# System Design

High-level architecture overview for SCMIRN.

## Reference

- **Full hierarchical architecture (interviews & placements):** [System Architecture Tree](./system-architecture-tree.md)  
  Use this for a clean, layered view: deployment, logical layers, directory mapping, patterns, and a one-minute pitch.

## Summary

- **Tiers:** Client (React SPA) → Application (Flask API + AI microservice) → Data (DB, Redis, Elasticsearch) + external services.
- **Backend layers:** Presentation (web/mobile/chat) → API → Application (CQRS-style) → Domain → Infrastructure.
- **Patterns:** Application factory, blueprints, repository, CQRS, domain entities, event handlers.
- **Details:** See [system-architecture-tree.md](./system-architecture-tree.md).
