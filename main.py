"""Demo FastAPI app: an in-memory Books API with Rich access logging and health endpoints."""

import asyncio
import logging
import os
import random
import re
import time
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Annotated, Literal, Self
from uuid import UUID

import httpx2
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Request, Response, status
from fastapi.responses import PlainTextResponse, RedirectResponse
from pydantic import BaseModel, ConfigDict, Field, model_validator
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
REQUEST_ID_HEADER = "X-Request-ID"
# Only echo client-supplied IDs that are short and log-safe; anything else is replaced.
SAFE_REQUEST_ID = re.compile(r"[A-Za-z0-9._-]{1,64}", re.ASCII)
REQUEST_ID_WIDTH = 36  # length of a UUID, so generated IDs line up in the log
LEVEL_WIDTH = 8  # fits "CRITICAL" so the level column lines up like RichHandler's

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
# RichHandler already renders the time, level, and source columns, so the formatter
# must emit only the message or each of them is printed twice.
log_handler = RichHandler(markup=True)
log_handler.setFormatter(logging.Formatter("%(message)s"))
logging.basicConfig(level="INFO", handlers=[log_handler])
logger = logging.getLogger(APP_NAME)

logging.getLogger("httpx2").setLevel(logging.WARNING)
logging.getLogger("httpcore2").setLevel(logging.WARNING)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

console = Console()


class AccessLogHandler(logging.Handler):
    """Print the pre-styled Rich line carried by each access record, unchanged."""

    def emit(self, record: logging.LogRecord) -> None:
        """Print the record's Rich Text; the level is also on the record for filtering."""
        console.print(record.msg)


# Own logger so the colorful line is not wrapped in RichHandler's own columns; the line
# draws its level itself.
access_logger = logging.getLogger(f"{APP_NAME}.access")
access_logger.setLevel(logging.INFO)
access_logger.propagate = False
access_logger.addHandler(AccessLogHandler())


# ---------------- Models ----------------
class BookBase(BaseModel):
    """Fields shared by every book payload."""

    title: str = Field(min_length=1, max_length=200)
    author: str = Field(min_length=1, max_length=100)
    year: int = Field(ge=1900, le=2100)


class BookCreate(BookBase):
    """Request body for creating a book; unknown fields are rejected."""

    model_config = ConfigDict(extra="forbid")


class BookUpdate(BaseModel):
    """Request body for a partial update; omitted fields are left unchanged."""

    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=1, max_length=200)
    author: str | None = Field(default=None, min_length=1, max_length=100)
    year: int | None = Field(default=None, ge=1900, le=2100)

    @model_validator(mode="after")
    def reject_explicit_nulls(self) -> Self:
        """Omitted fields are untouched, but sending null would erase a required field."""
        nulls = sorted(name for name in self.model_fields_set if getattr(self, name) is None)
        if nulls:
            raise ValueError(f"fields cannot be null: {', '.join(nulls)}")
        return self


class PageParams(BaseModel):
    """Offset-pagination query parameters."""

    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=DEFAULT_PAGE_LIMIT, ge=1, le=MAX_PAGE_LIMIT)


class SearchParams(PageParams):
    """Pagination plus the search term."""

    q: str = Field(min_length=1, max_length=100)


class BookResponse(BookBase):
    """A stored book as returned by the API."""

    id: UUID
    created_at: datetime


class BookListResponse(BaseModel):
    """One page of books plus the paging metadata."""

    items: list[BookResponse]
    total: int
    skip: int
    limit: int


class HealthResponse(BaseModel):
    """Payload for the lightweight health endpoint."""

    status: Literal["ok"]
    books: int
    traffic_generator_enabled: bool
    chaos_headers_enabled: bool


class RootMetadata(BaseModel):
    """Payload describing the API and its documentation links."""

    name: str
    version: str
    docs_url: str
    redoc_url: str
    openapi_url: str
    traffic_generator_enabled: bool
    chaos_headers_enabled: bool


class DeleteResponse(BaseModel):
    """Confirmation message returned after a delete."""

    message: str


class InMemoryBookStore:
    """Process-local book storage; not shared across workers or restarts."""

    def __init__(self, books: dict[UUID, BookResponse] | None = None) -> None:
        """Start from an optional copy of existing books."""
        self._books: dict[UUID, BookResponse] = dict(books or {})

    def list(self) -> list[BookResponse]:
        """Return every book in insertion order."""
        return list(self._books.values())

    def count(self) -> int:
        """Return how many books are stored."""
        return len(self._books)

    def search(self, query: str) -> list[BookResponse]:
        """Return books whose title or author contains the query, ignoring case."""
        normalized_query = query.casefold()
        return [
            book
            for book in self.list()
            if normalized_query in book.title.casefold()
            or normalized_query in book.author.casefold()
        ]

    def get(self, book_id: UUID) -> BookResponse | None:
        """Return the book with this ID, or None if it does not exist."""
        return self._books.get(book_id)

    def create(self, payload: BookCreate) -> BookResponse:
        """Store a new book with a generated ID and creation time."""
        book = BookResponse(id=uuid.uuid4(), created_at=utc_now(), **payload.model_dump())
        self._books[book.id] = book
        return book

    def update(self, book: BookResponse, payload: BookUpdate) -> BookResponse:
        # model_validate (not model_copy) so the merged result is re-checked against the schema.
        """Apply the supplied fields to a book and return the validated result."""
        merged = {**book.model_dump(), **payload.model_dump(exclude_unset=True)}
        updated = BookResponse.model_validate(merged)
        self._books[book.id] = updated
        return updated

    def delete(self, book_id: UUID) -> None:
        """Remove a book; deleting a missing book is a no-op."""
        self._books.pop(book_id, None)


