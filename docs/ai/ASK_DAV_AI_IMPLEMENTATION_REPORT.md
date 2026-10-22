# Ask Dav AI implementation report

## Architecture audit (recorded before implementation)

The React 19/TypeScript/Vite frontend renders `StoredDrugCatalog` directly, with no router or account authentication. Axios serves the existing pharmaceutical explorer. Existing styles, semantic cards, Vitest/Testing Library and Playwright provide the reusable UI and verification foundation. The explorer must retain its existing default URL and behavior; the new workspace will use `/ask` with ordinary navigation.

The normal FastAPI application mounts catalog, safety, evidence and report routes. It has request logging and exact-origin CORS, but no verified user authentication. CORS is not a session boundary. No agent routes will be mounted there. `is_deployed_environment()` and `connect_release()` deny deployed pharmaceutical serving before SQLite access.

Agent v2 already supplies `ProductSession`, opaque candidate references, explicit confirmation, fresh identity verification, lifetime/budget checks, `ResearchAgent.research`, bounded killable `ProcessBackend` workers, approved loopback Ollama models, strict `ResearchBriefing` contracts and deterministic evidence assembly. Reuse these without changing matching, counting, source selection, or pharmaceutical database services. The evaluation framework separates native tool planning from deterministic completion; the UI must retain the recorded routing distinctions rather than generate a summary.

## Implementation design

Use a separate socket-bound loopback launcher, never an exported public ASGI application or environment enable flag. A locally issued pairing capability creates a session; an independent per-session bearer capability authorizes every subsequent operation. Ownership is generated server-side. All capabilities remain in browser memory, never URLs or storage. Require exact trusted loopback Host, peer and Origin, disallow credentials/proxies/redirects, and use bounded body/session/operation admission. Expiry, cancellation and shutdown reclaim tasks. Research is genuinely asynchronous with a polled typed result. The normal hosted application remains unchanged.

Implementation, tests, verification and run instructions will be recorded below after execution.

## Delivered architecture and security boundary

`frontend/src/App.tsx` adds ordinary links to `/` (existing explorer) and `/ask` (new workspace). The existing explorer component, services and tests were preserved. The new UI uses genuine serialized Agent v2 results; its synthetic JSON fixtures are imported only by tests. There is no model-written summary or medical advice generation.

`backend/app/local_research/` is a separate local application factory and launcher, deliberately absent from `app.main`. The factory requires an actual IPv4 socket already bound to `127.0.0.1`. The launcher supplies that same socket to Uvicorn on port 8001, disables proxy interpretation and access logging, and has no host option or environment enable flag. Factory creation, lifespan startup, every HTTP request and the underlying agent/release guard reject hosted environments. Tests cover staging/production/preview and the other existing hosting markers, including an attempted enable-variable override. Normal application routes never contain the local API.

There is no fabricated account or login. The launcher delivers a random 48-byte pairing capability directly to the interactive terminal (`/dev/tty`), outside application/access logs; noninteractive launching is refused. Pairing creates a random session ID, independent random per-session bearer capability and independent server-owned principal. The registry stores SHA-256 capability digests and constant-time compares them. The browser clears the pairing input after creation and keeps only its session capability in React memory. No cookies, credentialed fetches, URL credentials, localStorage or sessionStorage are used. New sessions require pairing and renewed product confirmation; refreshing loses the session credential.

Every request requires the exact bound Host, a loopback peer, and an exact Origin from `http://127.0.0.1:5173`, `http://localhost:5173`, or `http://127.0.0.1:15173`. Missing/null/foreign Origins, untrusted Hosts and forwarding headers are rejected. CORS permits only those origins, GET/POST, Content-Type and Authorization, without credentials. Bearer authentication remains independently mandatory. The frontend deliberately targets fixed `http://127.0.0.1:8001`; existing deployed API configuration cannot enable this API. Local proxy/tunnel exposure is not supported.

