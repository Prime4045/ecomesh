import io
import os
import base64
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from PIL import Image

from graph.workflow import EcoMeshWorkflow
from agents.base import RISK_LEVEL_COLORS, RISK_LEVEL_NAMES
from services.aqi_client import AQIClient, CITY_FIXTURES, load_env_file
from services.vision import WasteVisionDetector

load_env_file()

app = FastAPI(
    title="EcoMesh API",
    description="Environmental Multi-Agent Risk Intelligence & Autonomous Decision Support Platform",
    version="2.5.0"
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Workflow instance
workflow = EcoMeshWorkflow(
    waqi_token=os.getenv("WAQI_API_TOKEN", "146d114a5f357f730c9087d526cce439bf3df728"),
    gemini_api_key=os.getenv("GEMINI_API_KEY", "")
)
vision_detector = WasteVisionDetector()

class PipelineRequest(BaseModel):
    city: str = "Delhi NCR"
    kill_water: bool = False
    stale_air: bool = False
    override_air_aqi: Optional[float] = None
    water_params: Optional[Dict[str, float]] = None
    gemini_key: Optional[str] = None
    waqi_token: Optional[str] = None

class PolicySimulateRequest(BaseModel):
    city: str = "Delhi NCR"
    baseline_aqi: float = 180.0
    baseline_wqi: float = 65.0
    baseline_litter: int = 4
    ev_adoption_pct: float = 0.0          # 0 - 100%
    smog_scrubbers_count: int = 0         # 0 - 50 towers
    river_effluent_ban: bool = False      # True / False
    drone_sweepers_active: bool = False   # True / False
    diesel_truck_ban: bool = False        # True / False

class StreamFrameRequest(BaseModel):
    image_base64: str

@app.get("/api/status")
def get_status():
    return {
        "status": "online",
        "system": "EcoMesh Autonomous Environmental Intelligence Ecosystem",
        "version": "2.5.0",
        "agents": [
            {"id": "air", "name": "Atmospheric Air Specialist", "role": "Pollutant Telemetry", "source": "WAQI API & Open-Meteo"},
            {"id": "water", "name": "Hydrological Catchment Specialist", "role": "WQI Physical Chem Model", "source": "NSF/CPCB Simulator"},
            {"id": "waste", "name": "Optical Computer Vision Specialist", "role": "Surface Debris Detection", "source": "YOLOv8n Neural Engine"},
            {"id": "health", "name": "Epidemiological Health Specialist", "role": "Clinical Exposure & Hospital Surge", "source": "CDC Cohort Matrix"},
            {"id": "policy", "name": "Municipal Policy & Logistics Specialist", "role": "Enforcement & Budget ROI", "source": "Civic Operations Command"},
            {"id": "coordinator", "name": "Consensus Coordinator Arbiter", "role": "Autonomous Synthesis & Debate", "source": "LangGraph StateGraph & Gemini 2.5"}
        ]
    }

@app.get("/api/locations/search")
def search_locations(q: str = Query(..., min_length=1)):
    """Dynamic worldwide search for any city or region globally."""
    results = AQIClient.search_worldwide_locations(q)
    return {"results": results}

@app.get("/api/stations")
def get_stations():
    stations = []
    for city_name, data in CITY_FIXTURES.items():
        geo = data.get("city", {}).get("geo", [20.5937, 78.9629])
        aqi = data.get("aqi", 100)
        risk = 4 if aqi > 250 else (3 if aqi > 150 else (2 if aqi > 100 else (1 if aqi > 50 else 0)))
        stations.append({
            "city": city_name,
            "lat": geo[0],
            "lon": geo[1],
            "aqi": aqi,
            "risk_level": risk,
            "category": RISK_LEVEL_NAMES.get(risk, "Normal"),
            "station_name": data.get("city", {}).get("name", city_name)
        })
    return {"stations": stations}

@app.post("/api/pipeline/run")
def run_pipeline(req: PipelineRequest):
    force_statuses = {
        "air": "stale" if req.stale_air else "ok",
        "water": "missing" if req.kill_water else "ok",
        "waste": "ok",
        "health": "ok",
        "policy": "ok"
    }

    force_overrides = {}
    if req.override_air_aqi is not None and req.override_air_aqi > 0:
        force_overrides["air"] = float(req.override_air_aqi)

    w_params = req.water_params

    # Use active token from .env or request override
    token = req.waqi_token or os.getenv("WAQI_API_TOKEN", "146d114a5f357f730c9087d526cce439bf3df728")
    gemini_key = req.gemini_key or os.getenv("GEMINI_API_KEY", "")

    wf = EcoMeshWorkflow(
        waqi_token=token,
        gemini_api_key=gemini_key
    )

    result = wf.run_pipeline(
        city=req.city,
        water_params=w_params,
        image_input=None,
        force_statuses=force_statuses,
        force_overrides=force_overrides
    )

    # Convert PIL images or binary in payload to serializable format
    signals_data = {}
    for agent_id, sig in result["signals"].items():
        sig_dict = sig.model_dump() if hasattr(sig, "model_dump") else sig.dict()
        if "detail" in sig_dict and "annotated_image" in sig_dict["detail"]:
            pil_img = sig_dict["detail"]["annotated_image"]
            if isinstance(pil_img, Image.Image):
                buf = io.BytesIO()
                pil_img.save(buf, format="JPEG")
                sig_dict["detail"]["annotated_image_base64"] = base64.b64encode(buf.getvalue()).decode("utf-8")
                sig_dict["detail"].pop("annotated_image", None)
        signals_data[agent_id] = sig_dict

    verdict_data = result["verdict"].model_dump() if hasattr(result["verdict"], "model_dump") else result["verdict"].dict()

    return {
        "city": result["city"],
        "signals": signals_data,
        "verdict": verdict_data,
        "trace_logs": result["trace_logs"],
        "risk_colors": RISK_LEVEL_COLORS
    }

@app.post("/api/policy/simulate")
def simulate_policy(req: PolicySimulateRequest):
    """What-If Policy Sandboxing Engine:
       Computes environmental impact, economic health savings, and 30-day forecast curves.
    """
    # 1. Atmospheric AQI Mitigation Math
    ev_reduction = (req.ev_adoption_pct / 100.0) * 0.28  # Up to 28% reduction from full EV transition
    scrubber_reduction = min(0.25, req.smog_scrubbers_count * 0.007) # Up to 25% from 50 towers
    diesel_reduction = 0.16 if req.diesel_truck_ban else 0.0

    total_air_reduction_pct = min(0.65, ev_reduction + scrubber_reduction + diesel_reduction)
    simulated_aqi = max(25.0, round(req.baseline_aqi * (1.0 - total_air_reduction_pct), 1))

    # 2. Hydrological Catchment WQI Improvement Math
    water_boost = 18.0 if req.river_effluent_ban else 0.0
    simulated_wqi = min(96.0, round(req.baseline_wqi + water_boost, 1))

    # 3. Waste Reduction Math
    waste_reduction_pct = 0.65 if req.drone_sweepers_active else 0.0
    simulated_litter = max(0, int(round(req.baseline_litter * (1.0 - waste_reduction_pct))))

    # 4. Composite Threat Recalculation
    air_risk = 4 if simulated_aqi > 250 else (3 if simulated_aqi > 150 else (2 if simulated_aqi > 100 else (1 if simulated_aqi > 50 else 0)))
    water_risk = 4 if simulated_wqi < 40 else (3 if simulated_wqi < 55 else (2 if simulated_wqi < 70 else (1 if simulated_wqi < 85 else 0)))
    waste_risk = 4 if simulated_litter >= 6 else (3 if simulated_litter >= 4 else (2 if simulated_litter >= 2 else (1 if simulated_litter >= 1 else 0)))

    simulated_score = round((0.40 * air_risk) + (0.35 * water_risk) + (0.25 * waste_risk), 2)
    simulated_level = int(round(simulated_score))

    # 5. Economic & Healthcare ROI Model
    aqi_drop = max(0.0, req.baseline_aqi - simulated_aqi)
    est_annual_health_savings_m = round((aqi_drop / 10.0) * 4.8, 1) # $4.8M saved per 10 AQI reduction
    icu_admissions_prevented = int(round((aqi_drop / 10.0) * 320))

    # 6. Projected 30-Day Recovery Curve
    days = [f"Day {d}" for d in [1, 5, 10, 15, 20, 25, 30]]
    trajectory_aqi = [
        round(req.baseline_aqi - (aqi_drop * (1 - (0.85 ** (i + 1)))))
        for i in range(len(days))
    ]

    return {
        "city": req.city,
        "baseline": {
            "aqi": req.baseline_aqi,
            "wqi": req.baseline_wqi,
            "litter": req.baseline_litter
        },
        "simulated": {
            "aqi": simulated_aqi,
            "wqi": simulated_wqi,
            "litter": simulated_litter,
            "threat_score": simulated_score,
            "threat_level": simulated_level,
            "threat_category": RISK_LEVEL_NAMES.get(simulated_level, "Unknown")
        },
        "impact_metrics": {
            "aqi_reduction_pct": round(total_air_reduction_pct * 100, 1),
            "annual_health_savings_usd_m": est_annual_health_savings_m,
            "icu_admissions_prevented": icu_admissions_prevented,
            "carbon_offset_tons_daily": int(round(req.ev_adoption_pct * 12.5 + req.smog_scrubbers_count * 8.0))
        },
        "forecast_trajectory": {
            "labels": days,
            "projected_aqi": trajectory_aqi
        }
    }

@app.post("/api/vision/analyze")
async def analyze_vision_image(file: UploadFile = File(...)):
    contents = await file.read()
    annotated_img, count, density, detections = vision_detector.analyze_image(contents)

    buf = io.BytesIO()
    annotated_img.save(buf, format="JPEG")
    b64_img = base64.b64encode(buf.getvalue()).decode("utf-8")

    return {
        "litter_count": count,
        "litter_density": density,
        "detections": detections,
        "annotated_image_base64": b64_img
    }

@app.post("/api/vision/stream-frame")
def analyze_stream_frame(req: StreamFrameRequest):
    """Ultra-fast video stream frame parser for live webcam detection."""
    try:
        raw_b64 = req.image_base64
        if "," in raw_b64:
            raw_b64 = raw_b64.split(",")[1]
        
        img_bytes = base64.b64decode(raw_b64)
        annotated_img, count, density, detections = vision_detector.analyze_image(img_bytes)

        buf = io.BytesIO()
        annotated_img.save(buf, format="JPEG", quality=80)
        res_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

        return {
            "success": True,
            "litter_count": count,
            "litter_density": density,
            "detections": detections,
            "annotated_image_base64": res_b64
        }
    except Exception as e:
        return {"success": False, "error": str(e), "litter_count": 0, "detections": []}

# Mount static frontend directory
os.makedirs("frontend", exist_ok=True)
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
