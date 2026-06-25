from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from typing import Any, BinaryIO, TextIO

from .ast import Diagnostic
from .parser import parse_text


JsonObject = dict[str, Any]


@dataclass
class LspServer:
    stdin: BinaryIO = field(default_factory=lambda: sys.stdin.buffer)
    stdout: BinaryIO = field(default_factory=lambda: sys.stdout.buffer)
    stderr: TextIO = field(default_factory=lambda: sys.stderr)
    documents: dict[str, str] = field(default_factory=dict)
    shutdown_requested: bool = False

    def run(self) -> int:
        while True:
            message = self._read_message()
            if message is None:
                return 0

            response, notifications, should_exit = self.handle_message(message)
            if response is not None:
                self._write_message(response)
            for notification in notifications:
                self._write_message(notification)
            if should_exit:
                return 0

    def handle_message(self, message: JsonObject) -> tuple[JsonObject | None, list[JsonObject], bool]:
        method = message.get("method")
        message_id = message.get("id")

        if method == "initialize":
            return self._response(message_id, _initialize_result()), [], False
        if method == "shutdown":
            self.shutdown_requested = True
            return self._response(message_id, None), [], False
        if method == "exit":
            return None, [], True
        if method == "textDocument/didOpen":
            notification = self._did_open(message)
            return None, [notification] if notification else [], False
        if method == "textDocument/didChange":
            notification = self._did_change(message)
            return None, [notification] if notification else [], False

        if message_id is None:
            return None, [], False
        return self._error_response(message_id, -32601, f"Method not found: {method}"), [], False

    def _did_open(self, message: JsonObject) -> JsonObject | None:
        text_document = message.get("params", {}).get("textDocument", {})
        uri = text_document.get("uri")
        text = text_document.get("text")
        if not isinstance(uri, str) or not isinstance(text, str):
            return None

        self.documents[uri] = text
        return self._publish_diagnostics(uri, text)

    def _did_change(self, message: JsonObject) -> JsonObject | None:
        params = message.get("params", {})
        uri = params.get("textDocument", {}).get("uri")
        changes = params.get("contentChanges", [])
        if not isinstance(uri, str) or not isinstance(changes, list) or not changes:
            return None

        latest = changes[-1]
        text = latest.get("text") if isinstance(latest, dict) else None
        if not isinstance(text, str):
            return None

        self.documents[uri] = text
        return self._publish_diagnostics(uri, text)

    def _publish_diagnostics(self, uri: str, text: str) -> JsonObject:
        result = parse_text(text)
        return {
            "jsonrpc": "2.0",
            "method": "textDocument/publishDiagnostics",
            "params": {
                "uri": uri,
                "diagnostics": [_to_lsp_diagnostic(diagnostic) for diagnostic in result.diagnostics],
            },
        }

    def _read_message(self) -> JsonObject | None:
        headers: dict[str, str] = {}
        while True:
            line = self.stdin.readline()
            if line == b"":
                return None
            if line in {b"\r\n", b"\n"}:
                break
            name, _, value = line.decode("ascii").partition(":")
            headers[name.lower()] = value.strip()

        length = int(headers.get("content-length", "0"))
        if length <= 0:
            return None
        payload = self.stdin.read(length)
        return json.loads(payload.decode("utf-8"))

    def _write_message(self, message: JsonObject) -> None:
        payload = json.dumps(message, separators=(",", ":")).encode("utf-8")
        header = f"Content-Length: {len(payload)}\r\n\r\n".encode("ascii")
        self.stdout.write(header + payload)
        self.stdout.flush()

    def _response(self, message_id: Any, result: Any) -> JsonObject:
        return {"jsonrpc": "2.0", "id": message_id, "result": result}

    def _error_response(self, message_id: Any, code: int, message: str) -> JsonObject:
        return {"jsonrpc": "2.0", "id": message_id, "error": {"code": code, "message": message}}


def main() -> int:
    return LspServer().run()


def _initialize_result() -> JsonObject:
    return {
        "capabilities": {
            "textDocumentSync": {
                "openClose": True,
                "change": 1,
            }
        },
        "serverInfo": {
            "name": "tdd-dsl-lsp",
            "version": "0.1.0",
        },
    }


def _to_lsp_diagnostic(diagnostic: Diagnostic) -> JsonObject:
    start_line = max(diagnostic.line - 1, 0)
    start_character = max(diagnostic.column - 1, 0)
    return {
        "range": {
            "start": {"line": start_line, "character": start_character},
            "end": {"line": start_line, "character": start_character + 1},
        },
        "severity": 1,
        "source": "tdd-dsl",
        "message": diagnostic.message,
    }
