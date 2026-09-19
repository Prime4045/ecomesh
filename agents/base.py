from datetime import datetime
from typing import Literal, Dict, Any, List, Optional
from pydantic import BaseModel, Field

RISK_LEVEL_NAMES = {
    0: "Good",
    1: "Satisfactory",
    2: "Moderate",
    3: "Poor",
    4: "Severe"
}

RISK_LEVEL_COLORS = {
    0: "#10B981",  # Emerald Green
    1: "#06B6D4",  # Cyan Blue
    2: "#F59E0B",  # Amber Yellow
    3: "#F97316",  # Vibrant Orange
    4: "#EF4444"   # Crimson Red
}

class SignalReport(BaseModel):
    agent: Literal["air", "water", "waste", "health", "policy"]
    status: Literal["ok", "stale", "missing"] = "ok"
    value: float                                    # AQI / WQI / litter-density / index
    unit: str                                       # "AQI index", "WQI index", "items/m²", etc.
    risk_level: int = Field(ge=0, le=4)             # 0 to 4
    category: str                                   # "Good", "Satisfactory", "Moderate", "Poor", "Severe"
    confidence: float = Field(ge=0.0, le=1.0)       # 0.0 to 1.0
    weight: float                                   # default weight e.g. 0.35 / 0.25 / 0.15 / 0.15 / 0.10
    timestamp: datetime                             # sample timestamp
    source: str                                     # e.g., "WAQI Live API", "WQI Simulator", "YOLOv8 Vision"
    summary: str                                    # agent concise rationale
    detail: Dict[str, Any] = Field(default_factory=dict) # raw metrics (pollutants, chemical values, bounding boxes)

class CoordinatorVerdict(BaseModel):
    combined_level: int                             # 0 to 4
    combined_category: str                          # "Good", "Satisfactory", "Moderate", "Poor", "Severe"
    combined_score: float                           # Weighted composite score 0.0 - 4.0
    final_confidence: float                         # 0.0 - 1.0 after penalties
    weights_used: Dict[str, float]                  # Effective weights after redistribution
    contributions: Dict[str, float]                 # Signal contribution breakdown
    conflict: bool                                  # True if specialist conflict detected
    conflict_detail: Optional[str] = None           # Details on discrepancy
    stale_signals: List[str] = Field(default_factory=list)
    missing_signals: List[str] = Field(default_factory=list)
    narrative: str                                  # AI Executive synthesis
    recommended_action: str                         # Decision support action item
    sector_directives: Dict[str, List[str]] = Field(default_factory=dict) # Sector specific action plans
    debate_transcript: List[Dict[str, Any]] = Field(default_factory=list) # Multi-Agent War Room Debate
    agent_votes: List[Dict[str, Any]] = Field(default_factory=list)      # Agent Voting Matrix
    timestamp: datetime = Field(default_factory=datetime.now)
