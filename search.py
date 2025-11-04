#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
from __future__ import annotations

import json
import sys
import time
from collections import deque
from dataclasses import dataclass
from html.parser import HTMLParser
from itertools import islice
from typing import Callable, Iterable, Iterator, Protocol, Sequence, TextIO
from urllib import error, parse, request
from xml.etree import ElementTree

DEFAULT_RESULT_LIMIT = 10
DEFAULT_TIMEOUT = 10.0
DEFAULT_RETRIES = 2
BACKOFF_SECONDS = 3.0
_DUCKDUCKGO_API_DEFAULTS = {
    "format": "json",
    "no_html": "1",
    "no_redirect": "1",
}
_ROBOT_TOKENS = (
    "too many requests",
    "captcha",
    "complete the following challenge",
    "unfortunately, bots use",
    "robot check",
    "are you human",
    "access denied",
)
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0 Safari/537.36"
)

Result = tuple[str, str]
FetchHtml = Callable[[str], str]
type Engines = Sequence[SearchEngine]


class SearchEngine(Protocol):
    name: str

    def build_url(self, query: str) -> str: ...  # ...

    def extract_results(self, html: str, limit: int) -> list[Result]: ...  # ...


class _BaseParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._queue: deque[Result] = deque()
        self._current_href: str | None = None
        self._buffer: list[str] = []

    def _enqueue(self, title: str, href: str) -> None:
        self._queue.append((title, href))

    def _flush(self) -> None:
        title = "".join(self._buffer).strip()
        if title and self._current_href:
            self._enqueue(title, self._current_href)
        self._current_href = None
        self._buffer.clear()

    def iter_results(self) -> Iterator[Result]:
        while self._queue:
            yield self._queue.popleft()


class _DuckDuckGoParser(_BaseParser):
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a" or self._current_href is not None:
            return
        attr_map = {key: value or "" for key, value in attrs}
        href = attr_map.get("href", "")
        classes = attr_map.get("class", "").split()
        if "result__a" in classes and href.startswith(("http://", "https://")):
            self._current_href = href
            self._buffer.clear()

    def handle_data(self, data: str) -> None:
        if self._current_href is not None:
            self._buffer.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._current_href is not None:
            self._flush()


def _brave_href_and_classes(
    attrs: list[tuple[str, str | None]],
) -> tuple[str, set[str]]:
    """Return href and class set from Brave anchor attributes."""
    attr_map = {key: value or "" for key, value in attrs}
    classes = set(attr_map.get("class", "").split())
    return attr_map.get("href", ""), classes


class _BraveParser(_BaseParser):
    TARGET_CLASSES = {"heading-serpresult", "title"}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a" or self._current_href is not None:
            return
        href, classes = _brave_href_and_classes(attrs)
        if href.startswith(("http://", "https://")) and self.TARGET_CLASSES.issubset(
            classes
        ):
            self._current_href = href
            self._buffer.clear()

    def handle_data(self, data: str) -> None:
        if self._current_href is not None:
            self._buffer.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._current_href is not None:
            self._flush()


def _iter_unique_results(results: Iterable[Result]) -> Iterator[Result]:
    """Yield results with duplicate hrefs removed."""
    seen: set[str] = set()
    for title, href in results:
        if href in seen:
            continue
        seen.add(href)
        yield title, href


def _iter_bing_items(html: str) -> Iterator[ElementTree.Element]:
    """Yield <item> elements from a Bing RSS payload."""
    try:
        root = ElementTree.fromstring(html)
    except ElementTree.ParseError:
        return
    yield from root.findall(".//item")


def _item_to_result(item: ElementTree.Element) -> Result | None:
    """Convert a Bing RSS item to a result tuple."""
    title = (item.findtext("title") or "").strip()
    link = (item.findtext("link") or "").strip()
    if not title or not link:
        return None
    return title, link


def _iter_bing_results(html: str) -> Iterator[Result]:
    """Yield parsed results from a Bing RSS payload."""
    for item in _iter_bing_items(html):
        result = _item_to_result(item)
        if result is not None:
            yield result


def _load_duckduckgo_payload(html: str) -> dict[str, object] | None:
    """Parse DuckDuckGo API payload into a dictionary."""
    try:
        data = json.loads(html)
    except json.JSONDecodeError:
        return None
    if isinstance(data, dict):
        return data
    return None


def _duckduckgo_leaf_result(node: dict[str, object]) -> Result | None:
    """Return the result tuple for a single DuckDuckGo topic."""
    text = str(node.get("Text") or "").strip()
    url = str(node.get("FirstURL") or "").strip()
    if text and url:
        return text, url
    return None


def _iter_duckduckgo_topic(node: object) -> Iterator[Result]:
    """Yield results for a single DuckDuckGo topic node."""
    if not isinstance(node, dict):
        return
    result = _duckduckgo_leaf_result(node)
    if result is not None:
        yield result
    nested = node.get("Topics")
    if isinstance(nested, list):
        yield from _iter_duckduckgo_topics(nested)


