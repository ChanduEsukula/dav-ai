# DAV AI Repository Reference Report

> Historical note: the filename is a legacy artifact from an earlier project name. The current public project name is DAV AI. This file is retained as a historical repository reference report and does not supersede `README.md` or `frontend/README.md` for current MVP status.

This report documents an earlier DAV AI repository inspection from local project files. It is intended to be copied into Word or shared as a reference document.

No application source code, package file, test file, or folder structure was changed during this documentation cleanup.

## 1. Project Overview

### What DAV AI Is

DAV AI is a healthcare safety intelligence platform prototype. Its purpose is to make public healthcare safety data easier to search, understand, and audit.

The current repository is a full-stack MVP with:

- A FastAPI backend under `backend/`
- A React + TypeScript frontend under `frontend/`
- A live RecallRadar workflow that searches public openFDA recall/enforcement data
- A transparent, rule-based Recall Review Score
- Source-aware audit information and medical safety disclaimers

### What the Current MVP Does

The current MVP focuses on searching drug recall/enforcement records from the openFDA Drug Enforcement API.

Users can:

- Search by product, drug, brand, or recall keyword
- Receive normalized FDA recall records
- See product description, recall reason, FDA class, status, recall date, distribution pattern, and recalling firm
- See a transparent risk/review score for each recall
- Inspect source metadata and retrieval timestamps
- Read plain-English cautionary context

### What RecallRadar Is

RecallRadar is the main working module in the MVP. It is a recall search and review workflow that connects the React frontend to the FastAPI backend, retrieves public FDA recall data, scores each result, and presents source-aware cards to the user.

### What Is Already Working

- React frontend renders the DAV AI interface.
- RecallRadar search input calls the backend API.
- FastAPI backend exposes health/root endpoints and a recall search endpoint.
- Backend calls the openFDA Drug Enforcement API.
- Backend normalizes selected recall fields.
- Backend calculates a rule-based recall score.
- Frontend displays recall cards, score labels, score components, audit details, and disclaimers.
- Backend unit tests exist for the scoring logic.
- Git working tree was clean before this report file was added.

### What Is Not Built Yet

- No database or persistent storage.
- No user accounts.
- No saved searches or alerts.
- No persistent audit log.
- No DrugSignal module implementation.
- No Briefing Engine implementation.
- No Supabase integration.
- No Docker setup.
- No CI/CD pipeline.
- No deployed frontend/backend configuration.
- No route tests or openFDA client tests yet.

## 2. Current Folder Structure

```text
dav-ai/
├── .gitignore
├── README.md
├── legacy repository reference report file
├── backend/
│   ├── pytest.ini
│   ├── requirements.txt
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   └── recalls.py
│   │   ├── schemas/
│   │   │   └── __init__.py
│   │   ├── scoring/
│   │   │   ├── __init__.py
│   │   │   └── recall_score.py
│   │   └── services/
│   │       ├── __init__.py
│   │       └── openfda_client.py
│   └── tests/
│       └── test_recall_score.py
└── frontend/
    ├── .gitignore
    ├── README.md
    ├── eslint.config.js
    ├── index.html
    ├── package-lock.json
    ├── package.json
    ├── public/
    │   ├── favicon.svg
    │   └── icons.svg
    ├── src/
    │   ├── App.css
    │   ├── App.tsx
    │   ├── api/
    │   │   └── recalls.ts
    │   ├── assets/
    │   │   ├── hero.png
    │   │   ├── react.svg
    │   │   └── vite.svg
    │   ├── components/
    │   │   ├── AboutPage.tsx
    │   │   ├── AuditPanel.tsx
    │   │   ├── FaqPage.tsx
    │   │   ├── Hero.tsx
    │   │   ├── InfoPage.tsx
    │   │   ├── Navbar.tsx
    │   │   ├── RecallRadar.tsx
    │   │   └── Signals.tsx
    │   ├── data/
    │   │   ├── faqs.ts
    │   │   ├── infoPages.ts
    │   │   └── signals.ts
    │   ├── index.css
    │   ├── main.tsx
    │   ├── styles/
    │   │   ├── about.css
    │   │   ├── animations.css
    │   │   ├── faq.css
    │   │   ├── hero.css
    │   │   ├── navbar.css
    │   │   ├── pages.css
    │   │   ├── recallradar.css
    │   │   └── signals.css
    │   ├── types/
    │   │   └── navigation.ts
    │   └── utils/
    │       └── recallFormatters.ts
    ├── tsconfig.app.json
    ├── tsconfig.json
    ├── tsconfig.node.json
    └── vite.config.ts
```

