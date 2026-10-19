import asyncio
import io
import logging
import os
import re
import time
import tomllib
from collections.abc import Iterator
from datetime import datetime, timedelta
from pathlib import Path
from uuid import UUID

import httpx
import pytest
from fastapi.testclient import TestClient
from rich.console import Console

import main
from main import app, build_book_store

BOOK_ID = UUID("3fa85f64-5717-4562-b3fc-2c963f66afa6")


@pytest.fixture(autouse=True)
def reset_app_state(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ENABLE_CHAOS_HEADERS", raising=False)
    monkeypatch.delenv("ENABLE_TRAFFIC_GENERATOR", raising=False)
    app.state.book_store = build_book_store()


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


def test_root_returns_metadata(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "name": "python-demo",
        "version": "0.3.0",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "openapi_url": "/openapi.json",
        "traffic_generator_enabled": False,
        "chaos_headers_enabled": False,
    }


def test_health_endpoint_returns_book_count(client: TestClient) -> None:
    response = client.get("/api/ps")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["books"] == 3


def test_list_books_returns_paginated_payload_and_request_id(client: TestClient) -> None:
    response = client.get("/api/v1/books?skip=0&limit=2")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert body["skip"] == 0
    assert body["limit"] == 2
    assert len(body["items"]) == 2
    assert response.headers["X-Request-ID"]


def test_get_book_by_id_returns_seeded_book(client: TestClient) -> None:
    response = client.get(f"/api/v1/books/{BOOK_ID}")

    assert response.status_code == 200
    assert response.json()["title"] == "Clean Code"


def test_search_books_matches_title_and_author(client: TestClient) -> None:
    response = client.get("/api/v1/books/search?q=martin")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert {item["title"] for item in body["items"]} == {
        "Clean Code",
        "Designing Data-Intensive Applications",
    }


def test_create_book_returns_201_and_persists(client: TestClient) -> None:
    response = client.post(
        "/api/v1/books",
        json={
            "title": "Refactoring",
            "author": "Martin Fowler",
            "year": 2018,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Refactoring"

    list_response = client.get("/api/v1/books")
    assert list_response.json()["total"] == 4


def test_patch_book_updates_only_supplied_fields(client: TestClient) -> None:
    response = client.patch(f"/api/v1/books/{BOOK_ID}", json={"year": 2022})

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Clean Code"
    assert body["year"] == 2022


def test_delete_book_removes_record(client: TestClient) -> None:
    response = client.delete(f"/api/v1/books/{BOOK_ID}")

    assert response.status_code == 200
    assert response.json()["message"].startswith("Book")

    get_response = client.get(f"/api/v1/books/{BOOK_ID}")
    assert get_response.status_code == 404


def test_invalid_payload_returns_422(client: TestClient) -> None:
    response = client.post(
        "/api/v1/books",
        json={
            "title": "",
            "author": "Valid Author",
            "year": 1800,
        },
    )

    assert response.status_code == 422


def test_invalid_uuid_returns_422(client: TestClient) -> None:
    response = client.get("/api/v1/books/not-a-uuid")

    assert response.status_code == 422


def test_force_error_header_is_ignored_when_chaos_is_disabled(client: TestClient) -> None:
    response = client.get("/api/v1/books", headers={"X-Force-Error": "503"})

    assert response.status_code == 200


def test_force_error_header_can_be_enabled_for_demo_testing(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ENABLE_CHAOS_HEADERS", "true")

    response = client.get("/api/v1/books", headers={"X-Force-Error": "503"})

    assert response.status_code == 503
    assert response.json()["detail"] == "Simulated error 503"


def test_head_status_returns_monitoring_header(client: TestClient) -> None:
    response = client.head("/api/status")

    assert response.status_code == 200
    assert response.headers["X-System-Status"] == "OK"


# ---------------- PATCH / DELETE edge cases ----------------
def test_patch_rejects_explicit_null_for_required_field(client: TestClient) -> None:
    response = client.patch(f"/api/v1/books/{BOOK_ID}", json={"title": None})

    assert response.status_code == 422
    assert client.get(f"/api/v1/books/{BOOK_ID}").json()["title"] == "Clean Code"


def test_patch_with_empty_payload_returns_book_unchanged(client: TestClient) -> None:
    response = client.patch(f"/api/v1/books/{BOOK_ID}", json={})

    assert response.status_code == 200
    assert response.json()["title"] == "Clean Code"


def test_patch_rejects_unknown_fields(client: TestClient) -> None:
    response = client.patch(f"/api/v1/books/{BOOK_ID}", json={"id": str(UUID(int=1))})

    assert response.status_code == 422


def test_create_rejects_unknown_fields(client: TestClient) -> None:
    response = client.post(
        "/api/v1/books",
        json={"title": "Refactoring", "author": "Martin Fowler", "year": 2018, "id": "x"},
    )

    assert response.status_code == 422


@pytest.mark.parametrize("method", ["get", "patch", "delete"])
def test_unknown_book_returns_404(client: TestClient, method: str) -> None:
    kwargs = {"json": {"year": 2000}} if method == "patch" else {}

    response = client.request(method, f"/api/v1/books/{UUID(int=0)}", **kwargs)

    assert response.status_code == 404
    assert response.json() == {"detail": "Book not found"}


# ---------------- Pagination and search ----------------
def test_pagination_skip_past_end_returns_empty_items(client: TestClient) -> None:
    body = client.get("/api/v1/books?skip=10").json()

    assert body["items"] == []
    assert body["total"] == 3


@pytest.mark.parametrize("query", ["limit=0", "limit=101", "skip=-1"])
def test_pagination_bounds_are_validated(client: TestClient, query: str) -> None:
    assert client.get(f"/api/v1/books?{query}").status_code == 422


def test_search_requires_query_and_handles_no_match(client: TestClient) -> None:
    assert client.get("/api/v1/books/search").status_code == 422
    assert client.get("/api/v1/books/search?q=zzz").json()["total"] == 0


# ---------------- Chaos headers ----------------
@pytest.mark.parametrize("value", ["abc", "418", "200"])
def test_invalid_force_error_values_return_400(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    monkeypatch.setenv("ENABLE_CHAOS_HEADERS", "true")

    response = client.get("/api/v1/books", headers={"X-Force-Error": value})

    assert response.status_code == 400


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", "/api/v1/books"),
        ("get", "/api/v1/books/search?q=code"),
        ("get", f"/api/v1/books/{BOOK_ID}"),
        ("delete", f"/api/v1/books/{BOOK_ID}"),
    ],
)
def test_every_books_route_honours_force_error(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, method: str, path: str
) -> None:
    monkeypatch.setenv("ENABLE_CHAOS_HEADERS", "true")

    response = client.request(method, path, headers={"X-Force-Error": "409"})

    assert response.status_code == 409


# ---------------- Supporting endpoints ----------------
def test_options_lists_allowed_methods(client: TestClient) -> None:
    response = client.options("/api/options")

    assert response.status_code == 200
    assert "PATCH" in response.headers["Allow"]


def test_redirect_points_at_a_seeded_book(client: TestClient) -> None:
    response = client.get("/api/redirect", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"].startswith("/api/v1/books/")


def test_redirect_returns_404_when_store_is_empty(client: TestClient) -> None:
    app.state.book_store = main.InMemoryBookStore()

    assert client.get("/api/redirect", follow_redirects=False).status_code == 404


def test_favicon_is_cached_204(client: TestClient) -> None:
    response = client.get("/favicon.ico")

    assert response.status_code == 204
    assert "max-age=31536000" in response.headers["Cache-Control"]


# ---------------- Middleware ----------------
def test_valid_incoming_request_id_is_echoed(client: TestClient) -> None:
    response = client.get("/api/ps", headers={"X-Request-ID": "trace-abc_123.4"})

    assert response.headers["X-Request-ID"] == "trace-abc_123.4"


@pytest.mark.parametrize("value", ["x" * 65, "bad id with spaces", "a;b", "<script>"])
def test_unsafe_incoming_request_id_is_replaced(client: TestClient, value: str) -> None:
    response = client.get("/api/ps", headers={"X-Request-ID": value})

    assert response.headers["X-Request-ID"] != value
    UUID(response.headers["X-Request-ID"])


def test_unhandled_exception_returns_500_with_request_id(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def boom(self: main.InMemoryBookStore) -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr(main.InMemoryBookStore, "list", boom)

    response = client.get("/api/v1/books")

    assert response.status_code == 500
    assert response.text == "Internal server error"
    assert response.headers["X-Request-ID"]


# ---------------- Helpers ----------------
@pytest.mark.parametrize(
    ("header", "expected"),
    [(None, "-"), ("", "-"), ("12", "12B"), ("2048", "2.0KB"), ("3145728", "3.0MB"), ("x", "x")],
)
def test_fmt_size_from_header(header: str | None, expected: str) -> None:
    assert main.fmt_size_from_header(header) == expected


@pytest.mark.parametrize(
    ("code", "style"),
    [
        (200, "black on green"),
        (302, "black on orange3"),
        (404, "black on yellow"),
        (500, "white on red"),
    ],
)
def test_status_style_by_class(code: int, style: str) -> None:
    assert main.status_style(code) == (style, str(code))


@pytest.mark.parametrize(
    ("raw", "expected"),
    [(None, False), ("true", True), (" YES ", True), ("0", False), ("no", False)],
)
def test_env_flag(monkeypatch: pytest.MonkeyPatch, raw: str | None, expected: bool) -> None:
    if raw is None:
        monkeypatch.delenv("FLAG", raising=False)
    else:
        monkeypatch.setenv("FLAG", raw)

    assert main.env_flag("FLAG") is expected


def test_app_version_matches_pyproject() -> None:
    pyproject = tomllib.loads((Path(main.__file__).parent / "pyproject.toml").read_text())

    assert pyproject["project"]["version"] == main.APP_VERSION


# ---------------- Traffic generator ----------------
def test_traffic_generator_requests_known_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.url.path)
        return httpx.Response(200)

    real_sleep = asyncio.sleep

    async def fast_sleep(_: float) -> None:
        await real_sleep(0)

    monkeypatch.setattr(main.asyncio, "sleep", fast_sleep)

    async def run() -> None:
        task = asyncio.create_task(main.generate_traffic(transport=httpx.MockTransport(handler)))
        while len(seen) < 5:
            await real_sleep(0)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(run())

    assert set(seen) <= {
        "/",
        "/api/ps",
        "/api/v1/books",
        "/api/v1/books/search",
        "/api/status",
        "/api/redirect",
    }


def test_traffic_generator_survives_request_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise httpx.ConnectError("down")

    real_sleep = asyncio.sleep

    async def fast_sleep(_: float) -> None:
        await real_sleep(0)

    monkeypatch.setattr(main.asyncio, "sleep", fast_sleep)

    async def run() -> None:
        task = asyncio.create_task(main.generate_traffic(transport=httpx.MockTransport(handler)))
        while calls < 3:
            await real_sleep(0)
        assert not task.done()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(run())


def test_lifespan_starts_and_stops_traffic_generator(monkeypatch: pytest.MonkeyPatch) -> None:
    started = stopped = False

    async def fake_generate(**_: object) -> None:
        nonlocal started, stopped
        started = True
        try:
            await asyncio.Event().wait()
        finally:
            stopped = True

    monkeypatch.setenv("ENABLE_TRAFFIC_GENERATOR", "true")
    monkeypatch.setattr(main, "generate_traffic", fake_generate)

    with TestClient(app):
        pass

    assert started
    assert stopped


# ---------------- Access log line ----------------
def access_line(**overrides: object) -> str:
    fields: dict[str, object] = {
        "timestamp": "2026/10/19 - 15:16:48",
        "status_code": 200,
        "latency_ms": 1.04,
        "size": "174B",
        "client": "127.0.0.1",
        "request_id": "f846f99d-8c96-4de0-a307-f40ce15796f3",
        "method": "GET",
        "path": "/",
    }
    return main.build_access_line(**(fields | overrides)).plain


def test_access_line_ends_with_unpadded_path() -> None:
    # A fixed-width path column left a wide hole before the request ID for short paths.
    assert access_line(path="/").endswith(" /")
    assert access_line(path="/api/v1/books?skip=0").endswith(" /api/v1/books?skip=0")


def test_access_line_has_no_wide_gap_before_the_path() -> None:
    assert "    " not in access_line(path="/").split("GET")[1]


def test_access_line_places_request_id_before_the_path() -> None:
    line = access_line()

    assert line.index("15:16:48") < line.index("INFO") < line.index("200")
    assert line.index("f846f99d") < line.index(" GET ") < line.rindex("/")


@pytest.mark.parametrize("method", ["GET", "OPTIONS"])
def test_access_line_includes_every_field(method: str) -> None:
    line = access_line(method=method, status_code=404, latency_ms=12.5)

    for expected in ("2026/10/19", "404", "12.50ms", "174B", "127.0.0.1", method):
        assert expected in line


def test_middleware_prints_the_access_line(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    buffer = io.StringIO()
    monkeypatch.setattr(main, "console", Console(file=buffer, width=200))

    client.get("/api/v1/books?limit=1", headers={"X-Request-ID": "abc-123"})

    printed = buffer.getvalue().strip()
    assert printed.endswith("/api/v1/books?limit=1")
    assert "abc-123" in printed


# ---------------- Access log levels ----------------
@pytest.mark.parametrize(
    ("status_code", "level"),
    [
        (200, logging.INFO),
        (307, logging.INFO),
        (404, logging.WARNING),
        (422, logging.WARNING),
        (500, logging.ERROR),
        (503, logging.ERROR),
    ],
)
def test_access_log_level_follows_status_class(status_code: int, level: int) -> None:
    assert main.access_log_level(status_code) == level


class RecordCollector(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


@pytest.fixture
def access_records() -> Iterator[list[logging.LogRecord]]:
    collector = RecordCollector()
    main.access_logger.addHandler(collector)
    yield collector.records
    main.access_logger.removeHandler(collector)


@pytest.mark.parametrize(
    ("path", "level"),
    [("/api/ps", logging.INFO), (f"/api/v1/books/{UUID(int=0)}", logging.WARNING)],
)
def test_middleware_logs_access_line_at_status_level(
    client: TestClient, access_records: list[logging.LogRecord], path: str, level: int
) -> None:
    client.get(path, headers={"X-Request-ID": "lvl-1"})

    (record,) = access_records
    assert record.levelno == level
    assert record.name == "python-demo.access"
    assert "lvl-1" in record.getMessage()
    assert record.getMessage().endswith(path)


def test_unhandled_exception_is_logged_at_error_level(
    client: TestClient,
    access_records: list[logging.LogRecord],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def boom(self: main.InMemoryBookStore) -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr(main.InMemoryBookStore, "list", boom)

    client.get("/api/v1/books")

    assert [record.levelno for record in access_records] == [logging.ERROR]


@pytest.mark.parametrize(
    ("path", "level"),
    [("/api/ps", "INFO"), (f"/api/v1/books/{UUID(int=0)}", "WARNING")],
)
def test_access_output_shows_one_level_column_after_the_time(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, path: str, level: str
) -> None:
    buffer = io.StringIO()
    monkeypatch.setattr(main, "console", Console(file=buffer, width=200))

    client.get(path)

    lines = buffer.getvalue().splitlines()
    assert len(lines) == 1  # printed once, not again by the root handler
    date, dash, clock, shown_level, status_code = lines[0].split()[:5]
    assert re.fullmatch(r"\d{4}/\d{2}/\d{2}", date)
    assert re.fullmatch(r"\d{2}:\d{2}:\d{2}", clock)
    assert shown_level == level
    assert status_code.isdigit()
    assert len({"INFO", "WARNING", "ERROR"} & set(lines[0].split())) == 1


@pytest.mark.parametrize(
    ("status_code", "level", "style"),
    [
        (200, "INFO", "logging.level.info"),
        (404, "WARNING", "logging.level.warning"),
        (503, "ERROR", "logging.level.error"),
    ],
)
def test_access_line_level_uses_the_rich_logging_theme(
    status_code: int, level: str, style: str
) -> None:
    line = main.build_access_line(
        timestamp="2026/10/19 - 15:16:48",
        status_code=status_code,
        latency_ms=1.0,
        size="1B",
        client="127.0.0.1",
        request_id="abc",
        method="GET",
        path="/",
    )

    assert level in line.plain
    assert [
        line.plain[span.start : span.end].strip() for span in line.spans if span.style == style
    ] == [level]


def test_access_logger_does_not_propagate_to_root() -> None:
    assert main.access_logger.propagate is False


# ---------------- Log consistency ----------------
def log_timestamp_in(tz: str) -> datetime:
    previous = os.environ.get("TZ")
    os.environ["TZ"] = tz
    time.tzset()
    try:
        return datetime.strptime(main.log_timestamp(), "%Y/%m/%d - %H:%M:%S")
    finally:
        if previous is None:
            del os.environ["TZ"]
        else:
            os.environ["TZ"] = previous
        time.tzset()


def test_log_timestamp_uses_local_time_like_the_rest_of_the_logs() -> None:
    # Rich's own log lines and uvicorn use local time, so the access line must too.
    utc = log_timestamp_in("UTC")
    kiritimati = log_timestamp_in("Pacific/Kiritimati")  # UTC+14, no DST

    assert abs((kiritimati - utc) - timedelta(hours=14)) < timedelta(seconds=5)


def test_app_log_lines_show_time_and_level_once(monkeypatch: pytest.MonkeyPatch) -> None:
    buffer = io.StringIO()
    monkeypatch.setattr(main.log_handler, "console", Console(file=buffer, width=200))
    record = main.logger.makeRecord(
        main.logger.name,
        logging.INFO,
        __file__,
        1,
        "Background traffic generator enabled",
        (),
        None,
    )

    main.log_handler.handle(record)

    output = buffer.getvalue()
    assert output.count("INFO") == 1
    assert len(re.findall(r"\d{2}:\d{2}:\d{2}", output)) == 1
