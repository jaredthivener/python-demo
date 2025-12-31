# AGENTS.md - Guidance for AI Coding Agents

Description: This is a **demo** FastAPI project for learning Python, FastAPI, API best practices, security, performance, logging & monitoring, and coding best practices. It features colorful logging with Rich, background traffic generation, and example endpoints for HTTP methods and error simulation.

You are an expert software engineer for this project.

## Project Overview

- Framework: FastAPI (0.128.0)
- Language: Python 3.14+
- Key dependencies: uvicorn (0.40.0), httpx (0.28.1), rich (14.2.0)
- Focus areas:
  - API design with various HTTP methods (GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS)
  - Logging: Structured, color-coded access logs with Rich
  - Performance: Response time tracking, async operations
  - Security: Error handling, request IDs, header-based simulations
  - Monitoring: Health checks, traffic simulation
  - Best practices: Type hints, async context, middleware

Keep the project small and educational—prioritize readability and idiomatic Python/FastAPI patterns.

## Important Commands

Use these exact commands:

- Run the development server:  
  ```bash
  uvicorn main:app --reload --no-access-log

- Install dependencies (using uv):
  ```bash
  uv sync

- Activate virtual environment:
  ```bash 
  source .venv/bin/activate  # On Windows: .venv\Scripts\activate

Never install packages without confirmation unless listed in pyproject.toml.

## Code Style Guidelines

- Follow PEP 8 and PEP 257.
- Use type hints everywhere—no `Any`.
- Prefer async/await for I/O-bound operations.
- Use explicit configurations (e.g., via constants like WARN_MS, SLOW_MS).
- File structure:
  - `main.py`: Core app, endpoints, middleware, helpers
  - Keep all code in `main.py` for simplicity unless expanding
  - Add new files only for major features (e.g., `routers/` for API splits)
- Naming: Descriptive variables (e.g., `status_style`), constants in UPPER_CASE.
- Avoid globals; use dependencies or context managers.
- Use Rich for console output where appropriate.

## Testing Instructions

- Add tests using pytest (install if needed via uv add pytest).
- Write unit/integration tests for new endpoints.
- Test structure: `tests/test_main.py` mirroring app logic.
- Cover:
  - Happy paths
  - Errors (e.g., forced via X-Force-Error header)
  - Performance (e.g., latency thresholds)
- Run tests:
  ```bash
  pytest  

Aim for high coverage on critical parts like middleware and traffic generator.

## Security Considerations
- Validate inputs with FastAPI's built-in features (e.g., path params).
- Use headers for simulations (e.g., X-Force-Error, X-Request-ID).
- Never log sensitive data.
- Implement rate limiting if expanding (e.g., via slowapi).
- Use HTTPS in production; handle redirects securely.
- Sanitize user inputs in future expansions.

## Performance Best Practices

- Use async endpoints and httpx.AsyncClient.
- Simulate delays with asyncio.sleep for testing.
- Monitor latency with thresholds (WARN_MS=100ms, SLOW_MS=500ms).
- Optimize traffic generator to avoid overload (e.g., random sleeps).
- Cache static responses (e.g., favicon).

## Logging & Monitoring

- Use RichHandler for color-coded logs.
- Log levels: INFO for access, WARNING/ERROR for issues.
- Include timestamps, status, latency, size, client, method, path, request ID.
- Add health endpoints (e.g., /api/ps, /api/status).
- Simulate traffic for monitoring real-world behavior.

## Additional Guidelines

- Commit messages: Use Conventional Commits (e.g., `feat: add new endpoint`, `fix: improve error handling`).
- Keep PRs small and focused.
- Update README.md with new features/endpoints.
- Favor short functions with single responsibility.
- Use contextlib.asynccontextmanager for lifespan events.  