# ---------------- Helpers ----------------
def env_flag(name: str, default: bool = False) -> bool:
    """Read a boolean environment variable (1, true, yes, or on)."""
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def server_port() -> int:
    """Return the port the traffic generator should call."""
    return int(os.getenv("SERVER_PORT", str(DEFAULT_SERVER_PORT)))


def traffic_generator_enabled() -> bool:
    """Return whether the background traffic generator is switched on."""
    return env_flag("ENABLE_TRAFFIC_GENERATOR", default=False)


def chaos_headers_enabled() -> bool:
    """Return whether X-Force-Error simulation is switched on."""
    return env_flag("ENABLE_CHAOS_HEADERS", default=False)


def status_style(status_code: int) -> tuple[str, str]:
    """Return the Rich style and display text for an HTTP status code."""
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
    """Return the Rich style for an HTTP method badge."""
    return METHOD_STYLES.get(method.upper(), "white on #333333")


def fmt_size_from_header(header_value: str | None) -> str:
    """Format a Content-Length header value as a short human-readable size."""
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
    """Return the current time as a timezone-aware UTC datetime."""
    return datetime.now(UTC)


def log_timestamp() -> str:
    """Return the current local time for access lines, matching Rich and uvicorn logs."""
    return datetime.now().strftime("%Y/%m/%d - %H:%M:%S")


def latency_style(latency_ms: float) -> str:
    """Return the Rich style for a latency, using the WARN_MS and SLOW_MS thresholds."""
    if latency_ms >= SLOW_MS:
        return "bold red"
    if latency_ms >= WARN_MS:
        return "yellow"
    return "green"


def access_log_level(status_code: int) -> int:
    """Return the log level for a response: INFO below 400, WARNING for 4xx, ERROR for 5xx."""
    if status_code >= 500:
        return logging.ERROR
    if status_code >= 400:
        return logging.WARNING
    return logging.INFO


def build_access_line(
    *,
    timestamp: str,
    status_code: int,
    latency_ms: float,
    size: str,
    client: str,
    request_id: str,
    method: str,
    path: str,
) -> Text:
    """Build one colorized access-log line.

    Fixed-width fields come first (time, level, status, ...) and the variable-length
    path comes last, so it is never padded and short paths leave no gap in the line.
    """
    badge_style, status_text = status_style(status_code)
    level_name = logging.getLevelName(access_log_level(status_code))
    line = Text()
    line.append(f" {timestamp}", style="dim")
    # Same theme styles RichHandler uses, so access and app lines share level colors.
    line.append(f" {level_name:<{LEVEL_WIDTH}}", style=f"logging.level.{level_name.lower()}")
    line.append(f" {status_text:^5}", style=badge_style)
    line.append(f" {latency_ms:>8.2f}ms", style=latency_style(latency_ms))
    line.append(f" {size:>7}", style="dim")
    line.append(f" {client:<15}", style="dim")
    line.append(f" {request_id:<{REQUEST_ID_WIDTH}}", style="cyan")
    line.append(f" {method:^7}", style=method_style(method))
    line.append(f" {path}", style="bold")
    return line


def seed_books() -> dict[UUID, BookResponse]:
    """Return the books every fresh store starts with."""
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
    """Create a store pre-loaded with the seed books."""
    return InMemoryBookStore(seed_books())


def get_book_store(request: Request) -> InMemoryBookStore:
    """Dependency that returns the app-wide book store."""
    return request.app.state.book_store


BookStoreDep = Annotated[InMemoryBookStore, Depends(get_book_store)]
Pagination = Annotated[PageParams, Query()]
Search = Annotated[SearchParams, Query()]


def paginate_books(items: list[BookResponse], page: PageParams) -> BookListResponse:
    """Slice a list of books into one page with its paging metadata."""
    return BookListResponse(
        items=items[page.skip : page.skip + page.limit],
        total=len(items),
        skip=page.skip,
        limit=page.limit,
    )


def get_book_or_404(book_id: UUID, store: BookStoreDep) -> BookResponse:
    """Dependency that returns the requested book or raises 404."""
    book = store.get(book_id)
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return book


ExistingBook = Annotated[BookResponse, Depends(get_book_or_404)]


