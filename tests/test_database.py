"""
Unit tests for SetuSentry database module.
Uses a temporary isolated SQLite file to verify schema and CRUD queries.
"""

import gc
import os
import tempfile
import unittest
import sys

# Ensure parent directory is in path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from database import (
    add_bridge,
    add_inspection,
    delete_bridge,
    get_all_bridges,
    get_all_inspections,
    get_bridge,
    get_inspections_for_bridge,
    get_overdue_bridges,
    get_unresolved_inspections,
    init_db,
    update_bridge,
    update_inspection_status,
)


class TestDatabaseModule(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.db_path = os.path.join(self.temp_dir.name, "test_setusentry.db")
        init_db(self.db_path)

    def tearDown(self):
        gc.collect()
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    def test_init_db(self):
        self.assertTrue(os.path.exists(self.db_path))
        bridges = get_all_bridges(self.db_path)
        self.assertEqual(len(bridges), 0)

    def test_bridge_crud(self):
        test_bridge = {
            "bridge_id": "TEST-001",
            "name": "Test Girder Bridge [DEMONSTRATION RECORD]",
            "location": "Test City",
            "state": "Test State",
            "bridge_type": "Beam",
            "construction_year": 1990,
            "span_length": 500.0,
            "design_load": 70.0,
            "last_inspection_date": "2024-01-01",
            "risk_flood_zone": 1,
            "risk_high_traffic": 0,
            "risk_age_over30": 1,
            "risk_previous_scour": 0,
            "risk_previous_cracks": 1,
            "notes": "Test notes",
        }

        # Create
        row_id = add_bridge(test_bridge, self.db_path)
        self.assertGreater(row_id, 0)

        # Read
        b = get_bridge("TEST-001", self.db_path)
        self.assertIsNotNone(b)
        self.assertEqual(b["name"], "Test Girder Bridge [DEMONSTRATION RECORD]")
        self.assertEqual(b["risk_flood_zone"], 1)

        # Update
        updated = update_bridge("TEST-001", {"name": "Updated Bridge Name", "design_load": 85.0}, self.db_path)
        self.assertTrue(updated)
        b_up = get_bridge("TEST-001", self.db_path)
        self.assertEqual(b_up["name"], "Updated Bridge Name")
        self.assertEqual(b_up["design_load"], 85.0)

        # Delete
        deleted = delete_bridge("TEST-001", self.db_path)
        self.assertTrue(deleted)
        self.assertIsNone(get_bridge("TEST-001", self.db_path))

    def test_inspection_crud(self):
        # Insert parent bridge
        add_bridge({
            "bridge_id": "TEST-002",
            "name": "Arch Bridge [DEMONSTRATION RECORD]",
            "location": "Riverfront",
            "state": "AP",
            "bridge_type": "Arch",
            "construction_year": 1980,
            "span_length": 300.0,
            "design_load": 60.0,
            "last_inspection_date": "2023-01-01",
        }, self.db_path)

        insp_data = {
            "bridge_id": "TEST-002",
            "inspection_date": "2024-05-10",
            "inspector_name": "Er. Test Inspector",
            "inspection_type": "Visual",
            "observations": "Minor surface wear",
            "severity_rating": 2,
            "action_status": "Pending",
            "ai_crack_detected": 0,
            "ai_confidence": 0.85,
            "ai_severity": "None",
        }
        insp_id = add_inspection(insp_data, self.db_path)
        self.assertGreater(insp_id, 0)

        # Verify bridge last_inspection_date auto-updated
        b = get_bridge("TEST-002", self.db_path)
        self.assertEqual(b["last_inspection_date"], "2024-05-10")

        # Query inspections for bridge
        records = get_inspections_for_bridge("TEST-002", self.db_path)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["action_status"], "Pending")

        # Update status
        ok = update_inspection_status(insp_id, "Completed", self.db_path)
        self.assertTrue(ok)
        unres = get_unresolved_inspections(self.db_path)
        self.assertEqual(len(unres), 0)

    def test_overdue_bridges(self):
        add_bridge({
            "bridge_id": "OVERDUE-001",
            "name": "Old Overdue Bridge",
            "location": "Loc",
            "state": "ST",
            "bridge_type": "Beam",
            "last_inspection_date": "2020-01-01",
        }, self.db_path)
        add_bridge({
            "bridge_id": "RECENT-002",
            "name": "Recent Bridge",
            "location": "Loc",
            "state": "ST",
            "bridge_type": "Beam",
            "last_inspection_date": "2026-02-01",
        }, self.db_path)

        overdue = get_overdue_bridges(days_threshold=365, reference_date="2026-03-01", db_path=self.db_path)
        self.assertEqual(len(overdue), 1)
        self.assertEqual(overdue[0]["bridge_id"], "OVERDUE-001")


if __name__ == "__main__":
    unittest.main()
