# Dav AI — reproducible local demonstration

This guide describes the current Phase 3B + refined UI working tree. It uses the
existing frozen release and local services, without changing publication or
hosted-serving authorization. Run all repository-root commands from the checkout.

## 1. Prerequisites

- Python **3.13**, Node **24** (repository/CI targets). The Phase 5 host uses Python
  3.13.7, Node 25.9.0 and npm 11.12.1; that is an observation, not a portability claim.
- A populated `.venv` and `frontend/node_modules`, or network access for the
  documented locked installation below. Do not replace working environments.
- The separately authorized frozen pharmaceutical release, excluded from Git:
  `data/releases/dav_ai_pharma_v1/phase4b-communications-2026-10-06/pharma.sqlite`.
  Expected **4,825,108,480 bytes**, SHA-256
  `87779eda6b06c75f10603762b18f8c66a5cb7b12ed37d47ab1bf9b4825639c71`.
  Keep the database and publication metadata unchanged. The loader verifies it
  and uses read-only/immutable connections. A clone alone is insufficient.
- An interactive terminal with `/dev/tty` for the research launcher.
- Optional: existing Ollama on `127.0.0.1:11434`, with approved installed
  `llama3.2:3b` and/or `qwen3.5:4b-q4_K_M`. Do not download models during a demo.
- Optional: separately provisioned local BGE-small model, compatible FAISS/BGE
  Python environment and external corpus/index. See section 5.

An alternative existing database location can be selected before starting either
backend: `export DAV_AI_PHARMA_RELEASE_DB="/path/to/authorized/pharma.sqlite"`.
Do not combine that with managed-artifact configuration or change release metadata.

For a **new** environment:

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install --require-hashes --only-binary=:all: -r backend/requirements-dev.txt
.venv/bin/python -m pip check
cd frontend
npm ci
```

Dependency installation needs network access. The runtime-only lock does not
include every development/test tool. Do not recreate or install over an existing
working environment solely to follow these commands.

## 2. Start three loopback services

Terminal A — ordinary Explorer API:

```bash
PYTHONPATH=backend .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

Terminal B — dedicated research API:

```bash
PYTHONPATH=backend .venv/bin/python -m app.local_research
```

It prints a fresh 64-character URL-safe pairing capability directly to the
interactive terminal. It is not an account password or a `dav_pair_...` token.
Keep it private and the terminal open. Do not place it in a URL, screenshot, log,
source file or browser storage. Per-session credentials are separate and held in
browser memory. Restarting the server invalidates pairing and sessions.

Terminal C — frontend:

```bash
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Open **http://127.0.0.1:5173/home**. Home, About, FAQ and Overview need no backend.
The existing Explorer stays at `/`; Ask is `/ask`. Only the ordinary API uses
`VITE_API_BASE_URL` (default `http://127.0.0.1:8000`). Research uses fixed loopback
port 8001 and admitted Origins 5173/15173. Never broaden these gates for a demo.

Ollama is independently managed. Check `ollama list` or its local status before
opting into generation. Deterministic evidence retrieval does not need Ollama.

## 3. Five-minute walkthrough

1. **Home:** show the original source-trail graphic, Everyday/Research Pro entry
   links and Operational Overview. Open About/FAQ; demonstrate keyboard disclosures
   or reduced-motion behavior if relevant.
2. **Explorer:** open `/`, search `0002-0152`, choose the Zepbound formulation and
   inspect its identity, recall coverage and ingredient reporting limitations.
   Product availability and missing evidence are properties of the frozen release.
3. **PDF:** choose Generate PDF Report, enter a demonstration name and optional
   age, and download. These fields identify the report; they do not estimate risk.
   Keep real personal details out of demonstration captures.
4. **Everyday:** open Ask, paste the current pairing capability, create a session,
   search `0002-0152`, select its candidate and explicitly confirm. A singleton
   result still needs confirmation. Select Drug labeling; uncheck other categories
   for a short label-focused run.
