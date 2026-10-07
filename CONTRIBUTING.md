# Working on this fork

**Setup:** each of us has one branch and does whatever we want in it: `osh` for Osh (Triode works
in his own repo, or a `triode` branch here if he likes). No per-task branches, no rebasing.
`main` follows Triode's SDK; `osh` reaches `main` through one long-running pull request.

Three rules (agreed 2026-10-06):

1. **Checks must pass before merging into `main`.** Every push and pull request runs type check,
   tests and a build (`.github/workflows/checks.yml`). Red means no merge.
2. **Tag a release when something works end to end** (`v0.1.0`, …) and attach the built
   `.np3theme`.
3. **No secrets in git** (dev tokens stay in `.env.local`), and commit messages follow the SDK's
   style: `feat:`, `fix:`, `docs:`, `style:`, `refactor:`, `chore:`.

Run the same checks locally before pushing: `npm run typecheck && npm test && npm run build`.
