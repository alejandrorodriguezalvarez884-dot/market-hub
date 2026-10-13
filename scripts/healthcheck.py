#!/usr/bin/env python3
"""Ask the three live sites whether they are well, and say what is not.

    python3 scripts/healthcheck.py            the pages, the public API and the certificates
    python3 scripts/healthcheck.py --logs     also yesterday's errors in Cloud Run (needs gcloud signed in)

It only reads: every request is a GET with no session, the kind a visitor makes. It never asks
the portal to refresh its news (that is a POST, and it spends on the model) and it never calls a
route that does. Standard library only, so it runs with any Python 3.

One line per check: ok, WARN or FAIL. It exits with 1 if anything failed; a warning does not.
"""

from __future__ import annotations

import json
import socket
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

PORTAL = "https://themarkethub.app"
FUNDAMENTALS = "https://fundamentals.themarkethub.app"
RADAR_HUB = "https://radar.themarkethub.app"
RADAR = "https://earningsradar.app"

# The portal's pages a visitor opens. They are static: the page loads and then asks the API.
PAGES = ["/", "/today/", "/markets/", "/news/", "/news/article/", "/opinion/", "/opinion/article/",
         "/opinion/submit/", "/media/", "/quote/?t=AAPL", "/signin/", "/dashboard/", "/portfolio/",
         "/watchlist/", "/community/", "/community/competitions/", "/tools/", "/privacy/", "/terms/"]

# The Cloud Run services behind the sites (the project has others, which are not ours to read).
SERVICES = ["market-hub", "fundamentals-lab", "earnings-radar", "earnings-radar-hub"]

TIMEOUT = 30            # seconds for one request
SLOW = 8.0              # an answer slower than this is a warning (a cold start takes a few seconds)
NEWS_OLD_HOURS = 48     # the news refreshes when someone visits; older than this, nobody could
CERT_WARN_DAYS = 14     # Cloud Run renews its certificates long before this

results: list[tuple[str, str, str]] = []


def say(level: str, name: str, detail: str = "") -> None:
    results.append((level, name, detail))
    print(f"{level:<4}  {name}" + (f"  ({detail})" if detail else ""), flush=True)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def trust() -> ssl.SSLContext:
    """The certificates to believe. A Python installed from python.org on a Mac comes with none
    of its own; the system's list is in /etc/ssl/cert.pem."""
    context = ssl.create_default_context()
    if not context.cert_store_stats()["x509_ca"]:
        for bundle in ("/etc/ssl/cert.pem", "/etc/ssl/certs/ca-certificates.crt"):
            try:
                context.load_verify_locations(bundle)
                break
            except OSError:
                continue
    return context


TRUST = trust()
opener = urllib.request.build_opener(NoRedirect, urllib.request.HTTPSHandler(context=TRUST))


def get(url: str) -> tuple[int, dict, bytes, float]:
    """A GET that follows no redirect: the status, the headers, the body and how long it took."""
    request = urllib.request.Request(url, headers={"User-Agent": "market-hub-healthcheck"})
    start = time.monotonic()
    try:
        with opener.open(request, timeout=TIMEOUT) as response:
            body = response.read()
            return response.status, dict(response.headers), body, time.monotonic() - start
    except urllib.error.HTTPError as error:
        return error.code, dict(error.headers), error.read(), time.monotonic() - start


