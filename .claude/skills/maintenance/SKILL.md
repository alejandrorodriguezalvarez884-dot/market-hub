---
name: maintenance
description: The daily maintenance run of Market Hub - check that the live sites are well, write and publish the day's opinion articles, tell the portal's Media page what the account last posted on Instagram, and report to the user. It is what the scheduled task "market-hub-maintenance" runs every morning with nobody watching; use it too when the user asks to run the maintenance by hand ("lanza el mantenimiento", "pasa la revisión diaria").
---

# The daily maintenance run

You are running Market Hub's daily maintenance. Usually nobody is watching: a scheduled task of
the Claude desktop app started this session, and the user reads your last message when they
next look. So there is nobody to ask. Decide, do, and say what you decided.

Work from the root of the workspace (the folder with `CLAUDE.md`, `scripts/` and the
submodules). Its `CLAUDE.md`, and the `CLAUDE.md` of any repo you touch, hold as in any other
session. This run is the one thing in the workspace that is scheduled, and the user asked for it
(2026-10-13): where a rule says nothing runs on a timer, this run is the exception it names.

## Before the tasks

```bash
scripts/sync.sh        # each submodule at the tip of its main; safe to run again
```

A repo that `sync.sh` left alone (uncommitted changes, another branch) has someone else's work in
it: other sessions edit these repos in parallel. Never stash, reset, check out or commit what is
not yours. A task that needs that repo clean says below what to do instead.

## The tasks

Do them in this order, each from its own file in `tasks/`. Read the file when you get to it.

| # | Task | File |
|---|---|---|
| 1 | The live sites: are they up, are they right, did they log errors | [tasks/health.md](tasks/health.md) |
| 2 | The opinion section: one to five new articles, published | [tasks/opinion.md](tasks/opinion.md) |
| 3 | The Media page: the account's latest posts on Instagram, told to the portal | [tasks/instagram.md](tasks/instagram.md) |

A task that fails does not stop the ones after it, unless its file says so. Note what failed
and go on.

To add a task: write `tasks/<name>.md` (what to do, what it may never do, what to report), add
its row to the table, and give it its heading in the report below.

## What no task may do

Running alone changes what is allowed. Whatever a task's own file says, this run never:

- deploys, rolls back or changes the configuration of a service (`make deploy`, `gcloud run ...`,
  DNS, secrets, spending caps, rate limits). It finds and reports; the user fixes, or says to;
- edits the code of a product repo, or commits to one. The only repo it writes to is
  `market-hub-opinion`, and only what the opinion task says;
- spends on an API key of the user's. Reading the sites as a visitor is free; asking the portal
  to refresh its news (`POST /api/public/news/refresh`) or calling a tool's model route is not;
- sends anything to anyone: no email, no message, no post. The report is your last message.
  Telling the portal what the account already posted on Instagram (task 3) reads Instagram and
  posts nothing there;
- publishes a reader's article, or a video. Those are the user's call, one by one;
- touches a broker connector, for anything;
- looks for another way in when a credential fails (`gcloud`, `git push`). Say what failed and
  what the user has to run, and go on with what does not need it.

If a tool asks for a permission and nobody answers, that step did not happen: say so in the
report, with the command, so the user can allow it for the next run.

## The report

Your last message, in Spanish, short, and nothing after it. What is wrong goes first.

```
**Mantenimiento de Market Hub · <fecha>**

**Atención** (solo si hay algo: lo que falló o pide una decisión, una línea cada cosa)

**Webs** — <N> comprobaciones: todo bien / <n> fallos, <n> avisos
- (cada fallo o aviso: qué, dónde, la causa probable y qué haría falta para arreglarlo)

**Opinión** — <n> artículos publicados
- [Título](https://themarkethub.app/opinion/article/?slug=<slug>): su tesis en una línea. Portada: <estilo>.
- (lo que no se escribió y por qué; de lo que no estés seguro)
- Artículos de lectores esperando revisión: <n>

**Instagram en Media** — <n> posts en la página
- (los nuevos desde ayer: qué son y su primera línea; lo que falló)

**No se hizo** (solo si algo se saltó: qué y por qué)
```

Say only what you checked. "Todo bien" means the check ran and passed, not that you did not look.
