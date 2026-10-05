"""The portal's service: the site and the API, from one origin.

    GET    /api/health
    GET    /api/config              Google client id and the tools' addresses (public)
    POST   /api/auth/google         {credential}: Google ID token -> session cookie
    POST   /api/auth/logout
    GET    /api/me                  the signed-in user, or 401
    DELETE /api/me                  delete the account and everything saved
    GET    /api/portfolio           positions and watchlist
    PUT    /api/portfolio           replace them
    GET    /api/dashboard           positions valued at today's prices, favourites, history
    GET    /api/search?q=           companies by ticker or name

Everything else is the static site, when MARKETHUB_STATIC_DIR points at its build.
"""

from __future__ import annotations

import logging
import os
import secrets
import threading
import time
from collections import defaultdict, deque
from pathlib import Path

from fastapi import Body, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from . import dashboard
from .auth import InvalidToken, Verifier, google_verifier, verify
from .config import (EARNINGS_RADAR_URL, FUNDAMENTALS_LAB_URL, GOOGLE_CLIENT_ID, PER_IP_PER_HOUR,
                     SECURE_COOKIES, SESSION_DAYS, SESSION_SECRET)
from .market import Directory, Fmp, MarketUnavailable
from .users import InvalidPortfolio, UserStore, clean, default_users, empty, touch

log = logging.getLogger("markethub.api")

UNSAFE = {"POST", "PUT", "PATCH", "DELETE"}


class RateLimiter:
    def __init__(self, limit: int, window: float = 3600.0):
        self.limit, self.window = limit, window
        self._calls: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, who: str) -> bool:
        now = time.monotonic()
        with self._lock:
            calls = self._calls[who]
            while calls and now - calls[0] > self.window:
                calls.popleft()
            if len(calls) >= self.limit:
                return False
            calls.append(now)
            return True


