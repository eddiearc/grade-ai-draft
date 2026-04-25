#!/usr/bin/env python3
"""
AI draft revision server.

Renders one prose draft in a local browser UI, lets the user mark exact passages
with rewrite comments, and blocks until the user clicks 完成. The browser writes
a sidecar JSON file that the agent uses to revise the source draft.
"""

import argparse
import html
import http.server
import json
import os
import socket
import socketserver
import subprocess
import sys
import threading
import time
import urllib.parse
import webbrowser


def find_free_port(start=7890, tries=20):
    for port in range(start, start + tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def open_in_browser(url):
    try:
        if sys.platform == "darwin":
            subprocess.Popen(["open", url])
        elif sys.platform.startswith("win"):
            os.startfile(url)  # noqa: F821
        else:
            webbrowser.open(url)
    except Exception as exc:
        print(f"[ai-redraft] could not auto-open browser: {exc}", file=sys.stderr)
        print(f"[ai-redraft] please open manually: {url}", file=sys.stderr)


def read_text(path):
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def render_template(template_path, source_path, sidecar_path):
    content = read_text(source_path)
    template = read_text(template_path)
    title = os.path.basename(source_path)
    safe_content = content.replace("</script>", "<\\/script>")
    return (
        template.replace("{{CONTENT}}", safe_content)
        .replace("{{TITLE}}", html.escape(title, quote=True))
        .replace("{{SOURCE_PATH}}", html.escape(source_path, quote=True))
    )


class UiHeartbeat:
    def __init__(self, now=None, grace_seconds=12):
        self._now = now or time.monotonic
        self.grace_seconds = grace_seconds
        self._last_seen = None
        self._lock = threading.Lock()

    def beat(self):
        with self._lock:
            self._last_seen = self._now()

    def should_shutdown(self):
        with self._lock:
            if self._last_seen is None:
                return False
            return self._now() - self._last_seen > self.grace_seconds


def exit_code_for_result(result):
    if result.get("closed"):
        return 2
    if result.get("cancelled"):
        return 3
    return 0


def main():
    parser = argparse.ArgumentParser(description="Open a local AI redraft UI.")
    parser.add_argument("--port", type=int, default=0, help="Port to bind (0 = auto-pick from 7890)")
    parser.add_argument("--source", required=True, help="Absolute path to the draft file")
    parser.add_argument("--timeout", type=int, default=1800, help="Seconds to wait for completion")
    parser.add_argument(
        "--close-grace-seconds",
        type=float,
        default=12,
        help="Seconds without browser heartbeat before auto-shutdown",
    )
    parser.add_argument("--no-open", action="store_true", help="Do not auto-open the browser")
    args = parser.parse_args()

    if args.port == 0:
        args.port = find_free_port()

    skill_dir = os.path.dirname(os.path.abspath(__file__))
    source_path = os.path.abspath(args.source)
    sidecar_path = source_path + ".annotations.json"
    template_path = os.path.join(skill_dir, "template.html")

    if not os.path.exists(source_path):
        print(f"[ai-redraft] source not found: {source_path}", file=sys.stderr)
        sys.exit(2)
    if not os.path.exists(template_path):
        print(f"[ai-redraft] template not found: {template_path}", file=sys.stderr)
        sys.exit(2)

    done_event = threading.Event()
    result_holder = {}
    ui_heartbeat = UiHeartbeat(grace_seconds=args.close_grace_seconds)

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def _cors(self):
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")

        def _send_json(self, payload, status=200):
            raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Connection", "close")
            self._cors()
            self.end_headers()
            self.wfile.write(raw)

        def _read_json_body(self):
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8") if length else ""
            return json.loads(body) if body else {}

        def _write_sidecar(self, data):
            data.setdefault("source_file", source_path)
            data.setdefault("source_name", os.path.basename(source_path))
            data.setdefault("annotations", [])
            with open(sidecar_path, "w", encoding="utf-8") as handle:
                json.dump(data, handle, ensure_ascii=False, indent=2)
            result_holder["path"] = sidecar_path
            result_holder["count"] = len(data.get("annotations", []))

        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path in ("/", "/index.html"):
                rendered = render_template(template_path, source_path, sidecar_path)
                raw = rendered.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(raw)))
                self.send_header("Connection", "close")
                self._cors()
                self.end_headers()
                self.wfile.write(raw)
                return
            if parsed.path == "/ping":
                raw = b"pong"
                self.send_response(200)
                self.send_header("Content-Length", str(len(raw)))
                self.send_header("Connection", "close")
                self._cors()
                self.end_headers()
                self.wfile.write(raw)
                return
            if parsed.path == "/heartbeat":
                ui_heartbeat.beat()
                self._send_json({"ok": True})
                return
            if parsed.path == "/favicon.svg":
                favicon_path = os.path.join(skill_dir, "favicon.svg")
                if os.path.exists(favicon_path):
                    with open(favicon_path, "rb") as handle:
                        raw = handle.read()
                    self.send_response(200)
                    self.send_header("Content-Type", "image/svg+xml")
                    self.send_header("Content-Length", str(len(raw)))
                    self.send_header("Cache-Control", "no-cache")
                    self.send_header("Connection", "close")
                    self.end_headers()
                    self.wfile.write(raw)
                    return
                self.send_response(404)
                self.end_headers()
                return
            if parsed.path == "/favicon.ico":
                self.send_response(204)
                self.end_headers()
                return
            self.send_response(404)
            self.end_headers()

        def do_OPTIONS(self):
            self.send_response(204)
            self._cors()
            self.end_headers()

        def do_POST(self):
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path == "/heartbeat":
                ui_heartbeat.beat()
                self._send_json({"ok": True})
                return

            if parsed.path == "/save":
                try:
                    self._write_sidecar(self._read_json_body())
                    self._send_json({"ok": True})
                except Exception as exc:
                    self._send_json({"ok": False, "error": str(exc)}, status=400)
                return

            if parsed.path == "/close":
                try:
                    data = self._read_json_body()
                    if data.get("annotations") is not None:
                        self._write_sidecar(data)
                    self._send_json({"ok": True, "path": sidecar_path})
                except Exception as exc:
                    self._send_json({"ok": False, "error": str(exc)}, status=400)
                return

            if parsed.path == "/done":
                if done_event.is_set():
                    self._send_json({"ok": True, "already_done": True})
                    return
                try:
                    data = self._read_json_body()
                    if data.get("annotations") is not None:
                        self._write_sidecar(data)
                    self._send_json({"ok": True, "path": sidecar_path})
                    done_event.set()
                except Exception as exc:
                    self._send_json({"ok": False, "error": str(exc)}, status=400)
                return

            if parsed.path == "/cancel":
                result_holder["cancelled"] = True
                self._send_json({"ok": True})
                done_event.set()
                return

            self.send_response(404)
            self.end_headers()

    class ReusableServer(socketserver.TCPServer):
        allow_reuse_address = True

    def monitor_ui_heartbeat():
        while not done_event.wait(1):
            if ui_heartbeat.should_shutdown():
                result_holder["closed"] = True
                done_event.set()
                return

    try:
        with ReusableServer(("127.0.0.1", args.port), Handler) as server:
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            monitor_thread = threading.Thread(target=monitor_ui_heartbeat, daemon=True)
            monitor_thread.start()
            url = f"http://localhost:{args.port}/"
            print(f"[ai-redraft] serving {url} for {source_path}", flush=True)
            if not args.no_open:
                open_in_browser(url)
            print(f"[ai-redraft] waiting for 完成 click (timeout {args.timeout}s)...", flush=True)
            completed = done_event.wait(timeout=args.timeout)
            server.shutdown()

            if not completed:
                print(f"[ai-redraft] timed out after {args.timeout}s", flush=True)
                sys.exit(1)
            if result_holder.get("cancelled"):
                print("[ai-redraft] user cancelled", flush=True)
                sys.exit(exit_code_for_result(result_holder))
            if result_holder.get("closed"):
                print("[ai-redraft] browser closed before 完成: auto-shutdown", flush=True)
                sys.exit(exit_code_for_result(result_holder))

            count = result_holder.get("count", 0)
            print(f"[ai-redraft] user clicked 完成: saved {count} comments to {sidecar_path}", flush=True)
            sys.exit(exit_code_for_result(result_holder))
    except OSError as exc:
        print(f"[ai-redraft] server error: {exc}", file=sys.stderr)
        print(f"[ai-redraft] port {args.port} may be in use, try --port 7891", file=sys.stderr)
        sys.exit(4)


if __name__ == "__main__":
    main()
