# Dav AI — Final Portfolio Documentation Audit Report

Date: 2026-10-22. Application baseline: `9e78e90`, branch `feat/private-staging-authorization`. Scope: documentation corrections and two narrow ignore rules only. No application features, orchestration, pharmaceutical business logic, frontend source, deployment configuration, data or model changes were made. Nothing was staged, committed, pushed, deployed or made public.

## Outcome

The five portfolio documents now describe the actual local architecture, controls, UI actions, evidence scopes and measured runs. Supporting evaluation documentation was corrected where it contradicted its original JSON/scorer. The README uses GitHub-compatible relative links/images and standard Mermaid instead of private file URLs and an unsupported carousel. The resume content has one headline, one technical summary, four scoped bullets, a short LinkedIn description and ten interview points for graduate engineering applications.

**Repository publication remains subject to human review.** Tests passed, but tracked historical local paths/contact-bearing data, history/secrets review, evidence redistribution and unresolved evaluation/scorer limitations remain blockers to an unconditional publication-readiness claim. Hosting remains a separate denied decision.

## Concise claim audit

| Original wording / claim | Correction | Supporting implementation or evidence |
| --- | --- | --- |
| “Zero-hallucination guarantees,” “impenetrable,” “zero data leakage” | Model text is excluded from evidence assembly; specified validation boundaries are tested, without universal guarantees | `agent/workflow.py`, `briefing.py`, `local_research/api.py`; original run failures retained |
| “100% workflow completion” | Separate exact native planning, backend completion, status counts and overall case predicates | Mode C JSON: Llama 7/8 overall passes, Qwen 6/8; `evaluation/runner.py` |
| Llama 85.7% / 6-of-7, Qwen 7-of-7 | Framework run: Llama 7/8 (87.5%) and Qwen 8/8 exact tool-set matches | `evaluation_results_mode_c.json`, case rows and model summaries |
| 1.84/3.21 s medians; 2.42/3.89 s end-to-end | Same recorded eight-trial run: 1.160/3.023 s model; 6.645/8.811 s end-to-end | Medians recomputed from eight positive latency values/model |
| 271.8 s Mode B; “100% data fidelity” | 236.552 s; 23/23 defined case passes, including five resolver checks and 18 evidence comparisons | `evaluation_results_mode_b.json`; `score_evidence_fidelity` and runner |
| “8/8 attacks blocked per model,” “before every database access” | Nine Mode A adversarial-flagged cases pass their assertions; live Mode C contains expected-stop mismatches; no generalized attack-blocking rate | Case rows, `score_safety_behavior`; status mismatch sets the “violation” flag |
| Safety flag proves unsafe output | Flag is partly status-based; investigate failures without declaring either malicious execution or a proven harmless false positive | `metrics.py`; live case 31 proposes permitted recall tool rather than injected forbidden tool |
| 3,332 recalls / 3,121 FAERS summaries | 17,974 stored recall records; 3,332 product-recall link rows; 3,174 stored FAERS summary rows | Read-only COUNT queries agree with release metadata table counts |
| All 116K+ products available through endpoint | 116,741 stored products; 95,426 consumer-eligible rows; query/result eligibility and bounds still apply | `products.eligibility_mode` counts; repository `search()` filter |
| Entire snapshot ends June 2026 | FAERS window ends June 2026; NDC/label/recall/FAERS source snapshots have separate September dates | `release_metadata()`, stored source dates and release metadata |
| Air-gapped / zero external API dependencies | Research/inference use frozen local data and loopback Ollama without paid cloud inference; installation, external citation links and ingestion are separate | `agent/model.py`, `source_tools.py`, worker/repository and client |
| Streaming status / invented UI actions | Async task with polling; actual Search, Confirm selected product and Research selected evidence controls | `Workspace.tsx`, `client.ts`, `local_research/api.py` |
| One-use hex pairing token; inactivity expiry | URL-safe encoding of 48 random bytes, reusable until server exit; per-session 600-second lifetime from creation | `__main__.py`, `Registry`, `ProductSession.authorize` |
| Worker infers via Ollama / directly asks human to confirm | Workflow calls Ollama; source worker reads repository; human confirmation travels through UI and API | Architecture flow/sequence diagrams matched to actual call sites |
| Hard CPU/RAM sandbox and cryptographically impossible database writes | Killable processes, payload limits and wall-clock deadlines; checksum/read-only guards are not owner-proof write prevention or OS resource quotas | `ProcessBackend`, `Limits`, `connect_release()` |
| Every cloud provider detected / cryptographic publication authorization | Exact existing environment markers documented; publication metadata is a disclosure, not signed authorization | `is_deployed_environment()`, release guard, metadata `publication_validated=false` |
| All medical applications need 510(k), trials, Part 11/ISO 13485 | Separate product-specific regulatory/legal/privacy/safety review; no applicability or clearance conclusion | Official FDA CDS guidance linked in publication audit |
| All tracked files safe / ignored files cannot be published | Targeted scan has limited coverage; current index, tracked history, untracked data and forced staging are separate risks | Git inventory and [publication audit](PUBLICATION_READINESS_AUDIT.md) |
| “Senior” professional claims / clinical validation | Graduate-project engineering work with explicit repository-agreement scope | Revised [resume/LinkedIn content](PORTFOLIO_RESUME_CONTENT.md) |

