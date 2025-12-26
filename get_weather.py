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
from typing import List, Optional, Dict, Tuple
from datetime import date
from collections import Counter, defaultdict
from statistics import mean, stdev

@dataclass(frozen=True)
class DailyData:
    date: date
    source: str
    min_temp: Optional[float]
    max_temp: Optional[float]
    min_wind: Optional[float]
    max_wind: Optional[float]
    direction: Optional[str]
    prognosis: Optional[str]
    rain_prob: Optional[float]

@dataclass(frozen=True)
class ConsensusForecast:
    location: str
    date: str
    min_temp: Optional[float]
    max_temp: Optional[float]
    min_wind_kmh: Optional[float]
    max_wind_kmh: Optional[float]
    wind_direction: Optional[List[str]]
    prognosis: Optional[str]
    rain_prob: Optional[float]
    sources: List[str]

class WeatherTaxonomy:
    @staticmethod
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

    @staticmethod
    def map_wttr_text(text: str) -> str:
        text = text.lower()
        if "sunny" in text or "clear" in text:
            return "CLEAR"
        if "partly cloudy" in text or "cloudy" in text:
            return "CLOUDY"
        if "rain" in text:
            return "RAIN"
        return "UNKNOWN"

    @staticmethod
    def map_bom_text(text: str) -> str:
        text = text.lower()
        if "fine" in text or "sunny" in text or "clear" in text:
            return "CLEAR"
        if "cloud" in text:
            return "CLOUDY"
        if "shower" in text or "rain" in text:
            return "RAIN"
        if "storm" in text:
            return "STORM"
        return "UNKNOWN"

    @staticmethod
    def pick_worst(candidates: List[str]) -> str:
        ranking = ["STORM", "SNOW", "RAIN", "CLOUDY", "CLEAR"]
        for rank in ranking:
            if rank in candidates:
                return rank
        return "UNKNOWN"

class ConsensusPolicy:
    pass

class ForecastWindow:
    def __init__(self, dates: List[date]):
        self.dates = dates

def _group_by_date(data: List[DailyData]) -> Dict[str, List[DailyData]]:
    grouped = defaultdict(list)
    for d in data:
        grouped[str(d.date)].append(d)
    return grouped

def _compute_robust_mean(values: List[float]) -> Optional[float]:
    if not values:
        return None
    if len(values) > 2:
        try:
            sigma = stdev(values)
            if sigma > 0:
                mu = mean(values)
                filtered = [v for v in values if abs(v - mu) <= 1.5 * sigma]
                if filtered:
                    return mean(filtered)
        except Exception:
            pass 
    return mean(values)

def _compute_wind_range(records: List[DailyData]) -> Tuple[Optional[float], Optional[float]]:
    min_winds = [r.min_wind for r in records if r.min_wind is not None]
    max_winds = [r.max_wind for r in records if r.max_wind is not None]
    return (min(min_winds) if min_winds else None, max(max_winds) if max_winds else None)

def _compute_wind_direction(records: List[DailyData]) -> Optional[List[str]]:
    directions = {r.direction for r in records if r.direction is not None}
    return sorted(list(directions)) if directions else None

def _compute_prognosis(records: List[DailyData]) -> Optional[str]:
    prognoses = [r.prognosis for r in records if r.prognosis is not None]
    if not prognoses:
        return None
    counts = Counter(prognoses)
    max_count = max(counts.values())
    candidates = [p for p, c in counts.items() if c == max_count]
    return candidates[0] if len(candidates) == 1 else WeatherTaxonomy.pick_worst(candidates)

def _compute_rain_prob(records: List[DailyData]) -> Optional[float]:
    probs = [r.rain_prob for r in records if r.rain_prob is not None]
    return max(probs) if probs else None

def _extract_sources(records: List[DailyData]) -> List[str]:
    valid_sources = []
    for r in records:
        if any(x is not None for x in [r.min_temp, r.max_temp, r.min_wind, r.max_wind, r.direction, r.prognosis, r.rain_prob]):
            valid_sources.append(r.source)
    return sorted(valid_sources)

class ConsensusEngine:
    @staticmethod
    def calculate_consensus(
        window: ForecastWindow, 
        data: List[DailyData], 
        policy: ConsensusPolicy,
        location_name: str = "Unknown"
    ) -> List[ConsensusForecast]:
        if not data:
            return []
        
        grouped = _group_by_date(data)
        results = []

        for target_date in window.dates:
            d_str = str(target_date)
            if d_str not in grouped:
                continue
            
            day_records = grouped[d_str]
            sources = _extract_sources(day_records)
            if not sources:
                continue

            min_t = _compute_robust_mean([r.min_temp for r in day_records if r.min_temp is not None])
            max_t = _compute_robust_mean([r.max_temp for r in day_records if r.max_temp is not None])
            min_w, max_w = _compute_wind_range(day_records)
            w_dir = _compute_wind_direction(day_records)
            prog = _compute_prognosis(day_records)
            rain = _compute_rain_prob(day_records)

            results.append(ConsensusForecast(
                location=location_name,
                date=d_str,
                min_temp=min_t, max_temp=max_t, 
                min_wind_kmh=min_w, max_wind_kmh=max_w,
                wind_direction=w_dir, prognosis=prog, 
                rain_prob=rain, sources=sources
            ))
            
        return results
