# DPDP readiness matrix

**Status:** privacy engineering inventory only. This is not a legal opinion or a claim of DPDP compliance. Applicable legal commencement and obligations must be confirmed by Indian counsel at deployment time.

| Data / flow | Purpose visible in implementation | Storage / recipient | Retention / deletion | Access / control | Gap / action |
|---|---|---|---|---|---|
| Issue title, description, category, coordinates, landmark | Display/report civic issue | Canonical `issues`/`srs_issues`; frontend map/analytics | No complete retention/deletion schedule verified | Public anonymous API; rate limiting on some routes | Define notice, necessity, precise-location minimization, access/export/erasure and public visibility. |
| Optional reporter phone/contact | Report follow-up | Canonical issue DB | No verified expiry | Public report endpoint; no account link required | Remove unless necessary; document purpose/consent, mask logs, protect access and delete on schedule. |
| Images/media | Attach context to report | Upload folder/path metadata and API | No verified storage lifecycle | Upload/download controls not fully tested | Malware scan, MIME/content checks, private object store, access checks, deletion and processor terms. |
| AI chat prompt/response | Assistant response and continuity | Canonical `chat_logs` table; AI provider behavior depends on runtime config | No verified TTL or deletion | Public endpoint; no per-user access boundary demonstrated | Provide just-in-time notice and lawful basis; minimize or avoid storing prompts; vendor DPA/region/retention review. |
| Document fields (name, phone, address, issue details) | Draft generation | `documents` table and generated file path | No verified TTL | Public generation route; download ACL unverified | Minimize fields, consent/notice, private access, deletion/export and security scan before enabling. |
| Office lookup/geolocation query | Find local records or center the map | Map tiles load from OpenStreetMap/Esri; unmatched place searches go to OpenStreetMap Nominatim only after opt-in; browser location is requested only on button click. Report coordinates are sent only when separately selected. | Provider-specific; browser location remains in client state unless the user elects to include coordinates in a demo report | Provider disclosure, search opt-in and explicit geolocation request | Confirm provider terms/region/retention and provide a first-party/offline map option before any public service. |
| Authentication identifiers/password hash | Account access | Canonical `users` table | No verified account lifecycle/erasure | Auth boundary incomplete | Do not enable production accounts until hardened auth, password reset, MFA for staff and breach controls. |
| Source triage description | Temporary routing request | Canonical API stores HMAC fingerprint + derived facts only in `route_decisions`; API tests check that raw description is absent | 30-day decision deadline; purge is exposed by CLI but no production scheduler is configured | Public consent gate; no tenant-specific result access needed | Verify PostgreSQL behavior, scheduled purge and deletion monitoring; allow deletion/withdrawal where required. |
| Registry/source metadata | Explain routes and legal service data | Versioned source/service/rule tables | Append-only versions; review windows/effective dates | Public read; operator seed only | Assign named reviewer, expiry notification and correction process. |
| Audit event identifiers/metadata | Security/accountability and retention records | `audit_events` hash chain in source design | No general retention policy defined | Metadata only; no raw report text permitted | Set retention, access/export, key management and external anchor policy; minimize identifiers. |
| Newsletter email | Send updates | No collection path; footer signup form was removed | No subscription record | Not collected by current footer | Add only with a processor, notice, double-opt-in, unsubscribe and retention controls. |

## Required rights/process work

| Capability | Current state |
|---|---|
| Clear notice and purpose limitation | Partial copy exists only for source triage; canonical global notice not verified. |
| Consent and withdrawal | Source triage uses unchecked explicit consent; canonical report/chat/document consent design needs review. |
| Correction, access, export and erasure | No complete citizen request workflow verified. |
| Grievance contact and response SLA | Not verified. |
| Child-related handling | Not defined; product age/guardian policy requires counsel. |
| Breach notification and processor controls | Draft incident plan exists; vendor and statutory obligations require counsel/operator. |
| Cross-border processing / data location | Not verified for AI, geocoding, email, hosting or backups. |

Do not claim “DPDP compliant.” Complete legal review, processor inventory, notices, rights workflow and auditable deletion before production.
