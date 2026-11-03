import importlib.util
import io
import os
import sys
import types
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

HERE = Path(__file__).parent
store: dict[str, str] = {}


class FakeS3:
    def put_object(self, Bucket, Key, Body, **_):
        store[Key] = Body

    def list_objects_v2(self, Bucket, Prefix, MaxKeys):
        return {
            "Contents": [{"Key": k} for k in store if k.startswith(Prefix)][:MaxKeys]
        }

    def get_object(self, Bucket, Key):
        return {"Body": io.BytesIO(store[Key].encode())}


sys.modules["boto3"] = types.SimpleNamespace(client=lambda name: FakeS3())
os.environ.update(BUCKET_NAME_LOCAL="local", STAGE="local")


def load(name):
    spec = importlib.util.spec_from_file_location(
        name, HERE / "lambda_src" / name / "index.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


orders, users = load("orders"), load("users")


class Handler(BaseHTTPRequestHandler):
    def _send(self, status, body, ctype="application/json"):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.end_headers()
        self.wfile.write(body.encode())

    def _route(self, method):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode() if length else None
        if self.path == "/api/orders":
            result = orders.handler({"httpMethod": method, "body": body}, None)
        elif self.path.startswith("/users/"):
            result = users.handler(
                {"pathParameters": {"id": self.path.split("/")[-1]}}, None
            )
        else:
            return self._send(
                200, (HERE / "site" / "index.html").read_text(), "text/html"
            )
        self._send(result["statusCode"], result["body"])

    def do_GET(self):
        self._route("GET")

    def do_POST(self):
        self._route("POST")


print("Open http://localhost:8000  (type http://localhost:8000 in the Users URL box)")
HTTPServer(("", 8000), Handler).serve_forever()
