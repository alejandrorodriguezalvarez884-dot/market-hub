"""Sign in with Google.

The browser gets an ID token from Google Identity Services and posts it once to
``/api/auth/google``. The server checks it (signature, audience, issuer, expiry, verified email)
and keeps only the user's id in a signed, HTTP-only session cookie. The token itself is not
stored.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

ISSUERS = {"accounts.google.com", "https://accounts.google.com"}


@dataclass(frozen=True)
class GoogleUser:
    id: str  # Google's stable "sub": the key of the user's data
    email: str
    name: str
    picture: str


class InvalidToken(Exception):
    pass


# (token, client_id) -> the token's claims. Tests pass their own.
Verifier = Callable[[str, str], dict]

_transport = google_requests.Request()


def google_verifier(token: str, client_id: str) -> dict:
    """Checks the signature against Google's published keys (cached by google-auth), the
    audience and the expiry."""
    return id_token.verify_oauth2_token(token, _transport, audience=client_id, clock_skew_in_seconds=10)


def verify(token: str, client_id: str, verifier: Verifier = google_verifier) -> GoogleUser:
    if not client_id:
        raise InvalidToken("sign-in is not configured")
    try:
        claims = verifier(token, client_id)
    except ValueError as exc:  # google-auth raises ValueError for every bad token
        raise InvalidToken("invalid token") from exc
    if claims.get("iss") not in ISSUERS:
        raise InvalidToken("wrong issuer")
    if claims.get("aud") != client_id:
        raise InvalidToken("wrong audience")
    if not claims.get("email") or not claims.get("email_verified"):
        raise InvalidToken("email not verified")
    if not claims.get("sub"):
        raise InvalidToken("no subject")
    return GoogleUser(
        id=str(claims["sub"]),
        email=str(claims["email"]),
        name=str(claims.get("name") or claims["email"].split("@")[0]),
        picture=str(claims.get("picture") or ""),
    )
