from datetime import datetime
import logging
import time
import uuid
import asyncio
import random
from typing import Tuple
import json
import httpx

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, Response
from contextlib import asynccontextmanager
from rich.console import Console
from rich.text import Text
from rich.logging import RichHandler

# ---------------- Configuration ----------------
WARN_MS = 100.0    # >= this will show a warning color
SLOW_MS = 500.0    # >= this is "slow" (red)
FAVICON_PATH = "/favicon.ico"
FAVICON_CACHE_SECONDS = 31_536_000  # 1 year
SERVER_PORT = 8000 # Assumed port for the background traffic generator

# ---------------- Logging setup ----------------
logging.basicConfig(
    level="INFO",
    format="%(asctime)s %(levelname)s %(name)s:%(lineno)d %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[RichHandler(markup=True)]
)
logger = logging.getLogger("myapp")
# Silence httpx so we only see server-side logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
# silence uvicorn.access (we print our own pretty access lines)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

# console for pretty printing
console = Console()

# ---------------- Helpers ----------------
def status_style(status_code: int) -> Tuple[str, str]:
    """Return (style, label) for a numeric status."""
    if status_code >= 500:
        return ("white on red", str(status_code))
    if status_code >= 400:
        return ("black on yellow", str(status_code))
    if status_code >= 300:
        return ("black on cyan", str(status_code))
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


def fmt_size_from_header(hval: str | None) -> str:
    if not hval:
        return "-"
    try:
        n = int(hval)
    except Exception:
        return hval
    # human friendly
    if n < 1024:
        return f"{n}B"
    if n < 1024**2:
        return f"{n/1024:.1f}KB"
    return f"{n/1024**2:.1f}MB"

# ---------------- App & Middleware ----------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app lifespan events."""
    # Startup
    asyncio.create_task(generate_traffic())
    yield
    # Shutdown (if needed)


app = FastAPI(lifespan=lifespan)


async def generate_traffic():
    """Simulates random traffic to the local server."""
    # Give the server a moment to start up
    await asyncio.sleep(2.0)
    
    base_url = f"http://127.0.0.1:{SERVER_PORT}"
    
    # List of (Method, Path Template)
    # We will format the path with a random ID if needed
    operations = [
        ("GET", "/"),
        ("GET", "/api/tags"),
        ("GET", "/api/ps"),
        ("POST", "/api/pull"),
        ("PUT", "/api/items/{id}"),
        ("PATCH", "/api/items/{id}"),
        ("DELETE", "/api/items/{id}"),
        ("HEAD", "/api/status"),
        ("OPTIONS", "/api/options"),
        ("GET", "/api/error/400"),
        ("GET", "/api/error/404"),
        ("GET", "/api/error/500"),
        ("GET", "/api/error/503"),
    ]

    console.print(f"[bold cyan]Starting background traffic generator targeting {base_url}...[/bold cyan]")

    async with httpx.AsyncClient(base_url=base_url, timeout=5.0) as client:
        while True:
            method, path_template = random.choice(operations)
            
            # Insert a random ID if the path requires it
            path = path_template.format(id=random.randint(1000, 9999))
            
            try:
                await client.request(method, path)
            except Exception:
                # Ignore connection errors (e.g. if server is stopping)
                pass
            
            # Wait a random time between 0.5s and 2.0s
            await asyncio.sleep(random.uniform(0.5, 2.0))


@app.middleware("http")
async def colorful_access_log(request: Request, call_next):
    # quick favicon short-circuit to reduce noise + send caching header
    if request.url.path == FAVICON_PATH:
        return PlainTextResponse(
            status_code=204,
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
        # log exception with stacktrace, return 500 to client but still log nicely
        status_code = 500
        response = PlainTextResponse("Internal server error", status_code=500)
        logger.exception("Unhandled exception while handling request")

    # ensure request id on response for correlation
    response.headers["X-Request-ID"] = request_id

    end = time.monotonic()
    latency_ms = (end - start) * 1000.0
    latency_style = "green"
    if latency_ms >= SLOW_MS:
        latency_style = "bold red"
    elif latency_ms >= WARN_MS:
        latency_style = "yellow"

    # prepare fields
    status_style_str, status_text = status_style(status_code)
    mstyle = method_style(request.method)
    path = request.url.path
    if request.url.query:
        path = f"{path}?{request.url.query}"

    resp_size = fmt_size_from_header(response.headers.get("content-length"))

    # build compact rich Text with aligned columns
    line = Text()
    line.append(f"{timestamp:<19}", style="dim")
    line.append(f" {status_text:<6}", style=status_style_str)
    line.append(f" {latency_ms:>8.2f}ms", style=latency_style)
    line.append(f" {resp_size:>7}", style="dim")
    line.append(f" {client:<15}", style="dim")
    line.append(f" {request.method:<7}", style=mstyle)
    line.append(f" {path:<30}", style="bold")
    line.append(f" {request_id}", style="cyan")

    console.print(line)
    return response


# ---------------- Example endpoints ----------------
@app.get("/api/tags")
async def tags():
    # Simulate slight work
    await asyncio.sleep(0.05)
    return {"tags": ["fastapi", "logging", "rich"]}


@app.get("/api/ps")
async def ps():
    return {"ps": "ok"}


@app.post("/api/pull")
async def pull():
    # don't block the event loop: use asyncio.sleep
    await asyncio.sleep(0.12)
    return {"pulled": True}


@app.get("/")
async def root():
    return {"hello": "world"}


# ---------------- METHOD TESTS ----------------

@app.put("/api/items/{item_id}")
async def update_item(item_id: str):
    await asyncio.sleep(0.1)
    return {"method": "PUT", "id": item_id, "status": "updated"}


@app.patch("/api/items/{item_id}")
async def patch_item(item_id: str):
    # await asyncio.sleep(0.1)
    return {"method": "PATCH", "id": item_id, "status": "patched"}


@app.delete("/api/items/{item_id}")
async def delete_item(item_id: str):
    await asyncio.sleep(0.5)
    return {"method": "DELETE", "id": item_id, "status": "deleted"}


@app.head("/api/status")
async def status_head():
    # HEAD requests shouldn't return a body
    return Response(headers={"X-System-Status": "OK"}, status_code=200)


@app.options("/api/options")
async def options_test():
    return Response(
        headers={"Allow": "OPTIONS, GET, POST, PUT, PATCH, DELETE, HEAD"}, 
        status_code=200
    )


# ---------------- ERROR SIMULATIONS ----------------

@app.get("/api/error/400")
async def error_bad_request():
    """Simulate a 400 Bad Request error."""
    return Response(
        content=json.dumps({"error": "Invalid request parameters"}),
        status_code=400,
        media_type="application/json"
    )


@app.get("/api/error/404")
async def error_not_found():
    """Simulate a 404 Not Found error."""
    return Response(
        content=json.dumps({"error": "Resource not found"}),
        status_code=404,
        media_type="application/json"
    )


@app.get("/api/error/500")
async def error_internal_server():
    """Simulate a 500 Internal Server Error."""
    await asyncio.sleep(0.15)
    return Response(
        content=json.dumps({"error": "Internal server error"}),
        status_code=500,
        media_type="application/json"
    )


@app.get("/api/error/503")
async def error_service_unavailable():
    """Simulate a 503 Service Unavailable error."""
    await asyncio.sleep(0.6)
    return Response(
        content=json.dumps({"error": "Service temporarily unavailable"}),
        status_code=503,
        media_type="application/json"
    )