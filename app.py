"""Local assignment-statement recognizer. Run with Python 3.9 or newer."""

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
from urllib.parse import urlsplit
import webbrowser

from recognizer import MAX_STATEMENT_LENGTH, validate_statement


ROOT = Path(__file__).resolve().parent / "static"
ASSETS = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/style.css": ("style.css", "text/css; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/favicon.svg": ("favicon.svg", "image/svg+xml"),
}


class Handler(BaseHTTPRequestHandler):
    def respond(self, status, payload, content_type="application/json; charset=utf-8"):
        if isinstance(payload, dict):
            payload = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(payload)

    def do_GET(self):
        asset = ASSETS.get(urlsplit(self.path).path)
        if asset is None:
            self.respond(404, {"error": "Page not found."})
            return
        filename, content_type = asset
        self.respond(200, (ROOT / filename).read_bytes(), content_type)

    def do_HEAD(self):
        self.do_GET()

    def do_POST(self):
        if urlsplit(self.path).path != "/api/validate":
            self.respond(404, {"error": "Endpoint not found."})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.respond(400, {"error": "Invalid request length."})
            return
        if not 0 < length <= 32768:
            self.close_connection = True
            self.respond(413, {"error": "Request is empty or too large."})
            return
        try:
            body = json.loads(self.rfile.read(length).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            self.respond(400, {"error": "Send a JSON object containing a statement."})
            return
        if not isinstance(body, dict) or not isinstance(body.get("statement"), str):
            self.respond(400, {"error": "The statement must be text."})
            return
        if len(body["statement"]) > MAX_STATEMENT_LENGTH:
            self.respond(413, {"error": f"Use at most {MAX_STATEMENT_LENGTH} characters."})
            return
        self.respond(200, validate_statement(body["statement"]))


def main():
    parser = argparse.ArgumentParser(description="Run the local assignment recognizer.")
    parser.add_argument("--port", type=int, default=8000, help="Local port (default: 8000)")
    parser.add_argument("--no-browser", action="store_true", help="Do not open a browser automatically")
    args = parser.parse_args()
    try:
        server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    except OSError as exc:
        parser.exit(1, f"Could not start the server: {exc}\nTry another port: python app.py --port 8001\n")
    url = f"http://localhost:{server.server_port}"
    print(f"\n  ASSIGNMENT STATEMENTS RECOGNIZER\n  Running at {url}\n  Press Ctrl+C to stop.\n", flush=True)
    if not args.no_browser:
        timer = threading.Timer(0.5, webbrowser.open, args=(url,))
        timer.daemon = True
        timer.start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
