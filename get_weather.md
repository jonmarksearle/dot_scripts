# get_weather.md (Specification)

## Overview
A Python script (`.scripts/get_weather.py`) that aggregates weather forecasts from multiple public sources concurrently to provide a consensus forecast (up to 14 days) for an Australian location.

## Usage
```bash
uv run .scripts/get_weather.py "Aspendale, VIC"
```

## Requirements

1.  **Input:**
    *   Location string (e.g., "Aspendale, VIC"). Defaults to "Aspendale, VIC".

2.  **Output:**
    *   A JSON list of objects to stdout.
    *   **Fields (Nullable):**
        *   `location`: String (Resolved Name).
        *   `date`: String ("YYYY-MM-DD", Local Date).
        *   `min_temp`: Float | Null (Consensus Mean, Celsius).
        *   `max_temp`: Float | Null (Consensus Mean, Celsius).
        *   `min_wind_kmh`: Float | Null (Absolute Min across sources).
        *   `max_wind_kmh`: Float | Null (Absolute Max across sources).
        *   `wind_direction`: List[String] | Null (Sequence of observed directions, e.g., `["N", "SW"]`).
        *   `rain_prob`: Float | Null (Max probability, 0-100%).
        *   `prognosis`: String | Null (Consensus Mode).
        *   `sources`: List[str] (Names of providers that contributed to *this specific date*).

3.  **Forecast Horizon & Time Authority:**
    *   **Horizon:** Up to 14 Days.
    *   **Sparse Output:** Dates with *zero* valid data are omitted. Dates with partial data (e.g., Temp only) are included with nulls.
    *   **Authority:** `ForecastWindow` determines dates.

4.  **Concurrency & Reliability (Hard Limits):**
    *   **Total Script Deadline:** 20 seconds.
        *   *Policy:* Cancel pending tasks on deadline. Emit available partials.
        *   *Logging:* Errors to `stderr`. Exit 1 only if NO data.
    *   **Per-Provider Budget:** 12 seconds.
    *   **Retry:** Max 3, Exp Backoff (Base 0.5s), Jitter. Stop if budget < 0.5s.

5.  **Providers:**
    *   **OpenMeteoProvider** (Forecast).
    *   **MeteostatProvider** (Observation).
    *   **WttrProvider** (Forecast).
    *   **BomFtpProvider** (Forecast).

6.  **Consensus Logic (Policy):**
    *   **Grouping:** By Date.
    *   **Aggregation:**
        *   **Temp:** Mean of valid values (Outliers > 1.5 sigma removed if count > 2).
        *   **Wind Speed:** Range [Min, Max] of valid values.
        *   **Wind Direction:** Unique set of all valid directions seen (sorted alphabetically).
        *   **Rain Prob:** Max of valid probabilities.
        *   **Prognosis:** Mode (Tie-breaker: Severity `STORM > SNOW > RAIN > CLOUDY > CLEAR`).
