from typing import Dict, Any, List, Tuple
from services.gemini_engine import GeminiSynthesisEngine

class ExecutiveNarrativeEngine:
    @staticmethod
    def generate_narrative(
        verdict_score: float,
        combined_level: int,
        combined_category: str,
        signals: Dict[str, Any],
        weights_used: Dict[str, float],
        conflict: bool,
        conflict_detail: str,
        stale_signals: List[str],
        missing_signals: List[str],
        city: str = "Delhi NCR",
        gemini_api_key: str = ""
    ) -> Tuple[str, str, Dict[str, List[str]]]:
        """Generates an executive narrative, actionable recommendation,
        and sector directives using Gemini / heuristic engine.
        """
        engine = GeminiSynthesisEngine(api_key=gemini_api_key)
        synth = engine.synthesize_executive_brief(
            city=city,
            verdict_score=verdict_score,
            combined_level=combined_level,
            combined_category=combined_category,
            signals=signals,
            weights_used=weights_used,
            conflict=conflict,
            conflict_detail=conflict_detail,
            stale_signals=stale_signals,
            missing_signals=missing_signals
        )
        
        narrative = f"{synth['executive_summary']}\n\n{synth['cross_domain_analysis']}"
        recommendation = synth["recommended_action"]
        directives = synth.get("sector_directives", {})
        
        return narrative, recommendation, directives
