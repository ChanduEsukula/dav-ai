# Dav AI — Resume and LinkedIn Content

Graduate project content for AI Engineer, Agentic AI Engineer, ML Systems Engineer and Software Engineer applications. Claims below describe implemented work, not professional seniority, clinical validation or universal safety guarantees.

## Project headline

**Dav AI — Local LLM Pharmaceutical Evidence Research Workspace**

## One-line technical summary

Built a React/TypeScript and FastAPI research workspace that combines local LLM tool planning, human-confirmed product identity and deterministic evidence retrieval from a frozen FDA-derived SQLite release.

## Four resume bullets

- Built a local pharmaceutical research interface with React/TypeScript and FastAPI, requiring explicit confirmation of an exact product before retrieving admitted label, historical recall and ingredient-level FAERS evidence.
- Integrated approved Ollama models with strict tool schemas, session-owned opaque references and deterministic evidence contracts; separated model-selected tools from disclosed backend completion of valid incomplete plans.
- Implemented a capability-protected loopback API with server-owned sessions, expiry, cancellation and admission controls, plus killable read-only repository workers with request deadlines and bounded serialized outputs.
- Developed a 35-case evaluation corpus across 20 categories; recorded 23/23 selected frozen-repository case passes and compared eight live trials per model, with 7/8 Llama and 8/8 Qwen exact tool-set matches while reporting overall case failures separately.

## Short LinkedIn project description

Dav AI is my graduate engineering project exploring how local language models can plan pharmaceutical evidence retrieval while keeping product confirmation and factual evidence assembly under application control. I built the React/TypeScript interface, a local capability-protected FastAPI session boundary, bounded read-only workers and structured label/recall/FAERS views. The evaluation separates native tool planning, deterministic backend completion and agreement with a frozen repository, including recorded failures and limitations. It is a local research demonstration, not clinical decision support or medical advice.

## Ten technical interview talking points

1. **Why structured retrieval:** I chose explicit product resolution and typed source adapters so evidence scope and identity remain inspectable. This is a design choice, not proof that all RAG systems are unsuitable.
2. **Human confirmation:** Even singleton candidates require a user click and confirmation. The server freshly checks the stored product binding and locks it; a new product requires a new session. This reduces a defined identity-selection risk without eliminating human/data errors.
3. **Model authority:** Ollama receives the question, allowed tools and selected opaque reference. The model may propose invalid calls; Python checks the entire batch before dispatch and discards generated narrative from evidence output.
4. **Routing transparency:** Strict `model` routing requires all requested tools. `auto` can complete a valid nonempty subset, recording model and backend tools separately. Invalid calls receive no fallback; deterministic routing does not use inference.
5. **Local authorization:** The interactive launcher issues pairing authority. Each server-owned session has a separate unpredictable bearer capability, held in browser memory. Origin/Host/peer checks supplement capability validation; CORS is not authentication or a multiuser login system.
6. **Bounded work:** Fixed worker subprocesses read the immutable release with 20-second source deadlines; model and workflow limits are 45/70 seconds. Cancellation kills/reaps unfinished workers. Payload limits and one-operation admission are not hard OS RAM/CPU quotas.
7. **Evidence scope:** Labels must be admitted exact-product links; recalls retain package/lot limitations. This release projects FAERS as ingredient reporting associations with a null product total, never incidence, causality, comparative safety or personal risk.
8. **Reproducible evaluation:** The corpus has 35 cases. The stored live comparison has only eight per model: Llama 7/8 exact plans and 7/8 overall passes; Qwen 8/8 exact plans and 6/8 overall passes. The expected-stop mismatch and scorer limitations prevent an “all attacks blocked” claim.
9. **Latency interpretation:** That eight-case run records median model/end-to-end times of 1.160/6.645 seconds for Llama and 3.023/8.811 for Qwen. Different six-case historical values are not interchangeable, and one repetition does not establish general performance superiority.
10. **Next review before broader use:** Repository publication requires history/privacy/artifact review. Hosting requires separately approved authorization and operational design while preserving current denial. Any clinical/commercial product would need its own regulatory, legal, privacy and safety review; no specific clearance or infrastructure stack is automatically mandated here.

Metric authority, run IDs, numerators, denominators and scorer caveats are in [Recorded Evaluation Results](AGENT_EVALUATION_RESULTS.md). Current engineering checks and their skips/warnings are in the [documentation audit report](PORTFOLIO_DOCUMENTATION_AUDIT_REPORT.md). Test-suite agreement with repository data is not independent clinical validation.
