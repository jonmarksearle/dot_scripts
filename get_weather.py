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
from typing import List, Optional
from datetime import date

@dataclass
class DailyData:
    min_temp: float
    max_temp: float
    min_wind: float
    max_wind: float
    wind_direction: str
    prognosis: str
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

class ConsensusEngine:
    @staticmethod
    def calculate_consensus(window: ForecastWindow, data: List[DailyData], policy: ConsensusPolicy) -> List[ConsensusForecast]:
        if not data:
            return []
        raise NotImplementedError
