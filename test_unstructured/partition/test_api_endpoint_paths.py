"""Exercise API endpoint normalization through the real SDK and a local HTTP server."""

import io
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from unstructured.partition.api import partition_via_api


@pytest.mark.parametrize(
    ("api_path", "request_path"),
    [
        ("/general/v0/general/", "/general/v0/general"),
        ("/proxy/general/v0/general/", "/proxy/general/v0/general"),
        ("/general/v0/general-proxy", "/general/v0/general-proxy/general/v0/general"),
        ("/general/v0/general-proxy/", "/general/v0/general-proxy/general/v0/general"),
        ("", "/general/v0/general"),
        ("/", "/general/v0/general"),
        ("/general/v0/general", "/general/v0/general"),
        ("/proxy", "/proxy/general/v0/general"),
        ("/proxy/", "/proxy/general/v0/general"),
        ("/proxy/general/v0/general", "/proxy/general/v0/general"),
    ],
)
@pytest.mark.parametrize("input_type", ["filename", "file"])
def test_custom_endpoint_reaches_the_expected_route(api_path, request_path, input_type, tmp_path):
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            payload = self.rfile.read(int(self.headers["Content-Length"]))
            requests.append((self.path, payload))
            if self.path == request_path:
                self.send_response(200)
                response = [
                    {
                        "type": "NarrativeText",
                        "element_id": "api-element",
                        "text": "Uploaded text.",
                        "metadata": {"filetype": "text/plain"},
                    }
                ]
            else:
                self.send_response(400)
                response = {"detail": "Unexpected request path"}
            body = json.dumps(response).encode()
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        if input_type == "filename":
            path = tmp_path / "document.txt"
            path.write_bytes(b"Uploaded text.")
            source = {"filename": str(path)}
        else:
            source = {"file": io.BytesIO(b"Uploaded text."), "metadata_filename": "document.txt"}

        elements = partition_via_api(
            **source,
            api_url=f"http://127.0.0.1:{server.server_port}{api_path}",
            api_key="local-test-key",
            strategy="fast",
            retries_max_elapsed_time=1,
        )

        assert [element.text for element in elements] == ["Uploaded text."]
        assert elements[0].metadata.filetype == "text/plain"
        assert len(requests) == 1
        assert requests[0][0] == request_path
        assert b"Uploaded text." in requests[0][1]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
