# CI And Quality Gates

I use GitHub Actions to run the same checks I run locally before a commit.

The workflow has two jobs:

- Backend tests with Python 3.11 and `pytest`.
- Frontend checks with Node 22, `npm run lint`, `npm run typecheck`, and `npm run build`.

I keep backend and frontend as separate jobs so a failure points to the right side of the stack quickly. This also makes the repo easier to talk through in an interview: every push has a basic proof that the API tests and dashboard build still work.

Current limitation: this is not deployment CI yet. It does not build Docker images, push releases, or deploy to Vercel/Render. I will add that after the app is ready for a public demo.
