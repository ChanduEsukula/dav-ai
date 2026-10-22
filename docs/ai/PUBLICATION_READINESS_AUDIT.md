# Dav AI — Publication Readiness Audit

Reviewed 2026-10-22 against application commit `9e78e90`, the current working tree/index and the recorded evaluation artifacts. **Publication is not approved by this audit.** Documentation corrections improve the presentation; they do not clear the repository/history for public release, authorize hosting, or establish regulatory compliance.

## Scope and observed repository state

At audit start: **400 tracked files**, **484 individual untracked files** (directory-collapsed `git status` is much shorter), and **no staged changes**. README already had working-tree edits; four requested portfolio documents were untracked. Those requested documents were corrected in place; other user research files were preserved. Counts are a dated inventory, not a permanent project metric.

Checks performed:

- Enumerated tracked files and the Git index with `git ls-files` and `git diff --cached`; inventoried untracked files separately.
- Scanned tracked text files up to 8 MiB with targeted patterns for private-key headers, AWS/GitHub/OpenAI-style credential strings, quoted secret assignments, local absolute paths and email-like contact strings. Matches were recorded by path/line without printing credential values. Reviewed intended portfolio documents and linked evaluation artifacts separately.
- Inspected tracked artifact extensions/large files, actual local data directories, `.gitignore`, frontend ignore rules, environment examples and deployment configuration paths. Compared evidence claims with code and JSON/scorer definitions.
- Visually reviewed the existing three `/ask` screenshots. They show medication research examples and evidence, with no visible pairing capability or private user input; no image OCR, hidden-metadata certification or exhaustive pixel review is claimed.
- Reran the existing backend, security, artifact and frontend lint/build/unit checks; results and exact modified paths are in the [documentation audit report](PORTFOLIO_DOCUMENTATION_AUDIT_REPORT.md).

This is **not** a full Git-history secret scan, dedicated entropy scanner, penetration test, license/IP review, clinical validation, or proof that no secret exists. Ignored/untracked raw datasets and every experiment were not exhaustively reviewed. A clean current index does not clear earlier commits.

## Findings and publication blockers

| Area | Observation | Required human decision / remediation |
| --- | --- | --- |
| Credentials | No matches for the selected credential patterns in scanned tracked text; only `.env.example` files are tracked | Review full Git history and publish candidates with a dedicated secret scanner; inspect ignored local configuration privately. No “zero secrets” certification. If a real credential is found, rotate/revoke and review history remediation separately. |
| Historical local paths | After correcting README links, 19 original match locations remain in other tracked files; some are generic path fixtures, others reveal local environment details | Review the exact files below for sanitization before publication. They were not silently edited or deleted. |
| Contact/PII-like text | 455 email-pattern line matches at baseline, mostly curated/fixture public-source contacts, with a few verification logs | Verify provenance, license and intended publication of contact data; public-source availability does not automatically resolve privacy or redistribution questions. No medical/patient identity clearance is implied. |
| Large artifacts | No tracked file over 10 MiB and no tracked `.db`, `.sqlite`, `.sqlite3`, `.dump`, `.parquet` or `.arrow` files in this inventory | Review history as well as current files. Keep the frozen database, recovery dump and raw/derived datasets outside this documentation staging set. |
| Evaluation artifacts | Original JSON and raw v1/v2 model responses are tracked; some contain deliberate adversarial text and recovery-source identifiers | Review prompt/response contents and provenance for publication; label them as evaluation data. Do not describe raw outputs as verified medical statements. |
| Screenshots | Three tracked screenshots show the local pharmaceutical demo; no visible capability identified in visual review | Maintainer should approve public display of the complete images and file metadata; retain no credential-bearing screenshots or terminal captures. |
| Untracked research | Hundreds of untracked nested files include source modules, migrations, tests, cohort/derived data and reports | Leave in place. Review individually in a separate workstream; no broad staging, deletion, stash or blanket source-directory ignore. |
| Evaluation claims | Mode C contains three failed expected-status assertions and known scorer/report-label limitations | Preserve disclosed failures. Investigate live case/scorer mismatches separately before using attack-blocking or generalized reliability claims. No code was changed here. |
| Existing demo limitation | The screenshot and link-renderer code show an official download.open.fda.gov recall citation rendered as `Source URL unavailable` | Record this as a frontend allowlist mismatch; citation remains in typed evidence. Fixing application code is outside this documentation audit. |
| Deployment | Existing Vercel/Render and other tracked operational artifacts remain present and unchanged | Publishing code is not permission to enable serving, alter hosting privacy controls, publish artifacts or make a repository public. |

Tracked local-path matches requiring manual review (relative locations; values intentionally not reproduced):

