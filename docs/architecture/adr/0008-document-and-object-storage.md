# ADR-0008: Documents, uploads and object storage

**Status:** Production storage decision deferred; public upload/download disabled  
**Date:** 2026-10-01

## CONTEXT

The prototype has local document and upload paths, but production malware scanning, private ACLs, content validation, retention and access authorization are not verified. Production routes are gated.

## OPTIONS

1. Enable current local filesystem paths in production.
2. Select private object storage with malware scanning and lifecycle controls.
3. Keep uploads/downloads disabled until data class, operator and legal basis are approved.

## DECISION

Keep upload and legacy document routes disabled in production. Do not choose an object store until deployment jurisdiction, key management, retention, scanning and access requirements are known.

## WHY

Current code cannot demonstrate safe evidence storage or document lifecycle.

## SECURITY IMPACT

No citizen evidence is accepted through the production allowlist; temporary local demo data must be synthetic only.

## OPERABILITY IMPACT

There is no production object storage, virus-scanning service or storage-outage runbook with a live system to exercise.

## MIGRATION IMPACT

Future storage requires metadata schema, encrypted transfer, object inventory, deletion verification and retention migration.

## REVERSIBILITY

High before evidence is accepted; low after external references and retention obligations exist.

## STATUS

Production object storage deferred; upload/download remain disabled.