def _iter_duckduckgo_topics(nodes: Iterable[object]) -> Iterator[Result]:
    """Yield DuckDuckGo API results from topic nodes."""
    for node in nodes:
        yield from _iter_duckduckgo_topic(node)


class _GoogleParser(_BaseParser):
    TARGET_CLASS = "result__a"

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a" or self._current_href is not None:
            return
        attr_map = {key: value or "" for key, value in attrs}
        href = attr_map.get("href", "")
        classes = attr_map.get("class", "").split()
        if self.TARGET_CLASS in classes and href.startswith(("http://", "https://")):
            self._current_href = href
            self._buffer.clear()

    def handle_data(self, data: str) -> None:
        if self._current_href is not None:
            self._buffer.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._current_href is not None:
            self._flush()


class DuckDuckGoEngine:
    name = "DuckDuckGo"
    _endpoint = "https://duckduckgo.com/html/"

    def build_url(self, query: str) -> str:
        """Build the DuckDuckGo HTML search URL."""
        params = parse.urlencode({"q": query})
        return f"{self._endpoint}?{params}"

    def extract_results(self, html: str, limit: int) -> list[Result]:
        """Parse DuckDuckGo HTML results."""
        parser = _DuckDuckGoParser()
        parser.feed(html)
        parser.close()
        return list(islice(parser.iter_results(), limit))


class BraveEngine:
    name = "Brave"
    _endpoint = "https://search.brave.com/search"

    def build_url(self, query: str) -> str:
        """Build the Brave search URL."""
        params = parse.urlencode({"q": query, "source": "web"})
        return f"{self._endpoint}?{params}"

    def extract_results(self, html: str, limit: int) -> list[Result]:
        """Return up to limit unique Brave results."""
        parser = _BraveParser()
        parser.feed(html)
        parser.close()
        return list(islice(_iter_unique_results(parser.iter_results()), limit))


class BingRssEngine:
    name = "Bing"
    _endpoint = "https://www.bing.com/search"

    def build_url(self, query: str) -> str:
        """Build the Bing RSS search URL."""
        params = parse.urlencode({"q": query, "format": "rss"})
        return f"{self._endpoint}?{params}"

    def extract_results(self, html: str, limit: int) -> list[Result]:
        """Return up to limit Bing RSS results."""
        return list(islice(_iter_bing_results(html), limit))


class DuckDuckGoApiEngine:
    name = "DuckDuckGo API"
    _endpoint = "https://api.duckduckgo.com/"

    def build_url(self, query: str) -> str:
        """Build the DuckDuckGo JSON API URL."""
        params = {"q": query, **_DUCKDUCKGO_API_DEFAULTS}
        return f"{self._endpoint}?{parse.urlencode(params)}"

    def extract_results(self, html: str, limit: int) -> list[Result]:
        """Return up to limit DuckDuckGo API results."""
        payload = _load_duckduckgo_payload(html)
        if payload is None:
            return []
        topics = payload.get("RelatedTopics")
        if not isinstance(topics, list):
            return []
        return list(islice(_iter_duckduckgo_topics(topics), limit))


class GoogleEngine:
    name = "Google"
    _endpoint = "https://www.google.com/search"

    def build_url(self, query: str) -> str:
        """Build the Google search URL."""
        params = parse.urlencode({"q": query})
        return f"{self._endpoint}?{params}"

    def extract_results(self, html: str, limit: int) -> list[Result]:
        """Parse Google HTML results."""
        parser = _GoogleParser()
        parser.feed(html)
        parser.close()
        return list(islice(parser.iter_results(), limit))


DEFAULT_ENGINES: Sequence[SearchEngine] = (
    BraveEngine(),
    DuckDuckGoEngine(),
    BingRssEngine(),
    DuckDuckGoApiEngine(),
    GoogleEngine(),
)


class _EngineCycle:
    def __init__(self, engines: Sequence[SearchEngine]) -> None:
        self._engines: deque[SearchEngine] = deque(engines)

    def next_order(self) -> Sequence[SearchEngine]:
        """Return current engine order and rotate for next call."""
        if not self._engines:
            return ()
        order = tuple(self._engines)
        self._engines.rotate(-1)
        return order


_ENGINE_CYCLE = _EngineCycle(DEFAULT_ENGINES)


def _is_robot_challenge(payload: str) -> bool:
    lowered = payload.lower()
    return any(token in lowered for token in _ROBOT_TOKENS)


_OPENER = request.build_opener(request.HTTPCookieProcessor())


def _read_response(req: request.Request) -> str:
    with _OPENER.open(req, timeout=DEFAULT_TIMEOUT) as response:  # nosec B310
        return response.read().decode("utf-8", errors="ignore")


def _build_request(url: str) -> request.Request:
    """Create a default request with search headers."""
    return request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept-Language": "en-US,en;q=0.9",
        },
    )


