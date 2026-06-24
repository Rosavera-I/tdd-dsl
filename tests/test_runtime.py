from __future__ import annotations

import json
import socket
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from tdd_dsl.runtime import MockServerHarness, RequestMatcher, Stub, StubResponse, _json_payload, _response_headers


def _loopback_sockets_available() -> bool:
    try:
        probe = socket.socket()
        probe.bind(("127.0.0.1", 0))
        probe.close()
        return True
    except OSError:
        return False


SOCKETS_AVAILABLE = _loopback_sockets_available()


class MockServerHarnessTests(unittest.TestCase):
    @unittest.skipUnless(SOCKETS_AVAILABLE, "loopback sockets are unavailable in this sandbox")
    def test_start_respond_verify_and_teardown(self) -> None:
        harness = MockServerHarness(
            (
                Stub(
                    name="health",
                    matcher=RequestMatcher(method="GET", path="/health"),
                    response=StubResponse(json_body={"ok": True}),
                    expected_calls=1,
                ),
            )
        ).start()

        try:
            with urlopen(f"{harness.url}/health", timeout=2) as response:
                self.assertEqual(response.status, 200)
                self.assertEqual(response.headers["Content-Type"], "application/json")
                self.assertEqual(json.loads(response.read().decode("utf-8")), {"ok": True})

            self.assertTrue(harness.verify().ok)
        finally:
            teardown = harness.teardown()

        self.assertTrue(teardown.ok)
        with self.assertRaises(RuntimeError):
            _ = harness.url

    @unittest.skipUnless(SOCKETS_AVAILABLE, "loopback sockets are unavailable in this sandbox")
    def test_json_body_matching_records_expected_stub(self) -> None:
        harness = MockServerHarness(
            (
                Stub(
                    name="create_charge",
                    matcher=RequestMatcher(method="POST", path="/charges", json_body={"amount": 42}),
                    response=StubResponse(status=201, json_body={"id": "ch_123"}),
                    expected_calls=1,
                ),
            )
        )

        with harness:
            request = Request(
                f"{harness.url}/charges",
                data=json.dumps({"amount": 42}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(request, timeout=2) as response:
                self.assertEqual(response.status, 201)
                self.assertEqual(json.loads(response.read().decode("utf-8")), {"id": "ch_123"})

            self.assertEqual(harness.requests[0].stub_name, "create_charge")
            self.assertEqual(harness.requests[0].json_body, {"amount": 42})
            self.assertTrue(harness.verify().ok)

    @unittest.skipUnless(SOCKETS_AVAILABLE, "loopback sockets are unavailable in this sandbox")
    def test_unmatched_request_returns_404_and_is_recorded(self) -> None:
        harness = MockServerHarness(
            (
                Stub(
                    name="health",
                    matcher=RequestMatcher(method="GET", path="/health"),
                    response=StubResponse(json_body={"ok": True}),
                ),
            )
        )

        with self.assertRaises(AssertionError):
            with harness:
                with self.assertRaises(HTTPError) as raised:
                    urlopen(f"{harness.url}/missing", timeout=2)

                self.assertEqual(raised.exception.code, 404)
                payload = json.loads(raised.exception.read().decode("utf-8"))
                self.assertEqual(payload["error"], "no matching stub")
                self.assertEqual(harness.requests[0].stub_name, None)

    def test_record_request_matches_json_without_opening_socket(self) -> None:
        harness = MockServerHarness(
            (
                Stub(
                    name="create_charge",
                    matcher=RequestMatcher(method="POST", path="/charges", json_body={"amount": 42}),
                    response=StubResponse(status=201, json_body={"id": "ch_123"}),
                    expected_calls=1,
                ),
            )
        )

        request = harness._record_request(
            "POST",
            "/charges",
            (("Content-Type", "application/json"),),
            json.dumps({"amount": 42}).encode("utf-8"),
        )

        self.assertEqual(request.stub_name, "create_charge")
        self.assertEqual(request.json_body, {"amount": 42})
        self.assertTrue(harness.verify().ok)

    def test_request_header_matching_is_case_insensitive_for_names(self) -> None:
        harness = MockServerHarness(
            (
                Stub(
                    name="json charge",
                    matcher=RequestMatcher(
                        method="POST",
                        path="/charges",
                        json_body={"amount": 42},
                        headers=(("Content-Type", "application/json"),),
                    ),
                    response=StubResponse(status=201, json_body={"id": "ch_123"}),
                    expected_calls=1,
                ),
            )
        )

        request = harness._record_request(
            "POST",
            "/charges",
            (("content-type", "application/json"),),
            json.dumps({"amount": 42}).encode("utf-8"),
        )

        self.assertEqual(request.stub_name, "json charge")
        self.assertTrue(harness.verify().ok)

    def test_request_matcher_can_expect_json_null_body(self) -> None:
        harness = MockServerHarness(
            (
                Stub(
                    name="null body",
                    matcher=RequestMatcher(method="POST", path="/charges", json_body=None),
                    response=StubResponse(status=204),
                    expected_calls=1,
                ),
            )
        )

        request = harness._record_request("POST", "/charges", (), b"null")

        self.assertEqual(request.stub_name, "null body")
        self.assertTrue(harness.verify().ok)

    def test_request_matcher_normalizes_method(self) -> None:
        harness = MockServerHarness(
            (
                Stub(
                    name="health",
                    matcher=RequestMatcher(method="get", path="/health"),
                    response=StubResponse(json_body={"ok": True}),
                    expected_calls=1,
                ),
            )
        )

        request = harness._record_request("GET", "/health", (), b"")

        self.assertEqual(request.stub_name, "health")
        self.assertTrue(harness.verify().ok)

    def test_reset_clears_recorded_requests(self) -> None:
        harness = MockServerHarness(
            (
                Stub(
                    name="health",
                    matcher=RequestMatcher(method="GET", path="/health"),
                    response=StubResponse(json_body={"ok": True}),
                    expected_calls=1,
                ),
            )
        )
        harness._record_request("GET", "/health", (), b"")
        self.assertTrue(harness.verify().ok)

        harness.reset()

        self.assertEqual(harness.requests, ())
        result = harness.verify()
        self.assertFalse(result.ok)
        self.assertEqual(result.errors, ("stub 'health' expected 1 call(s), got 0",))

    def test_duplicate_stub_names_are_rejected(self) -> None:
        stub = Stub(
            name="health",
            matcher=RequestMatcher(method="GET", path="/health"),
            response=StubResponse(json_body={"ok": True}),
        )

        with self.assertRaisesRegex(ValueError, "duplicate stub name 'health'"):
            MockServerHarness((stub, stub))

    def test_negative_expected_calls_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "expected_calls must be non-negative or None"):
            Stub(
                name="health",
                matcher=RequestMatcher(method="GET", path="/health"),
                response=StubResponse(json_body={"ok": True}),
                expected_calls=-1,
            )

    def test_invalid_response_status_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "response status must be an HTTP status code"):
            StubResponse(status=99, json_body={"ok": False})

    def test_response_headers_are_case_insensitive_and_content_length_is_authoritative(self) -> None:
        response = StubResponse(
            json_body={"ok": True},
            headers=(
                ("Content-Type", "application/vnd.test+json"),
                ("Content-Length", "999"),
                ("X-Trace", "abc"),
            ),
        )
        payload = _json_payload(response.json_body)

        headers = _response_headers(response, payload)

        self.assertEqual(
            headers,
            (
                ("content-type", "application/vnd.test+json"),
                ("content-length", str(len(payload))),
                ("x-trace", "abc"),
            ),
        )

    def test_recorded_request_normalizes_method_and_header_names(self) -> None:
        harness = MockServerHarness(
            (
                Stub(
                    name="health",
                    matcher=RequestMatcher(method="GET", path="/health", headers=(("X-Trace", "abc"),)),
                    response=StubResponse(json_body={"ok": True}),
                ),
            )
        )

        request = harness._record_request("get", "/health", (("X-Trace", "abc"),), b"")

        self.assertEqual(request.method, "GET")
        self.assertEqual(request.headers, (("x-trace", "abc"),))
        self.assertEqual(request.stub_name, "health")

    def test_verify_reports_expected_call_mismatch(self) -> None:
        harness = MockServerHarness(
            (
                Stub(
                    name="health",
                    matcher=RequestMatcher(method="GET", path="/health"),
                    response=StubResponse(json_body={"ok": True}),
                    expected_calls=1,
                ),
            )
        )

        result = harness.verify()

        self.assertFalse(result.ok)
        self.assertEqual(result.errors, ("stub 'health' expected 1 call(s), got 0",))

    def test_verify_reports_unmatched_requests_without_opening_socket(self) -> None:
        harness = MockServerHarness(
            (
                Stub(
                    name="health",
                    matcher=RequestMatcher(method="GET", path="/health"),
                    response=StubResponse(json_body={"ok": True}),
                    expected_calls=None,
                ),
            )
        )

        request = harness._record_request("GET", "/missing", (), b"")
        result = harness.verify()

        self.assertIsNone(request.stub_name)
        self.assertFalse(result.ok)
        self.assertEqual(result.errors, ("unexpected GET request for /missing",))


if __name__ == "__main__":
    unittest.main()