### Purpose of `frontend/`

The `frontend/` folder contains the React + TypeScript user interface. It renders the DAV AI landing experience, RecallRadar search UI, result cards, audit panel, informational pages, and styling.

### Purpose of `backend/`

The `backend/` folder contains the FastAPI API server. It connects to openFDA, exposes recall search endpoints, normalizes response data, and calculates the Recall Review Score.

### Purpose of Tests and Config Files

- `backend/tests/` contains backend unit tests.
- `backend/pytest.ini` configures pytest discovery and import paths.
- `frontend/package.json` defines frontend dependencies and npm scripts.
- `frontend/vite.config.ts` configures Vite with React.
- `frontend/tsconfig*.json` files configure TypeScript.
- `.gitignore` files keep virtual environments, node modules, build output, logs, and local environment files out of Git.

## 3. Backend File-by-File Explanation

### `backend/pytest.ini`

- Main purpose: Configures pytest for the backend.
- Important settings:
  - `pythonpath = .` lets tests import from `app`.
  - `testpaths = tests` tells pytest to look in the backend `tests/` directory.
- Contribution: Makes backend test runs simple from the `backend/` folder.
- Status: Basic and working for the current test layout.

### `backend/requirements.txt`

- Main purpose: Lists backend Python dependencies.
- Current dependencies:
  - `fastapi`
  - `uvicorn`
  - `pydantic`
  - `httpx`
  - `python-dotenv`
  - `pytest`
- Contribution: Supports API serving, async HTTP calls, environment handling, and testing.
- Status: Basic. Future improvement could pin versions for reproducible installs.

### `backend/app/__init__.py`

- Main purpose: Marks `app` as a Python package.
- Important functions/classes/routes: None.
- Contribution: Allows imports like `from app.routes.recalls import router`.
- Status: Empty placeholder, appropriate for now.

### `backend/app/main.py`

- Main purpose: Creates and configures the FastAPI application.
- Important functions/routes:
  - `app = FastAPI(...)`
  - CORS middleware for local Vite origins:
    - `http://localhost:5173`
    - `http://127.0.0.1:5173`
  - Includes `recalls_router` at `/api/v1/recalls`
  - `GET /` root endpoint
  - `GET /health` health endpoint
- Contribution: This is the backend entry point used by Uvicorn.
- Status: Basic and functional. Future improvement could add production CORS settings, environment-based configuration, structured logging, and exception handling.

### `backend/app/routes/__init__.py`

- Main purpose: Marks `routes` as a Python package.
- Important functions/classes/routes: None.
- Contribution: Supports route module imports.
- Status: Empty placeholder, appropriate for now.

### `backend/app/routes/recalls.py`

- Main purpose: Defines the RecallRadar API route.
- Important route:
  - `GET /api/v1/recalls/search`
- Important logic:
  - Accepts query parameter `q` with minimum length 2.
  - Accepts `limit`, defaulting to 10, with allowed range 1 to 25.
  - Calls `OpenFDAClient.search_drug_recalls`.
  - Iterates through openFDA `results`.
  - Calls `calculate_recall_risk_score` for each raw record.
  - Returns normalized result objects with source metadata.
  - Returns a top-level medical disclaimer.
  - Converts exceptions into a `502` response.
- Contribution: This file connects the API request, openFDA service, scoring logic, and frontend response shape.
- Status: Functional for the MVP. Future improvement should add narrower error handling, tests for route behavior, empty-result handling, and typed response schemas.

### `backend/app/schemas/__init__.py`

- Main purpose: Marks `schemas` as a Python package.
- Important functions/classes/routes: None yet.
- Contribution: Placeholder for future Pydantic request/response models.
- Status: Empty placeholder. Needs future improvement if the API response should be strongly documented and validated.

