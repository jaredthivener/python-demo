# Python FastAPI Demo

A colorful FastAPI server with rich logging, background traffic generation, and comprehensive endpoint examples for testing HTTP methods and error scenarios.

## Features

- **Rich Console Logging**: Colorized, formatted access logs with response times, status codes, and request IDs
- **Background Traffic Generator**: Simulates realistic traffic patterns to test your server
- **HTTP Method Examples**: GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS
- **Error Simulation**: Built-in endpoints for testing 400, 404, 500, and 503 responses
- **Request Correlation**: X-Request-ID headers for request tracing
- **Performance Metrics**: Response time tracking with visual indicators (green/yellow/red)

## Prerequisites

- Python 3.14 or higher
- [uv](https://docs.astral.sh/uv/) - Modern Python package manager

## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/jaredthivener/python-demo.git
cd python-demo
```

### 2. Create a Virtual Environment and Install Dependencies

```bash
uv sync
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

This command will create a virtual environment and install all dependencies from `pyproject.toml`. The `.venv/bin/activate` step activates the environment so you can use the installed packages.

## Running the Server

Activate the virtual environment first (if not already activated):

```bash
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

Then start the development server with auto-reload:

```bash
uvicorn main:app --reload --no-access-log
```

The server will be available at `http://127.0.0.1:8000`

### Server Features

- **Auto-reload**: The server automatically restarts when you modify `main.py`
- **Background Traffic**: Once running, the server generates simulated traffic to itself
- **Rich Logging**: All requests are logged with color-coded formatting

## API Endpoints

### Basic Endpoints

- `GET /` - Returns a simple hello message
- `GET /api/tags` - Returns a list of tags
- `GET /api/ps` - Health check endpoint

### Data Operations

- `POST /api/pull` - Simulates a pull operation
- `PUT /api/items/{id}` - Updates an item
- `PATCH /api/items/{id}` - Partially updates an item
- `DELETE /api/items/{id}` - Deletes an item

### HTTP Method Tests

- `HEAD /api/status` - Returns headers only
- `OPTIONS /api/options` - Returns allowed methods

### Error Simulation Endpoints

- `GET /api/error/400` - Returns 400 Bad Request
- `GET /api/error/404` - Returns 404 Not Found
- `GET /api/error/500` - Returns 500 Internal Server Error
- `GET /api/error/503` - Returns 503 Service Unavailable

## Example Usage

```bash
# Test GET endpoint
curl http://127.0.0.1:8000/api/tags

# Test POST endpoint
curl -X POST http://127.0.0.1:8000/api/pull

# Test error endpoint
curl http://127.0.0.1:8000/api/error/404
```

## Development

### Project Structure

```
python-demo/
├── main.py              # Main application file
├── requirements.txt     # Python dependencies
├── README.md           # This file
└── .venv/              # Virtual environment (ignored by git)
```

### Configuration

Key settings in `main.py`:

- `WARN_MS`: Response time threshold for yellow warning (default: 100ms)
- `SLOW_MS`: Response time threshold for red slow indicator (default: 500ms)
- `SERVER_PORT`: Port for background traffic generation (default: 8000)

## Logging

The application uses Rich for beautiful console logging. Each request line includes:

- Timestamp
- Status code (color-coded: green 2xx, cyan 3xx, yellow 4xx, red 5xx)
- Response time in milliseconds
- Response size
- Client IP
- HTTP method (color-coded by method type)
- Request path
- Request ID for correlation

## Stopping the Server

Press `CTRL+C` to stop the development server.

## Dependencies

- **fastapi**: Modern web framework for building APIs
- **uvicorn**: ASGI server for running FastAPI
- **httpx**: Async HTTP client for background traffic generation
- **rich**: Beautiful terminal rendering and logging

## License

MIT

## Support

For issues or questions, please open an issue on the GitHub repository.
