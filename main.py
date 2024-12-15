from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
import json
import mimetypes

PORT = 3000
STORAGE_DIR = Path("storage")
DATA_FILE = STORAGE_DIR / "data.json"
TEMPLATE_DIR = Path(".")
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

STORAGE_DIR.mkdir(exist_ok=True)
if not DATA_FILE.exists():
    DATA_FILE.write_text("{}", encoding="utf-8")


class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path == "/":
            self.send_html_file("index.html")
        elif parsed_path.path == "/message":
            self.send_html_file("message.html")
        elif parsed_path.path == "/read":
            self.show_messages()
        elif Path(parsed_path.path[1:]).exists():
            self.send_static_file(parsed_path.path[1:])
        else:
            self.send_html_file("error.html", 404)

    def do_POST(self):
        if self.path == "/message":
            content_length = int(self.headers["Content-Length"])
            body = self.rfile.read(content_length).decode("utf-8")
            data = parse_qs(body)
            username = data.get("username", [""])[0]
            message = data.get("message", [""])[0]
            self.save_message(username, message)

            self.send_response(302)
            self.send_header("Location", "/")
            self.end_headers()
        else:
            self.send_html_file("error.html", 404)

    def send_html_file(self, filename, status=200):
        file_path = Path(filename)
        if not file_path.exists():
            self.send_error_page()
            return
        self.send_response(status)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        with file_path.open("rb") as file:
            self.wfile.write(file.read())

    def send_static_file(self, filepath):
        try:
            file_path = Path(filepath)
            if not file_path.exists():
                self.send_html_file("error.html", 404)
                return
            self.send_response(200)
            mime_type, _ = mimetypes.guess_type(file_path)
            self.send_header("Content-type", mime_type or "application/octet-stream")
            self.end_headers()
            with file_path.open("rb") as file:
                self.wfile.write(file.read())
        except Exception:
            self.send_html_file("error.html", 404)

    def save_message(self, username, message):
        timestamp = datetime.now().isoformat()
        if DATA_FILE.exists():
            with DATA_FILE.open("r", encoding="utf-8") as file:
                data = json.load(file)
        else:
            data = {}
        
        data[timestamp] = {"username": username, "message": message}
        
        with DATA_FILE.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

    def show_messages(self):
        with DATA_FILE.open("r", encoding="utf-8") as file:
            messages = json.load(file)
        template = env.get_template("read.html")
        rendered_content = template.render(messages=messages)
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(rendered_content.encode("utf-8"))

    def send_error_page(self):
        self.send_html_file("error.html", 404)


def run():
    server_address = ("", PORT)
    httpd = HTTPServer(server_address, HttpHandler)
    print(f"Сервер запущено на порті {PORT}...")
    httpd.serve_forever()


if __name__ == "__main__":
    run()
