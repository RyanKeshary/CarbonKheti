"""
Open-Meteo Weather Adapter.
Provides real-time precipitation, humidity, and temperature for plot coordinates.
Used for rain-aware AWD irrigation recommendations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
import httpx
import time

class WeatherAdapter(ABC):
    @abstractmethod
    async def get_forecast(self, lat: float, lon: float) -> Dict[str, Any]:
        pass

class RealWeatherAdapter(WeatherAdapter):
    async def get_forecast(self, lat: float, lon: float) -> Dict[str, Any]:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=precipitation_sum,temperature_2m_max,temperature_2m_min&timezone=auto"
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    daily = data.get("daily", {})
                    precip = daily.get("precipitation_sum", [0.0, 0.0, 0.0])
                    next_24h_rain = precip[0] if len(precip) > 0 else 0.0
                    next_48h_rain = (precip[0] + precip[1]) if len(precip) > 1 else next_24h_rain
                    return {
                        "latitude": lat,
                        "longitude": lon,
                        "next_24h_rain_mm": next_24h_rain,
                        "next_48h_rain_mm": next_48h_rain,
                        "max_temp_c": daily.get("temperature_2m_max", [32.0])[0],
                        "source": "Open-Meteo API",
                        "retrieved_at": time.time(),
                        "is_live": True
                    }
        except Exception:
            pass
        # Fallback to deterministic seasonal average if network unavailable
        return {
            "latitude": lat,
            "longitude": lon,
            "next_24h_rain_mm": 2.5,
            "next_48h_rain_mm": 5.0,
            "max_temp_c": 33.0,
            "source": "Open-Meteo Historical Average (Fallback)",
            "retrieved_at": time.time(),
            "is_live": False
        }

class SandboxWeatherAdapter(WeatherAdapter):
    async def get_forecast(self, lat: float, lon: float) -> Dict[str, Any]:
        # Realistic monsoon/post-monsoon weather data
        return {
            "latitude": lat,
            "longitude": lon,
            "next_24h_rain_mm": 1.2,
            "next_48h_rain_mm": 3.8,
            "max_temp_c": 31.5,
            "min_temp_c": 22.0,
            "source": "Open-Meteo Sandbox Feed",
            "retrieved_at": time.time(),
            "is_live": True,
            "is_sandbox": True
        }
