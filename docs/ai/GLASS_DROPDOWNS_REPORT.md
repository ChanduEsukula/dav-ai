# Evidence Explorer glass dropdown refinement

Implemented locally October 27, 2026. Current branch and all pre-existing uncommitted/untracked work preserved. No commit, push or deployment. No backend, clinical evidence, source-verification, publication or exact-product authorization changes.

## Implementation

Strength and Dosage form now use a shared `GlassSelect` wrapper around **@radix-ui/react-select 2.4.1**, added because no accessible select/listbox primitive was installed. Research Pro's sort menu uses the same component, retaining its existing sort options and behavior. Radix handles keyboard focus, arrow/Home/End navigation, typeahead, Enter/Space selection, Escape dismissal, outside pointers and focus restoration. Reference: [official Radix Select documentation](https://www.radix-ui.com/primitives/docs/components/select).

Everyday menus have a dark translucent teal surface with aqua borders/highlights. Research Pro uses midnight indigo and lavender, with slightly denser rows. Both share 18px rounded glass surfaces, white text, selected checkmarks and visible focus/hover states. Opening and closing use 150ms CSS opacity/transform animations; reduced motion removes them.

Menus portal to `document.body` with explicit theme tokens and z-index 1000, escaping the app's isolated glass layers and overflow clipping. Popper positioning flips/shifts against viewport edges, with collision padding derived from the measured sticky-header clearance. Menus constrain their height to available space and expose primitive-provided scroll controls. No page layout is moved when a menu opens.

All options still derive from the actual returned products. The UI maps index keys to original stored values, so the empty-string All filter remains unambiguous. A strength such as `.25 mg/1` displays as `0.25 mg / 1` without changing its underlying filtering value or inventing a unit/formulation. Immediate-release and extended-release products remain distinct. Labeler/NDC filtering, sorting, product details and exact-product selection retain the same logic.

Everyday's More product filters remains a native keyboard-accessible disclosure. It now contains a compact, responsive glass toolbar with side-by-side labeler/NDC fields on desktop and wrapping fields on mobile. Research Pro retains its immediately visible technical fields.

## Exact changed files

1. `frontend/package.json` — add `@radix-ui/react-select`.
2. `frontend/package-lock.json` — lock the primitive and its transitive dependencies.
3. `frontend/src/components/GlassSelect.tsx` — new shared accessible select wrapper and viewport/header positioning.
4. `frontend/src/components/glass-select.css` — teal/violet trigger/menu styles, selected states, transitions and compact toolbar.
5. `frontend/src/components/GlassSelect.test.tsx` — new primitive-integration tests for stored values, selection, Escape and focus restoration.
6. `frontend/src/components/MedicationDiscovery.tsx` — use glass filters, readable strength labels, compact advanced toolbar and matching Pro sort.
7. `frontend/src/components/MedicationDiscovery.test.tsx` — exercise actual option selection instead of firing a native select change.
8. `frontend/src/test/setup.ts` — jsdom pointer-capture/scroll API shims; actual behavior tested in Chromium.
9. `frontend/e2e/glass-select.spec.ts` — keyboard, mouse, touch, filtering, checkmarks, outside dismissal, viewport bounds and stacking checks.
10. `scripts/capture_glass_dropdowns.mjs` — reproducible actual-data open-menu screenshots.
11. `docs/ai/GLASS_DROPDOWNS_REPORT.md` — this report.

Additional generated artifacts: 13 files under `docs/ai/screenshots/glass-dropdowns-2026-10-27/`: eight open-menu screenshots (two filters × two modes × desktop/mobile), two expanded-toolbar screenshots, review PNG/HTML and JSON receipt.

## Screenshots

- [Four open-menu comparison](screenshots/glass-dropdowns-2026-10-27/dropdown-review.png)
- [Browsable comparison](screenshots/glass-dropdowns-2026-10-27/dropdown-review.html)
- [Everyday strength](screenshots/glass-dropdowns-2026-10-27/everyday-strength-1440.png)
- [Research Pro dosage form on mobile](screenshots/glass-dropdowns-2026-10-27/research_pro-form-390.png)
- [Compact advanced toolbar](screenshots/glass-dropdowns-2026-10-27/advanced-toolbar-1440.png)

Each filter was captured open independently, matching normal select behavior (one active menu at a time). Captures use actual frozen-release API responses, with no response mocks. Eight capture checks found no page exceptions or horizontal overflow. Tests separately verify viewport bounds and hit-testing above other layers.

## Verification

- ESLint: pass.
- TypeScript (`tsc -b`) and Vite build: pass.
- Vitest: **165 passed** across 18 files.
- Existing Chromium regressions: **29 passed**.
- New glass-filter Chromium journeys: **3 passed** (Everyday and Pro keyboard/mouse flows, plus touch/reduced-motion/positioning). Final targeted reruns wait for real option focus and the 150ms opening animation before outside dismissal; no arbitrary sleeps or application behavior bypasses.
- Real frozen-release search, admitted-source inspection and PDF export: **3 passed**, with outbound network blocked.
- `git diff --check`: pass.

Browser tests confirm filtering to two actual 0.25mg products, resetting to nine products, separately selecting extended-release tablets, then narrowing to the exact NDC. They verify selected checkmarks, restored trigger focus, keyboard Space/Enter/Home/End/Escape, pointer selection and click-outside dismissal. Touch checks cover both themes, both menus, viewport edges, hit-testing above glass layers and reduced motion. Existing tests retain six-route navigation, mobile layouts, source units and research workflows. No manual screen-reader/device audit is claimed.

## Dependency and performance notes

One direct runtime dependency was added, with 37 transitive packages installed. Production main JS is about 614 kB (192 kB gzip), versus about 524 kB (161 kB gzip) before this change; CSS is about 131 kB (26 kB gzip). The increase buys an established accessibility/positioning primitive instead of bespoke interaction code. The lazy 3D scene is unchanged at about 922 kB (245 kB gzip), and Vite's existing large-chunk warning remains visible.

`npm audit` reports one existing high-severity development-tool advisory in `zod@4.3.6`, pulled by the pre-existing eslint-plugin-react-hooks/zod-validation-error chain, not the new Radix runtime dependency. This task did not run an unrelated dependency-wide audit fix. See [GHSA-mrhx-c7xc-m3w5](https://github.com/advisories/GHSA-mrhx-c7xc-m3w5).
