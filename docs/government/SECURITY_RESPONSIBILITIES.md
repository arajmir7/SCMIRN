# Security responsibilities

| Control area | Accountable role | Current evidence / status |
|---|---|---|
| Application secure design and remediation | Product security lead | Threat model draft exists; no assigned lead. |
| Cloud/network/IAM/database secrets | Hosting/operator security owner | No production boundary, secret provider or least-privilege role evidence. |
| Staff identity and role authorization | Agency identity owner + product security | MFA/SSO/RBAC not verified; no government workspace authorization evidence. |
| Source/legal content review | Agency/legal data owner | No assigned source reviewer; source candidate hash missing. |
| Data privacy, notices, rights, breach assessment | Data fiduciary/operator privacy lead + counsel | Field-level engineering registry covers 452 mapped columns; purpose basis, owner, notices, rights workflows and accountable legal approval remain incomplete. |
| Vulnerability scans and penetration test | DevSecOps + independent authorized assessor | Current scans not verified; external assessment pending. |
| Backup, restore, DR and incident response | SRE/operator | Draft runbooks only; no drill evidence. |
| Government API credentials and connector action | Participating agency owner | None supplied; all production connectors disabled. |

No agent-generated document assigns legal accountability. The operating organization must name owners and approve responsibilities before launch.
