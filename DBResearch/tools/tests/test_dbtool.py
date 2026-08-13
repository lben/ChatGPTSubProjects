from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import dbtool  # noqa: E402


class DbToolTests(unittest.TestCase):
    def test_loopback_urls_are_allowed(self) -> None:
        self.assertEqual(dbtool.validate_loopback_url("http://127.0.0.1:8765"), "http://127.0.0.1:8765")
        self.assertEqual(dbtool.validate_loopback_url("http://localhost:9000/"), "http://localhost:9000")
        self.assertEqual(dbtool.validate_loopback_url("http://[::1]:8765"), "http://[::1]:8765")

    def test_remote_or_credential_urls_are_rejected(self) -> None:
        for value in (
            "https://127.0.0.1:8765",
            "http://example.com:8765",
            "http://" + "user:pass@127.0.0.1:8765",
            "http://127.0.0.1",
        ):
            with self.subTest(value=value), self.assertRaises(dbtool.ToolError):
                dbtool.validate_loopback_url(value)

    def test_forbidden_credential_key_is_found_recursively(self) -> None:
        value = {"request": {"auth": {"password": "not-allowed"}}}
        self.assertEqual(dbtool.find_forbidden_key(value), "$.request.auth.password")

    def test_normal_query_request_has_no_forbidden_key(self) -> None:
        value = {
            "request_id": "E001",
            "purpose": "aggregate match test",
            "operation": "query",
            "sql": "SELECT COUNT(*) AS tested FROM candidate",
            "limits": {"max_rows": 1},
        }
        self.assertIsNone(dbtool.find_forbidden_key(value))

    def test_command_contract_requires_request_and_output(self) -> None:
        with self.assertRaises(dbtool.ToolError):
            dbtool.validate_config(
                {
                    "transport": "command",
                    "argv": ["external-runner"],
                    "timeout_seconds": 60,
                    "max_result_bytes": 1000,
                }
            )

    def test_expand_command_is_argument_based(self) -> None:
        request = ROOT / ".agent" / "local" / "db-requests" / "E001.json"
        output = ROOT / ".agent" / "local" / "db-results" / "E001.json"
        argv = dbtool.expand_command(["runner", "--request", "{request}", "--output={output}"], request, output)
        self.assertEqual(argv[2], str(request))
        self.assertEqual(argv[3], f"--output={output}")


if __name__ == "__main__":
    unittest.main()
