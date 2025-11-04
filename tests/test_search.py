from __future__ import annotations

import io
import json
from dataclasses import dataclass
from textwrap import dedent
from email.message import Message
from typing import Iterable
from urllib import error

import pytest

import search


GoogleEntry = tuple[str, str]
DDGNode = dict[str, object]


@pytest.fixture()
def google_engine() -> search.SearchEngine:
    google_engine_cls = getattr(search, "GoogleEngine", None)
    if google_engine_cls is None:
        pytest.fail("GoogleEngine not yet implemented")
    assert google_engine_cls is not None
    return google_engine_cls()


@pytest.fixture()
def duckduckgo_api_engine() -> search.SearchEngine:
    api_engine_cls = getattr(search, "DuckDuckGoApiEngine", None)
    if api_engine_cls is None:
        pytest.fail("DuckDuckGoApiEngine not yet implemented")
    assert api_engine_cls is not None
    return api_engine_cls()


@pytest.fixture()
def google_limit_entries() -> list[GoogleEntry]:
    return [
        ("One", "https://example.com/1"),
        ("Two", "https://example.com/2"),
        ("Three", "https://example.com/3"),
    ]


@pytest.fixture()
def bing_sample_feed() -> str:
    return dedent(
        """<?xml version="1.0" encoding="utf-8"?>
        <rss version="2.0">
          <channel>
            <item>
              <title>Example Title</title>
              <link>https://example.com</link>
            </item>
            <item>
              <title>Another Example</title>
              <link>https://example.org</link>
            </item>
          </channel>
        </rss>
        """
    )


def _google_anchor(text: str, href: str) -> str:
    return f'        <a class="result__a" href="{href}">{text}</a>'


def _google_html(lines: Iterable[str]) -> str:
    anchors = "\n".join(lines)
    return dedent(
        f"""
        <html>
          <body>
{anchors}
          </body>
        </html>
        """
    )


def _google_html_for_entries(entries: Iterable[GoogleEntry]) -> str:
    return _google_html(_google_anchor(title, href) for title, href in entries)


def _ddg_topic(text: str, url: str) -> DDGNode:
    return {"Text": text, "FirstURL": url}


def _ddg_category(name: str, topics: Iterable[DDGNode]) -> DDGNode:
    return {"Name": name, "Topics": list(topics)}


def _ddg_api_payload(related_topics: Iterable[DDGNode]) -> str:
    return json.dumps({"RelatedTopics": list(related_topics)})


@dataclass(slots=True)
class StubEngine:
    name: str
    results: list[search.Result]

    def build_url(self, query: str) -> str:
        return f"https://{self.name}/{query}"

    def extract_results(self, html: str, limit: int) -> list[search.Result]:
        return self.results[:limit]


def test__search_outcomes__all_engines_fail__fail() -> None:
    engines = (
        StubEngine("A", []),
        StubEngine("B", []),
    )
    outcomes = list(
        search.search_outcomes(
            ["query"],
            engines=engines,
            fetch_html=lambda _: "<html>",
        )
    )
    assert outcomes[0].is_error
    error_msg = outcomes[0].error
    assert error_msg is not None
    assert "failed to search 'query'" in error_msg


def test__main__writes_errors__fail(monkeypatch: pytest.MonkeyPatch) -> None:
    stdout = io.StringIO()
    stderr = io.StringIO()
    outcome = search.QueryOutcome("q", None, "bad")

    monkeypatch.setattr(search, "search_outcomes", lambda *_: iter([outcome]))

    exit_code = search.main(stdin=[], stdout=stdout, stderr=stderr)
    assert exit_code == 1
    assert "bad" in stderr.getvalue()
    assert stdout.getvalue() == ""


def test__search_outcomes__engine_returns_results__success() -> None:
    engines = (
        StubEngine("good", [("Title", "https://example.com")]),
        StubEngine("unused", []),
    )
    outcomes = list(
        search.search_outcomes(
            ["foo"],
            engines=engines,
            fetch_html=lambda _: "<html>",
        )
    )
    assert not outcomes[0].is_error
    block = outcomes[0].block
    assert block is not None
    assert "Title" in block
    assert "good" in block