def _fetch_with_retries(req: request.Request) -> str:
    """Fetch a request, retrying on 429 responses."""
    for attempt in range(DEFAULT_RETRIES + 1):
        try:
            return _read_response(req)
        except error.HTTPError as exc:
            if exc.code != 429 or attempt >= DEFAULT_RETRIES:
                raise
            time.sleep(BACKOFF_SECONDS)
    raise RuntimeError("Exhausted retries while fetching HTML")


def _default_fetch_html(url: str) -> str:
    """Fetch HTML for a URL using the default retry policy."""
    return _fetch_with_retries(_build_request(url))


def iter_queries(stream: Iterable[str]) -> Iterator[str]:
    """Yield stripped, non-empty queries from the stream."""
    for raw in stream:
        cleaned = raw.strip()
        if cleaned:
            yield cleaned


@dataclass(frozen=True)
class QueryOutcome:
    query: str
    block: str | None
    error: str | None

    @property
    def is_error(self) -> bool:
        """Return True if this outcome represents an error."""
        return self.error is not None


def iter_formatted_lines(
    query: str,
    engine_name: str,
    results: Iterable[Result],
) -> Iterator[str]:
    """Yield formatted output lines for a query result block."""
    yield f"Query: {query} (engine: {engine_name})"
    for index, (title, url) in enumerate(results, start=1):
        yield f"{index}. {title} — {url}"


def format_query_results(
    query: str,
    engine_name: str,
    results: Iterable[Result],
) -> str:
    """Join formatted lines for display."""
    return "\n".join(iter_formatted_lines(query, engine_name, results))


def _fetch_html_with_error(
    engine: SearchEngine,
    url: str,
    fetch_html: FetchHtml,
) -> tuple[str | None, str | None]:
    """Fetch HTML for an engine URL and report errors."""
    try:
        return fetch_html(url), None
    except (error.HTTPError, error.URLError) as exc:
        return None, f"{engine.name}: {exc}"


def _fetch_engine_html(
    engine: SearchEngine,
    query: str,
    fetch_html: FetchHtml,
) -> tuple[str | None, str | None]:
    """Fetch engine HTML or return an error message."""
    url = engine.build_url(query)
    return _fetch_html_with_error(engine, url, fetch_html)


def _format_empty_results(
    engine: SearchEngine,
    html: str,
) -> tuple[str | None, str | None]:
    """Format the error tuple for an empty result set."""
    if _is_robot_challenge(html):
        return None, f"{engine.name}: robot verification required"
    return None, f"{engine.name}: no results"


def _format_results(
    query: str,
    engine: SearchEngine,
    html: str,
) -> tuple[str | None, str | None]:
    """Format engine results or report empty/robot responses."""
    results = engine.extract_results(html, DEFAULT_RESULT_LIMIT)
    if results:
        return format_query_results(query, engine.name, results), None
    return _format_empty_results(engine, html)


def _run_engine(
    query: str,
    engine: SearchEngine,
    fetch_html: FetchHtml,
) -> tuple[str | None, str | None]:
    """Run a single engine and return its formatted block or error."""
    html, error_text = _fetch_engine_html(engine, query, fetch_html)
    if error_text is not None:
        return None, error_text
    assert html is not None
    return _format_results(query, engine, html)


def _build_error_outcome(query: str, errors: Sequence[str]) -> QueryOutcome:
    """Create a QueryOutcome for an exhausted set of engines."""
    if not errors:
        detail = f"Error: failed to search '{query}': no search engines configured"
    elif len(errors) == 1:
        detail = errors[0]
    else:
        joined = "; ".join(errors)
        detail = f"Error: failed to search '{query}': {joined}"
    return QueryOutcome(query, None, detail)


def _search_query(query: str, engines: Engines, fetch_html: FetchHtml) -> QueryOutcome:
    """Run engines until one succeeds or all fail."""
    errors: list[str] = []
    for engine in engines:
        block, error_text = _run_engine(query, engine, fetch_html)
        if error_text is None:
            return QueryOutcome(query, block, None)
        errors.append(error_text)
    return _build_error_outcome(query, errors)


def search_outcomes(
    stream: Iterable[str],
    *,
    engines: Sequence[SearchEngine] | None = None,
    fetch_html: FetchHtml = _default_fetch_html,
) -> Iterator[QueryOutcome]:
    """Yield search outcomes for each query in the stream."""
    for query in iter_queries(stream):
        order = engines if engines is not None else _ENGINE_CYCLE.next_order()
        yield _search_query(query, order, fetch_html)


def _write_outcome(outcome: QueryOutcome, stdout: TextIO, stderr: TextIO) -> int:
    """Write a query outcome to the appropriate stream."""
    if outcome.is_error:
        print(outcome.error, file=stderr)
        return 1
    if outcome.block:
        print(outcome.block, file=stdout)
        print(file=stdout)
    return 0


def main(
    stdin: Iterable[str] = sys.stdin,
    stdout: TextIO = sys.stdout,
    stderr: TextIO = sys.stderr,
) -> int:
    """Search the web for stdin queries and print formatted results."""
    exit_code = 0
    for outcome in search_outcomes(stdin):
        exit_code = max(exit_code, _write_outcome(outcome, stdout, stderr))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
