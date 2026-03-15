from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final

ROOT: Final = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DOCS_DIR: Final = ROOT / "website" / "docs"
STATIC_DIR: Final = ROOT / "website" / "static"
SITE_BASE_URL: Final = "https://jaredthivener.github.io/python-demo"
RAW_BASE_URL: Final = "https://raw.githubusercontent.com/jaredthivener/python-demo/main"
OPENAPI_PATH: Final = STATIC_DIR / "openapi.json"
DOCS_INDEX_PATH: Final = STATIC_DIR / "docs-index.json"
LLMS_PATH: Final = STATIC_DIR / "llms.txt"

FRONTMATTER_PATTERN: Final = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)
HEADING_PATTERN: Final = re.compile(r"^#\s+(?P<title>.+)$", re.MULTILINE)
PRIORITY_RANK: Final = {"critical": 0, "high": 1, "medium": 2, "low": 3}
PRIMARY_DOC_IDS: Final = (
    "intro",
    "getting-started",
    "api-books",
    "auth-overview",
    "deployment-overview",
)


@dataclass(frozen=True)
class DocumentEntry:
    doc_id: str
    title: str
    category: str
    canonical_url: str
    source_path: str
    raw_markdown_url: str
    priority: str
    summary: str
    related_artifacts: tuple[str, ...] = ()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate machine-readable artifacts for docs and API ingestion."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if generated artifact content differs from the checked-in files.",
    )
    return parser.parse_args()


def parse_frontmatter(text: str) -> tuple[dict[str, str | list[str]], str]:
    match = FRONTMATTER_PATTERN.match(text)
    if not match:
        return {}, text

    raw_frontmatter, body = match.groups()
    frontmatter: dict[str, str | list[str]] = {}
    current_list_key: str | None = None

    for raw_line in raw_frontmatter.splitlines():
        line = raw_line.rstrip()
        if not line:
            continue
        if line.startswith("  - "):
            if current_list_key is None:
                raise ValueError(f"List item without a frontmatter key: {raw_line!r}")
            existing = frontmatter.setdefault(current_list_key, [])
            if not isinstance(existing, list):
                raise ValueError(f"Frontmatter key {current_list_key!r} is not a list")
            existing.append(line[4:])
            continue

        key, separator, value = line.partition(":")
        if not separator:
            raise ValueError(f"Invalid frontmatter line: {raw_line!r}")

        normalized_key = key.strip()
        normalized_value = value.strip()
        if normalized_value:
            current_list_key = None
            frontmatter[normalized_key] = normalized_value.strip('"')
            continue

        current_list_key = normalized_key
        frontmatter[normalized_key] = []

    return frontmatter, body


def read_markdown(path: Path) -> tuple[dict[str, str | list[str]], str]:
    return parse_frontmatter(path.read_text(encoding="utf-8"))


def extract_title(body: str, path: Path) -> str:
    match = HEADING_PATTERN.search(body)
    if match:
        return match.group("title").strip()
    raise ValueError(f"Could not find a level-1 heading in {path}")


def extract_summary(frontmatter: dict[str, str | list[str]], body: str) -> str:
    description = frontmatter.get("description")
    if isinstance(description, str) and description:
        return description

    lines = body.splitlines()
    found_heading = False
    paragraph_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not found_heading:
            if stripped.startswith("# "):
                found_heading = True
            continue
        if not stripped:
            if paragraph_lines:
                break
            continue
        if stripped.startswith("#") or stripped.startswith("```") or stripped.startswith(":::"):
            if paragraph_lines:
                break
            continue
        paragraph_lines.append(stripped)

    if paragraph_lines:
        return " ".join(paragraph_lines)
    return "Documentation page"


def category_for_path(relative_path: Path) -> str:
    if len(relative_path.parts) == 1:
        return "overview"
    return relative_path.parts[0]


def document_id_for_path(relative_path: Path) -> str:
    if relative_path.name == "index.md":
        return f"{relative_path.parent.as_posix()}-overview"
    return relative_path.with_suffix("").as_posix().replace("/", "-")


def canonical_doc_path(relative_path: Path) -> str:
    if relative_path.name == "index.md":
        if relative_path.parent == Path("."):
            return "/docs"
        return f"/docs/{relative_path.parent.as_posix()}"
    return f"/docs/{relative_path.with_suffix('').as_posix()}"


def priority_for_path(doc_id: str, relative_path: Path) -> str:
    overrides = {
        "api-books": "critical",
        "intro": "high",
        "getting-started": "high",
        "auth-overview": "high",
        "auth-managed-identity": "high",
        "deployment-overview": "high",
    }
    if doc_id in overrides:
        return overrides[doc_id]

    stem = relative_path.stem
    if stem in {"aws", "gcp", "azure-functions", "app-service", "jwt-bearer", "entra-id"}:
        return "medium"
    if len(relative_path.parts) == 1:
        return "high"
    return "low"


def related_artifacts_for_doc(doc_id: str) -> tuple[str, ...]:
    if doc_id == "api-books":
        return (f"{SITE_BASE_URL}/openapi.json",)
    return ()


