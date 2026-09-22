#!/usr/bin/env python3
"""Deterministic evidence for the documented cubiczan_server.py surface.

Parses the server source with ``ast`` — no import (the module pulls in the
optional cubiczan-resilience dependency), no network — and asserts the
surface claimed by README.md and docs/: the route table, the CLI modes, the
standard-library HTTP stack, the API-key gate, the per-request backend/model
override, the documented inference defaults, and the OpenAI/Gemini dispatch.

Exit 0 when every check holds; exit 1 with the failing checks otherwise.
"""

import ast
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER_PATH = os.path.join(ROOT, "cubiczan_server.py")

EXPECTED_ROUTES = {
    # do_POST
    "/v1/chat/completions",
    "/v1/investor-relations/generate",
    "/v1/investor-relations/market-context",
    "/v1/critical-minerals/context",
    "/v1/veris/simulate",
    "/v1/veris/briefing",
    "/v1/veris/export",
    # do_GET
    "/health",
    "/v1/investor-relations/sample",
    "/v1/critical-minerals/sample",
    "/v1/veris/sample",
}


def _failures(checks):
    return [message for ok, message in checks if not ok]


def _is_self_path_comparison(node):
    """Match ``self.path == "<route>"`` comparisons."""
    if not isinstance(node, ast.Compare) or len(node.comparators) != 1:
        return False
    left = node.left
    if not (isinstance(left, ast.Attribute) and left.attr == "path"):
        return False
    return isinstance(node.comparators[0], ast.Constant)


def main():
    with open(SERVER_PATH, encoding="utf-8") as handle:
        tree = ast.parse(handle.read(), filename=SERVER_PATH)

    checks = []

    # S1 — every documented route is registered in the request handler.
    found_routes = {
        node.comparators[0].value
        for node in ast.walk(tree)
        if _is_self_path_comparison(node) and isinstance(node.comparators[0].value, str)
    }
    checks.append(
        (
            found_routes == EXPECTED_ROUTES,
            "S1 routes: expected exactly the 11 documented routes, "
            f"missing={sorted(EXPECTED_ROUTES - found_routes)}, "
            f"undocumented={sorted(found_routes - EXPECTED_ROUTES)}",
        )
    )

    # S2 — CLI modes: --test, --interactive, --port.
    cli_flags = {
        node.args[0].value
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "add_argument"
        and node.args
        and isinstance(node.args[0], ast.Constant)
        and isinstance(node.args[0].value, str)
        and node.args[0].value.startswith("--")
    }
    checks.append(
        (
            {"--test", "--interactive", "--port"}.issubset(cli_flags),
            f"S2 CLI flags: expected --test/--interactive/--port, found {sorted(cli_flags)}",
        )
    )

    # S3 — the server runs on the Python standard library (http.server).
    http_imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module == "http.server"
        for alias in node.names
    }
    checks.append(
        (
            {"HTTPServer", "BaseHTTPRequestHandler"}.issubset(http_imports),
            f"S3 stdlib server: expected HTTPServer + BaseHTTPRequestHandler "
            f"from http.server, found {sorted(http_imports)}",
        )
    )

    # S4 — CUBICZAN_SERVER_API_KEY gate runs before every request handler.
    auth_fn = next(
        (n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_is_authorized"),
        None,
    )
    auth_ok = False
    if auth_fn is not None:
        auth_constants = {
            c.value for c in ast.walk(auth_fn) if isinstance(c, ast.Constant)
        }
        auth_ok = "CUBICZAN_SERVER_API_KEY" in auth_constants and 401 in auth_constants
    handlers = [
        n for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef) and n.name in ("do_GET", "do_POST")
    ]
    gate_called = all(
        any(
            isinstance(c, ast.Call)
            and isinstance(c.func, ast.Attribute)
            and c.func.attr == "_is_authorized"
            for c in ast.walk(handler)
        )
        for handler in handlers
    )
    checks.append(
        (
            auth_fn is not None and auth_ok and gate_called and len(handlers) == 2,
            "S4 API-key gate: _is_authorized must check CUBICZAN_SERVER_API_KEY, "
            "send a 401, and be invoked by both do_GET and do_POST",
        )
    )

    # S5 — /v1/chat/completions honors per-request backend and model overrides.
    override_call = any(
        isinstance(node, ast.Call)
        and (
            (isinstance(node.func, ast.Name) and node.func.id == "get_model_response")
            or (isinstance(node.func, ast.Attribute) and node.func.attr == "get_model_response")
        )
        and {kw.arg for kw in node.keywords if kw.arg} >= {"backend", "model_name"}
        for node in ast.walk(tree)
    )
    do_post = next(
        (n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "do_POST"),
        None,
    )
    request_fields = set()
    if do_post is not None:
        for node in ast.walk(do_post):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "get"
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
                and node.args[0].value in ("backend", "model")
            ):
                request_fields.add(node.args[0].value)
    checks.append(
        (
            override_call and {"backend", "model"}.issubset(request_fields),
            "S5 backend override: the chat branch must read the request's "
            "backend and model fields and pass them to get_model_response",
        )
    )

    # S6 — documented defaults: openai backend, gpt-5.2 model.
    defaults = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            constants = [
                c.value
                for c in ast.walk(node.value)
                if isinstance(c, ast.Constant) and isinstance(c.value, str)
            ]
            if constants:
                defaults[node.targets[0].id] = constants
    checks.append(
        (
            "openai" in defaults.get("INFERENCE_BACKEND", [])
            and "gpt-5.2" in defaults.get("OPENAI_MODEL", []),
            "S6 defaults: INFERENCE_BACKEND must default to 'openai' and "
            f"OPENAI_MODEL to 'gpt-5.2', found {defaults}",
        )
    )

    # S7 — inference dispatch covers the OpenAI and Gemini backends.
    dispatch_fn = next(
        (n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "get_model_response"),
        None,
    )
    dispatch_backends = (
        {c.value for c in ast.walk(dispatch_fn) if isinstance(c, ast.Constant) and isinstance(c.value, str)}
        if dispatch_fn
        else set()
    )
    checks.append(
        (
            {"openai", "gemini"}.issubset(dispatch_backends),
            "S7 dispatch: get_model_response must handle the openai and gemini "
            f"backends, found {sorted(dispatch_backends)}",
        )
    )

    failures = _failures(checks)
    for ok, message in checks:
        print(f"{'OK  ' if ok else 'FAIL'} {message if not ok else message.split(': ', 1)[0] + ': ok'}")
    if failures:
        print(f"SERVER SURFACE: FAILED ({len(failures)} of {len(checks)} checks)")
        return 1
    print(f"SERVER SURFACE: OK ({len(checks)}/{len(checks)} checks)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