def test__main__writes_success__success(monkeypatch: pytest.MonkeyPatch) -> None:
    stdout = io.StringIO()
    stderr = io.StringIO()
    block = "Query: foo (engine: test)\n1. T — https://example.com\n"
    outcome = search.QueryOutcome("foo", block, None)

    monkeypatch.setattr(search, "search_outcomes", lambda *_: iter([outcome]))

    exit_code = search.main(stdin=[], stdout=stdout, stderr=stderr)
    assert exit_code == 0
    assert block in stdout.getvalue()
    assert stderr.getvalue() == ""


def test__search_outcomes__fetch_error__fail() -> None:
    engines = (StubEngine("good", []),)

    def failing_fetch(_: str) -> str:
        headers = Message()
        raise error.HTTPError("url", 500, "boom", headers, None)

    outcomes = list(
        search.search_outcomes(
            ["foo"],
            engines=engines,
            fetch_html=failing_fetch,
        )
    )
    assert outcomes[0].is_error
    error_msg = outcomes[0].error
    assert error_msg is not None
    assert "boom" in error_msg


def test__search_outcomes__rotates_default_engines(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class RecordingEngine:
        def __init__(self, name: str, results: list[search.Result]) -> None:
            self.name = name
            self._results = results

        def build_url(self, query: str) -> str:
            return f"https://example.com/{self.name}/{query}"

        def extract_results(self, html: str, limit: int) -> list[search.Result]:
            return self._results[:limit]

    engines: tuple[RecordingEngine, ...] = (
        RecordingEngine("alpha", [("alpha result", "https://alpha")]),
        RecordingEngine("beta", [("beta result", "https://beta")]),
    )
    cycle = search._EngineCycle(engines)
    monkeypatch.setattr(search, "_ENGINE_CYCLE", cycle)
    outcomes = list(
        search.search_outcomes(["first", "second"], fetch_html=lambda _: "<html>")
    )
    first_block = outcomes[0].block
    second_block = outcomes[1].block
    assert first_block is not None and "engine: alpha" in first_block
    assert second_block is not None and "engine: beta" in second_block


def test__search_outcomes__robot_detection__fail() -> None:
    engines = (StubEngine("guarded", []),)
    html = "Please complete the following challenge to confirm this search was made by a human."
    outcomes = list(
        search.search_outcomes(["query"], engines=engines, fetch_html=lambda _: html)
    )
    assert outcomes[0].is_error
    error_msg = outcomes[0].error
    assert error_msg is not None
    assert "robot verification" in error_msg


def test__google_engine__robot_challenge__fail(
    google_engine: search.SearchEngine,
) -> None:
    html = "Complete the following challenge to continue."
    outcome = next(
        search.search_outcomes(
            ["g"], engines=(google_engine,), fetch_html=lambda _: html
        )
    )
    assert outcome.is_error
    error_msg = outcome.error
    assert error_msg is not None
    assert error_msg.startswith("Google:")
    assert "robot verification required" in error_msg


def test__google_engine__http_error__fail(google_engine: search.SearchEngine) -> None:
    def failing_fetch(_: str) -> str:
        headers = Message()
        raise error.HTTPError("url", 503, "service unavailable", headers, None)

    outcome = next(
        search.search_outcomes(
            ["g"], engines=(google_engine,), fetch_html=failing_fetch
        )
    )
    assert outcome.is_error
    error_msg = outcome.error
    assert error_msg is not None
    assert error_msg.startswith("Google:")
    assert "service unavailable" in error_msg


def test__google_engine__no_supported_links__fail(
    google_engine: search.SearchEngine,
) -> None:
    html = _google_html([_google_anchor("Example", "/url?q=https://example.com")])
    outcome = next(
        search.search_outcomes(
            ["g"], engines=(google_engine,), fetch_html=lambda _: html
        )
    )
    assert outcome.is_error
    error_msg = outcome.error
    assert error_msg is not None
    assert error_msg.startswith("Google:")
    assert "no results" in error_msg


def test__google_engine__respects_limit__edge(
    google_engine: search.SearchEngine,
    google_limit_entries: list[GoogleEntry],
) -> None:
    html = _google_html_for_entries(google_limit_entries)
    results = google_engine.extract_results(html, limit=2)
    assert results == google_limit_entries[:2]


@pytest.mark.parametrize(
    ("raw_entries", "limit", "expected"),
    [
        pytest.param(
            [
                ("First Result", "https://example.com"),
                ("Duplicate Result", "https://example.com"),
            ],
            5,
            [
                ("First Result", "https://example.com"),
                ("Duplicate Result", "https://example.com"),
            ],
            id="duplicates",
        ),
        pytest.param(
            [("   Example Title   ", "https://example.com")],
            5,
            [("Example Title", "https://example.com")],
            id="whitespace",
        ),
        pytest.param(
            [("Rock &amp; Roll", "https://example.com")],
            5,
            [("Rock & Roll", "https://example.com")],
            id="entities",
        ),
    ],
)
def test__google_engine__parses_entries__edge(
    google_engine: search.SearchEngine,
    raw_entries: list[GoogleEntry],
    limit: int,
    expected: list[GoogleEntry],
) -> None:
    html = _google_html_for_entries(raw_entries)
    results = google_engine.extract_results(html, limit=limit)
    assert results == expected


def test__google_engine__formats_success_block__success(
    google_engine: search.SearchEngine,
) -> None:
    html = _google_html([_google_anchor("Example Title", "https://example.com")])
    outcome = next(
        search.search_outcomes(
            ["python"], engines=(google_engine,), fetch_html=lambda _: html
        )
    )
    assert not outcome.is_error
    block = outcome.block
    assert block is not None
    assert "Query: python (engine: Google)" in block
    assert "1. Example Title — https://example.com" in block


def test__google_engine__build_url_encodes_query__success(
    google_engine: search.SearchEngine,
) -> None:
    engine_type = type(google_engine)
    url = engine_type().build_url("c++ test")
    assert "q=c%2B%2B+test" in url


def test__duckduckgo_api_engine__extracts_related_topics__success(
    duckduckgo_api_engine: search.SearchEngine,
) -> None:
    entries = [
        ("Example One", "https://example.com/1"),
        ("Example Two", "https://example.com/2"),
    ]
    payload = _ddg_api_payload(_ddg_topic(text, url) for text, url in entries)
    results = duckduckgo_api_engine.extract_results(payload, limit=5)
    assert results == entries


def test__duckduckgo_api_engine__extracts_nested_topics__success(
    duckduckgo_api_engine: search.SearchEngine,
) -> None:
    entries = [
        ("Nested One", "https://example.com/n1"),
        ("Nested Two", "https://example.com/n2"),
    ]
    payload = _ddg_api_payload(
        [
            _ddg_category("Category", (_ddg_topic(text, url) for text, url in entries)),
        ]
    )
    results = duckduckgo_api_engine.extract_results(payload, limit=5)
    assert results == entries


def test__duckduckgo_api_engine__empty_payload__fail(
    duckduckgo_api_engine: search.SearchEngine,
) -> None:
    payload = _ddg_api_payload([])
    results = duckduckgo_api_engine.extract_results(payload, limit=3)
    assert results == []


def test__default_engines__includes_google__edge() -> None:
    names = [engine.name for engine in search.DEFAULT_ENGINES]
    assert "Google" in names
    assert "DuckDuckGo API" in names


def test__search_outcomes__default_cycle_includes_all_engines__success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[str] = []

    def recording_run(
        query: str, engine: search.SearchEngine, fetch_html: search.FetchHtml
    ) -> tuple[str | None, str | None]:
        captured.append(engine.name)
        return None, f"{engine.name}: no results"

    monkeypatch.setattr(search, "_run_engine", recording_run)
    outcomes = list(search.search_outcomes(["query"], fetch_html=lambda _: ""))
    assert outcomes[0].is_error
    expected_order = [engine.name for engine in search.DEFAULT_ENGINES]
    assert captured == expected_order


def test__bing_rss_engine__parses_items__success(bing_sample_feed: str) -> None:
    engine = search.BingRssEngine()
    results = engine.extract_results(bing_sample_feed, limit=5)
    expected_pairs = [
        ("Example Title", "https://example.com"),
        ("Another Example", "https://example.org"),
    ]
    assert results == expected_pairs
