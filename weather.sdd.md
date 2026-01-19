# weather.sdd.md (System Design Document)

## 1. Goal
Implement a robust, extensible CLI tool for hourly coastal weather and tide forecasts, using a decentralized provider model with rank-based data consolidation.

## 2. Architectural Overview
*   **Concurrency:** Use `asyncio.gather` to fetch from all providers in parallel for "Always Fresh" data.
*   **Consolidation:** A single `HourlyWeather` dataclass is used for both raw and merged data. Merging follows a "First Non-None by Rank Wins" field-level strategy.
*   **Decentralized Location:** Each provider independently resolves the raw location string (e.g., "Aspendale") to its own internal identifiers.
*   **Fault Tolerance:** Provider failures are logged to `stderr` but do not stop the overall execution if other data is available.

## 3. Core Data Model (Pydantic)

Using `pydantic.BaseModel` for automatic validation and type safety.

```python
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from enum import StrEnum

class WindDirection(StrEnum):
    N = "↓ N"
    NE = "↙ NE"
    E = "← E"
    SE = "↖ SE"
    S = "↑ S"
    SW = "↗ SW"
    W = "→ W"
    NW = "↘ NW"
    VAR = "• VAR"

class WeatherCondition(StrEnum):
    CLEAR = "☀️ Clear"
    CLOUDY = "☁️ Cloudy"
    PARTLY_CLOUDY = "⛅ Partly Cloudy"
    RAIN = "🌧️ Rain"
    STORM = "⛈️ Storm"
    SNOW = "🌨️ Snow"
    UNKNOWN = "❓ Unknown"

class HourlyWeather(BaseModel):
    rank: int = Field(ge=1)
    date: str
    hour: str
    condition: Optional[WeatherCondition] = None
    temp: Optional[int] = Field(None, ge=-50, le=60)
    feels_like: Optional[int] = Field(None, ge=-50, le=60)
    wind_speed: Optional[int] = Field(None, ge=0)
    wind_dir: Optional[WindDirection] = None
    tide_height: Optional[float] = None
    rain_prob: Optional[int] = Field(None, ge=0, le=100)
    uv_index: Optional[int] = Field(None, ge=0)
    humidity: Optional[int] = Field(None, ge=0, le=100)
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
*   **Wind:** Displayed as the string value of `wind_dir`.
*   **Tide Tag:** Calculated by comparing the `tide_height` of the current hour with its immediate neighbors in the consolidated sequence.
    *   **High Tide:** `height > previous` AND `height >= next`.
    *   **Low Tide:** `height < previous` AND `height <= next`.
    *   **Tie-breaker:** First hour in a plateau gets the tag.
*   **Formatting:** Fixed-width columns for vertical alignment.
*   **Rounding:** All numeric values are rounded to integers (except Tide height at 1 decimal).

## 6. Adapters (Peripheral/I-O)
*   **`BomAdapter` (Rank 1)**: Primary authority for weather condition, temperature, and rainfall. Fetches from the BOM accessible forecast or API.
*   **`WillyWeatherAdapter` (Rank 1 for Tides)**: Specialized provider for tide heights and extremes.
*   **`OpenMeteoAdapter` (Rank 2)**: Reliable secondary source for weather metadata (UV, Humidity, Feels Like) and fallback for primary weather data.

## 7. CLI Execution Flow & Libraries
*   **Libraries:**
    *   **Typer:** For strict CLI argument parsing and help generation.
    *   **Rich:** For rendering the final output lines, ensuring consistent styling (colors, emoji handling) and potentially handling the fixed-width columns via a `Table` or formatted `Text` objects.
*   **Flow:**
1.  `Typer` entry point parses `[DAYS_EXTRA]` and `[LOCATION]`.
2. Instantiate all `WeatherProvider` implementations (`BomAdapter`, `WillyWeatherAdapter`, `OpenMeteoAdapter`).
3. Execute `asyncio.gather(*[p.fetch_weather(...) for p in providers])`.
4. Pass results to `ConsolidationEngine`.
5. Apply Tide Extremum calculations to the consolidated list.
6. Print output grouped by date headers using `Rich`.

## 8. Prior Art & Legacy Insights (`get_weather.py`)
*   **Grouping Strategy:** The legacy script uses `itertools.groupby` effectively for date-based aggregation. We will adapt this for `(date, hour)` grouping in the `ConsolidationEngine`.
*   **Statistical Robustness:** The legacy script employs `mean` and `stdev` for filtering outliers. While our primary strategy is "Rank Precedence," we may incorporate simple mean averaging for non-primary fields (e.g., if Rank 1 is missing, average Rank 2 and 3) if strictly necessary, though strict fallback is preferred for predictability.
*   **Enums:** The existing `WeatherCode` Enum aligns closely with our `WeatherCondition`. We will ensure our new Enums are compatible or superior in expressiveness.

## 9. Provider Landscape (Selection & Analysis)

| Rank | Provider | Focus | Key Advantage | Data Type | Auth | Endpoint | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | BOM | All | Official, AU accuracy | HTML/XML | None | `http://www.bom.gov.au/places/...` | MVP |
| 2 | WillyWeather | Tides/Coastal | Aspendale specific | HTML | None | `https://tides.willyweather.com.au/...` | MVP |
| 3 | OpenMeteo | Meta (UV/Hum) | High-speed, modern | JSON | None | `https://api.open-meteo.com/v1/forecast` | MVP |
| 4 | Seabreeze | Marine/Wind | Local Melb. sailing | HTML | None | `https://www.seabreeze.com.au/...` | Future |
| 5 | TimeAndDate | Astro/Meta | Clean formatting | HTML | None | `https://www.timeanddate.com/weather/...` | Future |
| 6 | StormGlass | Marine/Tides | Global maritime data | JSON | Key | `https://api.stormglass.io/v2/` | Future |
| 7 | WorldTides | Tides | Dedicated Tide API | JSON | Key | `https://www.worldtides.info/api/v3` | Future |
| 8 | OpenWeatherMap | General | Huge redundancy | JSON | Key | `https://api.openweathermap.org/data/3.0/` | Future |
| 9 | WeatherAPI | General | Very stable JSON | JSON | Key | `https://api.weatherapi.com/v1/` | Future |
| 10 | MetEye | Localized | 6km grid precision | HTML | None | `http://www.bom.gov.au/australia/meteye/` | Future |
| 11 | Wttr.in | Backup | Simple text fallback | Text | None | `https://wttr.in/` | Future |
| 12 | BayWx | Port Phillip | Live Bay conditions | HTML | None | `http://www.baywx.com.au/` | Future |

