import unittest
from datetime import datetime, timedelta
from agents.base import SignalReport, CoordinatorVerdict
from agents.air_agent import AirQualityAgent
from agents.water_agent import WaterQualityAgent
from agents.waste_agent import WasteQualityAgent
from agents.health_agent import EpidemiologicalHealthAgent
from agents.policy_agent import MunicipalPolicyAgent
from agents.coordinator import CoordinatorAgent
from services.wqi import WaterQualityCalculator
from graph.workflow import EcoMeshWorkflow

class TestEcoMeshMultiAgentSystem(unittest.TestCase):
    def test_wqi_calculator(self):
        params = {"ph": 7.2, "do": 7.5, "bod": 1.5, "turbidity": 3.0, "conductance": 300.0}
        wqi, risk, category = WaterQualityCalculator.calculate_wqi(params)
        self.assertGreaterEqual(wqi, 80.0)
        self.assertEqual(risk, 0)
        self.assertEqual(category, "Good")

    def test_air_agent(self):
        agent = AirQualityAgent()
        report = agent.run(city="Delhi NCR", force_aqi=250)
        self.assertEqual(report.agent, "air")
        self.assertEqual(report.risk_level, 3)
        self.assertEqual(report.category, "Poor")

    def test_water_agent(self):
        agent = WaterQualityAgent()
        report = agent.run(force_wqi=45.0)
        self.assertEqual(report.agent, "water")
        self.assertEqual(report.risk_level, 3)
        self.assertEqual(report.category, "Poor")

    def test_waste_agent(self):
        agent = WasteQualityAgent()
        report = agent.run(force_litter_count=5)
        self.assertEqual(report.agent, "waste")
        self.assertEqual(report.risk_level, 3)
        self.assertEqual(report.category, "Poor")

    def test_health_agent(self):
        agent = EpidemiologicalHealthAgent()
        report = agent.run(city="Delhi NCR", air_aqi=280.0, water_wqi=45.0, waste_count=6)
        self.assertEqual(report.agent, "health")
        self.assertGreaterEqual(report.risk_level, 3)
        self.assertIn("hospital_surge_risk_pct", report.detail)

    def test_policy_agent(self):
        agent = MunicipalPolicyAgent()
        report = agent.run(city="Delhi NCR", air_aqi=250.0, composite_risk=3)
        self.assertEqual(report.agent, "policy")
        self.assertGreaterEqual(report.risk_level, 2)
        self.assertIn("STAGE", report.detail.get("regulatory_stage", ""))

    def test_coordinator_weight_redistribution_when_missing(self):
        air_agent = AirQualityAgent()
        water_agent = WaterQualityAgent()
        waste_agent = WasteQualityAgent()
        coordinator = CoordinatorAgent()

        signals = {
            "air": air_agent.run(force_aqi=100),       # risk 1, weight 0.40
            "water": water_agent.run(force_status="missing"), # missing weight 0 -> redistributed
            "waste": waste_agent.run(force_litter_count=0) # risk 0, weight 0.25
        }

        verdict = coordinator.evaluate(signals)
        self.assertIn("water", verdict.missing_signals)
        self.assertAlmostEqual(verdict.weights_used["air"], 0.40 / 0.65, places=2)
        self.assertAlmostEqual(verdict.weights_used["waste"], 0.25 / 0.65, places=2)
        self.assertEqual(verdict.weights_used["water"], 0.0)

    def test_coordinator_conflict_detection(self):
        air_agent = AirQualityAgent()
        water_agent = WaterQualityAgent()
        waste_agent = WasteQualityAgent()
        coordinator = CoordinatorAgent()

        signals = {
            "air": air_agent.run(force_aqi=350),          # Risk 4 (Severe)
            "water": water_agent.run(force_wqi=90.0),       # Risk 0 (Good)
            "waste": waste_agent.run(force_litter_count=0) # Risk 0 (Good)
        }

        verdict = coordinator.evaluate(signals)
        self.assertTrue(verdict.conflict)
        self.assertIsNotNone(verdict.conflict_detail)
        self.assertIn("AIR", verdict.conflict_detail)

    def test_workflow_execution(self):
        workflow = EcoMeshWorkflow()
        state = workflow.run_pipeline(city="Bengaluru")
        self.assertIn("verdict", state)
        self.assertEqual(len(state["trace_logs"]), 6)
        self.assertIn("health", state["signals"])
        self.assertIn("policy", state["signals"])

if __name__ == "__main__":
    unittest.main()
