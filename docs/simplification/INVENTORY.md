# Simplification inventory and removal evidence

Recovery: `recovery/pharma-before-simplification-20261021` at `0e4c5112f0075199d98bc0436b0f890b5b3b2a11`.
580 source/documentation files were scanned for secret signatures, artifact extensions and size, captured using an alternate Git index, and verified byte-for-byte against recovery blobs. The working branch and index were not changed. Data, original evidence receipts, ignored artifacts and private environment files remain untouched locally. No simplified implementation commit is authorized.

Original application: 162 backend app files, 146 frontend source files; 38 OpenAPI paths. Full inventory and dependency closure are recorded in inventory.json and removal-plan.json. PostgreSQL ingestion/research and release-builder code remain offline tools.

Dependency method: Python AST imports followed transitively from all pharmaceutical repositories/services, research modules, retained jobs, and offline scripts. Public application imports will be reduced before deletion. Frontend imports are traced from main.tsx and the simplified App; obsolete pages and tests for removed UI are removed only after replacement. Mixed-responsibility files (main, reports route/schema, report_pdf, release_repository, drugCatalog, client, App, consumer-label tests) are edited rather than discarded. PDF files remain and reuse ReportLab, BytesIO, escaped paragraphs and existing visual conventions.

Delete only the explicitly enumerated obsolete backend files after replacing main and PDF imports. Their callers are obsolete routers/tests or other members of the same removal set. Legacy FDA live-search adapters are not used by preserved bulk ingestion or release builders. The independent semaglutide JSON route is removed because it bypasses the shared release gate. Label identity, matching and admission rules remain intact.

Backend tests for removed auth, chat, monitors, multi-domain workflows, semantic scores and dashboards will be removed. Pharmaceutical/research/build tests remain; mixed legacy catalog/safety tests will be updated for the frozen repository contract, and P0-1 policy assertions retained. Runtime Ask tests will be replaced by direct repository/API regressions without model calls. No evidence, data, release metadata, archive or migration is a deletion target.
