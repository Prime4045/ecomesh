import time
from typing import TypedDict, Dict, Any, List, Optional
from datetime import datetime
from agents.base import SignalReport, CoordinatorVerdict
from agents.air_agent import AirQualityAgent
from agents.water_agent import WaterQualityAgent
from agents.waste_agent import WasteQualityAgent
from agents.health_agent import EpidemiologicalHealthAgent
from agents.policy_agent import MunicipalPolicyAgent
from agents.coordinator import CoordinatorAgent

class EcoMeshState(TypedDict):
    city: str
    water_params: Optional[Dict[str, float]]
    image_input: Optional[Any]
    force_statuses: Dict[str, str]          # e.g. {"air": "ok", "water": "missing", "waste": "ok", "health": "ok", "policy": "ok"}
    force_overrides: Dict[str, float]       # e.g. {"air": 280.0, "water": 45.0, "waste": 8}
    signals: Dict[str, SignalReport]
    verdict: Optional[CoordinatorVerdict]
    trace_logs: List[Dict[str, Any]]

class EcoMeshWorkflow:
    def __init__(self, waqi_token: str = "demo", gemini_api_key: str = "", *args, **kwargs):
        self.air_agent = AirQualityAgent(waqi_token=waqi_token)
        self.water_agent = WaterQualityAgent()
        self.waste_agent = WasteQualityAgent()
        self.health_agent = EpidemiologicalHealthAgent()
        self.policy_agent = MunicipalPolicyAgent()
        self.coordinator = CoordinatorAgent()
        self.gemini_api_key = gemini_api_key or kwargs.get("gemini_api_key", "")

    def run_pipeline(
        self,
        city: str = "Delhi NCR",
        water_params: Optional[Dict[str, float]] = None,
        image_input: Optional[Any] = None,
        force_statuses: Optional[Dict[str, str]] = None,
        force_overrides: Optional[Dict[str, float]] = None
    ) -> EcoMeshState:
        """Executes the full 5-agent multi-agent pipeline:
           Air -> Water -> Waste -> Health -> Policy -> Coordinator -> Final State
        """
        if force_statuses is None:
            force_statuses = {"air": "ok", "water": "ok", "waste": "ok", "health": "ok", "policy": "ok"}
        if force_overrides is None:
            force_overrides = {}

        trace_logs: List[Dict[str, Any]] = []
        signals: Dict[str, SignalReport] = {}

        # Step 1: Air Quality Specialist Node
        t0 = time.time()
        air_status = force_statuses.get("air", "ok")
        air_aqi = force_overrides.get("air", None)
        air_report = self.air_agent.run(city=city, force_status=air_status, force_aqi=air_aqi)
        air_duration = round((time.time() - t0) * 1000, 1)
        signals["air"] = air_report
        trace_logs.append({
            "step": 1,
            "node": "air_agent",
            "agent_name": "Atmospheric Air Specialist",
            "timestamp": datetime.now().strftime("%H:%M:%S.%f")[:-3],
            "latency_ms": air_duration,
            "status": air_report.status,
            "output_summary": air_report.summary,
            "risk_level": air_report.risk_level,
            "category": air_report.category,
            "payload": air_report.model_dump() if hasattr(air_report, "model_dump") else air_report.dict()
        })

        # Step 2: Water Quality Specialist Node
        t1 = time.time()
        water_status = force_statuses.get("water", "ok")
        water_wqi = force_overrides.get("water", None)
        water_report = self.water_agent.run(
            city=city,
            water_params=water_params,
            force_status=water_status,
            force_wqi=water_wqi
        )
        water_duration = round((time.time() - t1) * 1000, 1)
        signals["water"] = water_report
        trace_logs.append({
            "step": 2,
            "node": "water_agent",
            "agent_name": "Hydrological Catchment Specialist",
            "timestamp": datetime.now().strftime("%H:%M:%S.%f")[:-3],
            "latency_ms": water_duration,
            "status": water_report.status,
            "output_summary": water_report.summary,
            "risk_level": water_report.risk_level,
            "category": water_report.category,
            "payload": water_report.model_dump() if hasattr(water_report, "model_dump") else water_report.dict()
        })

        # Step 3: Waste & Litter Specialist Node
        t2 = time.time()
        waste_status = force_statuses.get("waste", "ok")
        litter_count = int(force_overrides["waste"]) if "waste" in force_overrides else None
        waste_report = self.waste_agent.run(
            city=city,
            image_input=image_input,
            force_status=waste_status,
            force_litter_count=litter_count
        )
        waste_duration = round((time.time() - t2) * 1000, 1)
        signals["waste"] = waste_report
        
        waste_payload = waste_report.model_dump() if hasattr(waste_report, "model_dump") else waste_report.dict()
        if "detail" in waste_payload and "annotated_image" in waste_payload["detail"]:
            waste_payload["detail"].pop("annotated_image", None)

        trace_logs.append({
            "step": 3,
            "node": "waste_agent",
            "agent_name": "Optical Vision Specialist (YOLOv8)",
            "timestamp": datetime.now().strftime("%H:%M:%S.%f")[:-3],
            "latency_ms": waste_duration,
            "status": waste_report.status,
            "output_summary": waste_report.summary,
            "risk_level": waste_report.risk_level,
            "category": waste_report.category,
            "payload": waste_payload
        })

        # Step 4: Epidemiological Public Health Specialist Node
        t3 = time.time()
        health_status = force_statuses.get("health", "ok")
        health_report = self.health_agent.run(
            city=city,
            air_aqi=air_report.value,
            water_wqi=water_report.value,
            waste_count=waste_report.detail.get("litter_count", 1),
            force_status=health_status
        )
        health_duration = round((time.time() - t3) * 1000, 1)
        signals["health"] = health_report
        trace_logs.append({
            "step": 4,
            "node": "health_agent",
            "agent_name": "Epidemiological Health Specialist",
            "timestamp": datetime.now().strftime("%H:%M:%S.%f")[:-3],
            "latency_ms": health_duration,
            "status": health_report.status,
            "output_summary": health_report.summary,
            "risk_level": health_report.risk_level,
            "category": health_report.category,
            "payload": health_report.model_dump() if hasattr(health_report, "model_dump") else health_report.dict()
        })

        # Step 5: Municipal Policy & Logistics Node
        t4 = time.time()
        policy_status = force_statuses.get("policy", "ok")
        policy_report = self.policy_agent.run(
            city=city,
            composite_risk=max(air_report.risk_level, health_report.risk_level),
            air_aqi=air_report.value,
            water_wqi=water_report.value,
            force_status=policy_status
        )
        policy_duration = round((time.time() - t4) * 1000, 1)
        signals["policy"] = policy_report
        trace_logs.append({
            "step": 5,
            "node": "policy_agent",
            "agent_name": "Municipal Policy & Logistics",
            "timestamp": datetime.now().strftime("%H:%M:%S.%f")[:-3],
            "latency_ms": policy_duration,
            "status": policy_report.status,
            "output_summary": policy_report.summary,
            "risk_level": policy_report.risk_level,
            "category": policy_report.category,
            "payload": policy_report.model_dump() if hasattr(policy_report, "model_dump") else policy_report.dict()
        })

        # Step 6: Multi-Agent Coordinator Node (Consensus, War Room Debate & Gemini Reasoning)
        t5 = time.time()
        verdict = self.coordinator.evaluate(
            signals=signals,
            city=city,
            gemini_api_key=self.gemini_api_key
        )
        coord_duration = round((time.time() - t5) * 1000, 1)
        trace_logs.append({
            "step": 6,
            "node": "coordinator",
            "agent_name": "Multi-Agent Consensus Arbiter (Gemini 2.5)",
            "timestamp": datetime.now().strftime("%H:%M:%S.%f")[:-3],
            "latency_ms": coord_duration,
            "status": "verdict_reached",
            "output_summary": f"Unified Risk Level: {verdict.combined_category} (Score: {verdict.combined_score}, Conf: {int(verdict.final_confidence*100)}%)",
            "risk_level": verdict.combined_level,
            "category": verdict.combined_category,
            "payload": verdict.model_dump() if hasattr(verdict, "model_dump") else verdict.dict()
        })

        return {
            "city": city,
            "water_params": water_params,
            "image_input": image_input,
            "force_statuses": force_statuses,
            "force_overrides": force_overrides,
            "signals": signals,
            "verdict": verdict,
            "trace_logs": trace_logs
        }
