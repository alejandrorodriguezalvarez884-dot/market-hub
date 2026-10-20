# Task 1: the live sites

Find out whether the sites are up and right, and whether they logged errors since
yesterday. You only look. Nothing here fixes anything.

## 1. Run the check

```bash
python3 scripts/healthcheck.py --logs
```

It reads, as a visitor with no session, the portal's pages and public API
(https://themarkethub.app), the tools behind its login (https://fundamentals.themarkethub.app,
https://radar.themarkethub.app, https://playground.themarkethub.app,
https://peers.themarkethub.app, https://options.themarkethub.app), Bot League with its public board
(https://bots.themarkethub.app; and that the portal's old `/api/bot/spec` says it moved there), the
public radar (https://earningsradar.app) and their certificates; `--logs` adds the last 24 hours of errors and 5xx answers in their Cloud Run
services, read with the user's `gcloud` session. One line per check: `ok`, `WARN` or `FAIL`.

If the logs could not be read (no `gcloud` session), say so in the report: the rest of the check
still counts.

## 2. Look at what a request cannot see

If this session has a browser (the built-in browser's tools), open these pages one by one and
read the console and the failed network requests of each:

`https://themarkethub.app/`, `/today/`, `/markets/`, `/news/`, `/opinion/`, `/media/`,
`/quote/?t=AAPL`

A script error, a request that fails, a page that stays empty where it should show figures or
articles: each is a finding. Do not sign in, do not submit a form, do not click anything that
writes. If there is no browser, say in the report that the pages were not opened.

## 3. For each thing that is wrong, find why

A `FAIL` or a `WARN` is where the work starts, not the report. Before you write it down:

- Run that one request again (`curl -s -i <url>`): a cold start or a blip that does not repeat is
  an "aviso", not a "fallo". Say it was seen once.
- Read the service's log around it:
  `gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="<service>" AND severity>=WARNING' --freshness=2h --limit=50 --format='value(timestamp,severity,textPayload)'`
- Read the code that answers that route in its repo (the table in the workspace's `CLAUDE.md`
  says which folder is which site; the API is under `src/` in each) and the repo's
  `docs/HANDOFF.md`, which often says what is known to be fragile.
- The services are `market-hub` (the portal), `fundamentals-lab`, `earnings-radar`
  (earningsradar.app), `earnings-radar-hub` (radar.themarkethub.app), `market-hub-playground`,
  `peer-map` (peers.themarkethub.app), `options-lab` (options.themarkethub.app) and `bot-league`
  (bots.themarkethub.app).

A site added to the workspace gets its lines in `scripts/healthcheck.py` (its address, its
service); if the workspace's `CLAUDE.md` lists a live site the check does not read, say so in the
report.

Then report each as: what is wrong, where (the address), since when if the log says, the likely
cause, and what it would take to fix it. If you do not know the cause, say that and what you
ruled out.

What is expected and is not a finding:

- `stale: true` in the news: the portal refreshes its news when a visitor finds it old. Only news
  older than 48 hours is a warning (the check knows).
- Market figures that do not move at the weekend or out of hours.
- The portal answers 404 to `/robots.txt` and `/sitemap.xml`.
- `stale: true` or no `as of` on the Bot League board: its curves move when someone visits after a
  close (a POST the check never makes). The check prints it as information, not as a warning.

## What this task never does

It never deploys, restarts or reconfigures a service, never edits a product repo, never asks the
portal to refresh its news, never signs in. If a site is down, the report says so first, in
"Atención", and the run goes on to the next task.
