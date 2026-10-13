# Task 2: the day's opinion articles

Write between one and five new opinion articles, publish them and commit them, in
`market-hub-opinion/`. The user decided (2026-10-13) that these are published without anyone
reading them first. That makes you the last check: an article that is not solid does not go out.

How an article is written, drawn, checked and published is in
`market-hub-opinion/.claude/skills/update-opinion/SKILL.md`. Read it, and
`market-hub-opinion/CLAUDE.md`, and follow them step by step. This file only says what changes
when nobody is there.

## Before you write

Work from `market-hub-opinion/`. Look at where it stands:

```bash
git status --short && git branch --show-current
```

- On a branch other than `main`: someone is working here. Do not write today; report it.
- Uncommitted changes that are not yours: leave them exactly as they are. You may go on, and at
  the end you add and commit only the files you made, by name (never `git add -A` or `git add .`).
  If one of those changes is to a file `make check` or `make publish` reads (an article, a cover,
  `src/`), do not publish over someone's half-done work: do not write today; report it.

Then count what today already has: the files in `articles/` dated today (UTC). The day's limit is
five, whoever wrote them. If a run already wrote today's (the app was reopened, or the user ran
this by hand), write only what is left, and if nothing new has happened since, write none.

## How many

Between one and five, and the material decides, not the number:

- Count the subjects in the day's news where there is something to argue and the documents to
  argue it from. A busy day (results season, a central bank, a big deal) carries four or five; a
  quiet one or a weekend, one or two.
- Never pad. Five thin articles are worse than two good ones. An article whose argument repeats
  one of the last two weeks' is not a new article.
- One is the floor only if one holds up. If not a single subject has solid sources today, write
  none and say why. That is a result, not a failure.

## Where the skill says to ask or tell the user

There is nobody to ask. So:

- An existing article fails `make check` at the start: do not fix someone else's article alone.
  If it stops `make publish`, do not write today; report which article and what the check said.
- A fact you cannot trace to a source: it does not go in. If the argument needs it, that article
  is not written.
- A cover that still does not look right after three passes: draw a simpler one. An article does
  not go out without its cover.
- In doubt whether a sentence is advice: it is. Rewrite it or drop it.
- Before publishing, read each article once more from top to bottom as its reader would, against
  its sources: every figure, date and quotation is in a source it links, and the link opens.

## Publish, commit, verify

```bash
make check
make publish
```

- `make publish` fails for lack of credentials (`gcloud`): do not look for another way. Commit
  the articles (they are written and checked), do not push anything else, and report that they
  are **not live** and that the user has to run `gcloud auth application-default login` and then
  `make publish` in `market-hub-opinion/`.
- After publishing, check that each new article is on the portal:
  `curl -s "https://themarkethub.app/api/public/opinion/item?slug=<slug>"` answers with it, and
  its card in `curl -s "https://themarkethub.app/api/public/opinion"` has a `cover`. One that is
  not there after two minutes is a finding for the report.
- Commit only your files (the articles, `covers/src/<slug>.*`, `covers/<slug>.jpg`, the handoff)
  with a message that names the articles, and `git push`. If the push fails, say so: the articles
  are live but the repo is behind.

`docs/HANDOFF.md`: do not add a row per day. Keep one row in "Dónde estamos" for the daily run
("Artículos diarios"), and each day replace its text: the date, how many articles there are in
all, today's subjects and the styles of their covers. Update "Última actualización".

## Readers' articles

```bash
make inbox
```

Only count them for the report. Do not fetch, edit, publish or decline one: the user reads them
and says which runs.

## What to report

For each article: its title as a link, its argument in one line, the style of its cover. Then
what you chose not to write and why, anything you were not sure of, and how many readers'
articles are waiting.
