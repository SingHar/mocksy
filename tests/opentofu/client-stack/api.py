# Test API for the client stack: reports whether it reaches PostgreSQL and Valkey.
import http.server, json, os, socket, sys


def reach(host, port):
    try:
        with socket.create_connection((host, int(port)), timeout=3) as s:
            return True, s.getpeername()[0]
    except OSError as e:
        return False, str(e)


def cache_ping(host, port):
    try:
        with socket.create_connection((host, int(port)), timeout=3) as s:
            s.sendall(b"PING\r\n")
            return s.recv(64).decode().strip()
    except OSError as e:
        return str(e)


class Api(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            body = b"ok"
        else:
            db_ok, db_peer = reach(os.environ["DB_HOST"], os.environ["DB_PORT"])
            body = json.dumps({
                "task": socket.gethostname(),
                "path": self.path,
                "db": {"reachable": db_ok, "peer": db_peer, "password_set": bool(os.environ.get("DB_PASSWORD"))},
                "cache": cache_ping(os.environ["CACHE_HOST"], os.environ["CACHE_PORT"]),
                "via": self.headers.get("Via"),
            }).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        print(fmt % args, flush=True)


print("api starting; db", os.environ["DB_HOST"], os.environ["DB_PORT"], "cache", os.environ["CACHE_HOST"], flush=True)
http.server.ThreadingHTTPServer(("", 8080), Api).serve_forever()
