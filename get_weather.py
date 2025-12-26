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
from typing import Optional
from datetime import date
from collections import Counter
from statistics import mean, stdev
from itertools import groupby

@dataclass(frozen=True)
class DailyData:
    date: date
    source: str
    min_temp: float | None
    max_temp: float | None
    min_wind: float | None
    max_wind: float | None
    direction: str | None
    prognosis: str | None
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
    prognosis: str | None
    rain_prob: float | None
    sources: list[str]

def map_wmo_code(code: int) -> str:
    mapping = {
        0: "CLEAR", 1: "CLEAR",
        3: "CLOUDY",
        61: "RAIN",
        71: "SNOW",
        95: "STORM"
    }
    if code in mapping:
        return mapping[code]
    raise ValueError(f"Unknown WMO code: {code}")

_WTTR_MAPPING = (
    (("sunny", "clear"), "CLEAR"),
    (("partly cloudy", "cloudy"), "CLOUDY"),
    (("rain",), "RAIN")
)

_BOM_MAPPING = (
    (("fine", "sunny", "clear"), "CLEAR"),
    (("cloud",), "CLOUDY"),
    (("shower", "rain"), "RAIN"),
    (("storm",), "STORM")
)

def map_wttr_text(text: str) -> str:
    text = text.lower()
    for keywords, result in _WTTR_MAPPING:
        if any(k in text for k in keywords):
            return result
    return "UNKNOWN"

def map_bom_text(text: str) -> str:
    text = text.lower()
    for keywords, result in _BOM_MAPPING:
        if any(k in text for k in keywords):
            return result
    return "UNKNOWN"

def pick_worst(candidates: list[str], policy: ConsensusPolicy = None) -> str:
    ranking = policy.prognosis_ranking if policy else ("STORM", "SNOW", "RAIN", "CLOUDY", "CLEAR")
    for rank in ranking:
        if rank in candidates:
            return rank
    return "UNKNOWN"

@dataclass(frozen=True)
class ConsensusPolicy:
    sigma_threshold: float = 1.5
    min_count_for_outlier: int = 3
    prognosis_ranking: tuple[str, ...] = ("STORM", "SNOW", "RAIN", "CLOUDY", "CLEAR")

@dataclass(frozen=True, slots=True)
class ForecastWindow:
    dates: list[date]

def _group_by_date(data: list[DailyData]) -> dict[str, list[DailyData]]:
    # Functional grouping: Sort first, then group
    sorted_data = sorted(data, key=lambda x: x.date)
    return {
        str(k): list(g) 
        for k, g in groupby(sorted_data, key=lambda x: x.date)
    }

def _calculate_mean_with_filter(values: list[float], mu: float, sigma: float, threshold: float) -> float:
    filtered = [v for v in values if abs(v - mu) <= threshold * sigma]
    return mean(filtered) if filtered else mu

def _compute_robust_mean(values: list[float], policy: ConsensusPolicy) -> float | None:
    if not values:
        return None
    if len(values) < policy.min_count_for_outlier:
        return mean(values)
    
    # Branch-only logic (no try/except)
    sigma = stdev(values)
    if sigma == 0:
        return mean(values)
    
    return _calculate_mean_with_filter(values, mean(values), sigma, policy.sigma_threshold)

def _compute_wind_range(records: list[DailyData]) -> tuple[float | None, float | None]:
    min_winds = (r.min_wind for r in records if r.min_wind is not None)
    max_winds = (r.max_wind for r in records if r.max_wind is not None)
    return (min(min_winds, default=None), max(max_winds, default=None))

def _compute_wind_direction(records: list[DailyData]) -> list[str] | None:
    directions = {r.direction for r in records if r.direction is not None}
    return sorted(directions) if directions else None

def _compute_prognosis(records: list[DailyData], policy: ConsensusPolicy) -> str | None:
    prognoses = (r.prognosis for r in records if r.prognosis is not None)
    # Counter consumes iterator directly
    counts = Counter(prognoses)
    if not counts:
        return None
    max_count = max(counts.values())
    candidates = [p for p, c in counts.items() if c == max_count]
    return candidates[0] if len(candidates) == 1 else pick_worst(candidates, policy)

def _compute_rain_prob(records: list[DailyData]) -> float | None:
    probs = (r.rain_prob for r in records if r.rain_prob is not None)
    return max(probs, default=None)

def _is_valid_record(r: DailyData) -> bool:
    # Generator expression for any()
    return any(x is not None for x in (
        r.min_temp, r.max_temp, r.min_wind, r.max_wind, 
        r.direction, r.prognosis, r.rain_prob
    ))

def _extract_sources(records: list[DailyData]) -> list[str]:
    # Sorted consumes generator
    return sorted(r.source for r in records if _is_valid_record(r))

def _build_single_consensus(
    d_str: str, 
    records: list[DailyData], 
    policy: ConsensusPolicy, 
    location_name: str
) -> ConsensusForecast | None:
    sources = _extract_sources(records)
    if not sources:
        return None
    
    return ConsensusForecast(
        location=location_name,
        date=d_str,
        min_temp=_compute_robust_mean([r.min_temp for r in records if r.min_temp is not None], policy),
        max_temp=_compute_robust_mean([r.max_temp for r in records if r.max_temp is not None], policy),
        min_wind_kmh=_compute_wind_range(records)[0],
        max_wind_kmh=_compute_wind_range(records)[1],
        wind_direction=_compute_wind_direction(records),
        prognosis=_compute_prognosis(records, policy),
        rain_prob=_compute_rain_prob(records),
        sources=sources
    )

def calculate_consensus(
    window: ForecastWindow, 
    data: list[DailyData], 
    policy: ConsensusPolicy,
    location_name: str = "Unknown"
) -> list[ConsensusForecast]:
    if not data:
        return []
    
    grouped = _group_by_date(data)
    return [
        result for d in window.dates
        if (result := _build_single_consensus(str(d), grouped.get(str(d), []), policy, location_name))
    ]
