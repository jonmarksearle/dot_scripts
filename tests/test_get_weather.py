#!/usr/bin/env python3
import sys
import pytest
from pathlib import Path
from datetime import date, timedelta
from typing import List, Optional

# --- Setup Import Path for Script ---
SCRIPT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SCRIPT_DIR))

try:
    import get_weather
except ImportError:
    get_weather = None # type: ignore

# --- Fixtures & Helpers ---

@pytest.fixture
def base_date() -> date:
    return date(2025, 12, 25)

class ForecastWindowStub:
    def __init__(self, dates: List[date]):
        self.dates = dates

@pytest.fixture
def window_stub(base_date: date) -> ForecastWindowStub:
    dates = [base_date + timedelta(days=i) for i in range(14)]
    return ForecastWindowStub(dates)

def mk_daily(
    d: date, 
    src: str = "Test", 
    min_t: Optional[float] = 20.0, max_t: Optional[float] = 30.0, 
    min_w: Optional[float] = 10.0, max_w: Optional[float] = 20.0, 
    w_dir: Optional[str] = "N", prog: Optional[str] = "CLEAR",
    rain_p: Optional[float] = 0.0
) -> get_weather.DailyData: # type: ignore
    return get_weather.DailyData(
        date=d, source=src, 
        min_temp=min_t, max_temp=max_t, 
        min_wind=min_w, max_wind=max_w, 
        direction=w_dir, prognosis=prog,
        rain_prob=rain_p
    )

def mk_empty_daily(d: date, src: str) -> get_weather.DailyData: # type: ignore
    """Helper for a daily record with ALL fields as None."""
    return mk_daily(d, src, None, None, None, None, None, None, None)


def mk_daily_from_kwargs(base: date, raw_kwargs) -> get_weather.DailyData: # type: ignore
    kwargs = dict(raw_kwargs)
    offset = kwargs.pop("offset", 0)
    d = base + timedelta(days=offset)
    if kwargs.pop("all_none", False):
        return mk_empty_daily(d, str(kwargs.get("src", "Test")))
    return mk_daily(d, **kwargs)


def mk_daily_list(base: date, *days_kwargs) -> List[get_weather.DailyData]: # type: ignore
    """Create a list of DailyData from terse dicts (offset, src, etc)."""
    return [mk_daily_from_kwargs(base, raw_kwargs) for raw_kwargs in days_kwargs]

def test__taxonomy__map_wmo__unknown_code__fail() -> None:
    """Ensure unknown WMO codes raise ValueError."""
    with pytest.raises(ValueError, match=r"Unknown WMO code"):
        get_weather.WeatherTaxonomy.map_wmo_code(9999)

@pytest.mark.parametrize("code,expected", [
    (0, "CLEAR"), (1, "CLEAR"), (3, "CLOUDY"), (61, "RAIN"), (71, "SNOW"), (95, "STORM")
])
def test__taxonomy__map_wmo__success(code: int, expected: str) -> None:
    """Ensure WMO codes map to standard taxonomy."""
    assert get_weather.WeatherTaxonomy.map_wmo_code(code) == expected

@pytest.mark.parametrize("text,expected", [
    ("Sunny", "CLEAR"), ("Partly cloudy", "CLOUDY"), ("Patchy rain nearby", "RAIN")
])
def test__taxonomy__map_wttr__success(text: str, expected: str) -> None:
    """Ensure wttr.in strings map to standard taxonomy."""
    assert get_weather.WeatherTaxonomy.map_wttr_text(text) == expected

@pytest.mark.parametrize("text,expected", [
    ("Fine", "CLEAR"), ("Cloudy", "CLOUDY"), ("Showers", "RAIN"), ("Possible storm", "STORM")
])
def test__taxonomy__map_bom__success(text: str, expected: str) -> None:
    """Ensure BOM text strings map to standard taxonomy."""
    assert get_weather.WeatherTaxonomy.map_bom_text(text) == expected

@pytest.mark.parametrize("candidates,expected", [
    (["CLEAR", "RAIN"], "RAIN"),
    (["SNOW", "RAIN"], "SNOW"),
    (["STORM", "SNOW"], "STORM"),
    (["CLOUDY", "CLEAR"], "CLOUDY"),
    (["RAIN", "CLOUDY"], "RAIN"),
])
def test__taxonomy__severity_ranking__success(candidates: list[str], expected: str) -> None:
    """Ensure pick_worst correctly resolves pairwise severity (STORM > SNOW > RAIN > CLOUDY > CLEAR)."""
    assert get_weather.WeatherTaxonomy.pick_worst(candidates) == expected

