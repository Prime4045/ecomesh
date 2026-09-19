from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from agents.base import SignalReport, RISK_LEVEL_NAMES
from services.aqi_client import AQIClient

class AirQualityAgent:
    def __init__(self, waqi_token: str = "demo"):
        self.name = "Air Quality Specialist"
        self.client = AQIClient(api_token=waqi_token)

    def run(
        self,
        city: str = "Delhi NCR",
        force_status: str = "ok",
        force_aqi: Optional[float] = None
    ) -> SignalReport:
        """Executes Air Quality agent evaluation."""
        if force_status == "missing":
            return SignalReport(
                agent="air",
                status="missing",
                value=0.0,
                unit="AQI index",
                risk_level=0,
                category="Missing",
                confidence=0.0,
                weight=0.40,
                timestamp=datetime.now(),
                source="WAQI API (Offline/Failed)",
                summary="Air Quality sensor feed unavailable or unreachable.",
                detail={}
            )

        data = self.client.fetch_city_air_quality(city=city)
        aqi_val = force_aqi if force_aqi is not None else float(data.get("aqi", 150))
        dominant_pol = data.get("dominentpol", "pm25").upper()
        station_name = data.get("city", {}).get("name", city)

        # Risk mapping
        if aqi_val <= 50:
            risk = 0
            category = "Good"
        elif aqi_val <= 100:
            risk = 1
            category = "Satisfactory"
        elif aqi_val <= 200:
            risk = 2
            category = "Moderate"
        elif aqi_val <= 300:
            risk = 3
            category = "Poor"
        else:
            risk = 4
            category = "Severe"

        # Stale check or forced stale
        timestamp = datetime.now()
        confidence = 0.95
        status = force_status

        if status == "stale":
            timestamp = datetime.now() - timedelta(hours=8)
            confidence = 0.70

        summary = (
            f"Air quality at station '{station_name}' measured AQI of {int(aqi_val)} "
            f"(Primary pollutant: {dominant_pol}). Rated {category.upper()} risk."
        )

        return SignalReport(
            agent="air",
            status=status,
            value=aqi_val,
            unit="AQI index",
            risk_level=risk,
            category=category,
            confidence=confidence,
            weight=0.40,
            timestamp=timestamp,
            source=f"WAQI Station ({station_name})",
            summary=summary,
            detail={
                "aqi": aqi_val,
                "dominant_pollutant": dominant_pol,
                "station": station_name,
                "city": data.get("city", {}),
                "geo": data.get("city", {}).get("geo", []),
                "iaqi": data.get("iaqi", {})
            }
        )