Defaults: eight registered sessions, one active local operation (including discovery/search/confirmation/research), 8 KiB request bodies with a five-second read deadline, 32 Uvicorn concurrent connections, ten-minute sessions and a one-second expiry sweeper (closed sessions also release capacity). Admission is nonwaiting: saturation returns 429. Existing Agent v2 budgets remain unchanged: 20-second source operations, 45-second model deadline, 70-second workflow, four session tool calls and at most three requested source tools, once per category. Availability discovery has an additional two-second bound. Memory stores only bounded candidates and one bounded result per session.

Research runs as a real asyncio task, not a persistent queue. A lost browser connection does not cancel an accepted research job; it remains bounded, can be polled/cancelled with the owned capability, and is reclaimed on expiry or shutdown. Cancellation closes the session and cancels/reaps its worker through the existing ProcessBackend. Admission release uses a task completion callback, including cancellation before task startup. Search and confirmation await a bounded operation; timeouts close the session. Session expiry forbids late publication. Stopped/completed sessions cannot resubmit research: a fresh session is required. This intentionally stricter one-run policy prevents accidental repeat execution and does not reset agent budgets.

All request contracts forbid extra fields. Owners, Python sessions and database product IDs are never accepted from clients. Opaque references come from the trusted session map; resolving again invalidates prior candidates. Singleton searches still require human selection and confirmation. Confirmation re-verifies the product and locks selection. The wire projection preserves source identifiers, provenance, complete evidence text, dates, limitations, release metadata and routing, while excluding repository product/formulation/ingredient/record identity keys. API errors return bounded stable codes without validation input, stack traces or internal exception text. Normal API responses use no-store, nosniff and no-referrer headers.

## API lifecycle

All paths start with `/api/local/research/sessions`. POST bodies are JSON; every call also requires a trusted Origin and the local Host/peer boundary above.

| Method and suffix | Authorization | Request | Result |
| --- | --- | --- | --- |
| POST base | Pairing bearer | `{}` | `session_id`, session `capability`, lifetime, actually installed approved models, runtime availability |
| POST `/{id}/resolve` | Session bearer | `{query}` | `confirmation_required` or `empty`, display candidates/opaque refs, search incompleteness |
| POST `/{id}/confirm` | Session bearer | `{product_ref}` | `confirmed`, locked medication display |
| POST `/{id}/research` | Session bearer | `{question,categories,model?}` | `running`; nonempty distinct categories, only two approved model names or null |
| GET `/{id}/result` | Session bearer | none | `running`, `completed`, `partial` or `stopped`, typed briefing or safe code |
| POST `/{id}/cancel` | Session bearer | `{}` | `stopped/cancelled`, capability/session destroyed |
| POST `/{id}/close` | Session bearer | `{}` | `closed`, capability/session destroyed |

A null model means explicit deterministic execution, visibly identified as such. Model mode uses Agent v2 `auto`: valid incomplete plans can be completed by backend policy, with both actual tool lists preserved. Invalid model calls fail closed. The model selector shows only installed members of the existing allowlist, never arbitrary model input. No pull/download or external paid API exists.

Representative failure codes: `authorization_required` (401), `pairing_forbidden`/`session_forbidden`/`local_boundary_required`/`hosted_serving_denied` (403), `session_expired` (410), `invalid_request` (422), `request_too_large` (413), `request_timeout` (408), `session_capacity`/`research_busy` (429), `timeout` (504), and safe conflict codes for stale references, locked products, changed bindings or repeated research (409). Source failures can produce a partial typed briefing instead of discarding independently verified evidence.

## Frontend components and files

