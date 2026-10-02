# Audit write or verification failure

## Symptoms

Metadata audit writes fail, hash-chain verification returns invalid, or a database audit trigger rejects an unexpected mutation. The local PostgreSQL rehearsal verified that an update was rejected; it did not test delete denial or external anchoring.

## Diagnosis

1. Stop or quarantine the operation that requires audit if it can change persistent state without its audit event.
2. Check the application request ID, database error code, migration head, trigger installation and audit-chain verifier output.
3. Do not run repair/update SQL over audit records before preserving evidence and receiving database/security approval.

## Safe action

Fail closed for the affected audited operation. Do not disable triggers or mutate audit rows to restore availability.

## Verification

Run read-only chain verification, confirm a synthetic append works, and verify direct update/delete denial on the actual database engine before reopening.

## Rollback / escalation

Escalate to the database and security owners. Use a reviewed migration rollback only if it preserves evidence and application compatibility.

## Data-risk notes

Audit metadata can still contain sensitive identifiers. Limit access and preserve a forensic copy under the incident process.
