from __future__ import annotations

import io
import json
import unittest

from tdd_dsl.lsp import LspServer


class LspServerTests(unittest.TestCase):
    def test_initialize_reports_text_document_sync(self) -> None:
        server = LspServer(stdin=io.BytesIO(), stdout=io.BytesIO())

        response, notifications, should_exit = server.handle_message(
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
        )

        self.assertFalse(should_exit)
        self.assertEqual(notifications, [])
        self.assertEqual(response["id"], 1)
        self.assertEqual(response["result"]["serverInfo"]["name"], "tdd-dsl-lsp")
        self.assertTrue(response["result"]["capabilities"]["textDocumentSync"]["openClose"])

    def test_did_open_publishes_parser_diagnostics(self) -> None:
        server = LspServer(stdin=io.BytesIO(), stdout=io.BytesIO())
        text = """suite "Calculator"
target python "calculator"

case "adds":
  given input:
    {"a": 1, "b": 2}
  when call "add"
"""

        response, notifications, should_exit = server.handle_message(
            {
                "jsonrpc": "2.0",
                "method": "textDocument/didOpen",
                "params": {"textDocument": {"uri": "file:///tmp/example.tdd", "text": text}},
            }
        )

        self.assertIsNone(response)
        self.assertFalse(should_exit)
        self.assertEqual(notifications[0]["method"], "textDocument/publishDiagnostics")
        diagnostics = notifications[0]["params"]["diagnostics"]
        self.assertEqual(diagnostics[0]["range"]["start"], {"line": 3, "character": 0})
        self.assertIn("requires then equals", diagnostics[0]["message"])

    def test_did_change_replaces_document_and_clears_diagnostics(self) -> None:
        server = LspServer(stdin=io.BytesIO(), stdout=io.BytesIO())
        uri = "file:///tmp/example.tdd"
        valid_text = """suite "Calculator"
target python "calculator"

case "adds":
  given input:
    {"a": 1, "b": 2}
  when call "add"
  then equals:
    3
"""

        _, notifications, _ = server.handle_message(
            {
                "jsonrpc": "2.0",
                "method": "textDocument/didChange",
                "params": {
                    "textDocument": {"uri": uri},
                    "contentChanges": [{"text": valid_text}],
                },
            }
        )

        self.assertEqual(server.documents[uri], valid_text)
        self.assertEqual(notifications[0]["params"]["diagnostics"], [])

    def test_stdio_loop_writes_content_length_framed_messages(self) -> None:
        messages = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            {"jsonrpc": "2.0", "id": 2, "method": "shutdown", "params": None},
            {"jsonrpc": "2.0", "method": "exit"},
        ]
        stdin = io.BytesIO(b"".join(_frame(message) for message in messages))
        stdout = io.BytesIO()
        server = LspServer(stdin=stdin, stdout=stdout)

        self.assertEqual(server.run(), 0)
        payloads = _read_framed_payloads(stdout.getvalue())

        self.assertEqual(payloads[0]["id"], 1)
        self.assertEqual(payloads[1], {"jsonrpc": "2.0", "id": 2, "result": None})


def _frame(message: dict[str, object]) -> bytes:
    payload = json.dumps(message).encode("utf-8")
    return f"Content-Length: {len(payload)}\r\n\r\n".encode("ascii") + payload


def _read_framed_payloads(data: bytes) -> list[dict[str, object]]:
    stream = io.BytesIO(data)
    payloads: list[dict[str, object]] = []
    while True:
        header = stream.readline()
        if header == b"":
            return payloads
        content_length = int(header.decode("ascii").partition(":")[2].strip())
        blank = stream.readline()
        if blank != b"\r\n":
            raise AssertionError(f"expected blank header line, got {blank!r}")
        payloads.append(json.loads(stream.read(content_length).decode("utf-8")))


if __name__ == "__main__":
    unittest.main()