--------------------------------------------
## ADENDUM: HourlyWeather as a dataclass

```python
from dataclasses import dataclass
from typing import Optional
from enum import StrEnum
from datetime import datetime

@dataclass(frozen=True, slots=True)
class HourlyWeather:
    rank: int
    date: str
    hour: str
    condition: Optional[WeatherCondition] = None
    temp: Optional[int] = None
    feels_like: Optional[int] = None
    wind_speed: Optional[int] = None
    wind_dir: Optional[WindDirection] = None
    tide_height: Optional[float] = None
    rain_prob: Optional[int] = None
    uv_index: Optional[int] = None
    humidity: Optional[int] = None

    def __post_init__(self):
        if self.rank < 1:
            raise ValueError(f"rank must be >= 1, got {self.rank}")
        
        try:
            datetime.strptime(self.date, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid date format: {self.date}. Expected YYYY-MM-DD")

        self._check_range("temp", self.temp, -50, 60)
        self._check_range("feels_like", self.feels_like, -50, 60)
        self._check_range("wind_speed", self.wind_speed, 0, 300)
        self._check_range("rain_prob", self.rain_prob, 0, 100)
        self._check_range("humidity", self.humidity, 0, 100)
        self._check_range("uv_index", self.uv_index, 0, 20)

    def _check_range(self, name: str, val: Optional[int], vmin: int, vmax: int):
        if val is not None and not (vmin <= val <= vmax):
            raise ValueError(f"{name} must be between {vmin} and {vmax}, got {val}")
```