### `backend/app/scoring/__init__.py`

- Main purpose: Marks `scoring` as a Python package.
- Important functions/classes/routes: None.
- Contribution: Supports imports from the scoring module.
- Status: Empty placeholder, appropriate for now.

### `backend/app/scoring/recall_score.py`

- Main purpose: Implements the transparent Recall Review Score.
- Important constants:
  - `CLASSIFICATION_WEIGHTS`
  - `STATUS_WEIGHTS`
- Important functions:
  - `calculate_recall_risk_score(record: dict) -> dict`
  - `_recency_score(date_string: str | None) -> int`
  - `_scope_score(distribution_pattern: str) -> int`
  - `_score_label(score: int) -> str`
- Contribution:
  - Turns raw recall fields into a score from 0 to 100.
  - Returns a label: `Low`, `Moderate`, `High`, or `Critical`.
  - Returns score components so users can see why the score was assigned.
  - Includes `score_version = "recall-risk-v0.1"`.
- Status: Functional and tested. Future improvement could document the algorithm in the README, add more edge-case tests, and eventually incorporate confidence/source quality only if the actual backend logic supports it.

### `backend/app/services/__init__.py`

- Main purpose: Marks `services` as a Python package.
- Important functions/classes/routes: None.
- Contribution: Supports service module imports.
- Status: Empty placeholder, appropriate for now.

### `backend/app/services/openfda_client.py`

- Main purpose: Provides an async client for openFDA recall data.
- Important constant:
  - `OPENFDA_DRUG_ENFORCEMENT_URL = "https://api.fda.gov/drug/enforcement.json"`
- Important class:
  - `OpenFDAClient`
- Important method:
  - `search_drug_recalls(query: str, limit: int = 10) -> dict[str, Any]`
- Contribution:
  - Builds an openFDA search query using `product_description:"{query}"`.
  - Limits results to a maximum of 25.
  - Uses `httpx.AsyncClient` to call openFDA.
  - Returns source name, endpoint, query, retrieval timestamp, and raw JSON.
- Status: Basic and functional. Future improvement should add retries, clearer error handling, API key support if needed, broader search fields, and tests with mocked HTTP responses.

### `backend/tests/test_recall_score.py`

- Main purpose: Unit tests for the Recall Review Score.
- Important tests:
  - Recent ongoing Class I nationwide recall should score 100 and `Critical`.
  - Old completed Class III local recall should score 22 and `Low`.
  - Missing fields use safe default component scores.
  - Invalid date uses default recency score.
- Contribution: Protects the core scoring logic from accidental regressions.
- Status: Good first test coverage. Future improvement should add boundary tests for score labels, recency thresholds, distribution pattern variations, and unknown classifications/statuses.

## 4. Frontend File-by-File Explanation

### `frontend/package.json`

- Main purpose: Defines frontend package metadata, scripts, dependencies, and dev dependencies.
- Important scripts:
  - `npm run dev`
  - `npm run build`
  - `npm run lint`
  - `npm run preview`
- Important dependencies:
  - `react`
  - `react-dom`
  - `axios`
- Important dev dependencies:
  - Vite
  - TypeScript
  - ESLint
  - React plugin tooling
- Contribution: Runs and builds the frontend app.
- Status: Functional. Future improvement could add test tooling such as Vitest and React Testing Library.

### `frontend/vite.config.ts`

- Main purpose: Vite configuration for the React app.
- Key configuration:
  - Uses `@vitejs/plugin-react`.
- Contribution: Enables Vite dev server and React compilation.
- Status: Basic and complete for the current MVP.

### `frontend/src/App.tsx`

- Main purpose: Main React application component.
- Key state:
  - `activePage`
  - `activeSection`
  - `query`
  - `data`
  - `loading`
  - `error`
- Key functions:
  - `handleSearch`
  - `goHome`
  - `goToRecallRadar`
  - `goToPage`
- Contribution:
  - Wires together navigation, page switching, RecallRadar search, and API response state.
  - Imports all major CSS files.
  - Renders `Hero`, `RecallRadar`, `Signals`, `AboutPage`, `FaqPage`, and `InfoPage`.
