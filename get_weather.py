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
from collections import Counter, defaultdict
from statistics import mean, stdev

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

def map_wttr_text(text: str) -> str:
    text = text.lower()
    mapping = [
        (["sunny", "clear"], "CLEAR"),
        (["partly cloudy", "cloudy"], "CLOUDY"),
        (["rain"], "RAIN")
    ]
    for keywords, result in mapping:
        if any(k in text for k in keywords):
            return result
    return "UNKNOWN"

def map_bom_text(text: str) -> str:
    text = text.lower()
    mapping = [
        (["fine", "sunny", "clear"], "CLEAR"),
        (["cloud"], "CLOUDY"),
        (["shower", "rain"], "RAIN"),
        (["storm"], "STORM")
    ]
    for keywords, result in mapping:
        if any(k in text for k in keywords):
            return result
    return "UNKNOWN"

def pick_worst(candidates: list[str]) -> str:
    ranking = ["STORM", "SNOW", "RAIN", "CLOUDY", "CLEAR"]
    for rank in ranking:
        if rank in candidates:
            return rank
    return "UNKNOWN"

class WeatherTaxonomy:
    @staticmethod
    def map_wmo_code(code: int) -> str:
        return map_wmo_code(code)

    @staticmethod
    def map_wttr_text(text: str) -> str:
        return map_wttr_text(text)

    @staticmethod
    def map_bom_text(text: str) -> str:
        return map_bom_text(text)

    @staticmethod
    def pick_worst(candidates: list[str]) -> str:
        return pick_worst(candidates)

class ConsensusPolicy:
    pass

class ForecastWindow:
    def __init__(self, dates: list[date]):
        self.dates = dates

def _group_by_date(data: list[DailyData]) -> dict[str, list[DailyData]]:
    grouped = defaultdict(list)
    for d in data:
        grouped[str(d.date)].append(d)
    return grouped

def _compute_robust_mean(values: list[float]) -> float | None:
    if not values:
        return None
    if len(values) > 2:
        try:
            sigma = stdev(values)
            if sigma > 0:
                mu = mean(values)
                # Keep values within 1.5 sigma
                filtered = [v for v in values if abs(v - mu) <= 1.5 * sigma]
                if filtered:
                    return mean(filtered)
        except (ValueError, ArithmeticError):
            pass # Fallback to simple mean if stats fail
    return mean(values)

def _compute_wind_range(records: list[DailyData]) -> tuple[float | None, float | None]:
    min_winds = [r.min_wind for r in records if r.min_wind is not None]
    max_winds = [r.max_wind for r in records if r.max_wind is not None]
    return (min(min_winds) if min_winds else None, max(max_winds) if max_winds else None)

def _compute_wind_direction(records: list[DailyData]) -> list[str] | None:
    directions = {r.direction for r in records if r.direction is not None}
    return sorted(list(directions)) if directions else None

def _compute_prognosis(records: list[DailyData]) -> str | None:
    prognoses = [r.prognosis for r in records if r.prognosis is not None]
    if not prognoses:
        return None
    counts = Counter(prognoses)
    max_count = max(counts.values())
    candidates = [p for p, c in counts.items() if c == max_count]
    return candidates[0] if len(candidates) == 1 else WeatherTaxonomy.pick_worst(candidates)

def _compute_rain_prob(records: list[DailyData]) -> float | None:
    probs = [r.rain_prob for r in records if r.rain_prob is not None]
    return max(probs) if probs else None

def _is_valid_record(r: DailyData) -> bool:
    return any(x is not None for x in [
        r.min_temp, r.max_temp, r.min_wind, r.max_wind, 
        r.direction, r.prognosis, r.rain_prob
    ])

def _extract_sources(records: list[DailyData]) -> list[str]:
    return sorted([r.source for r in records if _is_valid_record(r)])

def calculate_consensus(
    window: ForecastWindow, 
    data: list[DailyData], 
    policy: ConsensusPolicy,
    location_name: str = "Unknown"
) -> list[ConsensusForecast]:
    if not data:
        return []
    
    grouped = _group_by_date(data)
    
    def build_consensus(d_str: str) -> Optional[ConsensusForecast]:
        if d_str not in grouped:
            return None
        records = grouped[d_str]
        sources = _extract_sources(records)
        if not sources:
            return None
        
        return ConsensusForecast(
            location=location_name,
            date=d_str,
            min_temp=_compute_robust_mean([r.min_temp for r in records if r.min_temp is not None]),
            max_temp=_compute_robust_mean([r.max_temp for r in records if r.max_temp is not None]),
            min_wind_kmh=_compute_wind_range(records)[0],
            max_wind_kmh=_compute_wind_range(records)[1],
            wind_direction=_compute_wind_direction(records),
            prognosis=_compute_prognosis(records),
            rain_prob=_compute_rain_prob(records),
            sources=sources
        )

    return [
        cf for d in window.dates 
        if (cf := build_consensus(str(d))) is not None
    ]

class ConsensusEngine:
    @staticmethod
    def calculate_consensus(
        window: ForecastWindow, 
        data: list[DailyData], 
        policy: ConsensusPolicy,
        location_name: str = "Unknown"
    ) -> list[ConsensusForecast]:
        return calculate_consensus(window, data, policy, location_name)
