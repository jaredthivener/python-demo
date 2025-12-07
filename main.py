from datetime import datetime
import logging
import time
import uuid
import asyncio
import random
from typing import Tuple
import json
import httpx

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse, Response, RedirectResponse
from contextlib import asynccontextmanager
from rich.console import Console
from rich.text import Text
from rich.logging import RichHandler

# ---------------- Configuration ----------------
WARN_MS = 100.0
SLOW_MS = 500.0
FAVICON_PATH = "/favicon.ico"
FAVICON_CACHE_SECONDS = 31_536_000
SERVER_PORT = 8000

# ---------------- Logging setup ----------------
logging.basicConfig(
    level="INFO",
    format="%(asctime)s %(levelname)s %(name)s:%(lineno)d %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[RichHandler(markup=True)]
)
logger = logging.getLogger("myapp")

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

console = Console()


# ---------------- Helpers ----------------
def status_style(status_code: int) -> Tuple[str, str]:
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


def fmt_size_from_header(hval: str | None) -> str:
    if not hval:
        return "-"
    try:
        n = int(hval)
    except Exception:
        return hval
    if n < 1024:
        return f"{n}B"
    if n < 1024**2:
        return f"{n/1024:.1f}KB"
    return f"{n/1024**2:.1f}MB"


# ---------------- App & Lifespan ----------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(generate_traffic())
    yield


app = FastAPI(lifespan=lifespan)


# ---------------- Traffic Generator ----------------
async def generate_traffic():
    await asyncio.sleep(2.0)

    base_url = f"http://127.0.0.1:{SERVER_PORT}"

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
        ("GET", "/api/redirect"),
        # error simulations (realistic rerouting happens below)
        ("ERR", "400"),
        ("ERR", "404"),
        ("ERR", "500"),
        ("ERR", "503"),
    ]

    console.print(f"[bold cyan]Starting background traffic generator targeting {base_url}...[/bold cyan]")

    async with httpx.AsyncClient(base_url=base_url, timeout=5.0) as client:
        while True:
            method, value = random.choice(operations)

            # ---------------- ERROR SIMULATION PATCH ----------------
            if method == "ERR":
                item_id = random.randint(1000, 9999)
                path = f"/api/items/{item_id}"
                headers = {"X-Force-Error": value}

                # Use PATCH so the handler runs and X-Force-Error takes effect
                try:
                    await client.request("PATCH", path, headers=headers)
                except Exception:
                    pass

                await asyncio.sleep(random.uniform(0.5, 2.0))
                continue

            # ---------------- NORMAL ROUTES ----------------
            path = value.format(id=random.randint(1000, 9999))
            try:
                await client.request(method, path)
            except Exception:
                pass

            await asyncio.sleep(random.uniform(0.5, 2.0))


# ---------------- Middleware (Pretty Log) ----------------
@app.middleware("http")
async def colorful_access_log(request: Request, call_next):
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
        status_code = 500
        response = PlainTextResponse("Internal server error", status_code=500)
        logger.exception("Unhandled exception while handling request")

    response.headers["X-Request-ID"] = request_id

    latency_ms = (time.monotonic() - start) * 1000.0
    latency_style = (
        "bold red" if latency_ms >= SLOW_MS
        else "yellow" if latency_ms >= WARN_MS
        else "green"
    )

    status_style_str, status_text = status_style(status_code)
    mstyle = method_style(request.method)
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
    line.append(f" {request.method:<7}", style=mstyle)
    line.append(f" {path:<30}", style="bold")
    line.append(f" {request_id}", style="cyan")

    console.print(line)
    return response


# ---------------- Example Endpoints ----------------
@app.get("/api/tags")
async def tags():
    await asyncio.sleep(0.05)
    return {"tags": ["fastapi", "logging", "rich"]}


@app.get("/api/ps")
async def ps():
    return {"ps": "ok"}


@app.post("/api/pull")
async def pull():
    await asyncio.sleep(0.12)
    return {"pulled": True}


@app.get("/")
async def root():
    return {"hello": "world"}


# ---------------- Item Endpoints (with forced error support) ----------------
def maybe_force_error(request: Request):
    """Check for X-Force-Error header and raise an error if present."""
    forced = request.headers.get("X-Force-Error")
    if forced:
        code = int(forced)
        raise HTTPException(status_code=code, detail=f"Simulated error {code}")

@app.get("/api/redirect")
async def redirect_test():
    item_id = random.randint(1000, 9999)
    return RedirectResponse(url=f"/api/items/{item_id}", status_code=307)

@app.put("/api/items/{item_id}")
async def update_item(item_id: str, request: Request):
    maybe_force_error(request)
    await asyncio.sleep(0.1)
    return {"method": "PUT", "id": item_id, "status": "updated"}


@app.patch("/api/items/{item_id}")
async def patch_item(item_id: str, request: Request):
    maybe_force_error(request)
    return {"method": "PATCH", "id": item_id, "status": "patched"}


@app.delete("/api/items/{item_id}")
async def delete_item(item_id: str, request: Request):
    maybe_force_error(request)
    await asyncio.sleep(0.5)
    return {"method": "DELETE", "id": item_id, "status": "deleted"}


# ---------------- Status Endpoints ----------------
@app.head("/api/status")
async def status_head():
    return Response(headers={"X-System-Status": "OK"}, status_code=200)


@app.options("/api/options")
async def options_test():
    return Response(
        headers={"Allow": "OPTIONS, GET, POST, PUT, PATCH, DELETE, HEAD"},
        status_code=200
    )
