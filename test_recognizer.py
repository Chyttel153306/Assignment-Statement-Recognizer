"""Run with: python -m unittest -v"""

import json
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
import threading
import unittest

from app import Handler
from recognizer import MAX_STATEMENT_LENGTH, validate_statement


class RecognizerTests(unittest.TestCase):
    def test_valid_statements(self):
        for source in [
            "int sum = 1 + 1;", "int sum = 11 + 11 + 12 + 22;",
            "int x = 10;", "int total = a + b;", "int sum1 = 25 * 2;",
            "int Z9=0;", "int a = b;", "int a=1-2*3/4+5;",
            " \tint\tx9\n=\n001 + other2; \r\n", "int integer = 12345678901234567890;",
            "int a = 1 / 0;", "int a = a;",
        ]:
            with self.subTest(source=source):
                result = validate_statement(source)
                self.assertTrue(result["valid"], result)
                self.assertTrue(all(check["status"] == "pass" for check in result["checks"]))

    def test_invalid_statements(self):
        for source in [
            "sum = 1 + 1;", "x = 10;", "total = a + b;", "sum1 = 25 * 2;",
            "= 10;", "x = ;", "total = a +;", "2num = 10;", "x = 10",
            "int = 10;", "int 2num = 10;", "int num_2 = 10;", "int int = 10;",
            "INT x = 10;", "intx = 10;", "int sum 1 = 10;", "int x 10;",
            "int x == 10;", "int x = y = 10;", "int x = ;", "int x = +1;",
            "int x = -1;", "int x = 1 +;", "int x = 1 ** 2;", "int x = 1 // 2;",
            "int x = 1 2;", "int x = 2num;", "int x = (1 + 2);", "int x = 1.5;",
            "int x = 10", "int x = 1;;", "int x = 1; int y = 2;", "int x = 1;@",
            "int café = 1;", "int x = ١;", "int x = １;", "int x = 1 − 2;",
            "int x = int;", "int x = 1 % 2;", "int x = a_b;", "int x = 1; // comment",
            "int x\u00a0= 1;", "int x = <script>alert(1)</script>;", "", " \t\n",
            "a" * (MAX_STATEMENT_LENGTH + 1),
        ]:
            with self.subTest(source=source):
                result = validate_statement(source)
                self.assertFalse(result["valid"], result)
                self.assertEqual(sum(c["status"] == "fail" for c in result["checks"]), 1)

    def test_diagnostics_and_token_positions(self):
        result = validate_statement("int x = 1 +\n;")
        self.assertEqual((result["line"], result["column"]), (2, 1))
        self.assertEqual(result["message"], "Missing operand")
        source = "int total = a12 + 345;"
        result = validate_statement(source)
        self.assertEqual([t["kind"] for t in result["tokens"]],
                         ["datatype", "identifier", "assignment", "identifier", "operator", "integer", "semicolon"])
        for token in result["tokens"]:
            self.assertEqual(source[token["start"]:token["end"]], token["value"])

    def test_wrong_input_type(self):
        with self.assertRaises(TypeError):
            validate_statement(None)


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def request(self, method, path, body=None):
        connection = HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        try:
            connection.request(method, path, body, {"Content-Type": "application/json"})
            response = connection.getresponse()
            return response.status, response.read(), response.getheader("Content-Type")
        finally:
            connection.close()

    def test_static_assets(self):
        for path in ("/", "/style.css", "/app.js", "/favicon.svg"):
            with self.subTest(path=path):
                status, body, _ = self.request("GET", path)
                self.assertEqual(status, 200)
                self.assertTrue(body)
        self.assertEqual(self.request("HEAD", "/")[1], b"")
        self.assertEqual(self.request("GET", "/../app.py")[0], 404)

    def test_validation_endpoint(self):
        for source, valid in (("int sum = 1 + 1;", True), ("sum = 1 + 1;", False)):
            status, body, content_type = self.request("POST", "/api/validate", json.dumps({"statement": source}))
            self.assertEqual(status, 200)
            self.assertIn("application/json", content_type)
            self.assertEqual(json.loads(body)["valid"], valid)

    def test_bad_requests(self):
        for body in ("{", "[]", "null", '{"statement": 123}', "{}"):
            with self.subTest(body=body):
                self.assertEqual(self.request("POST", "/api/validate", body)[0], 400)
        self.assertEqual(self.request("POST", "/api/validate", json.dumps({"statement": "x" * 4097}))[0], 413)
        self.assertEqual(self.request("POST", "/api/validate", "x" * 32769)[0], 413)
        self.assertEqual(self.request("POST", "/missing", "{}")[0], 404)


if __name__ == "__main__":
    unittest.main()
