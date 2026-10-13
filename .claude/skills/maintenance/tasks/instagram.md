# Task 3: the account's latest posts on Instagram, for the Media page

The portal's Media page (https://themarkethub.app/media/) shows what Market Hub's account last
posted on Instagram, whatever it is: a reel, a picture, an album. The portal does not ask
Instagram (it holds no token): `the-market-hub-media` reads the account's posts and leaves a
card for each, with its cover, in the portal's Firestore. A reel published from that repo with
`make instagram` tells the portal at once; this task is for what was posted any other way, from
the phone. The user asked for it on 2026-10-13.

## 1. Tell the portal

```bash
cd the-market-hub-media && make posts
```

It reads the account's twelve latest posts with the token in `.secrets/instagram-token.txt`
(reading is free), makes only the covers the portal does not have yet, and writes the cards and
those covers to the portal's Firestore with the user's `gcloud` session. It lists the posts it
left there, newest first. It works whatever state the repo is in: it changes no file of it.

## 2. See that the page has them

```bash
curl -s https://themarkethub.app/api/public/instagram
```

The posts it answers should be the ones `make posts` listed, in that order. The portal keeps its
answer for a minute. A post that `make posts` said it left out (its cover could not be made) is
a finding: say which, and why.

## What to report

How many posts the page shows and, if any is new since yesterday's run, which (its kind and its
first line). If `make posts` failed, what it said: an expired token is renewed by the user
(`the-market-hub-media/README.md`, "Instagram"), and no `gcloud` session is theirs to open.

## What this task never does

It never posts, comments, deletes or changes anything on Instagram: it only reads. It never
edits or commits to `the-market-hub-media` or the portal, and never deploys. If the token or
`gcloud` fails, it does not look for another way in: the page keeps showing what it had.
