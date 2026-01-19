# weather.rdd (Requirements Document Definition)

## 1. Goal
A CLI tool to provide highly actionable hourly weather and tide forecasts for athletes (cyclists, swimmers, runners) in Aspendale and surrounding coastal areas.

## 2. CLI Input Specification
The tool is invoked as `weather` with optional arguments for timeframe and location.

*   **Syntax:** `weather [DAYS_EXTRA] [LOCATION]`
*   **DAYS_EXTRA:** Number of additional days beyond today (default: `1`).
    *   `0`: Remainder of today only.
    *   `1`: Remainder of today + tomorrow.
    *   `2`: Remainder of today + next two days.
*   **LOCATION:** Name of the location (default: `"Aspendale"`).
*   **Examples:**
    *   `weather` -> Today and tomorrow for Aspendale.
    *   `weather 0` -> Today only for Aspendale.
    *   `weather 2 "St Kilda"` -> Today and next two days for St Kilda.

## 3. Data Requirements
Each hourly block must contain the following comprehensive data set:
*   **Time:** The hour (e.g., `10:00 AM`).
*   **Condition:** Emoji + Text (e.g., `☀️ Clear`, `🌧️ Light Rain`).
*   **Temperature:** Actual temperature in Celsius.
*   **"Feels Like":** Apparent temperature in Celsius.
*   **Wind:** Speed in km/h and Direction using both an arrow and compass point (e.g., `↙ SW`, `↑ N`).
*   **Tide:** Tide height in meters, integrated into the chronological flow.
*   **Rain Probability:** Percentage chance of rain.
*   **UV Index:** Current UV level.
*   **Humidity:** Percentage.

## 4. Output Format
*   **Structure:** No summary section; straight into chronological hourly lines grouped by date.
*   **Style:** Single line per hour, space-separated for readability.
*   **Date Header:** Each day starts with a header (e.g., `--- Monday 19 Jan ---`).
*   **Line Format:**
    `[Time]  [Condition]  [Temp]([Feels])  [WindArrow] [WindDir] [WindSpeed]  [Tide] [[TIDE_TAG]]  Rain:[Rain%]  UV:[UV]  Hum:[Hum%]`
*   **Example Line:**
    `10:00 AM  ☀️ Clear  22°C (20°C)  ↙ SW 15km/h  0.8m [HIGH]  Rain:0%  UV:8  Hum:60%`
*   **Tide Integration (Hybrid):** 
    *   Tide height is shown for every hour.
    *   The hour block containing a High or Low tide extreme must be marked with `[HIGH]` or `[LOW]`.
    *   Hours without an extreme have no tag.

## 5. Robustness & Architectural Requirements
*   **Multiple Sources:** The system must be capable of fetching data from multiple providers (e.g., BOM, WillyWeather, TimeandDate) to ensure robustness.
*   **Seams:** Weather providers must be implemented using a Python `Protocol` class, allowing for a list of one or more forecast providers to be processed.
*   **Always Fresh:** No caching; the tool must fetch current data on every execution.

## 6. BDD Scenarios

### Scenario 1: Output Density and Date Headers
**Given** the current date is Monday 19 Jan and I want a 1-day forecast
**When** I run `weather 0`
**Then** the first line should be `--- Monday 19 Jan ---`
**And** each subsequent line should represent one hour in the prescribed one-line format
**And** there should be no empty lines between the header and the first hour

### Scenario 2: High/Low Tide Marker Implementation
**Given** a Low Tide occurs at 8:15 AM and a High Tide occurs at 2:34 PM
**When** the hourly blocks are displayed
**Then** the `08:00 AM` line should include the tag `[LOW]`
**And** the `02:00 PM` line should include the tag `[HIGH]`
**And** the `10:00 AM` line (not an extreme) should have no tide tag

### Scenario 3: Visuals - North Wind
**Given** a wind forecast of "North" (blowing South)
**When** the line is rendered
**Then** the wind arrow should be `↓` (pointing South)
**And** the text should be `N`

### Scenario 4: Visuals - South-West Wind
**Given** a wind forecast of "South-West" (blowing North-East)
**When** the line is rendered
**Then** the wind arrow should be `↗` (pointing North-East)
**And** the text should be `SW`

### Scenario 5: Visuals - East Wind
**Given** a wind forecast of "East" (blowing West)
**When** the line is rendered
**Then** the wind arrow should be `←` (pointing West)
**And** the text should be `E`

### Scenario 6: Visuals - West Wind
**Given** a wind forecast of "West" (blowing East)
**When** the line is rendered
**Then** the wind arrow should be `→` (pointing East)
**And** the text should be `W`

### Scenario 7: Visuals - North-East Wind
**Given** a wind forecast of "North-East" (blowing South-West)
**When** the line is rendered
**Then** the wind arrow should be `↙` (pointing South-West)
**And** the text should be `NE`

### Scenario 8: Visuals - South-East Wind
**Given** a wind forecast of "South-East" (blowing North-West)
**When** the line is rendered
**Then** the wind arrow should be `↖` (pointing North-West)
**And** the text should be `SE`

### Scenario 9: Visuals - North-West Wind
**Given** a wind forecast of "North-West" (blowing South-East)
**When** the line is rendered
**Then** the wind arrow should be `↘` (pointing South-East)
**And** the text should be `NW`

### Scenario 10: Visuals - South Wind
**Given** a wind forecast of "South" (blowing North)
**When** the line is rendered
**Then** the wind arrow should be `↑` (pointing North)
**And** the text should be `S`

### Scenario 11: Visuals - Standard Temperature
**Given** a temperature of 22.5°C
**When** the line is rendered
**Then** the temperature section should be formatted as `23°C` (rounded)

### Scenario 12: Visuals - Negative Temperature
**Given** a temperature of -2.4°C
**When** the line is rendered
**Then** the temperature section should be formatted as `-2°C`

### Scenario 13: Visuals - Zero Temperature
**Given** a temperature of 0.0°C
**When** the line is rendered
**Then** the temperature section should be formatted as `0°C`

### Scenario 14: Visuals - High Heat Temperature
**Given** a temperature of 41.8°C
**When** the line is rendered
**Then** the temperature section should be formatted as `42°C`

### Scenario 15: CLI - Default (Today + Tomorrow)
**Given** the user runs `weather`
**Then** the output should cover the remainder of Today and all of Tomorrow
**And** the location should be "Aspendale"

### Scenario 16: CLI - Today Only
**Given** the user runs `weather 0`
**Then** the output should cover only the remainder of Today
**And** the location should be "Aspendale"

### Scenario 17: CLI - Extended Forecast (2 Days)
**Given** the user runs `weather 2`
**Then** the output should cover the remainder of Today, Tomorrow, and the Day After (3 days span)
**And** the location should be "Aspendale"

### Scenario 18: CLI - Long Range (5 Days)
**Given** the user runs `weather 5`
**Then** the output should cover the remainder of Today plus the next 5 days
**And** the location should be "Aspendale"

### Scenario 19: CLI - Today Only with Location Override
**Given** the user runs `weather 0 "St Kilda"`
**Then** the output should cover only the remainder of Today
**And** the location should be "St Kilda"

### Scenario 20: CLI - Extended Forecast with Location Override
**Given** the user runs `weather 2 "Portsea"`
**Then** the output should cover Today + 2 extra days
**And** the location should be "Portsea"

### Scenario 21: CLI - Location Only (Implicit Time)
**Given** the user runs `weather "Geelong"`
**Then** the output should cover Today + Tomorrow (default `1`)
**And** the location should be "Geelong"