## Metric authority and remaining measurement issues

[Recorded Evaluation Results](AGENT_EVALUATION_RESULTS.md) is the human-readable metric register. It identifies corpus/run/time, exact model identifier, numerator/denominator, definition, median statistic, backend completion and limitations. Original machine-readable artifacts remain unchanged.

The historical `agent-v2-evaluation.json` has six trials/model (Llama 5/6, Qwen 6/6 correct selection), not the framework's eight-case denominator. It also has different model/end-to-end medians and narrower completion definitions. The historical v1 benchmark is a different single-source experiment. Those milestone reports were left as historical evidence, not rewritten to imply current metrics.

Three live framework case predicates failed, including both models' `case_31_forbidden_tool_attack` expected-stop mismatch and Qwen's exact-NDC resolver status. The safety scorer is not a complete leakage detector: some flags are constants, missing limitation strings are not enforced, and its safety-rate denominator is all trials. Fidelity shares repository logic and includes optimistic flags. The generated Mode C Markdown also used incorrect numerators and misleading safety labels; that document was corrected manually, with a note that the unchanged generator may reproduce the old labels. Improving the scorer/generator or investigating live stimuli requires a separate code task; no results were “repaired” in JSON.

The frozen table counts were independently checked using `mode=ro&immutable=1` queries and compared with existing metadata. The required artifact gate verified the pinned database. This does not independently validate the data clinically, certify every product's admission, or authorize redistribution.

## Actual verification this audit

All commands below were executed after documentation/ignore edits. Socket-bound agent/backend tests required local networking permission; the first permitted runs passed. No new live model evaluation, benchmark JSON generation, model download, browser session or deployment occurred in this documentation task.

| Command / check | Actual result |
| --- | --- |
| `PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/agent -q` | **177 passed**, 6.16 s |
| `PYTHONPATH=backend .venv/bin/python -m pytest backend/tests -m 'not release_artifact' -q` | **932 passed, 27 skipped, 7 deselected**, 15.03 s; one existing deprecation warning |
| `PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/security -q` | **246 passed**, 0.38 s |
| `PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/pharma_release -m release_artifact --require-pharma-artifact -q` | **7 passed, 370 deselected**, 6.63 s; required gate fully satisfied; one existing warning |
| `npm run lint` in frontend | Passed |
| `npm run build` in frontend | Passed TypeScript checks and Vite 8.3.5 build |
| `npm test` in frontend | **17 passed**, three files |
| `git diff --check` | Passed; new/untracked documentation also checked separately |
| Relative Markdown links and images | Local targets checked to exist; diagram syntax/flow manually reviewed against code |
| Intended-publication text scan | No selected credential-pattern matches or private file-URL/local-user-path links in the final ten changed files; not a comprehensive secret scan |

The 27 backend skips are the existing optional PostgreSQL ingestion checks without a disposable test database. The seven artifact tests were intentionally deselected from the general suite and passed separately. The warning is the existing Starlette TestClient/httpx deprecation, not a new failure. Agent and security tests are subsets of the backend total; do not add these counts as independent coverage.

Selective rerun decision: frontend Playwright (four mocked journeys), offline real-release explorer browser test (one journey), real Qwen browser integration and interactive launcher checks were executed for the preceding application milestone and documented in [Ask Dav AI implementation report](ASK_DAV_AI_IMPLEMENTATION_REPORT.md). They were **not rerun here**, because runtime and frontend code were unchanged. Existing screenshots were inspected, not regenerated. Dependency/bootstrap commands and CLI entry points were checked against manifests, CI and actual argument parsers; a fresh install was not performed.

