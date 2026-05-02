# IoMT SIEM Dashboard

Next.js frontend for the integrated IoMT cybersecurity monitoring demo.

Run the FastAPI backend first, then start this app:

```bash
npm install
npm run dev
```

The app reads `NEXT_PUBLIC_API_BASE_URL`; if unset, it uses `http://localhost:8000`.

Production preview:

```bash
npm run build
npm run start -- --hostname localhost --port 3001
```

The demo login uses a single Admin role. Full authentication and additional roles can be added later.