def build_document_entry(path: Path) -> DocumentEntry:
    relative_path = path.relative_to(DOCS_DIR)
    frontmatter, body = read_markdown(path)
    doc_id = document_id_for_path(relative_path)
    canonical_path = canonical_doc_path(relative_path)
    return DocumentEntry(
        doc_id=doc_id,
        title=extract_title(body, path),
        category=category_for_path(relative_path),
        canonical_url=f"{SITE_BASE_URL}{canonical_path}",
        source_path=path.relative_to(ROOT).as_posix(),
        raw_markdown_url=f"{RAW_BASE_URL}/{path.relative_to(ROOT).as_posix()}",
        priority=priority_for_path(doc_id, relative_path),
        summary=extract_summary(frontmatter, body),
        related_artifacts=related_artifacts_for_doc(doc_id),
    )


def build_documents() -> list[DocumentEntry]:
    documents = [build_document_entry(path) for path in sorted(DOCS_DIR.rglob("*.md"))]
    return sorted(documents, key=lambda doc: (PRIORITY_RANK[doc.priority], doc.source_path))


def build_docs_index(documents: list[DocumentEntry]) -> dict[str, object]:
    serialized_documents: list[dict[str, object]] = []
    for document in documents:
        entry: dict[str, object] = {
            "id": document.doc_id,
            "title": document.title,
            "category": document.category,
            "canonicalUrl": document.canonical_url,
            "sourcePath": document.source_path,
            "rawMarkdownUrl": document.raw_markdown_url,
            "priority": document.priority,
            "summary": document.summary,
        }
        if document.related_artifacts:
            entry["relatedArtifacts"] = list(document.related_artifacts)
        serialized_documents.append(entry)

    return {
        "name": "python-demo-docs",
        "version": 1,
        "site": {
            "title": "Python Demo API",
            "baseUrl": SITE_BASE_URL,
        },
        "ingestion": {
            "preferredSources": ["openapi", "docs-index", "sitemap", "markdown"],
            "notes": [
                "Use the OpenAPI contract for executable API tool generation.",
                "Use this manifest to rank canonical documentation pages.",
                "Use the sitemap for discovery only.",
                "Prefer raw markdown from the repository when available.",
            ],
        },
        "artifacts": {
            "openapi": {
                "url": f"{SITE_BASE_URL}/openapi.json",
                "path": OPENAPI_PATH.relative_to(ROOT).as_posix(),
            },
            "llms": {
                "url": f"{SITE_BASE_URL}/llms.txt",
                "path": LLMS_PATH.relative_to(ROOT).as_posix(),
            },
            "sitemap": {
                "url": f"{SITE_BASE_URL}/sitemap.xml",
                "path": "website/build/sitemap.xml",
            },
        },
        "documents": serialized_documents,
    }


def build_llms_text(documents: list[DocumentEntry]) -> str:
    docs_by_id = {document.doc_id: document for document in documents}
    primary_docs = [docs_by_id[doc_id] for doc_id in PRIMARY_DOC_IDS if doc_id in docs_by_id]

    lines = [
        "# Python Demo API",
        "",
        (
            "Python Demo API is a compact FastAPI reference app with a realistic Books "
            "API and supporting documentation for authentication and multi-cloud "
            "deployment."
        ),
        "",
        "Preferred ingestion order:",
        "1. /openapi.json",
        "2. /docs-index.json",
        "3. /sitemap.xml",
        "4. Source markdown under website/docs/",
        "",
        "Primary machine-readable artifacts:",
        f"- OpenAPI contract: {SITE_BASE_URL}/openapi.json",
        f"- Curated docs manifest: {SITE_BASE_URL}/docs-index.json",
        f"- Sitemap: {SITE_BASE_URL}/sitemap.xml",
        "",
        "Primary human-readable docs:",
    ]

    for document in primary_docs:
        lines.append(f"- {document.title}: {document.canonical_url}")

    lines.extend(
        [
            "",
            "Notes for tool builders:",
            "- Treat the OpenAPI contract as the source of truth for executable API tools.",
            "- Treat docs-index.json as the curated map of canonical topics and URLs.",
            "- Use sitemap.xml for discovery, not for ranking authority.",
            (
                "- Prefer raw markdown from the repository over scraping built HTML when "
                "deeper ingestion is possible."
            ),
            (
                "- The live demo app covers the Books API and observability endpoints; "
                "broader auth and cloud patterns live in the docs."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def build_openapi_json() -> str:
    from main import app

    return json.dumps(app.openapi(), indent=2) + "\n"


def write_or_check(path: Path, content: str, check: bool) -> bool:
    if check:
        if not path.exists() or path.read_text(encoding="utf-8") != content:
            print(f"Artifact is out of date: {path.relative_to(ROOT).as_posix()}")
            return False
        return True

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"Wrote {path.relative_to(ROOT).as_posix()}")
    return True


def main() -> int:
    args = parse_args()
    documents = build_documents()
    docs_index = json.dumps(build_docs_index(documents), indent=2) + "\n"
    llms = build_llms_text(documents)
    openapi = build_openapi_json()

    ok = True
    ok = write_or_check(OPENAPI_PATH, openapi, check=args.check) and ok
    ok = write_or_check(DOCS_INDEX_PATH, docs_index, check=args.check) and ok
    ok = write_or_check(LLMS_PATH, llms, check=args.check) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