def request_id_for(request: Request) -> str:
    """Reuse a safe client-supplied request ID, otherwise generate one."""
    supplied = request.headers.get(REQUEST_ID_HEADER, "")
    return supplied if SAFE_REQUEST_ID.fullmatch(supplied) else str(uuid.uuid4())


def maybe_force_error(request: Request) -> None:
    """Raise the HTTP error named by X-Force-Error when chaos headers are enabled."""
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
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Run the optional traffic generator for the lifetime of the app."""
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
async def generate_traffic(transport: httpx2.AsyncBaseTransport | None = None) -> None:
    """Send random demo requests to the local server until cancelled."""
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

    async with httpx2.AsyncClient(base_url=base_url, timeout=5.0, transport=transport) as client:
        while True:
            method, path = random.choice(operations)
            try:
                await client.request(method, path)
            except httpx2.HTTPError:
                logger.warning("Traffic generator request failed: %s %s", method, path)
            await asyncio.sleep(random.uniform(0.5, 1.5))


# ---------------- Middleware ----------------
@app.middleware("http")
async def colorful_access_log(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Assign a request ID, time the request, and print a colorized access line."""
    if request.url.path == FAVICON_PATH:
        return PlainTextResponse(
            status_code=status.HTTP_204_NO_CONTENT,
            headers={"Cache-Control": f"public, max-age={FAVICON_CACHE_SECONDS}"},
        )

    start = time.monotonic()
    timestamp = log_timestamp()
    client = request.client.host if request.client else "unknown"
    request_id = request_id_for(request)
    request.state.request_id = request_id

    try:
        response: Response = await call_next(request)
        status_code = response.status_code
    except Exception:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        response = PlainTextResponse(
            "Internal server error",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
        logger.exception("Unhandled exception while handling request %s", request_id)

    response.headers[REQUEST_ID_HEADER] = request_id

    latency_ms = (time.monotonic() - start) * 1000.0
    path = request.url.path
    if request.url.query:
        path = f"{path}?{request.url.query}"

    access_logger.log(
        access_log_level(status_code),
        build_access_line(
            timestamp=timestamp,
            status_code=status_code,
            latency_ms=latency_ms,
            size=fmt_size_from_header(response.headers.get("content-length")),
            client=client,
            request_id=request_id,
            method=request.method,
            path=path,
        ),
    )
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
async def ps(store: BookStoreDep) -> HealthResponse:
    """Return a lightweight health payload for local smoke testing."""
    return HealthResponse(
        status="ok",
        books=store.count(),
        traffic_generator_enabled=traffic_generator_enabled(),
        chaos_headers_enabled=chaos_headers_enabled(),
    )


@app.head("/api/status", tags=["Monitoring"])
async def status_head() -> Response:
    """Return a header-only status response for monitoring checks."""
    return Response(headers={"X-System-Status": "OK"}, status_code=status.HTTP_200_OK)


@app.options("/api/options", tags=["HTTP Behaviors"])
async def options_test() -> Response:
    """Return the methods used across this API in the Allow header (OPTIONS demo)."""
    return Response(
        headers={"Allow": "OPTIONS, GET, POST, PATCH, DELETE, HEAD"},
        status_code=status.HTTP_200_OK,
    )


@app.get("/api/redirect", tags=["HTTP Behaviors"])
async def redirect_test(store: BookStoreDep) -> RedirectResponse:
    """Redirect to a random seeded book to demonstrate 307 behavior."""
    books = store.list()
    if not books:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No books available")
    book = random.choice(books)
    return RedirectResponse(
        url=f"/api/v1/books/{book.id}",
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    )


# ---------------- Books API ----------------
books_router = APIRouter(
    prefix="/api/v1/books",
    tags=["Books API"],
    dependencies=[Depends(maybe_force_error)],
)


@books_router.get("", response_model=BookListResponse)
async def list_books(store: BookStoreDep, page: Pagination) -> BookListResponse:
    """List books with offset pagination."""
    return paginate_books(store.list(), page)


@books_router.get("/search", response_model=BookListResponse)
async def search_books(store: BookStoreDep, params: Search) -> BookListResponse:
    """Search books by title or author substring."""
    return paginate_books(store.search(params.q), params)


@books_router.post("", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def create_book(store: BookStoreDep, payload: BookCreate) -> BookResponse:
    """Create a book and add it to the in-memory store."""
    return store.create(payload)


@books_router.get("/{book_id}", response_model=BookResponse)
async def get_book(book: ExistingBook) -> BookResponse:
    """Return a single book by UUID."""
    return book


@books_router.patch("/{book_id}", response_model=BookResponse)
async def update_book(book: ExistingBook, store: BookStoreDep, payload: BookUpdate) -> BookResponse:
    """Apply a partial update to a book."""
    return store.update(book, payload)


@books_router.delete("/{book_id}", response_model=DeleteResponse)
async def delete_book(book: ExistingBook, store: BookStoreDep) -> DeleteResponse:
    """Delete a book from the in-memory store."""
    store.delete(book.id)
    return DeleteResponse(message=f"Book {book.id} deleted successfully")


app.include_router(books_router)
