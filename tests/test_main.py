import sys
from pathlib import Path
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from main import app, build_book_store

BOOK_ID = UUID("3fa85f64-5717-4562-b3fc-2c963f66afa6")


@pytest.fixture(autouse=True)
def reset_app_state(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ENABLE_CHAOS_HEADERS", raising=False)
    monkeypatch.delenv("ENABLE_TRAFFIC_GENERATOR", raising=False)
    app.state.book_store = build_book_store()


@pytest.fixture
def client() -> TestClient:
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
