import json
import socketserver
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler
from pathlib import Path

from src.storage import list_reports, load_report

_INDEX_HTML = Path(__file__).parent / "index.html"


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/":
            self._send_file(_INDEX_HTML, "text/html; charset=utf-8")
        elif path == "/api/reports":
            self._send_json(list_reports())
        elif path.startswith("/api/reports/"):
            filename = path[len("/api/reports/"):]
            try:
                self._send_json(load_report(filename))
            except (ValueError, FileNotFoundError):
                self.send_error(404)
        else:
            self.send_error(404)

    def _send_json(self, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: Path, content_type: str):
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass


def start_web_server(port_start: int = 8080):
    socketserver.TCPServer.allow_reuse_address = True
    httpd = None
    port = port_start
    for p in range(port_start, port_start + 20):
        try:
            httpd = socketserver.TCPServer(("", p), _Handler)
            port = p
            break
        except OSError:
            continue
    if httpd is None:
        print("Не удалось запустить веб-сервер: все порты заняты.")
        return

    url = f"http://localhost:{port}"
    print(f"  Веб-интерфейс: {url}  (Ctrl+C для выхода)\n")
    threading.Timer(1.0, webbrowser.open, args=[url]).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nСервер остановлен.")
    finally:
        httpd.server_close()