def check(name: str, url: str, status: int = 200, kind: str | None = None, test=None):
    """One request. `test` is given the parsed JSON (or the body) and returns what is wrong, or
    None. Returns the parsed answer, so that a later check can use it."""
    try:
        code, headers, body, seconds = get(url)
    except Exception as error:  # no answer at all: DNS, TLS, timeout
        say("FAIL", name, f"no answer: {error}")
        return None
    content_type = headers.get("Content-Type", headers.get("content-type", ""))
    if code != status:
        say("FAIL", name, f"status {code}, expected {status}")
        return None
    if kind and kind not in content_type:
        say("FAIL", name, f"content type {content_type!r}, expected {kind}")
        return None
    answer: object = body
    if "json" in content_type:
        try:
            answer = json.loads(body)
        except ValueError:
            say("FAIL", name, "the answer is not JSON")
            return None
    if test:
        try:
            wrong = test(answer)
        except Exception as error:  # an answer of another shape than the one the check reads
            wrong = f"unexpected answer: {error!r}"
        if wrong:
            say("WARN" if wrong.startswith("warn:") else "FAIL", name, wrong.removeprefix("warn:").strip())
            return answer
    if seconds > SLOW:
        say("WARN", name, f"slow: {seconds:.1f}s")
    else:
        say("ok", name, f"{seconds:.2f}s")
    return answer


def hours_since(stamp: str) -> float:
    return (datetime.now(timezone.utc) - datetime.fromisoformat(stamp)).total_seconds() / 3600


def portal() -> None:
    for page in PAGES:
        check(f"portal page {page}", PORTAL + page, kind="text/html",
              test=lambda body: None if len(body) > 2000 and b"</html>" in body else "the page is cut short")

    api = PORTAL + "/api"
    check("portal health", f"{api}/health", test=lambda d: None if d.get("ok") else "not ok")
    check("portal config", f"{api}/config",
          test=lambda d: None if d.get("google_client_id") and d.get("tools") else "no sign-in or tools in it")
    check("portal sign-in wall", f"{api}/me", status=401)

    def overview(d):
        if d.get("sample"):
            return "it is serving sample figures, not Yahoo's"
        empty = [k for k in ("indices", "sectors", "commodities", "currencies", "rates") if not d.get(k)]
        if empty:
            return f"empty: {', '.join(empty)}"
        if d.get("sample_sections"):
            return f"warn: sample figures in {', '.join(d['sample_sections'])}"
        return None
    check("markets overview", f"{api}/public/overview", test=overview)

    def quote(d):
        return "sample figures" if d.get("sample") else None if (d.get("price") or 0) > 0 else "no price"
    check("quote AAPL", f"{api}/public/quote?t=AAPL", test=quote)
    check("chart AAPL", f"{api}/public/chart?symbol=AAPL&range=1Y",
          test=lambda d: None if d.get("bars") else "no bars")
    check("search", f"{api}/search?q=apple", test=lambda d: None if d.get("companies") else "no companies")

    def news(d):
        if d.get("sample"):
            return "it is serving sample news"
        if not d.get("items"):
            return "no items"
        refreshed = d.get("refreshed_utc")
        if refreshed and hours_since(refreshed) > NEWS_OLD_HOURS:
            return f"warn: last refreshed {hours_since(refreshed):.0f}h ago"
        return None
    front = check("news", f"{api}/public/news?limit=20", test=news)
    if isinstance(front, dict) and front.get("items"):
        item = urllib.parse.quote(front["items"][0]["id"])
        check("news item", f"{api}/public/news/item?id={item}",
              test=lambda d: None if d.get("title") or d.get("item") else "no item in it")

    cards = check("opinion", f"{api}/public/opinion", test=lambda d: None if d.get("articles") else "no articles")
    if isinstance(cards, dict) and cards.get("articles"):
        newest = cards["articles"][0]
        slug = urllib.parse.quote(newest["slug"])
        check("opinion article", f"{api}/public/opinion/item?slug={slug}",
              test=lambda d: None if d else "empty")
        check("opinion comments", f"{api}/public/opinion/comments?slug={slug}")
        missing = [a["slug"] for a in cards["articles"] if not a.get("cover")]
        if missing:
            say("FAIL", "opinion covers", f"no cover: {', '.join(missing)}")
        else:
            version = newest["cover"]["v"]
            check("opinion cover", f"{api}/public/opinion/cover?slug={slug}&v={version}", kind="image/jpeg",
                  test=lambda body: None if len(body) > 10_000 else "the picture is too small to be one")