# --- ConsensusEngine Tests: Logic & Sparse Output ---

def test__consensus__empty_input__success(window_stub: ForecastWindowStub) -> None:
    assert get_weather.ConsensusEngine.calculate_consensus(window_stub, [], get_weather.ConsensusPolicy()) == []

@pytest.mark.skip(reason="TDD TipToe 0")
def test__consensus__date_omission__all_fields_none__success(window_stub: ForecastWindowStub, base_date: date) -> None:
    """Ensure a date is OMITTED if all its reports contain ONLY None values."""
    data = mk_daily_list(base_date, {"min_t": 20}, {"offset": 1, "all_none": True})
    results = get_weather.ConsensusEngine.calculate_consensus(window_stub, data, get_weather.ConsensusPolicy())
    assert len(results) == 1
    assert results[0].date == str(base_date)

@pytest.mark.skip(reason="TDD TipToe 0")
def test__consensus__sources_contribution__ignore_empty__success(window_stub: ForecastWindowStub, base_date: date) -> None:
    """Ensure a source is NOT listed if it contributes no valid data."""
    data = mk_daily_list(base_date, {"src": "A"}, {"src": "B", "all_none": True})
    res = get_weather.ConsensusEngine.calculate_consensus(window_stub, data, get_weather.ConsensusPolicy())[0]
    assert res.sources == ["A"]

# --- ConsensusEngine Tests: Aggregation Logic (Ignore None) ---

@pytest.mark.skip(reason="TDD TipToe 0")
def test__consensus__aggregation__temp__ignore_none__success(window_stub: ForecastWindowStub, base_date: date) -> None:
    """Ensure None values in temp are ignored for mean calculation."""
    data = mk_daily_list(base_date, {"min_t": 20}, {"min_t": None})
    res = get_weather.ConsensusEngine.calculate_consensus(window_stub, data, get_weather.ConsensusPolicy())[0]
    assert res.min_temp == 20.0

@pytest.mark.skip(reason="TDD TipToe 0")
def test__consensus__aggregation__wind_range__success(window_stub: ForecastWindowStub, base_date: date) -> None:
    """Ensure wind range captures absolute min and max across sources."""
    data = mk_daily_list(base_date, {"min_w": 10, "max_w": 20}, {"min_w": 5, "max_w": 30})
    res = get_weather.ConsensusEngine.calculate_consensus(window_stub, data, get_weather.ConsensusPolicy())[0]
    assert res.min_wind_kmh == 5.0
    assert res.max_wind_kmh == 30.0

@pytest.mark.skip(reason="TDD TipToe 0")
def test__consensus__aggregation__wind_range__ignore_none__success(window_stub: ForecastWindowStub, base_date: date) -> None:
    """Ensure None values in wind are ignored for Range calculation."""
    data = mk_daily_list(base_date, {"min_w": 10, "max_w": 20}, {"min_w": None, "max_w": None})
    res = get_weather.ConsensusEngine.calculate_consensus(window_stub, data, get_weather.ConsensusPolicy())[0]
    assert res.min_wind_kmh == 10.0
    assert res.max_wind_kmh == 20.0

@pytest.mark.skip(reason="TDD TipToe 0")
def test__consensus__aggregation__rain_prob__max_success(window_stub: ForecastWindowStub, base_date: date) -> None:
    """Ensure rain probability uses the Maximum value across sources."""
    data = mk_daily_list(base_date, {"rain_p": 10}, {"rain_p": 80})
    res = get_weather.ConsensusEngine.calculate_consensus(window_stub, data, get_weather.ConsensusPolicy())[0]
    assert res.rain_prob == 80.0

@pytest.mark.skip(reason="TDD TipToe 0")
def test__consensus__aggregation__rain_prob__ignore_none__success(window_stub: ForecastWindowStub, base_date: date) -> None:
    """Ensure None values in rain_prob are ignored for Max calculation."""
    data = mk_daily_list(base_date, {"rain_p": 50}, {"rain_p": None})
    res = get_weather.ConsensusEngine.calculate_consensus(window_stub, data, get_weather.ConsensusPolicy())[0]
    assert res.rain_prob == 50.0

