import json
import os
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

clients = set()

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        static_dir = os.path.join(os.path.dirname(__file__), '..', 'client')
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
        if self.path == '/sse':
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