def _client_address(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    return forwarded.split(",")[0].strip() or (request.client.host if request.client else "unknown")


def create_app(users: UserStore | None = None, market: Fmp | None = None, directory: Directory | None = None,
               verifier: Verifier = google_verifier, client_id: str | None = None,
               session_secret: str | None = None, secure_cookies: bool | None = None,
               static_dir: str | None = None) -> FastAPI:
    """App factory. Tests pass their own pieces, so they need no network and no Google."""
    logging.basicConfig(level=logging.INFO)
    app = FastAPI(title="Market Hub", docs_url=None, redoc_url=None, openapi_url=None)
    users = users or default_users()
    market = market or Fmp()
    directory = directory or Directory()
    client_id = GOOGLE_CLIENT_ID if client_id is None else client_id
    secret = session_secret or SESSION_SECRET
    if not secret:
        log.warning("SESSION_SECRET is not set: using a random one, sessions end on restart")
        secret = secrets.token_urlsafe(32)
    secure = SECURE_COOKIES if secure_cookies is None else secure_cookies
    limiter = RateLimiter(PER_IP_PER_HOUR)

    origins = [o.strip() for o in os.environ.get("MARKETHUB_ALLOWED_ORIGINS", "").split(",") if o.strip()]

    @app.middleware("http")
    async def same_origin_writes(request: Request, call_next):
        """Writes must come from this site. With the session cookie set to SameSite=Lax this
        closes cross-site request forgery: a foreign page can neither send the cookie on a POST
        nor pass this check."""
        if request.method in UNSAFE and request.url.path.startswith("/api/"):
            origin = request.headers.get("origin")
            own = f"{request.url.scheme}://{request.url.netloc}"
            forwarded_host = request.headers.get("x-forwarded-host") or request.headers.get("host", "")
            allowed = {own, f"https://{forwarded_host}", *origins}
            if origin not in allowed:
                return JSONResponse({"detail": "Cross-site request refused."}, status_code=403)
        response = await call_next(request)
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    # Added after the middleware above, so it runs first and the session is ready for it.
    app.add_middleware(SessionMiddleware, secret_key=secret, session_cookie="mh_session",
                       max_age=SESSION_DAYS * 86400, same_site="lax", https_only=secure)
    if origins:
        app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True,
                           allow_methods=["GET", "POST", "PUT", "DELETE"], allow_headers=["content-type"])

    def current(request: Request) -> dict:
        user = request.session.get("user")
        if not user:
            raise HTTPException(401, "Sign in first.")
        return user

    def load(user: dict) -> dict:
        doc = users.get(user["id"])
        if doc is None:
            doc = empty(user["id"])
        return doc

    def allow(request: Request) -> None:
        if not limiter.allow(_client_address(request)):
            raise HTTPException(429, "Too many requests from this address. Try again later.")

    @app.get("/api/health")
    def health() -> dict:
        return {"ok": True}

    @app.get("/api/config")
    def config() -> dict:
        return {
            "google_client_id": client_id,
            "tools": {
                "earnings_radar": EARNINGS_RADAR_URL or None,
                "fundamentals_lab": FUNDAMENTALS_LAB_URL or None,
            },
        }

    @app.post("/api/auth/google")
    def sign_in(request: Request, credential: str = Body(embed=True, max_length=4096)) -> dict:
        allow(request)
        try:
            g = verify(credential, client_id, verifier)
        except InvalidToken as exc:
            log.info("sign-in refused: %s", exc)
            raise HTTPException(401, "Google sign-in could not be verified.") from None
        doc = users.get(g.id)
        new = doc is None
        if new:
            doc = empty(g.id)
        # Profile fields are refreshed on every sign-in; they are only shown back to the user.
        users.put(g.id, touch(doc, email=g.email, name=g.name, picture=g.picture))
        request.session.clear()
        request.session["user"] = {"id": g.id, "email": g.email, "name": g.name, "picture": g.picture}
        log.info("sign-in ok new=%s", new)
        return {"user": request.session["user"], "new": new,
                "has_data": bool(doc.get("positions") or doc.get("watchlist"))}

    @app.post("/api/auth/logout")
    def sign_out(request: Request) -> dict:
        request.session.clear()
        return {"ok": True}

    @app.get("/api/me")
    def me(request: Request) -> dict:
        user = current(request)
        doc = load(user)
        return {"user": user, "has_data": bool(doc.get("positions") or doc.get("watchlist"))}

    @app.delete("/api/me")
    def delete_me(request: Request) -> dict:
        user = current(request)
        users.delete(user["id"])
        request.session.clear()
        log.info("account deleted")
        return {"deleted": True}

    @app.get("/api/portfolio")
    def portfolio(request: Request) -> dict:
        doc = load(current(request))
        return {"positions": doc.get("positions", []), "watchlist": doc.get("watchlist", []),
                "updated_utc": doc.get("updated_utc")}

    @app.put("/api/portfolio")
    def save_portfolio(request: Request, positions: list = Body(default=[]), watchlist: list = Body(default=[])) -> dict:
        user = current(request)
        try:
            pos, watch = clean(positions, watchlist, known=directory.known)
        except InvalidPortfolio as exc:
            raise HTTPException(400, str(exc)) from None
        except MarketUnavailable as exc:
            raise HTTPException(503, str(exc)) from None
        doc = touch(load(user), positions=pos, watchlist=watch)
        users.put(user["id"], doc)
        return {"positions": pos, "watchlist": watch, "updated_utc": doc["updated_utc"]}

    @app.get("/api/dashboard")
    def dash(request: Request) -> dict:
        user = current(request)
        allow(request)
        try:
            return dashboard.build(load(user), market)
        except MarketUnavailable as exc:
            raise HTTPException(503, str(exc)) from None

    @app.get("/api/search")
    def search(request: Request, q: str = Query(min_length=1, max_length=60)) -> dict:
        try:
            found = directory.search(q)
        except MarketUnavailable as exc:
            raise HTTPException(503, str(exc)) from None
        return {"companies": [{"ticker": c.ticker, "name": c.name} for c in found]}

    static_dir = static_dir or os.environ.get("MARKETHUB_STATIC_DIR", "")
    if static_dir and Path(static_dir).is_dir():
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="site")
    return app