5. **Question:** enter “What serious allergy appears in the Zepbound
   contraindications?”. Optional: check Include a grounded AI answer. Everyday
   uses deterministic tool planning; optional synthesis uses the default installed
   Llama model. Follow a citation to the exact source section. Acceptance is not
   an independent support judgment.
6. **Research Pro:** switch modes without changing the confirmed product. Inspect
   detailed provenance. Searching the cohort directory for a different product
   closes the locked session and asks for fresh pairing; pair again, search, add
   the product to the cohort and choose Deep Research. Re-resolve and explicitly
   confirm it before execution. The old session must not remain usable.
7. **Optional model planning:** Research Pro's Execution Inference Engine selects
   an actually installed approved model. Keep Deterministic evidence planning for
   the most reproducible source demonstration. Grounded generation has its own
   checkbox, independent of planning mode.
8. **Fallback:** in a fresh session, confirm Xanax `0009-0029` and ask for its
   contraindications with synthesis enabled. This release has no admitted exact
   label. The insufficient-evidence response retains recall/FAERS source cards when
   requested; it does not substitute another formulation's label.
9. **Finish:** New research session / Reset Session closes the active session.
   Ctrl+C only the services you launched. A refresh loses browser credentials;
   accepted server work remains subject to cancellation, deadlines and expiry.

Research uses bounded background work and polling, not streamed model tokens.
Cold artifact verification and source reads may take several seconds. The session
lifetime is ten minutes from creation, not inactivity. Cohort rows remain Not
 evaluated until that exact product is researched; there is no 50-product batch run.

## 4. Availability and expected fallback

| Missing condition | Expected behavior |
|---|---|
| Ordinary Explorer API or authorized release | Search/evidence/PDF shows an error; static supporting pages still render. |
| Dedicated research API | Pairing fails safely; no hosted agent fallback. |
| Ollama or approved model | Explicit deterministic retrieval still works. Optional synthesis is unavailable; source cards remain. |
| Corpus/index | RAG is `not_configured`; explicit admitted SQL sections can still authorize extractive selection. The UI may omit an unconfigured RAG panel but retains limitations. |
| BGE embedder only | Explicit-section SQL routing can degrade transparently; do not describe it as measured semantic retrieval. |
| Requested label/section/support | Insufficient evidence; no substitution, fabricated claim or candidate promotion. |
| Invalid model output / IDs | Output discarded; deterministic briefing remains. |
| Product switch / expired session | Fresh pairing and explicit confirmation required. |

Phase 5's real integration and exact limitations are in the
[readiness report](PHASE5_RELEASE_CANDIDATE.md). The historical 7/7 pilot is
[automated acceptance](PHASE3B_GROUNDED_ANSWER_RELIABILITY.md), not human-reviewed
clinical support. Independent reviews remain PENDING.

## 5. Optional FAISS/BGE preparation

The required dev lock does **not** provision a semantic model or all optional RAG
packages. Use a separately provisioned compatible Python environment containing
the project dependencies, NumPy, `faiss-cpu`, `sentence-transformers` and PyTorch,
plus an already available `BAAI/bge-small-en-v1.5` directory with safetensors.
The loader disables model downloads and remote code. No model provisioning was
performed in Phase 5. An offline wheelhouse/environment must be prepared before
an offline demonstration; package availability alone does not verify compatibility.

Choose durable locations **outside the repository and frozen release**. Replace
the placeholders with paths to existing resources; use fresh corpus/index outputs:

```bash
export DAV_AI_RAG_PYTHON="/path/to/provisioned/rag-env/bin/python"
export DAV_AI_BGE_MODEL_DIR="/path/to/existing/bge-small-en-v1.5"
export DAV_AI_RAG_WORK_DIR="/path/outside/checkout/dav-ai-rag-demo"
export DAV_AI_RAG_CORPUS_PATH="$DAV_AI_RAG_WORK_DIR/corpus.json"
export DAV_AI_RAG_INDEX_PATH="$DAV_AI_RAG_WORK_DIR/bge-index"

PYTHONPATH=backend "$DAV_AI_RAG_PYTHON" -m app.agent.rag.cli check
PYTHONPATH=backend "$DAV_AI_RAG_PYTHON" -m app.agent.rag.cli sample --out "$DAV_AI_RAG_CORPUS_PATH"
PYTHONPATH=backend "$DAV_AI_RAG_PYTHON" -m app.agent.rag.cli build \
  --corpus "$DAV_AI_RAG_CORPUS_PATH" --embedding bge --engine faiss \
  --model-dir "$DAV_AI_BGE_MODEL_DIR" --out "$DAV_AI_RAG_INDEX_PATH"
PYTHONPATH=backend "$DAV_AI_RAG_PYTHON" -m pytest backend/tests/rag -q -rs
PYTHONPATH=backend "$DAV_AI_RAG_PYTHON" -m app.local_research
```

