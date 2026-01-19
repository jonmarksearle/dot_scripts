# weather.sdd.md (System Design Document)

## 1. Goal
Implement a robust, extensible CLI tool for hourly coastal weather and tide forecasts, using a decentralized provider model with rank-based data consolidation.

## 2. Architectural Overview
*   **Concurrency:** Use `asyncio.gather` to fetch from all providers in parallel for "Always Fresh" data.
*   **Consolidation:** A single `HourlyWeather` dataclass is used for both raw and merged data. Merging follows a "First Non-None by Rank Wins" field-level strategy.
*   **Decentralized Location:** Each provider independently resolves the raw location string (e.g., "Aspendale") to its own internal identifiers.
*   **Fault Tolerance:** Provider failures are logged to `stderr` but do not stop the overall execution if other data is available.

## 3. Core Data Model

```python
from dataclasses import dataclass
from typing import Optional, Protocol, Iterator, Self

@dataclass(frozen=True, slots=True)
class HourlyWeather:
    rank: int            # Lower number = higher precedence
    date: str            # e.g., "2026-01-19"
    hour: str            # e.g., "10:00 AM"
    condition: Optional[str] = None      # e.g., "☀️ Clear"
    temp: Optional[int] = None           # Rounded Celsius
    feels_like: Optional[int] = None     # Rounded Celsius
    wind_speed: Optional[int] = None     # km/h
    wind_dir: Optional[str] = None       # e.g., "SW"
    wind_arrow: Optional[str] = None     # e.g., "↗"
    tide_height: Optional[float] = None  # Meters (1 decimal)
    tide_tag: Optional[str] = None       # "HIGH", "LOW", or None
    rain_prob: Optional[int] = None      # Percentage
    uv_index: Optional[int] = None       # Integer
    humidity: Optional[int] = None       # Percentage
```

## 4. Provider Interface

```python
class WeatherProvider(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def rank(self) -> int: ...

    async def fetch_weather(self, location: str, days_extra: int) -> Iterator[HourlyWeather]:
        """Fetch and yield hourly weather objects for the given location/range."""
        ...
```

## 5. Logic Components

### 5.1 Consolidation Engine
*   **Logic:** `def consolidate(data_sets: List[Iterable[HourlyWeather]]) -> List[HourlyWeather]`
*   **Strategy:** Group all input objects by `(date, hour)`.
*   **Field Merging:** For each field in the dataclass, iterate through the grouped objects sorted by `rank` (ascending). Pick the first non-`None` value.
*   **Tide Extremum Calculation:** 
    *   After field merging, iterate through the chronological list of `tide_height` values.
    *   **High Tide:** `height > previous` AND `height >= next`.
    *   **Low Tide:** `height < previous` AND `height <= next`.
    *   Tie-breaker: If a plateau exists, the first hour in the plateau gets the tag.

### 5.2 Visual Formatter
*   **Formatting:** Fixed-width columns for vertical alignment.
*   **Wind Arrows:** Point **TO** the direction of flow (e.g., N wind blows South -> `↓`).
*   **Rounding:** All numeric values are rounded to integers (except Tide height at 1 decimal).

## 6. CLI Execution Flow
1. Parse `[DAYS_EXTRA]` and `[LOCATION]`.
2. Instantiate all `WeatherProvider` implementations (BOM, WillyWeather, TimeandDate, etc.).
3. Execute `asyncio.gather(*[p.fetch_weather(...) for p in providers])`.
4. Pass results to `ConsolidationEngine`.
5. Apply Tide Extremum calculations to the consolidated list.
6. Print output grouped by date headers.
