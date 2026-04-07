import asyncio
import logging
import os
import random
import time
import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

import httpx
from fastapi import FastAPI, HTTPException, Query, Request, Response, status
from fastapi.responses import PlainTextResponse, RedirectResponse
from pydantic import BaseModel, Field
from rich.console import Console
from rich.logging import RichHandler
from rich.text import Text

# ---------------- Configuration ----------------
APP_NAME = "python-demo"
APP_VERSION = "0.3.0"
WARN_MS = 100.0
SLOW_MS = 500.0
FAVICON_PATH = "/favicon.ico"
FAVICON_CACHE_SECONDS = 31_536_000
DEFAULT_SERVER_PORT = 8000
DEFAULT_PAGE_LIMIT = 20
MAX_PAGE_LIMIT = 100
ALLOWED_FORCED_ERROR_CODES = {400, 404, 409, 500, 503}

OPENAPI_TAGS = [
    {
        "name": "Books API",
        "description": "CRUD, pagination, search, and partial updates for the demo resource.",
    },
    {
        "name": "Monitoring",
        "description": "Health and status endpoints used for smoke tests and uptime checks.",
    },
    {
        "name": "HTTP Behaviors",
        "description": "Small endpoints that demonstrate redirects and method negotiation.",
    },
]


# ---------------- Logging setup ----------------
logging.basicConfig(
    level="INFO",
    format="%(asctime)s %(levelname)s %(name)s:%(lineno)d %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[RichHandler(markup=True)],
)
logger = logging.getLogger(APP_NAME)

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

console = Console()


# ---------------- Models ----------------
class BookBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    author: str = Field(min_length=1, max_length=100)
    year: int = Field(ge=1900, le=2100)


class BookCreate(BookBase):
    pass


class BookUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    author: str | None = Field(default=None, min_length=1, max_length=100)
    year: int | None = Field(default=None, ge=1900, le=2100)


class BookResponse(BookBase):
    id: UUID
    created_at: datetime


class BookListResponse(BaseModel):
    items: list[BookResponse]
    total: int
    skip: int
    limit: int


class HealthResponse(BaseModel):
    status: str
    books: int
    traffic_generator_enabled: bool
    chaos_headers_enabled: bool


class RootMetadata(BaseModel):
    name: str
    version: str
    docs_url: str
    redoc_url: str
    openapi_url: str
    traffic_generator_enabled: bool
    chaos_headers_enabled: bool


class DeleteResponse(BaseModel):
    message: str


class InMemoryBookStore:
    def __init__(self, books: dict[UUID, BookResponse] | None = None) -> None:
        self._books: dict[UUID, BookResponse] = dict(books or {})

    def list(self) -> list[BookResponse]:
        return list(self._books.values())

    def count(self) -> int:
        return len(self._books)

    def search(self, query: str) -> list[BookResponse]:
        normalized_query = query.casefold()
        return [
            book
            for book in self.list()
            if normalized_query in book.title.casefold()
            or normalized_query in book.author.casefold()
        ]

    def get(self, book_id: UUID) -> BookResponse | None:
        return self._books.get(book_id)

    def create(self, payload: BookCreate) -> BookResponse:
        book = BookResponse(id=uuid.uuid4(), created_at=utc_now(), **payload.model_dump())
        self._books[book.id] = book
        return book

    def update(self, book_id: UUID, payload: BookUpdate) -> BookResponse:
        book = self.get(book_id)
        if book is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
        updated = book.model_copy(update=payload.model_dump(exclude_unset=True))
        self._books[book_id] = updated
        return updated

    def delete(self, book_id: UUID) -> None:
        if book_id not in self._books:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
        del self._books[book_id]


# ---------------- Helpers ----------------
def env_flag(name: str, default: bool = False) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def server_port() -> int:
    return int(os.getenv("SERVER_PORT", str(DEFAULT_SERVER_PORT)))


def traffic_generator_enabled() -> bool:
    return env_flag("ENABLE_TRAFFIC_GENERATOR", default=False)


def chaos_headers_enabled() -> bool:
    return env_flag("ENABLE_CHAOS_HEADERS", default=False)


def status_style(status_code: int) -> tuple[str, str]:
    if status_code >= 500:
        return ("white on red", str(status_code))
    if status_code >= 400:
        return ("black on yellow", str(status_code))
    if status_code >= 300:
        return ("black on orange3", str(status_code))
    return ("black on green", str(status_code))


METHOD_STYLES = {
    "GET": "white on blue",
    "POST": "white on magenta",
    "PUT": "black on yellow",
    "DELETE": "white on red",
    "HEAD": "white on purple",
    "OPTIONS": "white on dark_green",
    "PATCH": "black on bright_yellow",
}


def method_style(method: str) -> str:
    return METHOD_STYLES.get(method.upper(), "white on #333333")


