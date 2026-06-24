from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlsplit


_UNSET = object()


@dataclass(frozen=True)
class RequestMatcher:
    method: str
    path: str
    json_body: Any = _UNSET
    headers: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        method = self.method.upper()
        if not method:
            raise ValueError("request method is required")
        if not self.path.startswith("/"):
            raise ValueError("request path must start with '/'")
        object.__setattr__(self, "method", method)
        object.__setattr__(self, "headers", tuple((name.lower(), value) for name, value in self.headers))

    def matches(self, method: str, path: str, headers: tuple[tuple[str, str], ...], json_body: Any) -> bool:
        if method.upper() != self.method:
            return False
        if path != self.path:
            return False
        if self.json_body is not _UNSET and json_body != self.json_body:
            return False
        actual_headers = {name.lower(): value for name, value in headers}
        return all(actual_headers.get(name) == value for name, value in self.headers)


@dataclass(frozen=True)
class StubResponse:
    status: int = 200
    json_body: Any = None
    headers: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if self.status < 100 or self.status > 599:
            raise ValueError("response status must be an HTTP status code")
        object.__setattr__(self, "headers", tuple((name.lower(), value) for name, value in self.headers))


@dataclass(frozen=True)
class Stub:
    name: str
    matcher: RequestMatcher
    response: StubResponse
    expected_calls: int | None = 1

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("stub name is required")
        if self.expected_calls is not None and self.expected_calls < 0:
            raise ValueError("expected_calls must be non-negative or None")


@dataclass(frozen=True)
class RecordedRequest:
    method: str
    path: str
    headers: tuple[tuple[str, str], ...]
    body: bytes
    json_body: Any
    stub_name: str | None

    def __post_init__(self) -> None:
        object.__setattr__(self, "method", self.method.upper())
        object.__setattr__(self, "headers", tuple((name.lower(), value) for name, value in self.headers))


@dataclass(frozen=True)
class VerificationResult:
    errors: tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return not self.errors

    def raise_for_errors(self) -> None:
        if self.errors:
            raise AssertionError("\n".join(self.errors))


class MockServerHarness:
    def __init__(self, stubs: tuple[Stub, ...], host: str = "127.0.0.1", port: int = 0) -> None:
        self.stubs = stubs
        _validate_unique_stub_names(stubs)
        self.host = host
        self.port = port
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._requests: list[RecordedRequest] = []

    @property
    def url(self) -> str:
        if self._server is None:
            raise RuntimeError("mock server is not running")
        host, port = self._server.server_address
        return f"http://{host}:{port}"

    @property
    def requests(self) -> tuple[RecordedRequest, ...]:
        with self._lock:
            return tuple(self._requests)

    def start(self) -> MockServerHarness:
        if self._server is not None:
            return self
        handler = _handler_for(self)
        self._server = ThreadingHTTPServer((self.host, self.port), handler)
        self._thread = threading.Thread(target=self._server.serve_forever, name="tdd-dsl-runtime", daemon=True)
        self._thread.start()
        return self

    def stop(self) -> None:
        server = self._server
        thread = self._thread
        self._server = None
        self._thread = None
        if server is None:
            return
        server.shutdown()
        server.server_close()
        if thread is not None:
            thread.join(timeout=2)

    def reset(self) -> None:
        with self._lock:
            self._requests.clear()

    def verify(self) -> VerificationResult:
        with self._lock:
            requests = tuple(self._requests)
        errors: list[str] = []
        for stub in self.stubs:
            if stub.expected_calls is None:
                continue
            actual = sum(1 for request in requests if request.stub_name == stub.name)
            if actual != stub.expected_calls:
                errors.append(f"stub {stub.name!r} expected {stub.expected_calls} call(s), got {actual}")
        errors.extend(
            f"unexpected {request.method} request for {request.path}"
            for request in requests
            if request.stub_name is None
        )
        return VerificationResult(tuple(errors))

    def teardown(self, verify: bool = True) -> VerificationResult:
        result = self.verify() if verify else VerificationResult()
        try:
            if verify:
                result.raise_for_errors()
            return result
        finally:
            self.stop()

    def __enter__(self) -> MockServerHarness:
        return self.start()

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if exc_type is None:
            self.teardown(verify=True)
        else:
            self.stop()

    def _record_request(
        self,
        method: str,
        path: str,
        headers: tuple[tuple[str, str], ...],
        body: bytes,
    ) -> RecordedRequest:
        json_body = _parse_json_body(body)
        normalized_headers = tuple((name.lower(), value) for name, value in headers)
        stub = next(
            (stub for stub in self.stubs if stub.matcher.matches(method, path, normalized_headers, json_body)),
            None,
        )
        request = RecordedRequest(
            method=method.upper(),
            path=path,
            headers=normalized_headers,
            body=body,
            json_body=json_body,
            stub_name=stub.name if stub is not None else None,
        )
        with self._lock:
            self._requests.append(request)
        return request

    def _response_for(self, request: RecordedRequest) -> StubResponse:
        if request.stub_name is None:
            return StubResponse(status=404, json_body={"error": "no matching stub"})
        for stub in self.stubs:
            if stub.name == request.stub_name:
                return stub.response
        return StubResponse(status=404, json_body={"error": "no matching stub"})


def _handler_for(harness: MockServerHarness) -> type[BaseHTTPRequestHandler]:
    class _HarnessHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self._dispatch()

        def do_POST(self) -> None:
            self._dispatch()

        def do_PUT(self) -> None:
            self._dispatch()

        def do_PATCH(self) -> None:
            self._dispatch()

        def do_DELETE(self) -> None:
            self._dispatch()

        def log_message(self, format: str, *args: object) -> None:
            return

        def _dispatch(self) -> None:
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length) if length else b""
            path = urlsplit(self.path).path
            request = harness._record_request(self.command, path, tuple(self.headers.items()), body)
            response = harness._response_for(request)
            payload = _json_payload(response.json_body)

            self.send_response(response.status)
            for name, value in _response_headers(response, payload):
                self.send_header(name, value)
            self.end_headers()
            self.wfile.write(payload)

    return _HarnessHandler


def _parse_json_body(body: bytes) -> Any:
    if not body:
        return None
    try:
        return json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None


def _json_payload(value: Any) -> bytes:
    if value is None:
        return b""
    return json.dumps(value, sort_keys=True).encode("utf-8")


def _response_headers(response: StubResponse, payload: bytes) -> tuple[tuple[str, str], ...]:
    headers = {"content-type": "application/json"}
    for name, value in response.headers:
        headers[name.lower()] = value
    headers["content-length"] = str(len(payload))
    return tuple(headers.items())


def _validate_unique_stub_names(stubs: tuple[Stub, ...]) -> None:
    seen: set[str] = set()
    for stub in stubs:
        if stub.name in seen:
            raise ValueError(f"duplicate stub name {stub.name!r}")
        seen.add(stub.name)
