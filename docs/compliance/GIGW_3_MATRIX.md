# GIGW 3.0 readiness evidence matrix

**Status:** GIGW 3.0 readiness evidence prepared. This is an internal engineering self-assessment, not certification or an external conformity finding. Scope is the canonical React public experience and its Flask APIs at baseline 2026-10-01.

| Checkpoint | Applicability / implementation location | Evidence available | Status | Owner / remaining action |
|---|---|---|---|---|
| Quality: consistent navigation and information architecture | `src/frontend/src/App.tsx`, `components/layout/Navigation.tsx` | Existing Playwright direct-route/navigation tests; screenshot baseline | `PARTIAL` | Product owner: check every route, breadcrumbs, mobile nav and broken links. |
| Quality: page title, metadata, search indexing | `src/frontend/index.html`, Vite output | Build passes; no route-specific metadata audit | `NOT VERIFIED` | Content owner: titles/descriptions/canonical URLs, sitemap and robots policy. |
| Quality: content owner, last-reviewed metadata, archive lifecycle | Public copy/pages and enterprise docs | No complete page ownership/review registry verified | `NOT IMPLEMENTED` | Assign owner/date to legal/service claims; implement review and archival process. |
| Quality: contact, help, feedback, grievance | Footer and report UI | Newsletter is a frontend control; no confirmed delivery; no audited grievance owner | `NOT VERIFIED` | Publish staffed contact/help/feedback and grievance process. |
| Quality: privacy, terms, accessibility/security policy | App routes and docs | No complete public policy route set verified | `NOT VERIFIED` | Legal/content owner approves and publishes policies and effective dates. |
| Quality: broken links / HTML and CSS validation | Frontend route tree | Browser suite covers selected links; no exhaustive link/validator output | `PARTIAL` | Run automated link crawl and markup/style validation across every route. |
| Quality: mobile friendliness | Home and current routes | Playwright test confirms no horizontal overflow at a mobile viewport | `PARTIAL` | Test all routes, orientations, small widths and real devices. |
| Accessibility: WCAG AA, keyboard, landmarks, labels, focus | React components and Bootstrap styling | Skip-link and selected label/keyboard behavior; no full axe/manual report | `NOT VERIFIED` | Accessibility owner: test every route, keyboard, SR, errors, focus, zoom, contrast, reduced motion. |
| Accessibility: maps/charts/media/document alternatives | `CivicIssueMap`, Analytics and document views | No complete accessible map/table alternative or accessible PDF evidence | `NOT VERIFIED` | Add list/table map alternative, chart summaries, media captions/alt and accessible PDF verification. |
| Cybersecurity: secure transport, headers, CSP, cookies | Flask app, Docker/Nginx config | Some response headers and local CORS exist; production proxy/TLS not exercised | `PARTIAL` | SRE/security: validate TLS, CSP, HSTS at proxy, cookie settings, security headers in deployed environment. |
| Cybersecurity: authentication, authorization, privacy, secure development | Flask APIs/models, `docs/security/` | Unit tests cover selected API behavior; no tenant/admin authorization assurance | `NOT VERIFIED` | Security owner: close access-control and privacy gates; independent penetration test. |
| Cybersecurity: vulnerability and incident management | dependency and container files | Stale ZIP SARIF only; no current scan evidence | `NOT VERIFIED` | DevSecOps: fresh SAST/SCA/secret/container/DAST and incident process. |
| Lifecycle: deployment, backups, disaster recovery, monitoring, rollback | Docker/Compose and backend DB setup | Local build/test evidence only; no production restore or DR run | `NOT VERIFIED` | SRE: approved runbooks, backup/restore test, RTO/RPO, dashboards, alerts and rollback drill. |
| Lifecycle: content/legal data review and versioning | Current pages and source registry design | Source code has versioned registry models; current official candidate is unavailable | `PARTIAL` | Assign legal/source reviewers and expiry monitoring; no route until review evidence is valid. |
| Lifecycle: multilingual support | React components | No i18n catalogue or reviewed Hindi content verified | `NOT IMPLEMENTED` | Product/content owner establishes English/Hindi catalogs and reviewed legal translations. |
| Lifecycle: service availability and public error behavior | Flask `/health`, frontend error handling | Baseline API/frontend tests; no monitored SLO or full failure injection | `PARTIAL` | SRE: publish status page/availability target and validate dependency outage behavior. |

## Evidence commands

Baseline commands and counts are in [`../merge/TEST_EVIDENCE_MATRIX.md`](../merge/TEST_EVIDENCE_MATRIX.md). Automated accessibility coverage, exhaustive link checks, external audit, production topology, restore and DR evidence remain outstanding.