Set the environment **before** starting the research process, and use the compatible
interpreter for it: repository workers inherit that interpreter. Extraction reuses
admitted exact-product cards; outputs refuse existing paths. Keep derived corpus
text and model/index files private and outside Git. A mock embedding index is a
contract-test scaffold, never a substitute for a semantic demonstration.

The [original RAG experiment README](../../backend/app/agent/rag/README.md) is
historical; its early “not integrated” statements are not the current workflow.
The current adapter is `backend/app/agent/rag_adapter.py` and uses the environment
paths above. The recorded Phase 3B run used SQL admission with RAG unavailable.

## 6. Verification commands

From the repository root:

```bash
PYTHONPATH=backend .venv/bin/python -m pytest backend/tests -q -rs
PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/agent -q -rs
PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/rag -q -rs
PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/pharma_release \
  -m release_artifact --require-pharma-artifact -q
```

In `frontend`:

```bash
npm test -- --run
npm run lint
npm run build
npx playwright test --output=/tmp/dav-ai-browser-run
```

Playwright uses installed browsers only. The default configuration runs Chromium;
its ordinary journeys intercept API responses and are **mocked tests**. Firefox
and WebKit must be separately installed/available before claiming cross-browser
coverage. Browser downloads are not implicit in the commands above.

For a **real** Explorer journey, start the existing outbound-blocked verification
backend, use its matching frontend address, then run the dedicated config:

```bash
PORT=18000 PYTHONPATH=backend .venv/bin/python scripts/pharma_offline_server.py
# In frontend, a separate terminal:
VITE_API_BASE_URL=http://127.0.0.1:18000 npm run dev -- --host 127.0.0.1 --port 15173 --strictPort
# In frontend, another terminal:
PHARMA_OFFLINE_SMOKE=1 npx playwright test --config=playwright.pharma.config.ts --output=/tmp/dav-ai-real-explorer
```

For **real** Ask journeys against the frozen release and existing Ollama:

```bash
PYTHONPATH=backend .venv/bin/python scripts/verify_ask_research.py \
  --output /tmp/dav-ai-real-research-next
```

The output directory must not exist. Port 8001 must be free. The harness starts and
cleans up its own secured research API and frontend; it transfers ephemeral pairing
only through child-process memory/environment, never a URL or log. If your own
frontend is already running on the admitted loopback port 15173, add
`--reuse-frontend`; it will leave that frontend running. It requires installed
`llama3.2:3b` for Everyday generation; `--model` chooses an approved Research Pro
planning/generation model. No pull/download endpoint is called. Captures/results go
to the new output directory; historical repository screenshots are not overwritten.

## 7. Demo-day checks and limitations

Verify the authorized artifact, free ports, model status and optional semantic
artifacts before presenting. Prefer explicit deterministic execution if model
planning is unreliable. Use the API's existing wait bounds rather than promising
fixed response times. Show unavailable/partial data honestly, and keep claims about
FAISS/BGE limited to the environment and evaluation actually exercised.

Do not bypass Origin/Host checks, reuse expired capabilities, disable product locks,
change publication flags or expose loopback listeners. No clinical decisions,
personalized risk estimates or universal safety conclusions are supported. For
human evaluation use the [independent review checklist](INDEPENDENT_REVIEW_CHECKLIST.md)
and write judgments to a new versioned file; preserve original packets and raw results.
