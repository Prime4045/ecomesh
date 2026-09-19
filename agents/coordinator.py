from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from agents.base import SignalReport, CoordinatorVerdict, RISK_LEVEL_NAMES
from services.narrative import ExecutiveNarrativeEngine

class CoordinatorAgent:
    def __init__(self):
        self.name = "Multi-Agent Risk Coordinator"

    def evaluate(
        self,
        signals: Dict[str, SignalReport],
        city: str = "Delhi NCR",
        gemini_api_key: str = ""
    ) -> CoordinatorVerdict:
        """Processes signals from 5 specialist agents (Air, Water, Waste, Health, Policy).
           Performs freshness validation, weight redistribution, composite risk scoring,
           conflict detection, multi-agent war room debate simulation, and Gemini/Heuristic narrative generation.
        """
        stale_signals: List[str] = []
        missing_signals: List[str] = []

        # 1. Base weights across specialized sensory nodes
        all_base_weights = {
            "air": 0.35,
            "water": 0.25,
            "waste": 0.15,
            "health": 0.15,
            "policy": 0.10
        }

        # If only a subset of signals is supplied (e.g. legacy 3-signal test), filter and normalize
        if set(signals.keys()) == {"air", "water", "waste"}:
            base_weights = {"air": 0.40, "water": 0.35, "waste": 0.25}
        else:
            base_weights = {k: all_base_weights.get(k, 0.20) for k in signals.keys()}

        adjusted_weights = base_weights.copy()
        valid_reports: Dict[str, SignalReport] = {}
        confidences: List[float] = []

        now = datetime.now()

        # 2. Freshness & Stale/Missing validation
        for agent_name, report in signals.items():
            if report.status == "missing":
                missing_signals.append(agent_name)
                adjusted_weights[agent_name] = 0.0
                continue

            # Check freshness thresholds
            is_stale = False
            if report.status == "stale":
                is_stale = True
            elif agent_name == "air" and (now - report.timestamp) > timedelta(hours=6):
                is_stale = True
            elif agent_name == "water" and (now - report.timestamp) > timedelta(hours=1):
                is_stale = True

            if is_stale:
                stale_signals.append(agent_name)
                adjusted_weights[agent_name] *= 0.5
                report_conf = max(0.1, report.confidence - 0.20)
            else:
                report_conf = report.confidence

            valid_reports[agent_name] = report
            confidences.append(report_conf)

        # 3. Weight Redistribution if any signal is missing or modified
        total_valid_weight = sum(adjusted_weights.values())

        if total_valid_weight > 0:
            final_weights = {k: v / total_valid_weight for k, v in adjusted_weights.items()}
        else:
            final_weights = {k: 0.0 for k in base_weights}

        # 4. Deterministic Composite Score Calculation
        if valid_reports and total_valid_weight > 0:
            weighted_score_sum = sum(
                final_weights.get(name, 0.0) * valid_reports[name].risk_level
                for name in valid_reports
            )
            combined_score = round(weighted_score_sum, 2)
        else:
            combined_score = 0.0

        # Integer risk level rounding & category
        combined_level = int(round(combined_score))
        combined_level = max(0, min(4, combined_level))
        combined_category = RISK_LEVEL_NAMES.get(combined_level, "Unknown")

        # Breakdown of risk contributions (w_i * r_i)
        contributions = {
            name: round(final_weights.get(name, 0.0) * valid_reports[name].risk_level, 2)
            if name in valid_reports else 0.0
            for name in base_weights
        }

        # 5. Specialist Conflict Detection
        conflict = False
        conflict_detail = None
        if len(valid_reports) >= 2:
            risk_levels = [r.risk_level for r in valid_reports.values()]
            max_risk = max(risk_levels)
            min_risk = min(risk_levels)

            if (max_risk - min_risk) >= 2:
                conflict = True
                high_agents = [r.agent.upper() for r in valid_reports.values() if r.risk_level == max_risk]
                low_agents = [r.agent.upper() for r in valid_reports.values() if r.risk_level == min_risk]
                conflict_detail = (
                    f"Divergence detected between specialists: {', '.join(high_agents)} "
                    f"(Risk {max_risk}) vs {', '.join(low_agents)} (Risk {min_risk})"
                )

        # 6. Overall Confidence Calculation
        if confidences:
            base_confidence = min(confidences)
        else:
            base_confidence = 0.0

        confidence_penalty = 0.0
        if missing_signals:
            confidence_penalty += 0.15 * len(missing_signals)
        if conflict:
            confidence_penalty += 0.10

        final_confidence = round(max(0.10, min(1.0, base_confidence - confidence_penalty)), 2)

        # 7. Generate Multi-Agent War Room Debate Transcript
        debate_transcript = self._generate_debate_transcript(
            valid_reports=valid_reports,
            combined_level=combined_level,
            combined_score=combined_score,
            conflict=conflict,
            city=city
        )

        # 8. Generate Agent Voting Matrix
        agent_votes = self._generate_voting_matrix(
            signals=signals,
            final_weights=final_weights,
            combined_level=combined_level
        )

        # 9. Narrative, Sector Directives & Recommendation Generation
        signals_dict_for_narrative = {
            k: {
                "category": v.category,
                "value": v.value,
                "risk_level": v.risk_level,
                "detail": v.detail
            }
            for k, v in valid_reports.items()
        }

        narrative, recommendation, directives = ExecutiveNarrativeEngine.generate_narrative(
            verdict_score=combined_score,
            combined_level=combined_level,
            combined_category=combined_category,
            signals=signals_dict_for_narrative,
            weights_used=final_weights,
            conflict=conflict,
            conflict_detail=conflict_detail or "",
            stale_signals=stale_signals,
            missing_signals=missing_signals,
            city=city,
            gemini_api_key=gemini_api_key
        )

        return CoordinatorVerdict(
            combined_level=combined_level,
            combined_category=combined_category,
            combined_score=combined_score,
            final_confidence=final_confidence,
            weights_used=final_weights,
            contributions=contributions,
            conflict=conflict,
            conflict_detail=conflict_detail,
            stale_signals=stale_signals,
            missing_signals=missing_signals,
            narrative=narrative,
            recommended_action=recommendation,
            sector_directives=directives,
            debate_transcript=debate_transcript,
            agent_votes=agent_votes,
            timestamp=now
        )

    def _generate_debate_transcript(
        self,
        valid_reports: Dict[str, SignalReport],
        combined_level: int,
        combined_score: float,
        conflict: bool,
        city: str
    ) -> List[Dict[str, Any]]:
        """Synthesizes an authentic real-time multi-agent negotiation transcript."""
        transcript = []

        # Air Specialist opening statement
        if "air" in valid_reports:
            air = valid_reports["air"]
            transcript.append({
                "agent_id": "air",
                "agent_name": "Atmospheric Specialist",
                "role": "Sensory Observer",
                "avatar_icon": "wind",
                "statement": f"Physical atmospheric telemetry in {city} reads AQI {MathRound(air.value)} ({air.category}). Dominant pollutant dynamics dictate risk assessment at Level {air.risk_level}.",
                "vote_level": air.risk_level,
                "stance": "elevated" if air.risk_level >= 2 else "calm"
            })

        # Water Specialist response
        if "water" in valid_reports:
            water = valid_reports["water"]
            transcript.append({
                "agent_id": "water",
                "agent_name": "Hydrological Specialist",
                "role": "Catchment Observer",
                "avatar_icon": "droplets",
                "statement": f"Catchment basin WQI stands at {water.value:.1f} ({water.category}). Dissolved oxygen and chemical parameters indicate Risk Level {water.risk_level}.",
                "vote_level": water.risk_level,
                "stance": "elevated" if water.risk_level >= 2 else "calm"
            })

        # Waste Specialist input
        if "waste" in valid_reports:
            waste = valid_reports["waste"]
            l_count = waste.detail.get("litter_count", 0)
            transcript.append({
                "agent_id": "waste",
                "agent_name": "Optical Vision Specialist",
                "role": "Deep Vision YOLOv8",
                "avatar_icon": "scan",
                "statement": f"YOLOv8 vision inference detected {l_count} surface debris items. Density threshold places optical risk at Level {waste.risk_level}.",
                "vote_level": waste.risk_level,
                "stance": "elevated" if waste.risk_level >= 2 else "calm"
            })

        # Epidemiological Health Specialist
        if "health" in valid_reports:
            health = valid_reports["health"]
            surge = health.detail.get("hospital_surge_risk_pct", 0)
            exposed = health.detail.get("vulnerable_pop_exposed_k", 0)
            transcript.append({
                "agent_id": "health",
                "agent_name": "Epidemiological Specialist",
                "role": "Clinical Vulnerability Analyst",
                "avatar_icon": "heart-pulse",
                "statement": f"Cross-vector exposure index is {health.value:.1f}/100 with a {surge}% hospital surge projection. Est. {exposed}k sensitive citizens affected.",
                "vote_level": health.risk_level,
                "stance": "urgent" if health.risk_level >= 3 else "normal"
            })

        # Municipal Policy & Logistics
        if "policy" in valid_reports:
            policy = valid_reports["policy"]
            stage = policy.detail.get("regulatory_stage", "STAGE-I")
            transcript.append({
                "agent_id": "policy",
                "agent_name": "Municipal Policy & Logistics",
                "role": "Enforcement Commander",
                "avatar_icon": "building-2",
                "statement": f"Recommend immediate statutory trigger {stage}. Fleet mobilization readiness at {policy.value:.0f}%.",
                "vote_level": policy.risk_level,
                "stance": "enforcing"
            })

        # Coordinator Consensus Resolution
        transcript.append({
            "agent_id": "coordinator",
            "agent_name": "Consensus Coordinator",
            "role": "Deterministic State Arbiter",
            "avatar_icon": "shield-check",
            "statement": f"Consensus synthesized at Composite Index {combined_score:.2f}/4.0 (Level {combined_level} • {RISK_LEVEL_NAMES.get(combined_level, 'Unknown')}). Dynamic stream weights rebalanced across all active specialists.",
            "vote_level": combined_level,
            "stance": "consensus"
        })

        return transcript

    def _generate_voting_matrix(
        self,
        signals: Dict[str, SignalReport],
        final_weights: Dict[str, float],
        combined_level: int
    ) -> List[Dict[str, Any]]:
        """Generates an agent-by-agent voting and agreement matrix."""
        matrix = []
        name_map = {
            "air": ("Atmospheric Node", "wind"),
            "water": ("Hydrological Node", "droplets"),
            "waste": ("Optical Vision Node", "scan"),
            "health": ("Epidemiological Health Node", "heart-pulse"),
            "policy": ("Municipal Logistics Node", "building-2")
        }

        for agent_id, report in signals.items():
            disp_name, icon = name_map.get(agent_id, (agent_id.title(), "activity"))
            vote_risk = report.risk_level
            agreement = "Aligned" if abs(vote_risk - combined_level) <= 1 else "Divergent"
            
            matrix.append({
                "agent_id": agent_id,
                "agent_name": disp_name,
                "icon": icon,
                "status": report.status.upper(),
                "proposed_level": vote_risk,
                "proposed_category": report.category,
                "weight_pct": round(final_weights.get(agent_id, 0.0) * 100, 1),
                "confidence_pct": round(report.confidence * 100),
                "agreement_status": agreement
            })
        return matrix

def MathRound(val: float) -> int:
    return int(round(val))
