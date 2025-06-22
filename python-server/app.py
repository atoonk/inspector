import json
import os
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
from urllib.request import Request, urlopen

clients = set()

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        repo_root = os.path.join(os.path.dirname(__file__), "..")
        dist_dir = os.path.join(repo_root, "client", "dist")
        if os.path.exists(dist_dir):
            static_dir = dist_dir
        else:
            static_dir = os.path.join(repo_root, "client")
            print(
                "\u26A0\ufe0f Built client not found. Serving source files from client/. "
                "Run 'npm run build-client' for a production build."
            )
        print(f"Serving client files from {static_dir}")
        super().__init__(*args, directory=static_dir, **kwargs)

    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'ok'}).encode())
            return
        if self.path == '/config':
            env_str = os.environ.get('MCP_ENV_VARS', '{}')
            try:
                env = json.loads(env_str)
            except json.JSONDecodeError:
                env = {}
            config = {
                'defaultEnvironment': env,
                'defaultCommand': os.environ.get('MCP_PROXY_COMMAND', ''),
                'defaultArgs': os.environ.get('MCP_PROXY_ARGS', ''),
            }
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(config).encode())
            return
        parsed = urlparse(self.path)
        if parsed.path == '/sse':
            query = parse_qs(parsed.query)
            remote_url = query.get('url', [None])[0]
            if remote_url:
                try:
                    req = Request(remote_url, headers={'Accept': 'text/event-stream'})
                    with urlopen(req) as resp:
                        self.send_response(200)
                        self.send_header('Content-Type', 'text/event-stream')
                        self.send_header('Cache-Control', 'no-cache')
                        self.send_header('Connection', 'keep-alive')
                        self.end_headers()
                        for line in resp:
                            self.wfile.write(line)
                            self.wfile.flush()
                    return
                except Exception as e:
                    self.send_response(500)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': str(e)}).encode())
                    return
            else:
                # local SSE echo server
                self.send_response(200)
                self.send_header('Content-Type', 'text/event-stream')
                self.send_header('Cache-Control', 'no-cache')
                self.send_header('Connection', 'keep-alive')
                self.end_headers()
                clients.add(self.wfile)
                try:
                    while True:
                        time.sleep(1)
                except BrokenPipeError:
                    pass
                finally:
                    clients.discard(self.wfile)
                return

        if self.path in ('', '/', '/index.html'):
            self.path = '/index.html'
            return super().do_GET()

        file_path = self.translate_path(self.path)
        if not os.path.exists(file_path):
            self.path = '/index.html'
        return super().do_GET()

    def do_POST(self):
        if self.path.startswith('/message'):
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length)
            for c in list(clients):
                try:
                    c.write(b'data:' + body + b'\n\n')
                    c.flush()
                except Exception:
                    clients.discard(c)
            self.send_response(204)
            self.end_headers()
            return
        self.send_response(404)
        self.end_headers()


def run(host='0.0.0.0', port=6277):
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"⚙️ Python proxy server listening on {host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', '6277'))
    run(host, port)
