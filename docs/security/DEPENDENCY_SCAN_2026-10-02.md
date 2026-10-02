# Dependency scan and SBOM evidence

**Scan date:** 2026-10-02. **Scope:** dependency manifests and lockfiles only. This is not a complete security assessment.

## Results

| Ecosystem | Input | Tool | Result |
|---|---|---|---|
| Python runtime and development dependencies | [`requirements-dev.lock`](../../src/backend/requirements-dev.lock) | `pip-audit 2.10.1`, PyPI advisory service | No known vulnerabilities reported. 43 CycloneDX components. |
| Frontend production and development dependencies | [`package-lock.json`](../../src/frontend/package-lock.json) | `npm audit` with Node `v24.17.0`, npm `11.13.0` | 0 info, low, moderate, high, or critical findings. 152 CycloneDX components. |

## Evidence files and hashes

| Artifact | SHA-256 |
|---|---|
| [`sbom-python-cyclonedx.json`](sbom-python-cyclonedx.json) | `25fa81b2d4271c1f18442e3a17e7edec7aef60930e52b02444094e00bd5bb54f` |
| [`sbom-frontend-cyclonedx.json`](sbom-frontend-cyclonedx.json) | `09d78ff60c11a1fdcba7c210b4fa8bf38e787e463b1e9191e7bc45fdb0c84811` |
| [`npm-audit-20261002.json`](npm-audit-20261002.json) | `b3f1d7cbdea29ab43501abe241174c2de2cedfa6c934b118c063ff24f9b6ee96` |
| Python runtime lock input (`requirements.lock`) | `0df7ea755e0b7c9ce517a5475d5508972f3b940d30db7f19c69aacd40e994e57` |
| Python development lock input (`requirements-dev.lock`) | `90a79c09c4d5b6e069a5bd1e849c43bdb133bef47cd4b2dc35954e79f00883f9` |
| Frontend lock input | `0556ff7e169f9c332fb8c7a30c1251a72d50d20ce3ad505cad2c5f993bc48d8e` |

The Python audit emitted cache deserialization warnings, then completed and reported no known vulnerabilities. The generated SBOM files are local inventories; they are not signed or attached to an image digest.

## Not covered

- SAST, DAST, secret scanning, container/OS image scanning, runtime behavior, and transitive vulnerabilities outside the two lockfiles.
- Image SBOMs and signed provenance. No signing identity was used.
- Future advisories or changes after the scan date.

The result is a dependency-scan snapshot only. Production release remains blocked by the controls in [`INTERNAL_CONTROLS_CLOSED.md`](../government/INTERNAL_CONTROLS_CLOSED.md).
