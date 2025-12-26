#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#   "httpx",
#   "pydantic",
#   "defusedxml",
#   "tenacity",
# ]
# ///
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable
from datetime import date
from collections import Counter
from statistics import mean, stdev
from itertools import groupby
from enum import StrEnum


class WeatherCode(StrEnum):
    CLEAR = "CLEAR"
    CLOUDY = "CLOUDY"
    RAIN = "RAIN"
    SNOW = "SNOW"
    STORM = "STORM"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class DailyData:
    date: date
    source: str
    min_temp: float | None
    max_temp: float | None
    min_wind: float | None
    max_wind: float | None
    direction: str | None
    prognosis: WeatherCode | None
    rain_prob: float | None


@dataclass(frozen=True)
class ConsensusForecast:
    location: str
    date: str
    min_temp: float | None
    max_temp: float | None
    min_wind_kmh: float | None
    max_wind_kmh: float | None
    wind_direction: list[str] | None
    prognosis: WeatherCode | None
    rain_prob: float | None
    sources: list[str]


_WTTR_MAPPING = (
    (("sunny", "clear"), WeatherCode.CLEAR),
    (("partly cloudy", "cloudy"), WeatherCode.CLOUDY),
    (("rain",), WeatherCode.RAIN),
)

_BOM_MAPPING = (
    (("fine", "sunny", "clear"), WeatherCode.CLEAR),
    (("cloud",), WeatherCode.CLOUDY),
    (("shower", "rain"), WeatherCode.RAIN),
    (("storm",), WeatherCode.STORM),
)

_WMO_MAPPING = {
    0: WeatherCode.CLEAR,
    1: WeatherCode.CLEAR,
    3: WeatherCode.CLOUDY,
    61: WeatherCode.RAIN,
    71: WeatherCode.SNOW,
    95: WeatherCode.STORM,
}


def map_wmo_code(code: int) -> WeatherCode:
    """Map WMO integer code to standardized WeatherCode."""
    if code in _WMO_MAPPING:
        return _WMO_MAPPING[code]
    raise ValueError(f"Unknown WMO code: {code}")


def map_wttr_text(text: str) -> WeatherCode:
    """Map wttr.in text condition to standardized WeatherCode."""
    text = text.lower()
    for keywords, result in _WTTR_MAPPING:
        if any(k in text for k in keywords):
            return result
    return WeatherCode.UNKNOWN


def map_bom_text(text: str) -> WeatherCode:
    """Map BOM text forecast to standardized WeatherCode."""
    text = text.lower()
    for keywords, result in _BOM_MAPPING:
        if any(k in text for k in keywords):
            return result
    return WeatherCode.UNKNOWN


@dataclass(frozen=True)
class ConsensusPolicy:
    sigma_threshold: float = 1.5
    min_count_for_outlier: int = 3
    prognosis_ranking: tuple[WeatherCode, ...] = (
        WeatherCode.STORM,
        WeatherCode.SNOW,
        WeatherCode.RAIN,
        WeatherCode.CLOUDY,
        WeatherCode.CLEAR,
    )


def pick_worst(
    candidates: Iterable[str], policy: ConsensusPolicy | None = None
) -> WeatherCode:
    """Select the most severe prognosis from a list of candidates."""
    ranking = (
        policy.prognosis_ranking
        if policy
        else (
            WeatherCode.STORM,
            WeatherCode.SNOW,
            WeatherCode.RAIN,
            WeatherCode.CLOUDY,
            WeatherCode.CLEAR,
        )
    )
    c_set = set(candidates)
    for rank in ranking:
        if rank in c_set:
            return rank  # rank is WeatherCode
    return WeatherCode.UNKNOWN


@dataclass(frozen=True, slots=True)
class ForecastWindow:
    dates: tuple[date, ...]


def _group_by_date(data: Iterable[DailyData]) -> dict[str, tuple[DailyData, ...]]:
    """Group flat list of daily data by date string."""
    sorted_data = sorted(data, key=lambda x: x.date)
    return {str(k): tuple(g) for k, g in groupby(sorted_data, key=lambda x: x.date)}


def _calculate_mean_with_filter(
    values: tuple[float, ...], mu: float, sigma: float, threshold: float
) -> float:
    """Calculate mean of values within sigma threshold."""
    filtered = [v for v in values if abs(v - mu) <= threshold * sigma]
    return mean(filtered) if filtered else mu