def fmt_size_from_header(header_value: str | None) -> str:
    if not header_value:
        return "-"
    try:
        size = int(header_value)
    except ValueError:
        return header_value
    if size < 1024:
        return f"{size}B"
    if size < 1024**2:
        return f"{size / 1024:.1f}KB"
    return f"{size / 1024**2:.1f}MB"


def utc_now() -> datetime:
    return datetime.now(UTC)


def seed_books() -> dict[UUID, BookResponse]:
    now = utc_now()
    seeded = [
        BookResponse(
            id=UUID("3fa85f64-5717-4562-b3fc-2c963f66afa6"),
            title="Clean Code",
            author="Robert C. Martin",
            year=2008,
            created_at=now,
        ),
        BookResponse(
            id=UUID("1a5d9e27-8b16-4d8d-96a0-84b9a91db314"),
            title="The Pragmatic Programmer",
            author="David Thomas, Andrew Hunt",
            year=2019,
            created_at=now,
        ),
        BookResponse(
            id=UUID("6f4048c8-cf4c-4f0f-92d1-84a74fe7cb0d"),
            title="Designing Data-Intensive Applications",
            author="Martin Kleppmann",
            year=2017,
            created_at=now,
        ),
    ]
    return {book.id: book for book in seeded}


def build_book_store() -> InMemoryBookStore:
    return InMemoryBookStore(seed_books())


def get_book_store(request: Request) -> InMemoryBookStore:
    return request.app.state.book_store


def paginate_books(items: list[BookResponse], skip: int, limit: int) -> BookListResponse:
    return BookListResponse(
        items=items[skip : skip + limit],
        total=len(items),
        skip=skip,
        limit=limit,
    )


def get_book_or_404(request: Request, book_id: UUID) -> BookResponse:
    book = get_book_store(request).get(book_id)
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return book


def maybe_force_error(request: Request) -> None:
    if not chaos_headers_enabled():
        return

    forced = request.headers.get("X-Force-Error")
    if forced is None:
        return

    try:
        status_code = int(forced)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Force-Error must be an integer status code",
        ) from exc

    if status_code not in ALLOWED_FORCED_ERROR_CODES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Force-Error is limited to approved demo codes",
        )

    raise HTTPException(status_code=status_code, detail=f"Simulated error {status_code}")


# ---------------- App & Lifespan ----------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    traffic_task: asyncio.Task[None] | None = None
    if traffic_generator_enabled():
        traffic_task = asyncio.create_task(generate_traffic())
        logger.info("Background traffic generator enabled")
    yield
    if traffic_task is not None:
        traffic_task.cancel()
        try:
            await traffic_task
        except asyncio.CancelledError:
            logger.info("Background traffic generator stopped")


app = FastAPI(
    title="Python Demo API",
    version=APP_VERSION,
    summary="A compact FastAPI reference app with rich logging and a Books API.",
    description=(
        "Companion demo app for the concepts discussed in the docs. "
        "The live API focuses on request validation, pagination, partial updates, "
        "rich logging, health checks, redirects, and safe demo controls. "
        "Authentication and cloud deployment patterns are explained in the documentation."
    ),
    lifespan=lifespan,
    openapi_tags=OPENAPI_TAGS,
)
app.state.book_store = build_book_store()


# ---------------- Traffic Generator ----------------
async def generate_traffic() -> None:
    await asyncio.sleep(1.0)

    base_url = f"http://127.0.0.1:{server_port()}"
    operations = [
        ("GET", "/"),
        ("GET", "/api/ps"),
        ("GET", "/api/v1/books"),
        ("GET", "/api/v1/books/search?q=code"),
        ("HEAD", "/api/status"),
        ("GET", "/api/redirect"),
    ]

    console.print(
        f"[bold cyan]Starting background traffic generator targeting {base_url}...[/bold cyan]"
    )

    async with httpx.AsyncClient(base_url=base_url, timeout=5.0) as client:
        while True:
            method, path = random.choice(operations)
            try:
                await client.request(method, path)
            except httpx.HTTPError:
                logger.warning("Traffic generator request failed", extra={"path": path})
            await asyncio.sleep(random.uniform(0.5, 1.5))


