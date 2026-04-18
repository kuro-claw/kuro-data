# kuro-data

JSON data store for Kuro Platform. Served via GitHub Pages.

## Structure

```
kuroboard/     → KuroBoard module data
kurotrader/    → KuroTrader module data
goku-health/   → Goku Health module data
kuro-site/     → kuro-site module data
```

## Data Format

All endpoints return:

```json
{
  "updatedAt": "2026-04-17T22:30:00Z",
  "source": "daemon-name",
  "version": 1,
  "data": { ... }
}
```

## URLs

- https://kuro-claw.github.io/kuro-data/kuroboard/overview.json
- https://kuro-claw.github.io/kuro-data/kurotrader/overview.json
- https://kuro-claw.github.io/kuro-data/goku-health/overview.json
- https://kuro-claw.github.io/kuro-data/kuro-site/overview.json
