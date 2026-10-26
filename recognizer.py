"""Lexer and parser for: int identifier = operand (operator operand)* ;

This recognizes syntax only; identifiers need not be declared, and expressions
are never evaluated. Letters and digits are restricted to the ASCII alphabet.
"""

import re


MAX_STATEMENT_LENGTH = 4096
TOKEN = re.compile(r"[a-zA-Z][a-zA-Z0-9]*|[0-9]+|[=+*/;\-]")
LETTERS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
STEPS = [
    ("datatype", "Starts with the datatype int"),
    ("identifier", "Identifier starts with a letter"),
    ("assignment", "Exactly one assignment operator"),
    ("expression", "Operands and operators alternate"),
    ("semicolon", "Ends with a single semicolon"),
]


def validate_statement(source):
    """Return JSON-compatible diagnostics and tokens for one statement."""
    if not isinstance(source, str):
        raise TypeError("The statement must be text.")
    checks = [{"id": key, "label": label, "status": "pending"} for key, label in STEPS]
    tokens = []

    def status(key, state):
        next(check for check in checks if check["id"] == key)["status"] = state

    def fail(key, message, detail, index=None, length=1):
        status(key, "fail")
        index = len(source) if index is None else index
        return {
            "valid": False, "message": message, "detail": detail,
            "position": index, "length": length,
            "line": source.count("\n", 0, index) + 1,
            "column": index - source.rfind("\n", 0, index),
            "tokens": tokens, "checks": checks,
        }

    if len(source) > MAX_STATEMENT_LENGTH:
        return fail("datatype", "Statement too long", f"Use at most {MAX_STATEMENT_LENGTH} characters.", 0)
    if not source.strip():
        return fail("datatype", "Enter an assignment", "Start with int, then an identifier, =, an expression, and a semicolon.", 0)

    # Scan the entire source without discarding unknown characters.
    offset = 0
    bad_character = None
    while offset < len(source):
        if source[offset] in " \t\r\n":
            offset += 1
            continue
        match = TOKEN.match(source, offset)
        if not match:
            bad_character = offset
            break
        value = match.group()
        kind = ("datatype" if value == "int" else "identifier" if value[0] in LETTERS
                else "integer" if value[0] in "0123456789" else "assignment" if value == "="
                else "semicolon" if value == ";" else "operator")
        tokens.append({"value": value, "kind": kind, "start": offset, "end": match.end()})
        offset = match.end()

    cursor = 0

    def current():
        return tokens[cursor] if cursor < len(tokens) else None

    def position():
        token = current()
        return token["start"] if token else bad_character if bad_character is not None else len(source)

    if not tokens or tokens[0]["kind"] != "datatype":
        return fail("datatype", "Missing datatype", "Every statement must begin with int. Example: int sum = 1 + 1;", position())
    status("datatype", "pass")
    cursor += 1
    identifier = current()
    if not identifier or identifier["kind"] != "identifier":
        return fail("identifier", "Invalid identifier", "Use a name beginning with A–Z or a–z, followed only by letters and digits. The keyword int is reserved.", position())
    cursor += 1
    if current() and current()["kind"] in ("identifier", "integer", "datatype"):
        return fail("identifier", "Invalid identifier", "An identifier cannot contain spaces. Put = immediately after the identifier, with optional surrounding spaces.", position())
    status("identifier", "pass")
    if not current() or current()["value"] != "=":
        return fail("assignment", "Missing assignment operator", "Place one = after the identifier.", position())
    cursor += 1
    extra_equals = next((token for token in tokens[cursor:] if token["value"] == "="), None)
    if extra_equals:
        return fail("assignment", "Too many assignment operators", "Only one = is allowed in a statement.", extra_equals["start"])
    status("assignment", "pass")
    expecting_operand = True
    while current() and current()["value"] != ";":
        token = current()
        if expecting_operand:
            if token["kind"] not in ("integer", "identifier"):
                return fail("expression", "Missing or invalid operand", "Use an integer or identifier after = and after each arithmetic operator. Unary signs and parentheses are not part of this grammar.", position(), len(token["value"]))
        elif token["kind"] != "operator":
            return fail("expression", "Missing arithmetic operator", "Separate operands with +, -, *, or /. Identifiers cannot begin with digits.", position(), len(token["value"]))
        expecting_operand = not expecting_operand
        cursor += 1
    if bad_character is not None and cursor == len(tokens):
        return fail("expression", "Invalid character", f"The character {source[bad_character]!r} is not allowed. Use ASCII letters, digits, =, +, -, *, /, and ;.", bad_character)
    if expecting_operand:
        return fail("expression", "Missing operand", "The expression needs an integer or identifier after = and after every arithmetic operator.", position())
    status("expression", "pass")
    if not current():
        return fail("semicolon", "Missing semicolon", "End the statement with a semicolon (;).")
    cursor += 1
    if current() or bad_character is not None:
        return fail("semicolon", "Unexpected text after semicolon", "Enter one statement only, ending with a single semicolon.", position())
    status("semicolon", "pass")
    return {
        "valid": True, "message": "Valid assignment", "detail": "Your statement follows every rule of the assignment grammar.",
        "position": None, "length": 0, "line": None, "column": None,
        "tokens": tokens, "checks": checks,
    }
