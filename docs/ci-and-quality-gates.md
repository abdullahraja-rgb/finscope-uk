# CI And Quality Gates

GitHub Actions runs the same checks used locally before a commit.

The workflow has two jobs:

- Backend tests with Python 3.11 and `pytest`.
- Frontend checks with Node 22, `npm run lint`, `npm run typecheck`, and `npm run build`.

Backend and frontend jobs are separate so failures point to the right side of the stack quickly.

## Limitations

The workflow does not yet build Docker images, publish releases, or deploy to Vercel/Render.
