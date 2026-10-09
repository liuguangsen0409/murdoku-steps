# SDD ledger — plan: ../docs/superpowers/plans/2026-10-07-murdoku-tutorial.md
Ruling: Approved standalone directory replaces Git worktree and Git-dependent ledger helpers — parent is not a repository; do not initialize unrelated content.
Ruling: Preserve original SVG art per approved user plan, rather than generate replacement concept art.
Pre-flight: Task 1 Puzzle feeds Task 2 replay and Task 3 rendering; same 1-based cell IDs. Task 2 snapshots feed Task 3 currentIndex; 25 states include introduction.
Task 1: in progress.
Task 1: complete — 4 normalization tests RED→GREEN; 7 composed furniture SVGs + 6 portraits; original coordinates match all six placements.
Task 2: complete — 4 replay tests RED→GREEN; 24 steps / 25 snapshots; immutable prior states and character-scoped exclusions verified.
Task 3: complete — DOM/SVG implementation, responsive teaching layout, local-only runtime assets, typecheck and production build passed.
Final independent review: 3 P2 findings fixed in one pass: step 3 retained A candidates; mobile focus reset made visible/toggleable; specific furniture names added to cell labels. Two regression tests RED→GREEN, 10 total tests passing.
Ruling: No image-generated concept — approved spec explicitly preserves original art; visual QA compares map geometry to original and interface to approved written layout. Furniture base+detail layers and original tint restored after screenshot exposed white silhouette chairs.
Task 4: browser verified 1280×720 and 360×740; no mobile horizontal overflow; step 16→2 restores 0 placements and two A candidates; final step correct. Broken portrait path showed explicit paused-teaching alert; restored original JSON afterward.

Task 4: complete — final 10 tests and production build pass; keyboard/next/previous verified; screenshots saved and inspected with view_image. Reduced-motion CSS implemented; OS preference simulation not performed. No Git branch workflow applies to this standalone non-repository directory.