# ---------------- Middleware ----------------
@app.middleware("http")
async def colorful_access_log(request: Request, call_next):
    if request.url.path == FAVICON_PATH:
        return PlainTextResponse(
            status_code=status.HTTP_204_NO_CONTENT,
            headers={"Cache-Control": f"public, max-age={FAVICON_CACHE_SECONDS}"},
        )

    start = time.monotonic()
    timestamp = datetime.now().strftime("%Y/%m/%d - %H:%M:%S")
    client = request.client.host if request.client else "unknown"
    request_id = str(uuid.uuid4())

    try:
        response: Response = await call_next(request)
        status_code = response.status_code
    except Exception:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        response = PlainTextResponse(
            "Internal server error",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
        logger.exception("Unhandled exception while handling request")

    response.headers["X-Request-ID"] = request_id

    latency_ms = (time.monotonic() - start) * 1000.0
    latency_style = (
        "bold red" if latency_ms >= SLOW_MS else "yellow" if latency_ms >= WARN_MS else "green"
    )

    status_style_str, status_text = status_style(status_code)
    method = request.method
    path = request.url.path
    if request.url.query:
        path = f"{path}?{request.url.query}"

    resp_size = fmt_size_from_header(response.headers.get("content-length"))

    line = Text()
    line.append(f" {timestamp:<19}", style="dim")
    line.append(f" {status_text:<6}", style=status_style_str)
    line.append(f" {latency_ms:>8.2f}ms", style=latency_style)
    line.append(f" {resp_size:>7}", style="dim")
    line.append(f" {client:<15}", style="dim")
    line.append(f" {method:<7}", style=method_style(method))
    line.append(f" {path:<40}", style="bold")
    line.append(f" {request_id}", style="cyan")

    console.print(line)
    return response


# ---------------- Core Endpoints ----------------
@app.get("/", response_model=RootMetadata, tags=["Monitoring"])
async def root() -> RootMetadata:
    """Return high-level API metadata and local documentation links."""
    return RootMetadata(
        name=APP_NAME,
        version=APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        traffic_generator_enabled=traffic_generator_enabled(),
        chaos_headers_enabled=chaos_headers_enabled(),
    )


@app.get("/api/ps", response_model=HealthResponse, tags=["Monitoring"])
async def ps(request: Request) -> HealthResponse:
    """Return a lightweight health payload for local smoke testing."""
    return HealthResponse(
        status="ok",
        books=get_book_store(request).count(),
        traffic_generator_enabled=traffic_generator_enabled(),
        chaos_headers_enabled=chaos_headers_enabled(),
    )


@app.head("/api/status", tags=["Monitoring"])
async def status_head() -> Response:
    """Return a header-only status response for monitoring checks."""
    return Response(headers={"X-System-Status": "OK"}, status_code=status.HTTP_200_OK)


@app.options("/api/options", tags=["HTTP Behaviors"])
async def options_test() -> Response:
    """Return supported methods for quick HTTP tooling demos."""
    return Response(
        headers={"Allow": "OPTIONS, GET, POST, PATCH, DELETE, HEAD"},
        status_code=status.HTTP_200_OK,
    )


@app.get("/api/redirect", tags=["HTTP Behaviors"])
async def redirect_test(request: Request) -> RedirectResponse:
    """Redirect to a random seeded book to demonstrate 307 behavior."""
    books = get_book_store(request).list()
    if not books:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No books available")
    book = random.choice(books)
    return RedirectResponse(
        url=f"/api/v1/books/{book.id}",
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    )


# ---------------- Books API ----------------
@app.get("/api/v1/books", response_model=BookListResponse, tags=["Books API"])
async def list_books(
    request: Request,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE_LIMIT)] = DEFAULT_PAGE_LIMIT,
) -> BookListResponse:
    """List books with offset pagination."""
    maybe_force_error(request)
    books = get_book_store(request).list()
    return paginate_books(books, skip=skip, limit=limit)


@app.get("/api/v1/books/search", response_model=BookListResponse, tags=["Books API"])
async def search_books(
    request: Request,
    q: Annotated[str, Query(min_length=1, max_length=100)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE_LIMIT)] = DEFAULT_PAGE_LIMIT,
) -> BookListResponse:
    """Search books by title or author substring."""
    maybe_force_error(request)
    books = get_book_store(request).search(q)
    return paginate_books(books, skip=skip, limit=limit)


@app.post(
    "/api/v1/books",
    response_model=BookResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Books API"],
)
async def create_book(request: Request, payload: BookCreate) -> BookResponse:
    """Create a book and add it to the in-memory store."""
    maybe_force_error(request)
    return get_book_store(request).create(payload)


@app.get("/api/v1/books/{book_id}", response_model=BookResponse, tags=["Books API"])
async def get_book(request: Request, book_id: UUID) -> BookResponse:
    """Return a single book by UUID."""
    maybe_force_error(request)
    return get_book_or_404(request, book_id)


@app.patch("/api/v1/books/{book_id}", response_model=BookResponse, tags=["Books API"])
async def update_book(request: Request, book_id: UUID, payload: BookUpdate) -> BookResponse:
    """Apply a partial update to a book."""
    maybe_force_error(request)
    return get_book_store(request).update(book_id, payload)


@app.delete("/api/v1/books/{book_id}", response_model=DeleteResponse, tags=["Books API"])
async def delete_book(request: Request, book_id: UUID) -> DeleteResponse:
    """Delete a book from the in-memory store."""
    maybe_force_error(request)
    get_book_store(request).delete(book_id)
    return DeleteResponse(message=f"Book {book_id} deleted successfully")
