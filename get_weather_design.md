# get_weather_design.md (Design)

## 1. Domain Models (Immutables)
*   `LocationInfo`: `(name: str, lat: float, lon: float, state: str, timezone: str)`
*   `ForecastWindow`: `(start_date: date, end_date: date, dates: List[date])`
*   `ProviderCapabilities`: `(is_forecast: bool, max_horizon_days: int)`
*   `DailyData`: 
    *   `date: date`, `source: str`
    *   `min_temp: Optional[float]`, `max_temp: Optional[float]`
    *   `min_wind: Optional[float]`, `max_wind: Optional[float]`
    *   `direction: Optional[str]`, `prognosis: Optional[str]`
    *   `rain_prob: Optional[float]`
*   `ConsensusForecast`: Output Schema (All fields nullable except date/location/sources). Wind direction is `Optional[List[str]]`.

## 2. Core Logic Components (Pure)

### `ConsensusEngine`
*   **Responsibility:** Aggregates data per `ForecastWindow`.
*   **Key Method:** `calculate_consensus(window: ForecastWindow, all_data: List[DailyData], policy: ConsensusPolicy) -> List[ConsensusForecast]`
    *   *Logic:* Group by Date. Sparse output (omit dates with all-None data).
    *   *Aggregation:* Ignore `None` values. Apply Outlier logic to Temps. Union/Sort Wind Directions. Max Rain Prob. Mode Prognosis.

### `BomXmlParser`
*   **Responsibility:** XML Parsing & Deterministic Station Selection.
*   **Selection:** Haversine distance, < 50km threshold.

### `WeatherTaxonomy`
*   **Responsibility:** Maps provider-specific strings/codes to standardized Enums.
*   **Mapping:** WMO Codes, Wttr strings, BOM strings -> `{CLEAR, CLOUDY, RAIN, STORM, SNOW}`.

## 3. Provider Components (Async I/O)

### Interface: `WeatherProvider(Protocol)`
*   `capabilities: ProviderCapabilities`
*   `async def fetch(self, loc: LocationInfo, window: ForecastWindow, remaining_budget: float) -> List[DailyData]`
*   **Constraints:**
    *   `attempt_timeout = min(config_timeout, remaining_budget)`.
    *   Check `remaining_budget > 0.5s` before attempting.

### Implementations:
*   `OpenMeteoProvider`, `MeteostatProvider`, `WttrProvider`, `BomFtpProvider`.

## 4. Orchestration

### `WeatherOrchestrator`
*   **Responsibility:**
    1. Resolve Location.
    2. Construct `ForecastWindow`.
    3. `ProviderRunner`: Execute `fetch()` with Global (20s) and Provider (12s) deadlines.
        *   Log exceptions to `stderr`.
    4. Call `ConsensusEngine`.

## 5. TDD Sequence (Test Plan)
1.  **`WeatherTaxonomy`**: Test mapping tables & severity ranking.
2.  **`ConsensusEngine`**: Test sparse output, outlier logic, and field aggregation.
3.  **`BomXmlParser`**: Test deterministic selection.
4.  **`LocationResolver`**: Test Geocoding + TZ extraction.
5.  **Providers**: Test individual fetch with Budget Depletion logic mocked.
6.  **`WeatherOrchestrator`**: Test Global Timeout (partial success) and Provider Budget cutoffs.
7.  **`main`**: Integration.


## 6 Steps and TipToes

Overall Project Steps
   * Step 1: Write get_weather.md (Specification) and get_weather_design.md.
   * Step 2: Write .scripts/tests/test_get_weather.py (Tests).
   * Step 3: TDD LOOP (Implementation).
   * Step 4: Refactor LOOP (Improvement).

  ---

  Step 3: TDD Loop TipToes
   * TipToe 0: Make sure each test is disabled using skipped decorator. Run to confirm baseline GREEN.
   * TipToe 1: Enable the first test. Run uvx pytest to confirm RED.
   * TipToe 2: Implement the minimum code to make that test pass (GREEN).
   * TipToe 3: Enable the next test. Run uvx pytest to confirm RED.
   * TipToe 4: Implement the minimum code to make that second test pass (GREEN).
   * TipToe 5: Git Commit and Repeat TipToe 3 and TipToe 4 until all tests pass individually.
   * TipToe 6: Remove all skipped decorators. Run uvx pytest to ensure the entire suite is GREEN.

  ---

  Step 4: Refactor Loop TipToes
   * TipToe 7: Refactor code in get_weather.py to improve clarity and maintainability, ensuring all tests stay GREEN.
   * TipToe 8: Git Commit and Repeat TipToe 7 until satisfied with code quality.