@pytest.mark.skip(reason="TDD TipToe 0")
def test__consensus__aggregation__direction__union_and_sort__success(window_stub: ForecastWindowStub, base_date: date) -> None:
    """Ensure wind direction returns a sorted unique list of all observed directions."""
    data = mk_daily_list(base_date, {"w_dir": "SW"}, {"w_dir": "N"}, {"w_dir": "SW"})
    res = get_weather.ConsensusEngine.calculate_consensus(window_stub, data, get_weather.ConsensusPolicy())[0]
    assert res.wind_direction == ["N", "SW"]

@pytest.mark.skip(reason="TDD TipToe 0")
def test__consensus__aggregation__direction__ignore_none__success(window_stub: ForecastWindowStub, base_date: date) -> None:
    """Ensure None values in direction are ignored for unique list."""
    data = mk_daily_list(base_date, {"w_dir": "N"}, {"w_dir": None})
    res = get_weather.ConsensusEngine.calculate_consensus(window_stub, data, get_weather.ConsensusPolicy())[0]
    assert res.wind_direction == ["N"]

@pytest.mark.skip(reason="TDD TipToe 0")
def test__consensus__aggregation__prognosis__mode_and_tiebreaker__success(window_stub: ForecastWindowStub, base_date: date) -> None:
    """Ensure prognosis uses Mode with a severity tie-breaker."""
    # Tie between CLEAR and STORM. STORM should win.
    data = mk_daily_list(base_date, {"prog": "CLEAR"}, {"prog": "STORM"})
    res = get_weather.ConsensusEngine.calculate_consensus(window_stub, data, get_weather.ConsensusPolicy())[0]
    assert res.prognosis == "STORM"

@pytest.mark.skip(reason="TDD TipToe 0")
def test__consensus__aggregation__direction__all_none_is_none__success(window_stub: ForecastWindowStub, base_date: date) -> None:
    """Ensure if ALL directions are None, result is None (not empty list)."""
    data = mk_daily_list(base_date, {"min_t": 20, "w_dir": None}, {"min_t": 20, "w_dir": None})
    res = get_weather.ConsensusEngine.calculate_consensus(window_stub, data, get_weather.ConsensusPolicy())[0]
    assert res.wind_direction is None

# --- ConsensusEngine Tests: Outlier Edge Cases ---

@pytest.mark.skip(reason="TDD TipToe 0")
def test__consensus__outlier__count_2__no_removal__success(window_stub: ForecastWindowStub, base_date: date) -> None:
    """Ensure outliers are KEPT when count <= 2."""
    data = mk_daily_list(base_date, {"max_t": 20}, {"max_t": 100})
    res = get_weather.ConsensusEngine.calculate_consensus(window_stub, data, get_weather.ConsensusPolicy())[0]
    assert res.max_temp == 60.0

@pytest.mark.skip(reason="TDD TipToe 0")
def test__consensus__outlier__stddev_0__no_removal__success(window_stub: ForecastWindowStub, base_date: date) -> None:
    """Ensure NO removal if all values are identical (stddev == 0)."""
    data = mk_daily_list(base_date, {"max_t": 20}, {"max_t": 20}, {"max_t": 20})
    res = get_weather.ConsensusEngine.calculate_consensus(window_stub, data, get_weather.ConsensusPolicy())[0]
    assert res.max_temp == 20.0

@pytest.mark.skip(reason="TDD TipToe 0")
def test__consensus__outlier_ignore_nones__success(window_stub: ForecastWindowStub, base_date: date) -> None:
    """Ensure Nones are excluded from count checks for outlier logic."""
    # [20, 20, 20, None, 100]. Count valid=4. Outlier 100 removed. Mean 20.
    data = mk_daily_list(base_date, {"max_t": 20}, {"max_t": 20}, {"max_t": 20}, {"max_t": None}, {"max_t": 100})
    res = get_weather.ConsensusEngine.calculate_consensus(window_stub, data, get_weather.ConsensusPolicy())[0]
    assert res.max_temp == 20.0

@pytest.mark.skip(reason="TDD TipToe 0")
def test__consensus__grouping_determinism__success(window_stub: ForecastWindowStub, base_date: date) -> None:
    """Ensure unsorted mixed-date inputs produce sorted outputs."""
    data = mk_daily_list(base_date, {"offset": 1, "src": "A"}, {"offset": 0, "src": "B"})
    res = get_weather.ConsensusEngine.calculate_consensus(window_stub, data, get_weather.ConsensusPolicy())
    assert len(res) == 2
    assert (res[0].date, res[1].date) == (str(base_date), str(base_date + timedelta(days=1)))
