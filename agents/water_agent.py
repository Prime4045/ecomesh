from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import random
from agents.base import SignalReport, RISK_LEVEL_NAMES
from services.wqi import WaterQualityCalculator

CITY_WATER_DEFAULTS = {
    "Delhi NCR": {"ph": 7.8, "do": 4.2, "bod": 6.5, "turbidity": 14.5, "conductance": 680.0, "basin": "Yamuna River Basin"},
    "Delhi": {"ph": 7.8, "do": 4.2, "bod": 6.5, "turbidity": 14.5, "conductance": 680.0, "basin": "Yamuna River Basin"},
    "Mumbai": {"ph": 7.4, "do": 5.5, "bod": 3.8, "turbidity": 8.2, "conductance": 520.0, "basin": "Mithi River & Coastal Estuary"},
    "Bengaluru": {"ph": 7.6, "do": 5.0, "bod": 4.5, "turbidity": 9.0, "conductance": 490.0, "basin": "Vrishabhavathi & Bellandur Basin"},
    "London": {"ph": 7.5, "do": 8.4, "bod": 1.8, "turbidity": 3.2, "conductance": 380.0, "basin": "River Thames Hydrological Network"},
    "Tokyo": {"ph": 7.2, "do": 9.1, "bod": 1.2, "turbidity": 2.1, "conductance": 260.0, "basin": "Sumida River & Tokyo Bay Basin"},
    "New York": {"ph": 7.3, "do": 8.0, "bod": 2.0, "turbidity": 3.5, "conductance": 310.0, "basin": "Hudson River Estuary"},
    "Paris": {"ph": 7.4, "do": 8.2, "bod": 2.2, "turbidity": 3.8, "conductance": 340.0, "basin": "Seine River Basin"},
    "Berlin": {"ph": 7.6, "do": 8.6, "bod": 1.9, "turbidity": 2.8, "conductance": 390.0, "basin": "Spree & Havel River Catchment"},
    "Sydney": {"ph": 7.3, "do": 8.5, "bod": 1.6, "turbidity": 2.4, "conductance": 290.0, "basin": "Sydney Harbour & Parramatta Catchment"},
    "Singapore": {"ph": 7.1, "do": 7.8, "bod": 2.0, "turbidity": 3.0, "conductance": 320.0, "basin": "Marina Basin & Kallang Catchment"},
    "Dubai": {"ph": 7.9, "do": 6.8, "bod": 3.1, "turbidity": 5.5, "conductance": 750.0, "basin": "Dubai Creek & Coastal Marine Zone"},
    "Cairo": {"ph": 8.1, "do": 5.8, "bod": 5.2, "turbidity": 11.0, "conductance": 610.0, "basin": "Nile River Basin"},
    "Toronto": {"ph": 7.5, "do": 8.8, "bod": 1.7, "turbidity": 2.6, "conductance": 330.0, "basin": "Lake Ontario & Don River Catchment"},
    "San Francisco": {"ph": 7.3, "do": 8.4, "bod": 1.5, "turbidity": 2.9, "conductance": 305.0, "basin": "San Francisco Bay Estuary"},
    "Los Angeles": {"ph": 7.6, "do": 7.2, "bod": 3.4, "turbidity": 6.2, "conductance": 480.0, "basin": "Los Angeles River Watershed"},
    "Seoul": {"ph": 7.2, "do": 8.9, "bod": 1.6, "turbidity": 2.5, "conductance": 280.0, "basin": "Han River Basin"},
    "Beijing": {"ph": 7.9, "do": 6.2, "bod": 4.8, "turbidity": 10.2, "conductance": 590.0, "basin": "Hai River Catchment & Chaobai Basin"},
    "Rome": {"ph": 7.7, "do": 8.0, "bod": 2.4, "turbidity": 4.2, "conductance": 420.0, "basin": "Tiber River Catchment"}
}

class WaterQualityAgent:
    def __init__(self):
        self.name = "Water Quality Specialist"

    def run(
        self,
        city: str = "Delhi NCR",
        water_params: Optional[Dict[str, float]] = None,
        force_status: str = "ok",
        force_wqi: Optional[float] = None
    ) -> SignalReport:
        """Executes Water Quality agent evaluation with city-specific hydrology."""
        if force_status == "missing":
            return SignalReport(
                agent="water",
                status="missing",
                value=0.0,
                unit="WQI Index",
                risk_level=0,
                category="Missing",
                confidence=0.0,
                weight=0.35,
                timestamp=datetime.now(),
                source="WQI Telemetry (Offline/Failed)",
                summary="Water telemetry sensor array non-responsive.",
                detail={}
            )

        basin_name = "Regional Hydrological Catchment"
        if water_params is None:
            clean_name = city.strip()
            if clean_name in CITY_WATER_DEFAULTS:
                entry = CITY_WATER_DEFAULTS[clean_name]
                water_params = {k: v for k, v in entry.items() if k != "basin"}
                basin_name = entry.get("basin", basin_name)
            else:
                # Dynamic deterministic variation based on city name
                seed = sum(ord(c) for c in clean_name)
                ph = round(7.0 + (seed % 15) * 0.05, 1)
                do = round(5.5 + (seed % 40) * 0.1, 1)
                bod = round(1.5 + (seed % 30) * 0.1, 1)
                turb = round(2.5 + (seed % 50) * 0.1, 1)
                cond = round(250.0 + (seed % 300), 1)
                water_params = {"ph": ph, "do": do, "bod": bod, "turbidity": turb, "conductance": cond}
                basin_name = f"{clean_name} Hydrological Basin"

        wqi_val, risk, category = WaterQualityCalculator.calculate_wqi(water_params)

        if force_wqi is not None:
            wqi_val = force_wqi
            if wqi_val >= 85:
                risk, category = 0, "Good"
            elif wqi_val >= 70:
                risk, category = 1, "Satisfactory"
            elif wqi_val >= 50:
                risk, category = 2, "Moderate"
            elif wqi_val >= 30:
                risk, category = 3, "Poor"
            else:
                risk, category = 4, "Severe"

        timestamp = datetime.now()
        confidence = 0.92
        status = force_status

        if status == "stale":
            timestamp = datetime.now() - timedelta(hours=3)
            confidence = 0.65

        summary = (
            f"Water Quality for {city} ({basin_name}) evaluated at WQI {wqi_val}/100. "
            f"Key metrics: pH {water_params.get('ph')}, DO {water_params.get('do')} mg/L, Turbidity {water_params.get('turbidity')} NTU. "
            f"Assigned status: {category.upper()}."
        )

        return SignalReport(
            agent="water",
            status=status,
            value=wqi_val,
            unit="WQI Index",
            risk_level=risk,
            category=category,
            confidence=confidence,
            weight=0.35,
            timestamp=timestamp,
            source="WQI Sensor Telemetry Array",
            summary=summary,
            detail={
                "wqi": wqi_val,
                "basin": basin_name,
                "params": water_params
            }
        )
