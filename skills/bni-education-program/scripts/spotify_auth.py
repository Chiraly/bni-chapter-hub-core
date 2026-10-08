"""
spotify_auth.py — one-time: get a Spotify refresh token for the playlist refresh.

Run this once on your own machine. Nothing is sent anywhere except Spotify, and
the token is printed only in your terminal — paste it straight into Netlify's
environment variables. Do not paste it into a chat, a document, or the repo.

Before running, at https://developer.spotify.com/dashboard:
  1. Create an app (any name, e.g. "BNI Riverside playlist")
  2. Add this exact Redirect URI:   http://127.0.0.1:8888/callback
     (Spotify requires the numeric loopback address - "localhost" is rejected)
  3. Copy the Client ID and Client Secret

Then:
    python spotify_auth.py --client-id XXX --client-secret YYY

It opens your browser, you click Agree, and it prints the refresh token.
"""
import argparse
import base64
import http.server
import json
import secrets
import threading
import urllib.parse
import urllib.request
import webbrowser

PORT = 8888
REDIRECT = f"http://127.0.0.1:{PORT}/callback"
# Enough to replace items in a playlist you own, public or private.
SCOPES = "playlist-modify-public playlist-modify-private"

result = {}


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        result.update({k: v[0] for k, v in q.items()})
        ok = "code" in result
        body = ("<h2>Done - you can close this tab.</h2>"
                "<p>The refresh token is in your terminal.</p>" if ok else
                f"<h2>Authorisation failed</h2><p>{result.get('error','unknown')}</p>")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body.encode())

    def log_message(self, *a):
        pass                      # keep the terminal clean


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--client-id", required=True)
    ap.add_argument("--client-secret", required=True)
    a = ap.parse_args()

    state = secrets.token_urlsafe(16)
    auth_url = "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode({
        "client_id": a.client_id, "response_type": "code",
        "redirect_uri": REDIRECT, "scope": SCOPES, "state": state,
    })

    srv = http.server.HTTPServer(("127.0.0.1", PORT), Handler)
    threading.Thread(target=srv.handle_request, daemon=True).start()

    print(f"Opening your browser. If it doesn't open, visit:\n\n{auth_url}\n")
    webbrowser.open(auth_url)
    print("Waiting for you to click Agree...")

    for _ in range(1200):                      # ~2 minutes
        if result:
            break
        threading.Event().wait(0.1)
    srv.server_close()

    if "code" not in result:
        raise SystemExit(f"no authorisation code returned ({result or 'timed out'})")
    if result.get("state") != state:
        raise SystemExit("state mismatch - start again")

    basic = base64.b64encode(f"{a.client_id}:{a.client_secret}".encode()).decode()
    req = urllib.request.Request(
        "https://accounts.spotify.com/api/token",
        data=urllib.parse.urlencode({
            "grant_type": "authorization_code", "code": result["code"],
            "redirect_uri": REDIRECT,
        }).encode(),
        headers={"Authorization": f"Basic {basic}",
                 "Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        tok = json.load(r)

    print("\n" + "=" * 64)
    print("Set these four in Netlify -> Project configuration -> Environment variables")
    print("=" * 64)
    print(f"SPOTIFY_CLIENT_ID       {a.client_id}")
    print(f"SPOTIFY_CLIENT_SECRET   {a.client_secret}")
    print(f"SPOTIFY_REFRESH_TOKEN   {tok['refresh_token']}")
    print("SPOTIFY_PLAYLIST_ID     0OzCqqMEiCMbLcFTS885RF")
    print("=" * 64)
    print("The refresh token does not expire. Keep it out of the repo and out of chat.")


if __name__ == "__main__":
    main()
