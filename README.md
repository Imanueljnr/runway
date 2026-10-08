# Runway

Emmanuel's personal budget app. Installable on phone and laptop (PWA), data synced through Supabase.

- **Payday:** 40% savings (Risevest) · 40% living (converted to naira) · 20% stocks (Bamboo / Hisa)
- **Naira:** 50% needs · 30% wants · 20% set aside (emergency fund + buffer)
- **Monthly bills** you tick off, **everyday spending** you log, and a forecast of whether the month makes it.

## Layout
- `src/app.html` — the whole app (UI + budget maths). Edit this.
- `src/backend-supabase.js` — sign-in and sync.
- `build.py` — builds `docs/` (the site GitHub Pages serves) and `dist-artifact.html`.
- `supabase.json` — project URL and public anon key (safe to commit; data is protected by row-level security).

## Ship a change
```
python3 build.py && git add -A && git commit -m "..." && git push
```
GitHub Pages serves `docs/` from `main`. The service worker picks up the new version on the next open.

Font: Open Runde (SIL Open Font License, `fonts/OFL.txt`).
