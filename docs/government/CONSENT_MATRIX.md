# Consent and notice matrix

| Flow | Current user action/notice | Processing boundary | Status / required work |
|---|---|---|---|
| Source triage | Explicit unchecked consent is required before the request is sent. | Description processed in memory; bounded derived decision and keyed fingerprint stored for a 30-day deadline. | `PARTIAL`: confirm notice, purpose, withdrawal/deletion request path, and scheduled purge/monitoring. |
| Legacy issue/report | UI may ask user to submit text, contact, location or media. | Legacy production mutations are gated; local demo flows can persist data. | `NOT VERIFIED`: do not use with real data; design route-specific notice and consent before enabling. |
| Civic assistant / rights | Legacy UI can collect prompts. | AI-related legacy endpoints are disabled in production allowlist; provider behavior has not been verified. | `NOT VERIFIED`: no production prompt submission; define provider, disclosure, retention and access controls. |
| Document draft | Form may collect personal and issue details. | Draft routes are gated in production; secure private storage/deletion is unverified. | `NOT VERIFIED`: do not enter real personal data. |
| Browser geolocation / map search | Location is requested only after user action; search behavior is described in the privacy matrix. | Browser/provider path; not needed for text-only route flow. | `PARTIAL`: verify provider terms, disclosure, retention, and an offline/first-party alternative. |
| Email/newsletter | No current collection path verified; footer signup was removed. | No subscription storage path. | `NOT COLLECTED` by the current footer; implement only with an approved processor and unsubscribe/deletion lifecycle. |

Consent is purpose-specific and is not proof of statutory lawful basis. Do not bundle optional location, analytics, model training, or external submission into triage consent.

