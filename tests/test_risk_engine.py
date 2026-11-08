"""
Unit tests for SetuSentry Risk Prioritisation Engine.
Validates triage scoring logic, overdue weighting, explainable breakdowns,
and strict safety compliance rules (no "probability of collapse" wording).
"""

import unittest
import sys
import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from risk_engine import (
    calculate_bridge_risk,
    rank_bridges_by_risk,
    CATEGORY_LOW,
    CATEGORY_MEDIUM,
    CATEGORY_HIGH,
    CATEGORY_CRITICAL,
    DISCLAIMER_TEXT,
)


class TestRiskEngine(unittest.TestCase):

    def test_pristine_new_bridge_low_priority(self):
        bridge = {
            "bridge_id": "LOW-001",
            "name": "New Cable Bridge",
            "construction_year": 2022,
            "last_inspection_date": "2026-01-01",
            "risk_flood_zone": 0,
            "risk_high_traffic": 0,
            "risk_age_over30": 0,
            "risk_previous_scour": 0,
            "risk_previous_cracks": 0,
        }
        inspections = [
            {
                "inspection_date": "2026-01-01",
                "severity_rating": 1,
                "action_status": "Completed",
            }
        ]

        result = calculate_bridge_risk(bridge, inspections, reference_date="2026-03-01")
        self.assertEqual(result["category"], CATEGORY_LOW)
        self.assertLess(result["score"], 30)
        self.assertIn(DISCLAIMER_TEXT, result["disclaimer"])

    def test_overdue_and_aged_elevates_priority(self):
        bridge = {
            "bridge_id": "HIGH-001",
            "name": "Old Uninspected Bridge",
            "construction_year": 1965,  # 61 years old
            "last_inspection_date": "2022-01-01",  # Over 4 years overdue
            "risk_flood_zone": 1,
            "risk_previous_scour": 1,
            "risk_previous_cracks": 1,
        }
        inspections = [
            {
                "inspection_date": "2022-01-01",
                "severity_rating": 5,
                "action_status": "Escalated",
            }
        ]

        result = calculate_bridge_risk(bridge, inspections, reference_date="2026-03-01")
        self.assertIn(result["category"], [CATEGORY_HIGH, CATEGORY_CRITICAL])
        self.assertGreaterEqual(result["score"], 55)

        # Check explainable reasons
        reasons_text = " ".join(result["reasons"]).lower()
        self.assertIn("overdue", reasons_text)
        self.assertIn("scour", reasons_text)
        self.assertIn("escalated", reasons_text)

    def test_safety_rule_no_collapse_probability(self):
        """CRITICAL REQUIREMENT: Verify that 'probability of collapse' is NEVER used."""
        bridge = {
            "bridge_id": "CRIT-001",
            "name": "Severely Degraded Bridge",
            "construction_year": 1950,
            "last_inspection_date": "2018-01-01",
            "risk_flood_zone": 1,
            "risk_previous_scour": 1,
            "risk_previous_cracks": 1,
        }
        inspections = [
            {
                "inspection_date": "2018-01-01",
                "severity_rating": 5,
                "action_status": "Escalated",
            }
        ]

        result = calculate_bridge_risk(bridge, inspections, reference_date="2026-03-01")

        # Convert all result strings to lower case and verify
        full_output_str = str(result).lower()
        self.assertNotIn("probability of collapse", full_output_str)
        self.assertNotIn("chance of collapse", full_output_str)
        self.assertNotIn("collapse prediction", full_output_str)

    def test_ranking_order(self):
        bridges = [
            {
                "bridge_id": "B-LOW",
                "name": "Low Risk Bridge",
                "construction_year": 2020,
                "last_inspection_date": "2026-01-15",
            },
            {
                "bridge_id": "B-CRIT",
                "name": "Critical Risk Bridge",
                "construction_year": 1960,
                "last_inspection_date": "2021-01-01",
                "risk_flood_zone": 1,
                "risk_previous_scour": 1,
                "risk_previous_cracks": 1,
            },
        ]
        inspections_map = {
            "B-LOW": [{"inspection_date": "2026-01-15", "severity_rating": 1, "action_status": "Completed"}],
            "B-CRIT": [{"inspection_date": "2021-01-01", "severity_rating": 5, "action_status": "Escalated"}],
        }

        ranked = rank_bridges_by_risk(bridges, inspections_map, reference_date="2026-03-01")
        self.assertEqual(ranked[0]["bridge_id"], "B-CRIT")
        self.assertEqual(ranked[1]["bridge_id"], "B-LOW")


if __name__ == "__main__":
    unittest.main()