- `frontend/src/App.tsx`: navigation and `/ask` entry; existing explorer remains the default.
- `frontend/src/research/Workspace.tsx`, `workspace.css`: responsive connection/search/explicit confirmation, locked identity, editable question, explicit categories, installed-model selection, truthful running state, polled result, cancel/new session, retry/error/expiry handling, and synchronous submission guards.
- `frontend/src/research/client.ts`: fixed loopback transport, in-memory bearer, omitted credentials, no redirects/referrer/cache and bounded fetches.
- `frontend/src/research/contracts.ts`: generated serialization contracts. Regenerate with `PYTHONPATH=backend .venv/bin/python -m app.local_research.export_types`; a backend test detects drift.
- `frontend/src/research/Evidence.tsx`: separate label, recall and FAERS views, validated official source links, full expandable label text, ranked reactions/monthly evidence, grouped complete limitations, and actual model/backend routing.
- `backend/app/local_research/{__init__,__main__,api,export_types}.py`: dedicated local launcher, registry/authentication/admission, API schemas and wire projection, contract generation.
- `backend/tests/agent/test_local_api.py`: 28 new boundary/lifecycle/integration tests with synthetic repository/model data and real ProductSession/ResearchAgent/ResearchWorkflow.
- `frontend/src/research/Workspace.test.tsx`, `briefing.fixture.json`, `label.fixture.json`: synthetic UI/component fixtures and tests; no production dependency on fixture evidence.
- `frontend/e2e/ask-research.spec.ts`: bounded mocked browser journey.
- `scripts/verify_ask_research.py`, `frontend/e2e/verify-local-research.mjs`: reproducible real browser/Agent v2/frozen-release verification; capability passed privately in the child process environment, not printed or written to disk.
- This report and three screenshots under `docs/ai/screenshots/`.

Source-specific qualifications remain next to evidence, including the exact missing-label statement, no implication of absent warnings, recall lot/package uncertainty, and ingredient-level/noncausal/nonincidence/noncomparative/nonindividual-risk/no-summing FAERS statements. All original limitations remain in the wire result. Grouping uses disclosure text only to organize display; it does not rewrite or remove it. The top five ranked reaction terms remain visible; all remaining returned terms and full provenance identifiers are expandable.

## Verification results (2026-10-22)

| Check | Observed result |
| --- | --- |
| `PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/agent -q` | **177 passed** |
| `PYTHONPATH=backend .venv/bin/python -m pytest backend/tests -m 'not release_artifact' -q` | **932 passed, 27 skipped, 7 deselected** |
| `PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/security -q` | **246 passed** |
| `PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/pharma_release -m release_artifact --require-pharma-artifact -q` | **7 passed**, 370 deselected; required gate fully satisfied |
| `npm run build` in frontend | Passed TypeScript project checks and Vite production build |
| `npm run lint` in frontend | Passed |
| `npm test` in frontend | **17 passed**, 3 files |
| `npm run test:e2e` in frontend | **4 passed** (new workspace plus existing desktop/mobile/report keyboard journeys) |
| `PHARMA_OFFLINE_SMOKE=1 npm run test:e2e:release` | **1 passed**, real release search-to-PDF with outbound HTTP blocked |
| `PYTHONPATH=backend .venv/bin/python scripts/verify_ask_research.py` | Passed real local browser/API/Agent v2/model/frozen-data workflow and cleanup |
| `git diff --check` | Passed |

The backend skips are reported as skips, not release verification. The required artifact gate was run separately with the actual database. The existing FastAPI TestClient dependency emits a Starlette/httpx deprecation warning; no dependency/configuration change was made for that unrelated warning. The sandbox initially denied socket binding; socket/browser checks were rerun successfully with local networking permission. A cold artifact read also exceeded the real harness’s initial five-second assertion wait; that wait now matches the existing 25-second browser request deadline. Intermediate lint/type/import issues were corrected and the final frontend checks passed.

API tests cover creation, ownership, singleton confirmation, stale/foreign/invalid references, locked selection, changed product binding, raw-ID/owner/session injection, execution, repeat denial, admission, body size/read deadlines, closed-session capacity reclamation, source timeout, model timeout/offline, partial source preservation, all existing hosting markers, missing/untrusted Origin, Host/proxy/peer restrictions, expiry during execution, cancellation, shutdown cleanup and generated contract drift. UI tests cover search/empty states, candidate display/confirmation, category scope, completion/partial/missing labeling, recall limitations, FAERS interpretation, full label text, expiry/invalid selection/network failures, polling/cancellation and double-submit prevention.

## Real local evidence and visual verification

The real browser workflow searched **0009-0029**, explicitly selected/confirmed Xanax **.25 mg/1 TABLET**, selected installed **qwen3.5:4b-q4_K_M**, and requested labels, recalls and FAERS. It used the actual ProcessBackend workers and immutable release, with no response mocks. Qwen proposed all three permitted tools; routing was `model`, with no backend-completed tool credited to the model.

