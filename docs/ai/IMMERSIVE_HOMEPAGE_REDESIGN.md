# Dav AI — Template 3 homepage redesign

Implemented locally on October 27, 2026. Branch: `feat/private-staging-authorization`.
No commit, push, deployment, backend change, release-artifact modification, or public listener was performed.
Existing dirty work, research changes, screenshots, and backup files were preserved.

## Result

The `/home` route now follows the supplied **Immersive Visual Experience** reference:
deep navy/ocean/teal, frosted pill navigation, a two-line headline, working curved medication
search, three glass evidence cards, and a reflective floating capsule inside a glass orb.
The six navigation destinations and Everyday/Research Pro selector share the same header
geometry on all routes. The existing root Explorer, query format, explicit research
confirmation, capability handling, and source verification remain unchanged.

The hero search is a native GET form targeting `/?q=...`, preserving keyboard submission,
URL encoding, and the existing Explorer search behavior. Evidence cards scroll to real
category limitations. CTAs navigate to supported routes. There is no decorative PDF control.
Academic/graduate-project marketing copy was removed from the homepage, footer, About and
FAQ while retaining the lack of FDA approval, frozen-data boundary, and medical disclaimers.

## Files changed for this task

- `frontend/package.json`, `frontend/package-lock.json` — pinned requested visual packages.
- `frontend/src/App.tsx` — shared navigation and homepage class; preserved the user's existing portfolio theme behavior.
- `frontend/src/components/ExperienceSelector.tsx` — removed emoji decoration; retained persisted selection and keyboard behavior.
- `frontend/src/components/site-nav.css` — shared pill header, responsive menu, visible selector, route-specific palette.
- `frontend/src/portfolio/HomePage.tsx` — working hero, evidence category anchors, workflow, experience links, source boundaries.
- `frontend/src/portfolio/immersive.css` — scoped immersive glass design and responsive layouts.
- `frontend/src/portfolio/EvidenceIcon.tsx` — shared code-native decorative source symbols.
- `frontend/src/portfolio/useMotionPreference.ts` — subscribes to runtime reduced-motion preference changes.
- `frontend/src/portfolio/scene/ImmersiveOrb.tsx` — lazy loading, visibility tracking, error boundary and fallbacks.
- `frontend/src/portfolio/scene/OrbScene.tsx` — React Three Fiber scene, physical materials, studio lighting and restrained motion.
- `frontend/src/portfolio/scene/StaticOrb.tsx` — static vector illustration; no external image or HDRI requests.
- `frontend/src/portfolio/AboutPage.tsx`, `frontend/src/portfolio/FaqPage.tsx` — marketing-copy corrections.
- `frontend/src/portfolio/HomePage.test.tsx` — search contract, shared navigation, persisted mode, fallbacks and source limits.
- `frontend/src/portfolio/Portfolio.test.tsx` — updated homepage content expectations.
- `frontend/src/test/setup.ts` — browser API stand-ins for jsdom; no fake WebGL.
- `frontend/e2e/portfolio.spec.ts` — responsive route/keyboard checks, search integration, live WebGL and fallbacks.
- `frontend/e2e/grounded-answer.spec.ts` — aligned the existing unavailable-answer expectation with the already implemented evidence-summary heading.
- This report and new screenshots under `docs/ai/screenshots/immersive-homepage/`.

Other modified/untracked files visible in `git status` predate this task.

## Packages and compatibility

Runtime additions: `@react-three/fiber@9.8.2`, `three@0.186.1`, `motion@14.7.1`.
Development addition: `@types/three@0.186.0`.
Installed React and React DOM remain `19.2.5`; their versions were not changed.
No Drei, postprocessing, physics engine, model loader or external font was added to runtime code.

Compatibility was checked against installed versions, npm peer requirements and the
[React Three Fiber installation guide](https://r3f.docs.pmnd.rs/getting-started/installation)
and [Motion installation guide](https://motion.dev/docs/react-installation).

## Performance and accessibility

- Three.js/Fiber live only in the dynamically imported `OrbScene` chunk.
- The static SVG is available immediately while loading, under reduced motion, without
  usable WebGL2, on a major GPU performance caveat, after context loss, or if the scene fails.
- Reduced-motion changes take effect without reloading; the canvas is removed and decorative
  orbit motion stops. The static composition remains available.
- Intersection and document-visibility listeners pause rendering when the scene is offscreen
  or the document is hidden. Listeners and generated environment textures are cleaned up.
- Pixel density is bounded to 1–1.5. No shadows, bloom, particle system, downloaded models,
  external HDRIs, or full-screen postprocessing are used. The glass rim uses a small Fresnel shader.
- Entrance, hover, focus, scroll and card motion use transforms/opacity. Decorative symbols
  have no controls or tab stops. Search, CTAs, mode controls and mobile navigation remain usable.
- Initial application JS: about **493 KB / 153 KB gzip**; scene: about **921 KB / 245 KB gzip**;
  CSS: about **91 KB / 18 KB gzip**. These are Vite output sizes, not timing measurements.
  The scene remains large enough to trigger Vite's 500 KB chunk advisory; the warning is not suppressed.
  Reduced-motion and unsupported-WebGL tests verify that the scene module is not requested.
- Motion adds approximately 48 KB gzip to the existing main application bundle. GPU performance
  and Core Web Vitals have not been certified on physical mobile devices.

## Verification

Final commands from `frontend`:

```sh
npm run lint
npm test
npm run build
npx playwright test --workers=1 --output=/tmp/dav-ai-immersive/full-regression
```

- ESLint: passed, no warnings.
- Vitest: **135 passed**, 13 files.
- TypeScript project build and Vite production build: passed.
- Complete default Chromium suite: **16 passed**. API-dependent research/export journeys
  use the existing HTTP mocks; this is not a claim of live backend/model verification.
- Final glass geometry refinement: the **3 WebGL/fallback tests passed again**, with
  a fresh lint and production build.
- Shared navigation geometry, visible selector, themes, keyboard menu behavior and no document
  horizontal overflow checked on all six routes at **320, 390, 768, 1366 and 1920 pixels**.
- Live rendering, independent decorative animation, context loss, unavailable WebGL, and
  runtime reduced-motion changes exercised in Chromium. The test file explicitly enables
  Chromium's software WebGL renderer; the application still rejects performance-caveat
  contexts on ordinary devices. Native hardware/mobile, Firefox and Safari were not exercised.
- `git diff --check`: passed.

The first normal-motion headless attempt correctly used the static fallback; its GPU caveat
prevented the live-canvas expectation. Explicit test-only software-renderer flags allowed the
live-scene regression to run. Screenshot inspection also caught a surface overlap; matched
sphere tessellation and a separate outer radius remove that artifact.

`npm audit` reported one **pre-existing development-only Zod advisory** from the ESLint React
Hooks dependency tree (`zod@4.3.6`, GHSA-mrhx-c7xc-m3w5). The added visual runtime packages
were not identified in that advisory. No unrelated dependency upgrade was applied.
Three.js currently emits a development deprecation warning for Fiber's use of `THREE.Clock`;
this does not fail the build or browser checks.

## Release boundary

Ready for local visual review. Publication remains unauthorized (`publication_validated=false`).
This frontend work does not authorize public serving or change the local research-service boundary.
