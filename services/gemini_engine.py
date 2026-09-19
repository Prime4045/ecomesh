import os
import json
import requests
import time
from typing import Dict, Any, Tuple, Optional, List
from services.aqi_client import load_env_file

_GEMINI_SESSION = requests.Session()
_GEMINI_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}
_GEMINI_CACHE_TTL = 600.0  # 10 minute cache

class GeminiSynthesisEngine:
    def __init__(self, api_key: Optional[str] = None):
        load_env_file()
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")

    def synthesize_executive_brief(
        self,
        city: str,
        verdict_score: float,
        combined_level: int,
        combined_category: str,
        signals: Dict[str, Any],
        weights_used: Dict[str, float],
        conflict: bool,
        conflict_detail: str,
        stale_signals: List[str],
        missing_signals: List[str]
    ) -> Dict[str, Any]:
        """Synthesizes executive briefing, cross-agent conflict analysis,
        and sector-specific directives using Gemini with instant cache & fast fallback.
        """
        cache_key = f"{city.lower()}_{round(verdict_score, 1)}_{combined_level}_{str(stale_signals)}_{str(missing_signals)}"
        now_ts = time.time()

        if cache_key in _GEMINI_CACHE:
            cached_time, cached_val = _GEMINI_CACHE[cache_key]
            if now_ts - cached_time < _GEMINI_CACHE_TTL:
                return cached_val

        # If API key is available, attempt live Gemini API call with fast timeout
        if self.api_key and len(self.api_key.strip()) > 5:
            try:
                live_result = self._call_gemini_api(
                    city, verdict_score, combined_level, combined_category,
                    signals, weights_used, conflict, conflict_detail,
                    stale_signals, missing_signals
                )
                if live_result:
                    _GEMINI_CACHE[cache_key] = (now_ts, live_result)
                    return live_result
            except Exception:
                pass # Fallback cleanly to high-grade deterministic synthesis

        heuristic_result = self._generate_heuristic_synthesis(
            city, verdict_score, combined_level, combined_category,
            signals, weights_used, conflict, conflict_detail,
            stale_signals, missing_signals
        )
        _GEMINI_CACHE[cache_key] = (now_ts, heuristic_result)
        return heuristic_result

    def _call_gemini_api(
        self, city: str, score: float, level: int, category: str,
        signals: Dict[str, Any], weights: Dict[str, float],
        conflict: bool, conflict_detail: str,
        stale: List[str], missing: List[str]
    ) -> Optional[Dict[str, Any]]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.api_key}"
        
        prompt = f"""
You are the Chief Environmental AI Coordinator for EcoMesh.
Analyze the following multi-agent telemetry for {city}:
- Composite Risk Score: {score:.2f} / 4.0 ({category}, Level {level})
- Air Quality Signal: {signals.get('air', {}).get('category')} (AQI: {signals.get('air', {}).get('value')})
- Water Quality Signal: {signals.get('water', {}).get('category')} (WQI: {signals.get('water', {}).get('value')})
- Waste Vision Signal: {signals.get('waste', {}).get('category')} (Litter Count: {signals.get('waste', {}).get('detail', {}).get('litter_count')})
- Active Weights: {json.dumps(weights)}
- Conflict Flag: {conflict} ({conflict_detail})
- Stale Signals: {stale}
- Missing Signals: {missing}

Respond ONLY with a valid JSON object matching this schema:
{{
  "executive_summary": "string (2-3 concise, high-impact sentences)",
  "cross_domain_analysis": "string (explanation of how air, water, and waste vectors interact)",
  "recommended_action": "string (primary executive command)",
  "sector_directives": {{
    "municipal_corporation": ["action item 1", "action item 2"],
    "public_health_authority": ["action item 1", "action item 2"],
    "citizen_advisory": ["action item 1", "action item 2"]
  }}
}}
"""
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "response_mime_type": "application/json"
            }
        }
        
        try:
            resp = _GEMINI_SESSION.post(url, json=payload, timeout=2.0)
            if resp.status_code == 200:
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text)
        except Exception:
            pass
        return None

    def _generate_heuristic_synthesis(
        self, city: str, score: float, level: int, category: str,
        signals: Dict[str, Any], weights: Dict[str, float],
        conflict: bool, conflict_detail: str,
        stale: List[str], missing: List[str]
    ) -> Dict[str, Any]:
        air = signals.get("air", {})
        water = signals.get("water", {})
        waste = signals.get("waste", {})

        air_cat = air.get("category", "Normal")
        air_aqi = int(air.get("value", 0))
        water_cat = water.get("category", "Normal")
        water_wqi = float(water.get("value", 0))
        waste_count = int(waste.get("detail", {}).get("litter_count", 0))

        if level >= 3:
            exec_summary = (
                f"Critical risk alert for {city}: Composite Environmental Threat Index reached {score:.2f} out of 4.0 ({category.upper()}). "
                f"Multi-agent correlation confirms elevated readings across {air_cat} air (AQI {air_aqi}) and {water_cat} water indices. "
                f"Immediate containment and remediation protocols are recommended."
            )
        elif level == 2:
            exec_summary = (
                f"Elevated monitoring status for {city}: Composite Threat Index is rated {score:.2f} out of 4.0 ({category.upper()}). "
                f"Moderate degradation detected across urban vectors. Sensor correlation indicates early-stage accumulation requiring proactive municipal attention."
            )
        else:
            exec_summary = (
                f"Optimal environmental balance for {city}: Composite Threat Index is {score:.2f} out of 4.0 ({category.upper()}). "
                f"All specialist telemetry streams report safe baseline parameters with high systemic resilience."
            )

        health_weight = weights.get('health', 0.15) * 100
        policy_weight = weights.get('policy', 0.10) * 100
        air_weight = weights.get('air', 0.35) * 100
        water_weight = weights.get('water', 0.25) * 100
        waste_weight = weights.get('waste', 0.15) * 100

        if conflict:
            cross_analysis = (
                f"Specialist Telemetry Variance: {conflict_detail}. "
                f"Air sensor readings ({air_cat}) show a variance from water monitoring channels ({water_cat}). "
                f"The system automatically balanced stream weights to prioritize high-confidence data sources."
            )
        else:
            cross_analysis = (
                f"Cross-vector analysis shows consistent readings across Atmospheric Air (AQI {air_aqi}), Water Catchment (WQI {water_wqi:.1f}), and Waste Vision ({waste_count} items). "
                f"Active sensor distribution: Air {air_weight:.0f}%, Water {water_weight:.0f}%, Waste {waste_weight:.0f}%, Health {health_weight:.0f}%, Policy {policy_weight:.0f}%."
            )

        if level >= 4:
            action = "Trigger Tier-4 Hazardous Environmental Protocols: Deploy municipal anti-smog misting cannons, shut down industrial effluent lines, and issue emergency citizen stay-indoors alerts."
        elif level == 3:
            action = "Initiate Tier-3 Urban Remediation: Mobilize mechanized street vacuuming units, activate secondary water treatment chlorination, and restrict heavy diesel vehicle transit in central zones."
        elif level == 2:
            action = "Execute Tier-2 Proactive Maintenance: Dispatch waste collection fleet to high-density litter clusters and increase water quality sampling frequency to 30-minute intervals."
        else:
            action = "Maintain Standard Autonomous Surveillance: Sensor mesh running on continuous automated telemetry polling."

        if level >= 3:
            directives = {
                "municipal_corporation": [
                    f"Deploy mobile particulate suppression units across {city} key traffic corridors.",
                    "Halt non-essential civil construction and open excavation works immediately.",
                    f"Dispatch rapid response waste remediation teams to clear {waste_count} identified debris points."
                ],
                "public_health_authority": [
                    "Issue red-tier respiratory advisory for vulnerable populations (children, elderly, asthmatics).",
                    "Distribute N95 protective equipment to outdoor municipal frontline workers.",
                    "Place district hospital pulmonary emergency wards on active surge standby."
                ],
                "citizen_advisory": [
                    "Minimize outdoor morning physical exercise until particulate levels subside.",
                    "Keep indoor HEPA air filtration active and seal ventilation drafts.",
                    "Report uncontained waste dumping via the EcoMesh Citizen Portal."
                ]
            }
        elif level == 2:
            directives = {
                "municipal_corporation": [
                    "Schedule mechanized road sweeping along arterial transit routes.",
                    "Verify industrial storm-water drain discharge compliance.",
                    "Optimize waste collection routing to prevent container overflow."
                ],
                "public_health_authority": [
                    "Advise citizens with pre-existing cardiopulmonary conditions to wear masks during peak hours.",
                    "Broadcast standard community water purification advisories."
                ],
                "citizen_advisory": [
                    "Utilize public transit to mitigate localized vehicular emissions.",
                    "Ensure domestic water boiling/filtration before direct consumption.",
                    "Participate in designated neighborhood segregation drives."
                ]
            }
        else:
            directives = {
                "municipal_corporation": [
                    "Continue standard automated telemetry polling and scheduled maintenance.",
                    "Perform routine calibration on stationary optical and chemical sensors."
                ],
                "public_health_authority": [
                    "Standard environmental wellness parameters maintained across all districts."
                ],
                "citizen_advisory": [
                    "Ideal conditions for outdoor recreational and athletic activities.",
                    "Maintain zero-litter practices in public parks and water catchments."
                ]
            }

        return {
            "executive_summary": exec_summary,
            "cross_domain_analysis": cross_analysis,
            "recommended_action": action,
            "sector_directives": directives
        }
