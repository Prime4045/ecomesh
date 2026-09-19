from datetime import datetime
from typing import Dict, Any, Optional
from agents.base import SignalReport, RISK_LEVEL_NAMES

class EpidemiologicalHealthAgent:
    def __init__(self):
        self.name = "Epidemiological Public Health Specialist"

    def run(
        self,
        city: str,
        air_aqi: float = 100.0,
        water_wqi: float = 75.0,
        waste_count: int = 1,
        force_status: str = "ok"
    ) -> SignalReport:
        """Evaluates clinical respiratory stress, vulnerable population exposure index,
        and hospital surge probability based on cross-vector telemetry.
        """
        now = datetime.now()
        
        if force_status == "missing":
            return SignalReport(
                agent="health",
                status="missing",
                value=0.0,
                unit="Vulnerability Index",
                risk_level=0,
                category="Unknown",
                confidence=0.0,
                weight=0.15,
                timestamp=now,
                source="Epidemiological Hospital Surveillance",
                summary="Health surveillance node offline.",
                detail={"hospital_surge_risk": 0.0, "vulnerable_pop_exposed": 0}
            )

        # Calculate Vulnerability & Surge Index (0 - 100)
        # Higher AQI, Lower WQI, and higher waste contribute to hospital load
        air_factor = min(100.0, (air_aqi / 300.0) * 60.0)
        water_factor = max(0.0, (100.0 - water_wqi) * 0.25)
        waste_factor = min(15.0, waste_count * 2.5)

        vulnerability_index = round(air_factor + water_factor + waste_factor, 1)
        hospital_surge_pct = round(min(98.0, (vulnerability_index / 100.0) * 85.0), 1)

        # Estimate affected population (based on typical metropolitan demographic of ~15-20% sensitive group)
        estimated_exposed_k = int(round((vulnerability_index / 100.0) * 140)) # thousands

        if vulnerability_index >= 70:
            risk_level = 4
            category = "Severe"
            summary = f"Acute epidemiological risk: High hospital surge alert ({hospital_surge_pct}% ICU/pulmonary load projected). Est. {estimated_exposed_k}k vulnerable residents exposed."
        elif vulnerability_index >= 50:
            risk_level = 3
            category = "Poor"
            summary = f"Substantial pediatric & geriatric respiratory strain. Est. {estimated_exposed_k}k vulnerable citizens affected; advise masking and air purifiers."
        elif vulnerability_index >= 30:
            risk_level = 2
            category = "Moderate"
            summary = f"Mild epidemiological impact ({hospital_surge_pct}% clinic elevation). Sensitive cohorts advised to restrict strenuous outdoor exertion."
        elif vulnerability_index >= 15:
            risk_level = 1
            category = "Satisfactory"
            summary = f"Low epidemiological stress. Baseline hospital pulmonary admission rates nominal across metropolitan zones."
        else:
            risk_level = 0
            category = "Good"
            summary = f"Optimal health safety parameters. Zero environmental respiratory alerts triggered."

        confidence = 0.90 if force_status == "ok" else 0.65

        return SignalReport(
            agent="health",
            status=force_status,
            value=vulnerability_index,
            unit="Health Vulnerability Index",
            risk_level=risk_level,
            category=category,
            confidence=confidence,
            weight=0.15,
            timestamp=now,
            source="CDC / Global Health Cohort Surveillance",
            summary=summary,
            detail={
                "vulnerability_index": vulnerability_index,
                "hospital_surge_risk_pct": hospital_surge_pct,
                "vulnerable_pop_exposed_k": estimated_exposed_k,
                "respiratory_alert_tier": risk_level
            }
        )