- Status: Functional. Future improvement could add React Router if routes become real URLs, and better global error/empty-state handling.

### `frontend/src/App.css`

- Main purpose: Global app-level styling and design variables.
- Key content:
  - CSS custom properties for colors, shadows, and layout.
  - Global typography.
  - App background styling.
  - Layout shell for `.app`.
  - Shared stacking context for nav and sections.
- Contribution: Gives the app its polished clinical/healthcare visual identity.
- Status: Functional. Future improvement could split design tokens into a dedicated file if the design system grows.

### `frontend/src/main.tsx`

- Main purpose: React entry point.
- Key logic:
  - Imports `StrictMode`.
  - Creates the React root.
  - Renders `<App />`.
  - Imports `index.css`.
- Contribution: Boots the frontend application into the `#root` element from `index.html`.
- Status: Complete for the current MVP.

### `frontend/src/index.css`

- Main purpose: Baseline HTML/body/root styling.
- Key content:
  - Full-width layout.
  - Removes default margin and padding.
  - Prevents horizontal overflow.
  - Sets body background.
- Contribution: Provides the page reset needed for the app-level layout.
- Status: Basic and complete.

### `frontend/src/api/recalls.ts`

- Main purpose: Frontend API client for RecallRadar.
- Key constants/types/functions:
  - `API_BASE_URL = "http://127.0.0.1:8000"`
  - `RecallResult`
  - `RecallSearchResponse`
  - `searchRecalls(query: string, limit = 5)`
- Contribution:
  - Defines the expected backend response shape.
  - Sends `GET /api/v1/recalls/search` with `q` and `limit`.
  - Returns typed recall response data to React components.
- Status: Functional for local development. Future improvement should move the API base URL to environment config for deployment.

### `frontend/src/components/Navbar.tsx`

- Main purpose: Top navigation bar.
- Key props:
  - `activePage`
  - `activeSection`
  - `goHome`
  - `goToRecallRadar`
  - `goToPage`
- Contribution:
  - Lets users navigate Home, RecallRadar, About, FAQ, Help, Profile, and Sign Up placeholder pages.
  - Applies active button states.
- Status: Functional. Future improvement could add mobile navigation because links are hidden on small screens.

### `frontend/src/components/Hero.tsx`

- Main purpose: Landing hero section.
- Key props:
  - `data`
  - `goToRecallRadar`
  - `goToAbout`
- Contribution:
  - Presents DAV AI positioning.
  - Shows a styled dashboard preview.
  - If recall data exists, reflects the top result score and record count in the hero visual.
- Status: Functional visual component. Future improvement could use a real product screenshot or actual asset if desired.

### `frontend/src/components/Signals.tsx`

- Main purpose: Displays static feature/module cards from `signals.ts`.
- Key data:
  - Recall intelligence
  - Drug safety patterns
  - Weather risk context
- Contribution: Shows the broader product vision beyond the current RecallRadar MVP.
- Status: Basic static section. Important note: Drug safety patterns and weather risk context are shown as future/product-positioning concepts, not implemented workflows.

### `frontend/src/components/RecallRadar.tsx`

- Main purpose: Main search and results UI for RecallRadar.
- Key props:
  - `query`
  - `setQuery`
  - `data`
  - `loading`
  - `error`
  - `handleSearch`
- Key behavior:
  - Search input supports button click and Enter key.
  - Shows loading label while searching.
  - Shows error text if the API call fails.
  - Displays source summary strip after results load.
  - Renders `AuditPanel`.
  - Maps backend results into recall cards.
  - Shows technical details in a `<details>` block.
- Contribution: This is the main user-facing RecallRadar workflow.
- Status: Functional. Future improvement should add explicit empty-state UI when zero records are returned.

### `frontend/src/components/AuditPanel.tsx`

- Main purpose: Displays audit/source metadata for a recall search response.
- Key props:
  - `query`
  - `response`
- Contribution:
  - Shows data source, endpoint, search query, retrieved timestamp, record count, score version, and disclaimer.
