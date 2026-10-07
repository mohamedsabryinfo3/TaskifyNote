# TaskifyNote Release Checklist

- GitHub `main` contains `apps/android`, `apps/api`, `apps/web`.
- Neon schema migrations applied.
- Vercel API deployed with `DATABASE_URL` and `PERSONAL_API_KEY`.
- Vercel Web deployed with API URL and API key.
- `/api/v1/health` returns 200.
- Android points to the deployed API base URL.
- Gemini key is stored only as a Vercel Environment Variable.
