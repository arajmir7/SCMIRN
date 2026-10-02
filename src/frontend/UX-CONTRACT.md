# SCMIRN Frontend UX Contract

## Product context

- **Audience:** Citizens using source-grounded route guidance; staff provisioned by an organization with staff authentication enabled.
- **Primary jobs:** Check an official public-service route; explore isolated prototype Labs; list or update tenant-scoped metadata-only staff cases.
- **Target market:** India-facing product intent. The current UI is English-only; localization and local usability review are open work.
- **Active locales:** English browser locale. Dates use browser formatting; no product-wide timezone contract exists.
- **Accessibility target:** WCAG 2.2 AA target; not independently audited or certified.

## Business-context sources

| Domain / scope | Authoritative source | Source type | Reviewed date |
|---|---|---|---|
| Product boundaries and current route coverage | `../../docs/government/PRODUCT_BRIEF.md` | Product brief | 2026-10-02 |
| Demo and connector status | `../../docs/government/INTEGRATION_MATRIX.md` | Integration register | 2026-10-02 |
| Staff API endpoints and payloads | `../backend/app/staff_auth/api.py` | Implemented API | 2026-10-02 |
| Staff roles and attribute policy | `../../docs/security/STAFF_AUTHORIZATION_POLICY.md` | Authorization policy | 2026-10-02 |
| Staff session, MFA, CSRF, and cookies | `../backend/app/staff_auth/security.py` | Implemented security contract | 2026-10-02 |
| Personal-data field classification and approvals | `../../docs/government/data-governance-registry.yaml` | Data inventory; approvals incomplete | 2026-10-02 |

## Visual contract

- **Project design context:** [`DESIGN.md`](DESIGN.md).
- **Token ownership:** Existing runtime CSS is canonical; `DESIGN.md` mirrors it and does not generate tokens.
- **Runtime source:** `src/styles/scmirn.css`, `src/index.css`, `src/main.tsx`, and Bootstrap 5.
- **Adapters and drift gate:** No adapter or automated drift gate. Compare design updates with actual CSS/font imports during review.
- **Themes:** Light only.
- **Context owner:** Frontend maintainers; update this contract with any route, API permission, or user-visible lifecycle change.

## Canonical UI map

| Capability | Canonical owner | Source of truth | Allowed variants | Verification |
|---|---|---|---|---|
| Text/secret input | Native labelled input with Bootstrap classes | This contract and business API | Text, password, one-time code | Keyboard and staff E2E |
| Select/Listbox | Native `<select>` | Runtime browser control | Category, priority, valid next status | Keyboard selection and E2E |
| Form | Page-owned forms using shared API helpers | Implemented API contract | Sign-in, MFA, metadata create, status update | Required-field, busy, success, and error E2E |
| Case list | Staff case cards | `GET /api/v1/staff/cases` | Read-only or update-capable by role | List, empty, failure, role E2E |
| Feedback | Inline Bootstrap alerts/status regions | `apiGet`/`apiPost` result | Info, error, loading, unavailable | Browser role/name assertions |
| Dialogs | Existing application modal components | Existing component implementation | Report sample and draft tools under Labs | Existing modal E2E |
| CRUD | `StaffWorkspacePage` calling the staff case API | Backend transition map and authorization | Server-allowed transitions only | Full E2E create and status mutation with CSRF header |
| Navigation | React Router routes and `Navigation` component | `App.tsx` route table | Public, Labs, Staff | Direct-route and legacy-redirect E2E |

## Route and permission behavior

- `/` contains source-grounded public guidance. An official handoff appears only when the result passes `canRenderOfficialHandoff`; no action claims agency submission.
- `/labs` is the only navigation discovery route for office directory, issue map, tracker, analytics, draft templates, and showcase demos. Each `/labs/*` page carries a synthetic-data warning. Former direct paths redirect to their matching Labs path.
- `/staff` always checks `GET /api/v1/staff/auth/me` first. `STAFF_AUTH_DISABLED` shows an unavailable state and no credentials form; `AUTHENTICATION_REQUIRED` shows sign-in; network/server failure shows retry without exposing a workspace.
- Staff login sends tenant slug, email, and password to `/auth/login`, then requires a five-minute server-issued MFA challenge at `/auth/mfa`. The browser never stores the password or challenge beyond the active view and does not invent account recovery.
- A successful MFA response must confirm `mfa_verified` and contain the server user and roles. The API sets an HttpOnly session cookie and readable CSRF cookie. Authenticated mutations include the exact CSRF cookie value in `X-CSRF-Token`.
- `TENANT_ADMIN` and `CASE_OFFICER` can create and update metadata cases; `AUDITOR` can read but not mutate; `SOURCE_REVIEWER` receives no case feature because no source-review endpoint exists. Server authorization remains authoritative.
- The UI submits only the five API case categories and four API priorities. Valid next statuses mirror the backend transition map; a successful response replaces displayed status. No citizen text, identifiers, files, evidence, source content, or agency submission is collected.

