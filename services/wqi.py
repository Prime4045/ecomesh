from typing import Dict, Any, Tuple

class WaterQualityCalculator:
    """Calculates Water Quality Index (WQI) on a 0-100 scale using standard environmental weighting:
       100-90: Excellent (Risk 0)
       89-70: Good/Satisfactory (Risk 1)
       69-50: Medium/Moderate (Risk 2)
       49-25: Bad/Poor (Risk 3)
       24-0: Very Bad/Severe (Risk 4)
    """

    @staticmethod
    def calculate_wqi(params: Dict[str, float]) -> Tuple[float, int, str]:
        """Calculates WQI score, assigned risk level (0-4), and category string."""
        ph = params.get("ph", 7.2)
        do = params.get("do", 6.5)       # mg/L
        bod = params.get("bod", 2.0)     # mg/L
        turbidity = params.get("turbidity", 4.0) # NTU
        conductance = params.get("conductance", 350.0) # µS/cm

        # Sub-index calculations (q_i)
        # 1. pH sub-index (ideal 7.0)
        q_ph = 100 - abs(ph - 7.0) * 25.0
        q_ph = max(0.0, min(100.0, q_ph))

        # 2. Dissolved Oxygen sub-index (ideal >= 7.0 mg/L)
        q_do = min(100.0, (do / 8.0) * 100.0)

        # 3. Biological Oxygen Demand sub-index (ideal <= 2.0 mg/L)
        q_bod = max(0.0, 100.0 - (bod - 1.0) * 20.0)

        # 4. Turbidity sub-index (ideal <= 5 NTU)
        q_turb = max(0.0, 100.0 - (turbidity / 15.0) * 100.0)

        # 5. Conductance sub-index (ideal <= 500 µS/cm)
        q_cond = max(0.0, 100.0 - (conductance / 1000.0) * 100.0)

        # Weights (sum = 1.0)
        weights = {
            "do": 0.30,
            "bod": 0.25,
            "ph": 0.20,
            "turbidity": 0.15,
            "conductance": 0.10
        }

        wqi = (
            q_do * weights["do"] +
            q_bod * weights["bod"] +
            q_ph * weights["ph"] +
            q_turb * weights["turbidity"] +
            q_cond * weights["conductance"]
        )

        wqi = round(max(0.0, min(100.0, wqi)), 1)

        # Map WQI (0-100 quality score) to Risk Level (0-4) where 0 is safest, 4 is most severe
        if wqi >= 85:
            risk = 0
            category = "Good"
        elif wqi >= 70:
            risk = 1
            category = "Satisfactory"
        elif wqi >= 50:
            risk = 2
            category = "Moderate"
        elif wqi >= 30:
            risk = 3
            category = "Poor"
        else:
            risk = 4
            category = "Severe"

        return wqi, risk, category
