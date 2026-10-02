# Network architecture (target / unverified)

No deployed production network was provided for inspection. This file describes a proposed boundary, not the current runtime.

- Public browsers connect over HTTPS to a WAF/reverse proxy.
- The proxy serves static React assets and forwards only explicit API routes to Flask.
- Flask connects to a private PostgreSQL service through a least-privilege runtime credential.
- File/document objects remain in private storage and pass malware scanning before download.
- Administrative and government connector paths require separate identity, MFA and network policy.
- External providers are allowlisted, purpose-limited and disabled until approved.
- Database, backups, Redis/queues, monitoring and migration job are not public Internet services.
- Admin/control planes use restricted access and audited operator identity.

Before assessment, provide actual firewall/security-group rules, DNS/TLS certificate inventory, network diagram, ingress/egress allowlist, environment boundaries, backup network and threat analysis.