- Status: Functional but needs improvement. It currently hardcodes some audit fields:
  - `scoreVersion = "recall-risk-v1"` while the backend score version is `recall-risk-v0.1`.
  - `dataSource = "openFDA Drug Enforcement API"` is hardcoded instead of using `response.source_name`.
  - `endpoint = "/drug/enforcement.json"` is hardcoded instead of using backend endpoint metadata.

### `frontend/src/components/AboutPage.tsx`

- Main purpose: About page for product positioning and safety boundaries.
- Contribution:
  - Explains what the app does and does not do.
  - States openFDA data source transparency.
  - Describes the Recall Review Score.
  - Lists target audiences.
  - Includes a safety note that the app is not FDA approved and not medical advice.
- Status: Strong informational page. Needs minor copy review because it mentions score confidence, but the current backend score does not include a confidence component.

### `frontend/src/components/FaqPage.tsx`

- Main purpose: FAQ page.
- Key data source:
  - `faqs` from `frontend/src/data/faqs.ts`
- Contribution:
  - Presents expandable FAQ items.
  - Explains FDA approval status, medical advice boundary, data source, score meaning, and intended users.
- Status: Functional static page.

### `frontend/src/components/InfoPage.tsx`

- Main purpose: Reusable simple informational page component.
- Key props:
  - `eyebrow`
  - `title`
  - `text`
- Contribution:
  - Used for Help, Profile, and Sign Up placeholder pages.
- Status: Basic and appropriate for placeholders.

### `frontend/src/data/faqs.ts`

- Main purpose: Stores FAQ content.
- Contribution:
  - Keeps FAQ copy separate from the FAQ component.
  - Covers safety boundaries, source data, score interpretation, and target users.
- Status: Useful and beginner-friendly. Future improvement could align score wording exactly with backend scoring fields.

### `frontend/src/data/infoPages.ts`

- Main purpose: Stores content for Help, Profile, and Sign Up pages.
- Contribution:
  - Keeps placeholder page copy centralized.
  - Clearly says saved monitors and account creation are future work.
- Status: Basic and useful.

### `frontend/src/data/signals.ts`

- Main purpose: Stores static feature cards for the Signals section.
- Contribution:
  - Communicates the broader vision: recall intelligence, drug safety patterns, and weather risk context.
- Status: Basic. Future improvement should distinguish implemented modules from future modules if users might assume all are live.

### `frontend/src/types/navigation.ts`

- Main purpose: Defines TypeScript navigation state types.
- Key types:
  - `ActivePage`
  - `ActiveSection`
- Contribution: Keeps page navigation state type-safe in `App.tsx` and `Navbar.tsx`.
- Status: Basic and complete for the current navigation model.

### `frontend/src/utils/recallFormatters.ts`

- Main purpose: Formatting and explanation helpers for recall results.
- Key functions:
  - `formatDate`
  - `formatTimestamp`
  - `riskExplanation`
- Contribution:
  - Converts FDA date strings like `YYYYMMDD` into readable dates.
  - Formats retrieval timestamps.
  - Creates a plain-English explanation for each result.
- Status: Functional. Future improvement could add tests for date formatting and explanation text.

### `frontend/src/styles/about.css`

- Main purpose: Styles the About page.
- Contribution:
  - Defines about hero, feature grid, audience grid, and safety note layout.
- Status: Functional and responsive.

### `frontend/src/styles/animations.css`

- Main purpose: Shared animations.
- Contribution:
  - Defines reveal, fade, float, card, spin, and wave animations.
  - Uses CSS view timeline with a fallback.
- Status: Functional. Future improvement could consider reduced-motion support.

### `frontend/src/styles/faq.css`

- Main purpose: Styles the FAQ page.
- Contribution:
  - Defines FAQ hero, list, expandable cards, and responsive layout.
- Status: Functional.

### `frontend/src/styles/hero.css`

- Main purpose: Styles the home hero and visual dashboard preview.
- Contribution:
  - Creates the large headline, CTA buttons, hero visual, animated cards, score ring, and responsive layout.
- Status: Functional. Future improvement could reduce decorative complexity if performance becomes a concern.

### `frontend/src/styles/navbar.css`

- Main purpose: Styles the top navigation.
- Contribution:
  - Defines brand styling, nav link styling, active states, and responsive behavior.