## Component behavior

| Component | Default | Focus / keyboard | Disabled or busy | Error / recovery |
|---|---|---|---|---|
| Text input | Label visible; autocomplete set by purpose | Native tab and editing; paste allowed | Submit waits for active request | Inline alert; email/tenant retained, password cleared on auth failure |
| One-time code | Numeric, six-digit text input | Paste enabled; one-time-code autocomplete | Verify disabled until six digits | Generic verification error; code cleared |
| Native select | Current API-supported value | Native platform arrow/select behavior | Disabled during mutation only when needed | Server errors remain visible; prior value is retained |
| Button | Text label, one primary per form | Visible existing focus outline | Busy state prevents repeat action | Inline feedback; retry is explicit |
| Staff case card | Server-provided status and reference | Status select and update button in document order | Auditor has no mutation controls; closed case has no transition control | Failed update preserves the selected value for retry |
| Alert/status | Visible text and semantic role | Announced by the browser live-region semantics | N/A | Persists until a new action or explicit retry resolves it |

## Dataset navigation

- Staff case list: server-limited to at most 100 rows; no search, filter, sort, pagination, or selection UI exists.
- URL state: none; staff records and authentication state are not placed in the URL. Tenant, role, and assignment scope come only from the server session.
- Loading: visible status indicator. Empty: “No staff case records are visible to this account.” Error: inline message and retry.
- Refresh reloads from the API; mutation responses update the local displayed row. No optimistic updates or background queue.

## Flow ledger

| Operation | Trigger | Pending | Success feedback | Failure recovery | Focus outcome | Source ref |
|---|---|---|---|---|---|---|
| Staff session check | Open `/staff` or retry | Session check status | Workspace or sign-in | Disabled, network retry, or login state | Page remains at staff heading and state region | `StaffWorkspacePage.tsx`, `/auth/me` |
| Password login | Submit credentials | Button disabled with status | MFA challenge prompt | Generic error; password cleared; tenant/email preserved | Form stays open | `/auth/login` |
| MFA verify | Submit six digits | Button disabled | Workspace then authorized case load | Generic error; code cleared; allow restart | Form stays open | `/auth/mfa` |
| Read cases | Workspace entry or refresh | Loading status | List or explicit empty message | Inline retry; auth failure returns to sign-in | List heading remains stable | `GET /cases` |
| Create metadata case | Submit category and priority | Button disabled | Returned case reference and row | Inline error; form selections retained | Form remains usable | `POST /cases` |
| Update status | Choose a listed valid transition | Row action disabled | Returned status replaces old status | Inline error; chosen status retained for retry | Row remains in place | `POST /cases/{id}/status` |
| Sign out | Explicit button | Request pending | Return to sign-in | Error says server sign-out was not confirmed | Staff page remains available | `/auth/logout` |

## Navigation and responsive behavior

- React Router title remains the document's existing title; route-specific `<title>` management is not implemented.
- Legacy demo URLs redirect into `/labs/*`; unknown routes return to `/`.
- Staff case cards replace wide tables on every viewport. Native selects remain native.
- Navigation exposes Labs and Staff on mobile. Focus uses the existing global outline; verify that sticky navigation does not obscure focused content.
- A 401 from a case request clears the visible workspace and returns to sign-in. A 403 or role limitation does not reveal another tenant's records.

## Async and resilience

- Mutations are pessimistic and buttons prevent duplicate submission. The API does not advertise idempotency keys for staff actions.
- No offline queue or stale-data fallback is used. A failed GET does not render fabricated records.
- Failed requests preserve case form selections and selected status for an explicit retry. A 503 disabled response blocks sign-in and workspace actions.
- Session cookies are HttpOnly and SameSite Strict; CSRF token is read only for header submission and is never displayed. Password and MFA code are cleared after failure/success as appropriate.
- Challenge expiry, session expiry, network failure, authorization denial, loading, and empty lists have separate visible states.

## Validation and sensitive values

- Tenant/email/password are required; backend validation remains authoritative. Invalid credentials use one generic UI error.
- MFA input accepts exactly six numeric characters and supports password-manager/paste flows.
- Case forms contain only backend-supported enumerations. The UI explicitly says not to enter personal information; it has no free-text narrative or upload field.
- Do not log, persist to local storage, or place credentials, MFA, CSRF, tenant-private data, or case details in a URL.

## Verification

- **Static:** `npm run typecheck`, `npm run build`, and premium audit for `src/frontend`.
- **Browser:** `npm run test:e2e`; cover Labs separation, unavailable staff service, MFA flow, CSRF mutations, and auditor read-only state.
- **Responsive/accessibility:** Verify changed public navigation and staff forms at desktop and narrow mobile widths; keyboard, focus, status announcements, and reduced-motion behavior remain open for route-wide independent audit.
- **Known gaps:** No automated accessibility engine, screen-reader review, complete keyboard audit, 200%/400% zoom evidence, native-language review, or independent GIGW/WCAG certification is claimed.
