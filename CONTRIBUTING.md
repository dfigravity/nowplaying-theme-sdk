# Working on this fork

Two people, four rules (agreed 2026-10-06):

1. **One branch per task**, named `who/what` (e.g. `osh/fader-moves`, `triode/controller-feed`).
   Keep it small and merge within days.
2. **Checks must pass before merging.** Every pull request runs type check, tests and a build
   (`.github/workflows/checks.yml`). Red means no merge.
3. **Tag a release when something works end to end** (`v0.1.0`, …) and attach the built
   `.np3theme`.
4. **No secrets in git** (dev tokens stay in `.env.local`), and commit messages follow the SDK's
   style: `feat:`, `fix:`, `docs:`, `style:`, `refactor:`, `chore:`.

Run the same checks locally before pushing: `npm run typecheck && npm test && npm run build`.