- `backend/tests/pharma_release/test_explorer_reports.py:162` (a path-security fixture; assess separately from a real local path).
- `docs/USA_REAL_WORLD_SAFETY_SOURCES.md:91`, `docs/usa_safety_sources_registry.json:464`.
- `docs/hardening/verification/clean-python-install.txt:1`.
- `docs/operations_runbook.md:169`, `docs/render_cron_saved_monitors_plan.md:41`, `docs/scheduled_monitor_locking_design.md:31`.
- `docs/security-review/verification/private-compose.json:46,85,92` and `required-release-tests.txt:3`, `source-only-tests.txt:3`, `source-tests.txt:3` in that directory.
- `docs/simplification/verification/final-backend-collection.txt:84`, `frontend-tests.json:1`.
- `docs/staging-artifacts/verification/installation-unit-tests.txt:4`, `private-compose-config.json:46,85,92`.

Email-pattern matches occur in `backend/tests/fixtures/cpsc_recall_search_fixture.json`, `backend/tests/pharma_release/test_explorer_reports.py`, curated CPSC/food source JSON, `data/source_audits/usa_daily_safety_api_audit.json`, and historical hardening/simplification logs. A pattern match is a review candidate, not proof of private personal data. Likewise, source IDs referencing a relative recovery-dump path are provenance fields, not automatically credentials; review them rather than erase scientific provenance.

## Ignore rules and artifact handling

Existing rules already exclude root/backend virtual environments, `.env`/`.env.local`, Node/build/test output, `data/pharma_bulk_cache/`, `data/pharma_recovery/`, `data/research/`, `data/ml/` and `data/releases/`.

Only two missing directory-specific rules were added:

```gitignore
/data/cohorts/
/data/derived/
```

These contain actual local generated research outputs (two cohort files, five derived files at baseline), not production source. At baseline their sizes were approximately 3.23 MB and 23.98 MB; the local recovery dump was 2,213,621,015 bytes and the release directory contained multiple database versions. The intended 4,825,108,480-byte release remains local and unchanged.

No broad `backend/app/research/`, jobs, tests or scripts exclusion was added. No blanket database extension rule was needed for the observed paths, which are already protected by specific artifact directory rules. `.gitignore` **does not untrack committed files**, erase history, guarantee protection against forced staging, or authorize deletion. Existing research remains on disk; adding the two output rules only changes its default Git visibility.

## Local security controls and their limits

The dedicated launcher binds loopback, issues pairing via `/dev/tty`, validates per-session bearer digests with `secrets.compare_digest`, rejects wrong Origin/Host/peer/proxy headers, and has bounded admission, tasks and expiry. Browser credentials stay in memory. Pairing authority lasts until server exit, while sessions expire ten minutes from creation. CORS is supplementary, not authentication; credential permission is omitted rather than returned as a literal `false` header. These controls do not protect a compromised local machine or trusted development frontend and are not multiuser production authentication.

Workers have fixed read-only operations, kill/reap cancellation, wall-clock deadlines and serialized payload limits. They do **not** have hard OS CPU/RAM quotas or a general-purpose security sandbox. Unit tests and synthetic invalid-call fixtures test specified boundaries, not all SQL-injection or prompt-injection attacks. The live evaluation does not establish complete attack interception.

The frozen release SHA-256 pins expected data integrity. `publication_validated=false` in metadata and projected `publication_authorized=false` remain unchanged; neither is a cryptographic serving permission. Hosted denial uses the actual configured environment markers listed in the [architecture](../architecture/AGENTIC_RESEARCH_ARCHITECTURE.md#frozen-release-and-hosted-serving-denial), not an exhaustive detector of every cloud provider. No override, deployment configuration change or visibility change was made.

## Medical/regulatory scope

Dav AI is an academic pharmaceutical evidence research project. It is not represented as FDA-reviewed, FDA-endorsed, clinically validated, or authorized for medical decisions. Stored label, recall and ingredient-reporting data must retain their scope and missing-data limitations. FAERS associations do not establish causation, incidence, comparative safety or personal risk; recall matches do not establish that every lot/package was affected.

Any actual clinical/commercial use requires a **separate regulatory, legal, privacy, safety and product-specific review**. Do not assert that every medical-software function requires 510(k), a particular clinical-trial regime, 21 CFR Part 11 or ISO 13485. FDA distinguishes device and non-device software functions using applicable criteria; no applicability determination is made here. See the official [FDA Clinical Decision Support Software guidance](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/clinical-decision-support-software).

## Before any public repository release

- Review/sanitize tracked local paths and contact-bearing source/log artifacts, then review all relevant commit history.
- Review licenses, source-data redistribution terms, model-response artifacts and complete screenshots; keep runtime databases and private experimental outputs outside the publication set.
- Investigate the disclosed benchmark/scorer limitations before expanding reliability claims. Preserve original run evidence.
- Inspect an explicit staging diff and run a dedicated secrets/history review on the final publication candidate.
- Obtain the maintainer's explicit decision on repository visibility/publication. No such action was taken here.
- Keep application hosting, artifact serving and clinical/commercial authorization as separate blocked decisions. Current tests do not authorize any of them.