- Status: Functional. Mobile nav links are hidden, so a mobile menu is a future improvement.

### `frontend/src/styles/pages.css`

- Main purpose: Styles the generic `InfoPage` trust-style pages.
- Contribution:
  - Used by Help, Profile, and Sign Up placeholder pages.
- Status: Basic and complete.

### `frontend/src/styles/recallradar.css`

- Main purpose: Styles the RecallRadar search experience.
- Contribution:
  - Defines search panel, input/button layout, source strip, result cards, risk pills, metadata grid, audit box, disclaimer, and audit panel.
- Status: Functional. Future improvement should add explicit empty result styling and possibly stronger mobile polish.

### `frontend/src/styles/signals.css`

- Main purpose: Styles the static Signals section.
- Contribution:
  - Displays three product-vision cards in a responsive grid.
- Status: Functional.

### Other Frontend Files

- `frontend/index.html`: HTML shell that mounts React at `#root`. Status: standard Vite entry file.
- `frontend/eslint.config.js`: ESLint configuration for JavaScript, TypeScript, React Hooks, and React Refresh. Status: basic and useful.
- `frontend/tsconfig.json`: TypeScript project references. Status: standard Vite setup.
- `frontend/tsconfig.app.json`: TypeScript config for app source. Status: strict enough for the current MVP.
- `frontend/tsconfig.node.json`: TypeScript config for Vite config and Node-side tooling. Status: standard.
- `frontend/package-lock.json`: Locks npm dependency versions. Status: important for reproducible installs.
- `frontend/public/favicon.svg`: App favicon. Status: asset file.
- `frontend/public/icons.svg`: Public SVG icons asset. Status: asset file, needs review if icon usage grows.
- `frontend/src/assets/hero.png`: Image asset present in the repository. It was not seen imported in the inspected frontend code. Status: available asset, currently appears unused.
- `frontend/src/assets/react.svg` and `frontend/src/assets/vite.svg`: Default Vite/React assets. They were not seen imported in the inspected frontend code. Status: likely leftover template assets.
- `frontend/README.md`: Default React + TypeScript + Vite template README. Status: should eventually be replaced or expanded with DAV AI-specific frontend instructions.

## 5. Data Flow Explanation

1. User opens the frontend app.
2. `frontend/src/main.tsx` renders `App.tsx`.
3. `App.tsx` displays the home page with `Hero`, `RecallRadar`, and `Signals`.
4. User enters a product, drug, brand, or keyword in the RecallRadar search input.
5. User clicks `Analyze` or presses Enter.
6. `RecallRadar.tsx` calls the `handleSearch` function passed down from `App.tsx`.
7. `App.tsx` calls `searchRecalls(query.trim(), 5)` from `frontend/src/api/recalls.ts`.
8. `searchRecalls` sends an Axios GET request to:

```text
http://127.0.0.1:8000/api/v1/recalls/search?q=<query>&limit=5
```

9. FastAPI receives the request in `backend/app/routes/recalls.py`.
10. The route calls `OpenFDAClient.search_drug_recalls`.
11. `OpenFDAClient` sends an HTTP request to:

```text
https://api.fda.gov/drug/enforcement.json
```

12. The backend receives raw openFDA results.
13. For each record, the backend calls `calculate_recall_risk_score`.
14. The scoring module calculates component scores for classification, status, recency, and distribution scope.
15. The backend returns a normalized response containing:
    - Query
    - Count
    - Limit
    - Source name
    - Retrieval timestamp
    - Medical disclaimer
    - Results array
16. The frontend stores the response in React state.
17. `RecallRadar.tsx` displays:
    - Source summary strip
    - Audit panel
    - Recall cards
    - Risk score and label
    - Score components
    - Plain-English explanations
    - Technical audit details
    - Medical disclaimer

## 6. Recall Review Score Explanation

### Why the Score Exists

The Recall Review Score exists to help users prioritize public recall records for review. It is not a diagnosis, medical recommendation, or official FDA severity replacement.

The score makes recall review easier by turning several recall attributes into a transparent review-priority signal.

### What Inputs It Uses

The current backend score uses:

- FDA recall classification
- Recall status
- Recall initiation date
- Distribution pattern

### How Classification Contributes

The scoring logic assigns:

- `Class I`: 40 points
- `Class II`: 25 points
- `Class III`: 10 points
- Unknown or missing classification: 5 points

### How Status Contributes

The scoring logic assigns:

- `Ongoing`: 20 points
- `Completed`: 5 points
- `Terminated`: 0 points
- Unknown or missing status: 5 points

### How Recency Contributes

The scoring logic parses `recall_initiation_date` in `YYYYMMDD` format.

- 90 days old or newer: 20 points
- 365 days old or newer: 12 points
- 1095 days old or newer: 6 points
- Older than 1095 days: 2 points
- Missing or invalid date: 5 points

### How Distribution Scope Contributes

The scoring logic reads the `distribution_pattern` text.

- Contains `nationwide` or `nation wide`: 20 points
- Contains `multiple states` or `statewide`: 12 points
- Text length over 120 characters: 10 points
- Otherwise: 5 points

### Score Labels

After component scores are added, the total is clamped between 0 and 100.

- 81 to 100: `Critical`
- 61 to 80: `High`
- 31 to 60: `Moderate`
- 0 to 30: `Low`

### Why It Is Transparent and Rule-Based

The score is transparent because the backend returns each component score. Users can see how classification, status, recency, and scope contributed to the final number.

It is rule-based because it does not currently use machine learning, hidden model weights, or private assumptions. The logic is visible in `backend/app/scoring/recall_score.py`.

### Why It Is Not Medical Advice

The score is a public-data review signal. It does not know the user's product lot, medical history, dosage, condition, clinician guidance, or whether the recall applies to a specific item in the user's possession.

The app should continue to clearly say:

- It is not medical advice.
- It does not diagnose or treat.
- It does not tell users to start, stop, or change medication.
- Users should review the official source and consult qualified professionals for medical decisions.

### Future Score Improvements

Potential future improvements:

- Document the scoring system in the README.
- Add more tests for score boundaries and edge cases.
- Add source confidence only after designing and implementing a real confidence field.
- Add lot/package matching if source data supports it.
- Add explanations for why a record matched the search.
- Add score calibration after reviewing many real recall examples.
- Version the score consistently across backend and frontend.

## 7. Testing Status

### What Backend Tests Currently Exist

The backend currently has one test file:

```text
backend/tests/test_recall_score.py
```

It tests the scoring module only.

### What `test_recall_score.py` Validates

The tests validate that:

- A recent ongoing Class I nationwide recall scores as `Critical`.
- An old completed Class III local recall scores as `Low`.
- Missing fields receive safe default scores.
- Invalid recall dates receive a default recency score.

### How to Run Tests

From the backend folder:

```bash
cd backend
pytest
```

Or from the repository root:

```bash
cd backend
pytest tests
```

### What Passing Tests Prove

Passing tests prove that the current scoring function behaves as expected for the tested cases.

They do not yet prove:

- The openFDA client works correctly under all API conditions.
- The recall search route handles errors and empty responses correctly.
- The frontend renders results correctly.
- The full frontend/backend integration works in all cases.

### Tests That Should Be Added Next

- Unit tests for `_recency_score` boundary dates.
- Unit tests for `_scope_score` distribution variations.
- Unit tests for unknown classification and status values.
- Mocked tests for `OpenFDAClient`.
- FastAPI route tests for `/api/v1/recalls/search`.
- Tests for empty openFDA result responses.
- Tests for openFDA error responses.
- Frontend tests for RecallRadar loading, error, empty, and result states.

## 8. Current Strengths

- Clean frontend/backend separation.
- Real openFDA integration.
- FastAPI backend is simple and understandable.
- React + TypeScript frontend has typed API responses.
- Transparent scoring logic.
- Score components are exposed to users.
- Source-aware audit panel exists.
- Medical safety disclaimers are present.
- First backend unit tests are in place.
- The repo is cleaner now that backup files are no longer in the main `src/` root.
- Navigation and informational pages are separated into components.
- Static copy is separated into data files.

## 9. Current Gaps / Technical Debt

