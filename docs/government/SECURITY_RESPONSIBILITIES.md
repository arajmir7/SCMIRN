# Security responsibilities

| Control area | Accountable role | Current evidence / status |
|---|---|---|
| Application secure design and remediation | Product security lead | Threat model draft exists; no assigned lead. |
| Cloud/network/IAM/database secrets | Hosting/operator security owner | No production boundary, secret provider or least-privilege role evidence. |
| Staff identity and role authorization | Agency identity owner + product security | MFA/SSO/RBAC not verified; no government workspace authorization evidence. |
| Source/legal content review | Agency/legal data owner | Nine catalog page hashes carry a 2026-10-02 internal review date; no assigned accountable reviewer, independent checker, scheduled drift review, or legal approval workflow exists. The cybercrime portal candidate is withheld after TLS validation failed. |
| Data privacy, notices, rights, breach assessment | Data fiduciary/operator privacy lead + counsel | Engineering inventory covers 474 mapped columns across 35 tables, including 294 potentially personal/linkable candidates. There are 273 pending field approvals, 35 table-governance decisions and one profile approval; purpose, ownership, notices, rights workflows and accountable approval remain incomplete. |
| Vulnerability scans and penetration test | DevSecOps + independent authorized assessor | Current scans not verified; external assessment pending. |
| Backup, restore, DR and incident response | SRE/operator | Draft runbooks only; no drill evidence. |
| Government API credentials and connector action | Participating agency owner | None supplied; all production connectors disabled. |

No agent-generated document assigns legal accountability. The operating organization must name owners and approve responsibilities before launch.
