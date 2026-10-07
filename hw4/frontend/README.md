# Campus Customs — Frontend

React + Vite + TypeScript storefront and chat widget. See the main [README](../README.md) for full setup.

```bash
npm install
npm run dev      # http://localhost:5173 (needs the backend on :8000)
npm run build    # type-check + production build into dist/
npm run lint
```

`vite.config.ts` proxies `/api` and `/media` to the FastAPI backend at `http://localhost:8000`.