- No database yet.
- No persistent audit logs yet.
- No DrugSignal module yet.
- No Briefing Engine yet.
- No deployed backend/frontend yet.
- Limited tests.
- No CI/CD yet.
- No Docker yet.
- No Supabase integration yet.
- No frontend test suite yet.
- No typed Pydantic response schemas yet.
- API base URL is hardcoded in the frontend.
- AuditPanel has hardcoded source/version values.
- AuditPanel score version currently does not match backend score version.
- No explicit empty-state UI for zero recall results.
- No mobile navigation menu; nav links are hidden on smaller screens.
- Frontend README is still the default Vite template README.
- Some default Vite assets appear to remain even though they are not imported in the inspected app code.

## 10. Recommended Next Steps

### Step 1: Improve README and Document Recall Review Score

Update the project README with:

- How to run frontend and backend
- What RecallRadar does
- The exact score algorithm
- Safety disclaimer language
- Current limitations

### Step 2: Add More Backend Tests for openFDA Client and Recall Route

Add tests for:

- Successful route response
- Empty openFDA results
- openFDA HTTP errors
- Invalid query length
- Limit boundaries

### Step 3: Add Better Error Handling and Empty-State Handling

Improve:

- Backend error messages
- Frontend user-facing errors
- Empty result state when no records match
- Distinction between network failure and zero results

### Step 4: Add Source Registry/Audit Metadata Structure

Create a consistent structure for:

- Source name
- Full endpoint
- Retrieval timestamp
- Score version
- Data license or public source notes
- Query parameters used

### Step 5: Add DrugSignal Page Skeleton

Add only a skeleton after RecallRadar is stable. It should clearly say it is not live yet unless backed by real data and tests.

### Step 6: Add Database/Supabase Later

Add persistence only after the API contract is stable.

Potential future database items:

- Saved searches
- Audit logs
- User profiles
- Alert settings

### Step 7: Add Briefing Engine After RecallRadar Is Stable

The Briefing Engine should come after:

- RecallRadar search is reliable
- Audit metadata is consistent
- More tests exist
- Data persistence decisions are made

### Step 8: Deploy Frontend and Backend

Deployment should include:

- Environment-based API URLs
- Production CORS settings
- Backend hosting
- Frontend hosting
- Basic monitoring/logging

## 11. Commands Reference

### Install Backend Requirements

From the repository root:

```bash
cd backend
python -m pip install -r requirements.txt
```

### Run Backend

From the `backend/` folder:

```bash
uvicorn app.main:app --reload
```

Expected local backend URL:

```text
http://127.0.0.1:8000
```

FastAPI docs:

```text
http://127.0.0.1:8000/docs
```

### Run Backend Tests

From the `backend/` folder:

```bash
pytest
```

### Install Frontend Packages

From the `frontend/` folder:

```bash
npm install
```

### Run Frontend

From the `frontend/` folder:

```bash
npm run dev
```

Expected local frontend URL:

```text
http://localhost:5173
```

### Build Frontend

From the `frontend/` folder:

```bash
npm run build
```

### Lint Frontend

From the `frontend/` folder:

```bash
npm run lint
```

### Git Commit Workflow

From the repository root:

```bash
git status
git add .
git commit -m "Describe the change clearly"
git status
```

If pushing to GitHub:

```bash
git push
```

## 12. Final Summary for Chandu

DAV AI currently has a real full-stack MVP centered on RecallRadar. The frontend is a React + TypeScript app with a polished healthcare safety interface. The backend is a FastAPI app that calls openFDA, normalizes recall records, calculates a transparent Recall Review Score, and returns source-aware data to the frontend.

The repo is cleaner because the main app structure is now focused: backend logic lives under `backend/app`, tests live under `backend/tests`, and the frontend is organized into components, data files, styles, API helpers, types, and utilities.

The safest next coding step is to improve documentation and tests before adding major new features. Specifically, document the Recall Review Score, add route/client tests, and fix small consistency issues like the frontend audit score version mismatch.

What should not be added yet: a database, Supabase, DrugSignal, Briefing Engine, account system, or AI-heavy features. Those should wait until RecallRadar is stable, tested, documented, and deployed cleanly.