Observed result: **partial**. Label evidence was **unavailable** (no admitted exact-product label). Historical recall evidence was **incomplete**, including **D-0161-2016, Class II**, with unknown/restricted lot applicability retained. FAERS evidence was **available** for alprazolam: **18 deduplicated ingredient-report associations**, never a selected-product total (`product_report_total=null`). All present cards retained `publication_authorized=false`. Browser localStorage plus sessionStorage entries were **zero**. Explicit new-session closure left no registered session or active task. The verification blocks browser requests outside its two loopback service ports.

Actual screenshots (no credentials visible):

- [Local connection](screenshots/ask-local-connect.png)
- [Desktop results](screenshots/ask-local-results-desktop.png)
- [Mobile results](screenshots/ask-local-results-mobile.png)

Desktop and mobile screenshots were inspected after the first real run; the lengthy reaction list and provenance identifier were made expandable, preserving all evidence. The real verification was rerun to capture the final presentation. Mobile verification asserts no horizontal document overflow at 390 px. The exact interactive launcher also passed terminal capability delivery, authenticated session creation and closure through a bounded macOS system-terminal harness, with credentials redacted. An earlier Python pseudo-terminal harness stalled and was terminated; its result was not counted as a pass. The browser verification itself uses the same socket-bound application factory.

## Preservation

The database remains 4,825,108,480 bytes, mode 0444. Independent final SHA-256:

`87779eda6b06c75f10603762b18f8c66a5cb7b12ed37d47ab1bf9b4825639c71`

Inode, size, modification/change timestamps, mode and release metadata hash matched the preimplementation snapshot. `publication_validated` remains **false**. The release manifest, matching/aggregation services, normal FastAPI application, deployed detection, frozen-release connection/repository, Vercel and Render configuration were not changed. Existing untracked pharmaceutical/research/ingestion work was preserved. No deployment, download, paid API, Git staging, commit, push, merge or PR occurred.

## Running the local demonstration

Use an interactive terminal from the repository root:

```bash
PYTHONPATH=backend .venv/bin/python -m app.local_research
```

The capability is delivered directly to that terminal, not stdout/application logs. Keep the process running. In another terminal:

```bash
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Open `http://127.0.0.1:5173/ask`, paste the terminal capability, and create a session. Search `0009-0029`, select the displayed candidate and click **Confirm selected product**. Choose categories and deterministic execution or an installed approved local model, then run research. A fresh session requires re-pairing and explicit confirmation. Existing Ollama must already be running for model planning; deterministic execution does not require it. This implementation does not start Ollama or download models. No normal backend process is needed for `/ask`; the existing explorer remains served by its existing backend on port 8000.

For automated real verification, stop services occupying 8001/15173 first, then run:

```bash
PYTHONPATH=backend .venv/bin/python scripts/verify_ask_research.py
```

For the existing offline explorer release browser regression, separately run `PORT=18000 PYTHONPATH=backend .venv/bin/python scripts/pharma_offline_server.py`, then run the release Playwright command in `frontend`. That existing harness was used as-is.

## Known limitations and predeployment blockers

This is an explicitly local, single-developer development boundary, not multiuser authentication or deployment authorization. Pairing capabilities confer local session-creation authority and must be kept private; do not tunnel/proxy the listener or run untrusted code on the development origins. Refresh/navigation can lose the in-memory credential; expiry still reclaims abandoned work. Cancel closes the entire session. There is one research run per session, no persistent history, durable queue, streaming, fabricated progress, automatic retry or background clinical follow-up.

The UI distinguishes engine availability from evidence availability. A model can stop with an invalid/incomplete proposal; Agent v2 will not manufacture narrative or weaken validation. Missing and partial frozen evidence remain limitations, not bugs to fill with another product or newer external data. Real-data browser verification covered Xanax and three categories with Qwen; it is not a new full model benchmark or validation of every pharmaceutical product. Other existing evaluation artifacts were not rewritten.

Any deployment remains blocked by frozen-release publication authorization and hosted-serving denial. Deployment would require an independently reviewed authentication/authorization/session architecture, hosting and artifact activation approval, operational protections and additional product/security validation. None of those permissions or changes is implied by this local milestone.
