# Dav AI frontend

React + TypeScript + Vite pharmaceutical evidence explorer. The main screen reuses and simplifies `StoredDrugCatalog` into exact-product selection, two evidence panels, provenance and an accessible native PDF dialog. No account or personal-data persistence is required.

Use Node 24, `npm ci`, then `npm run dev`. Configure `VITE_API_BASE_URL` at build time; it defaults to `http://127.0.0.1:8000`. Run `npm run lint`, `npm test`, `npm run build` and `npm run test:e2e`. Browser tests use loopback port 15173 and recorded evidence; opt in to the real release journey with `PHARMA_OFFLINE_SMOKE=1 npm run test:e2e:release` and an offline verification API at port 18000. The Dockerfile serves the production build using Nginx.

`App.tsx` mounts `components/StoredDrugCatalog.tsx`; `api/drugCatalog.ts` defines the retained API types and `api/reports.ts` submits ephemeral report identifiers by POST. `test/evidence.json` is a recorded public FDA evidence fixture with shortened reaction/month arrays, not an alternate production source. The legacy app-shell service worker retires its old caches so removed pages cannot reappear on refresh. No report responses are cached.

See the repository README and current architecture for evidence interpretation, release gating and privacy limits.