def tools() -> None:
    for name, base in (("fundamentals", FUNDAMENTALS), ("radar (hub)", RADAR_HUB)):
        check(f"{name} health", f"{base}/api/health", test=lambda d: None if d.get("ok") else "not ok")
        # Without a session the tool sends the visitor to the portal's sign-in.
        try:
            code, headers, _, _ = get(base + "/")
        except Exception as error:
            say("FAIL", f"{name} sign-in wall", f"no answer: {error}")
            continue
        to = headers.get("Location", headers.get("location", ""))
        if code == 302 and to.startswith(PORTAL + "/signin/"):
            say("ok", f"{name} sign-in wall")
        else:
            say("FAIL", f"{name} sign-in wall", f"status {code} to {to or 'nowhere'}: it should send to the portal's sign-in")
    check("earningsradar.app health", f"{RADAR}/api/health", test=lambda d: None if d.get("ok") else "not ok")
    check("earningsradar.app page /", f"{RADAR}/", kind="text/html",
          test=lambda body: None if len(body) > 2000 else "the page is cut short")


def certificates() -> None:
    for base in (PORTAL, FUNDAMENTALS, RADAR_HUB, RADAR):
        host = urllib.parse.urlparse(base).hostname
        try:
            with socket.create_connection((host, 443), timeout=TIMEOUT) as raw:
                with TRUST.wrap_socket(raw, server_hostname=host) as tls:
                    expires = ssl.cert_time_to_seconds(tls.getpeercert()["notAfter"])
        except Exception as error:
            say("FAIL", f"certificate {host}", str(error))
            continue
        days = (expires - time.time()) / 86400
        say("WARN" if days < CERT_WARN_DAYS else "ok", f"certificate {host}", f"{days:.0f} days left")


def logs() -> None:
    """Yesterday's errors in Cloud Run: what the services logged at ERROR or above, and the
    requests they answered with a 5xx. Read with the user's gcloud session; nothing is changed."""
    names = " OR ".join(f'"{s}"' for s in SERVICES)
    query = (f'resource.type="cloud_run_revision" AND resource.labels.service_name=({names}) '
             f"AND (severity>=ERROR OR httpRequest.status>=500)")
    try:
        out = subprocess.run(
            ["gcloud", "logging", "read", query, "--freshness=24h", "--limit=300", "--format=json"],
            capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.TimeoutExpired) as error:
        say("WARN", "cloud run logs", f"not read: {error}")
        return
    if out.returncode != 0:
        say("WARN", "cloud run logs", f"not read: {out.stderr.strip().splitlines()[-1] if out.stderr.strip() else 'gcloud failed'}")
        return
    entries = json.loads(out.stdout or "[]")
    by_service: dict[str, list[dict]] = {s: [] for s in SERVICES}
    for entry in entries:
        by_service.setdefault(entry["resource"]["labels"].get("service_name", "?"), []).append(entry)
    for service, found in by_service.items():
        if not found:
            say("ok", f"logs {service}", "no errors in 24h")
            continue
        say("WARN", f"logs {service}", f"{len(found)} errors in 24h")
        seen: set[str] = set()
        for entry in found:
            request = entry.get("httpRequest") or {}
            text = entry.get("textPayload") or json.dumps(entry.get("jsonPayload") or {})
            line = (f"{request.get('status')} {request.get('requestMethod')} {request.get('requestUrl')}"
                    if request else text.strip().splitlines()[-1] if text.strip() else "(empty)")
            if line not in seen and len(seen) < 8:
                seen.add(line)
                print(f"        {entry.get('timestamp', '')[:19]}  {line[:200]}")


def main() -> int:
    portal()
    tools()
    certificates()
    if "--logs" in sys.argv:
        logs()
    failed = sum(1 for level, _, _ in results if level == "FAIL")
    warned = sum(1 for level, _, _ in results if level == "WARN")
    print(f"\n{len(results)} checks: {failed} failed, {warned} warnings.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