## Publication/security observations

The starting working-tree inventory had 400 tracked and 484 individual untracked files; no staged changes. Selected credential regexes found no candidates in scanned tracked text. README's private file links were replaced, but 19 original local-path match locations remain elsewhere in tracked historical material (some are fixtures); 455 baseline email-pattern matches mostly occur in curated source/fixture contact fields. These are review leads, not proof of a leak or clearance. Exact relative locations and scan scope are in the [publication audit](PUBLICATION_READINESS_AUDIT.md).

The two new ignore rules apply only to actual local generated `data/cohorts/` and `data/derived/` outputs. Existing rules already protect observed databases, recovery dumps, environments and frontend test/build output. No source/jobs/tests/research directory was hidden, no user research was deleted/overwritten/stashed, and ignore rules did not untrack files. Tracked history, raw evaluation response data, source-data licenses and screenshots still need maintainer review before publication.

A preexisting UI limitation is visible in the actual screenshot and renderer code: official `download.open.fda.gov` recall URLs can display as `Source URL unavailable` because frontend allowlisting is narrower than the backend provenance validator. Citation data remains in the typed response. The demo guide now discloses it; fixing the renderer is outside the authorized documentation-only scope.

## Preservation and exact changed-file list

The required release gate passed with expected SHA-256 `87779eda6b06c75f10603762b18f8c66a5cb7b12ed37d47ab1bf9b4825639c71`. Metadata retains `publication_validated=false`. Database size is 4,825,108,480 bytes and mode 0444. No database or release manifest edit was made. Original evaluation JSON, screenshots, application/backend/frontend code and hosting configurations remain unchanged; file-hash comparison against the pre-edit tracked/untracked inventory verifies that unrelated existing files were preserved.

Exactly ten files changed or were created for this audit (some requested files existed untracked beforehand):

1. `.gitignore` — two generated-data directory rules.
2. `README.md` — corrected portfolio entry point, claims, links, counts and demo.
3. `docs/architecture/AGENTIC_RESEARCH_ARCHITECTURE.md` — corrected diagrams and actual trust boundaries.
4. `docs/ai/LOCAL_DEMO_GUIDE.md` — actual prerequisites, commands, controls and limitations.
5. `docs/ai/PUBLICATION_READINESS_AUDIT.md` — scoped scan evidence and unresolved publication risks.
6. `docs/ai/PORTFOLIO_RESUME_CONTENT.md` — graduate-appropriate headline, summary, four bullets, LinkedIn text and ten talking points.
7. `docs/ai/AGENT_EVALUATION_RESULTS.md` — authoritative recorded-run register, metric definitions and caveats.
8. `docs/ai/AGENT_EVALUATION_FRAMEWORK.md` — corrected scorer, independence, resource and command claims.
9. `docs/ai/evaluation/evaluation_results_mode_c.md` — manual numerator/safety-label corrections; JSON unchanged.
10. `docs/ai/PORTFOLIO_DOCUMENTATION_AUDIT_REPORT.md` — this new report and claim audit.

## Recommended explicit staging, after human review

These commands are recommendations only; **none was executed**. They prepare this documentation change set, not a public-release approval. Review any already-present README edits and the four preexisting untracked portfolio documents as part of the diff. Do not add unrelated untracked research.

```bash
git diff --check
git add -- .gitignore README.md \
  docs/architecture/AGENTIC_RESEARCH_ARCHITECTURE.md \
  docs/ai/LOCAL_DEMO_GUIDE.md \
  docs/ai/PUBLICATION_READINESS_AUDIT.md \
  docs/ai/PORTFOLIO_RESUME_CONTENT.md \
  docs/ai/AGENT_EVALUATION_RESULTS.md \
  docs/ai/AGENT_EVALUATION_FRAMEWORK.md \
  docs/ai/evaluation/evaluation_results_mode_c.md \
  docs/ai/PORTFOLIO_DOCUMENTATION_AUDIT_REPORT.md
git diff --cached --name-only
git diff --cached --check
git diff --cached
```

No commit/push/visibility command is recommended here. Resolve history/privacy/license review and obtain explicit publication authorization separately. Deployment and clinical/commercial use require their own product-specific reviews and must not bypass existing serving denial.
