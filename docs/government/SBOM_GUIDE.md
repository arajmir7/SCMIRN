# SBOM and build provenance guide

## Current state

Python runtime/development dependencies are hash-pinned and frontend dependencies use a lockfile. Local Docker image builds were recorded earlier. No SBOM or signed provenance is generated or attached to the current workspace, and no fresh image vulnerability scan is recorded.

## Release evidence to retain

For each immutable release, generate a CycloneDX or SPDX SBOM from the exact source lockfiles and final images; record tool/version, source revision, image digest, build workflow, and timestamp; scan the SBOM and images; review licenses and vulnerabilities; sign the provenance and artifact; store results in the approved registry; and fail the release when required evidence is missing. Do not publish a local build as an approved artifact.

