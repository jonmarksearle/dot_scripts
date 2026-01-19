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
    tide_height: Optional[float] = None  # Meters (1 decimal)
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
*   **Responsibility:** Merges multiple `HourlyWeather` streams into a single list.
*   **Grouping:** Group all input objects by the tuple `(date, hour)`.
*   **Field Merging:** For each hour group, iterate through fields (temp, wind, etc.). For each field, select the value from the provider with the **lowest rank** that is not `None`.
*   **Error Resilience:** If a provider fails during the `asyncio.gather` phase, the error must be printed to `stderr`, and the consolidation must proceed using the data from the remaining successful providers. The program must not exit unless *all* providers fail or a critical configuration error occurs.

### 5.2 Visual Formatter
*   **Responsibility:** Renders the final terminal line by deriving visual elements.
*   **Wind Arrow:** Calculated from `wind_dir`. Arrows point **TO** the direction of flow (e.g., N wind blows South -> `↓`).
*   **Tide Tag:** Calculated by comparing the `tide_height` of the current hour with its immediate neighbors in the consolidated sequence.
    *   **High Tide:** `height > previous` AND `height >= next`.
    *   **Low Tide:** `height < previous` AND `height <= next`.
    *   **Tie-breaker:** First hour in a plateau gets the tag.
*   **Formatting:** Fixed-width columns for vertical alignment.
*   **Rounding:** All numeric values are rounded to integers (except Tide height at 1 decimal).

## 6. CLI Execution Flow & Libraries
*   **Libraries:**
    *   **Typer:** For strict CLI argument parsing and help generation.
    *   **Rich:** For rendering the final output lines, ensuring consistent styling (colors, emoji handling) and potentially handling the fixed-width columns via a `Table` or formatted `Text` objects.
*   **Flow:**
1.  `Typer` entry point parses `[DAYS_EXTRA]` and `[LOCATION]`.
2. Instantiate all `WeatherProvider` implementations (BOM, WillyWeather, TimeandDate, etc.).
3. Execute `asyncio.gather(*[p.fetch_weather(...) for p in providers])`.
4. Pass results to `ConsolidationEngine`.
5. Apply Tide Extremum calculations to the consolidated list.
6. Print output grouped by date headers.