def _compute_robust_mean(
    values: Iterable[float], policy: ConsensusPolicy
) -> float | None:
    """Compute mean excluding outliers > 1.5 sigma if count sufficient."""
    vals = tuple(values)
    if not vals:
        return None
    if len(vals) < policy.min_count_for_outlier:
        return mean(vals)

    sigma = stdev(vals)
    if sigma == 0:
        return mean(vals)

    return _calculate_mean_with_filter(vals, mean(vals), sigma, policy.sigma_threshold)


def _compute_wind_range(
    records: Iterable[DailyData],
) -> tuple[float | None, float | None]:
    """Compute absolute min and max wind speed across records."""
    min_winds = (r.min_wind for r in records if r.min_wind is not None)
    max_winds = (r.max_wind for r in records if r.max_wind is not None)
    return (min(min_winds, default=None), max(max_winds, default=None))


def _compute_wind_direction(records: Iterable[DailyData]) -> tuple[str, ...] | None:
    """Compute sorted unique list of observed wind directions."""
    directions = {r.direction for r in records if r.direction is not None}
    return tuple(sorted(directions)) if directions else None


def _compute_prognosis(
    records: Iterable[DailyData], policy: ConsensusPolicy
) -> WeatherCode | None:
    """Compute prognosis mode with severity tie-breaking."""
    prognoses = (r.prognosis for r in records if r.prognosis is not None)
    counts = Counter(prognoses)
    if not counts:
        return None
    max_count = max(counts.values())
    candidates = tuple(p for p, c in counts.items() if c == max_count)
    return candidates[0] if len(candidates) == 1 else pick_worst(candidates, policy)


def _compute_rain_prob(records: Iterable[DailyData]) -> float | None:
    """Compute max rain probability across records."""
    probs = (r.rain_prob for r in records if r.rain_prob is not None)
    return max(probs, default=None)


def _is_valid_record(r: DailyData) -> bool:
    """Check if record has at least one valid data field."""
    return any(
        x is not None
        for x in (
            r.min_temp,
            r.max_temp,
            r.min_wind,
            r.max_wind,
            r.direction,
            r.prognosis,
            r.rain_prob,
        )
    )


def _extract_sources(records: Iterable[DailyData]) -> tuple[str, ...]:
    """Extract sorted list of unique sources that provided valid data."""
    return tuple(sorted(r.source for r in records if _is_valid_record(r)))


def _build_forecast_dto(
    d_str: str,
    records: Iterable[DailyData],
    sources: tuple[str, ...],
    policy: ConsensusPolicy,
    location_name: str,
) -> ConsensusForecast:
    """Construct the output DTO from aggregated records."""
    w_dir = _compute_wind_direction(records)
    return ConsensusForecast(
        location=location_name,
        date=d_str,
        min_temp=_compute_robust_mean(
            (r.min_temp for r in records if r.min_temp is not None), policy
        ),
        max_temp=_compute_robust_mean(
            (r.max_temp for r in records if r.max_temp is not None), policy
        ),
        min_wind_kmh=_compute_wind_range(records)[0],
        max_wind_kmh=_compute_wind_range(records)[1],
        wind_direction=list(w_dir) if w_dir is not None else None,
        prognosis=_compute_prognosis(records, policy),
        rain_prob=_compute_rain_prob(records),
        sources=list(sources),
    )


def _build_single_consensus(
    d_str: str,
    records: Iterable[DailyData],
    policy: ConsensusPolicy,
    location_name: str,
) -> ConsensusForecast | None:
    """Build consensus for a single date if data exists."""
    sources = _extract_sources(records)
    if not sources:
        return None
    return _build_forecast_dto(d_str, records, sources, policy, location_name)


def calculate_consensus(
    window: ForecastWindow,
    data: Iterable[DailyData],
    policy: ConsensusPolicy,
    location_name: str = "Unknown",
) -> list[ConsensusForecast]:
    """Orchestrate the consensus calculation for the forecast window."""
    if not data:
        return []
    grouped = _group_by_date(data)
    return [
        cf
        for d in window.dates
        if (
            cf := _build_single_consensus(
                str(d), grouped.get(str(d), ()), policy, location_name
            )
        )
        is not None
    ]
