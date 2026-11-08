"""
SetuSentry Seed Data Generator
Pre-populates the SQLite database with 8 sample Indian bridge infrastructure assets
and realistic multi-year inspection logs (2023-2026) for demonstration and triage evaluation.
All sample records are clearly labeled as [DEMONSTRATION RECORD].
"""

from __future__ import annotations
import os
import sys
from typing import Optional

# Ensure parent directory is in path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from database import add_bridge, add_inspection, get_all_bridges, init_db


SAMPLE_BRIDGES = [
    {
        "bridge_id": "SS-NH19-001",
        "name": "NH-19 Ganga Bridge [DEMONSTRATION RECORD]",
        "location": "Varanasi",
        "state": "Uttar Pradesh",
        "bridge_type": "Beam",
        "construction_year": 1987,
        "span_length": 1120.0,
        "design_load": 70.0,
        "last_inspection_date": "2024-03-15",
        "risk_flood_zone": 1,
        "risk_high_traffic": 1,
        "risk_age_over30": 1,
        "risk_previous_scour": 0,
        "risk_previous_cracks": 1,
        "notes": "[DEMONSTRATION RECORD] Multi-span prestressed concrete girder bridge across river Ganga. Heavy commercial transport corridor with past shear crack reports on pier cap 4.",
    },
    {
        "bridge_id": "SS-AS-002",
        "name": "Brahmaputra Rail-Road Bridge [DEMONSTRATION RECORD]",
        "location": "Guwahati",
        "state": "Assam",
        "bridge_type": "Truss",
        "construction_year": 1962,
        "span_length": 1290.0,
        "design_load": 100.0,
        "last_inspection_date": "2023-11-20",
        "risk_flood_zone": 1,
        "risk_high_traffic": 0,
        "risk_age_over30": 1,
        "risk_previous_scour": 1,
        "risk_previous_cracks": 0,
        "notes": "[DEMONSTRATION RECORD] Double-deck steel truss structure over river Brahmaputra. Severe seasonal monsoon riverbed scour vulnerability near northern piers.",
    },
    {
        "bridge_id": "SS-MH-003",
        "name": "Bandra-Worli Sea Link [DEMONSTRATION RECORD]",
        "location": "Mumbai",
        "state": "Maharashtra",
        "bridge_type": "Cable-stayed",
        "construction_year": 2009,
        "span_length": 5600.0,
        "design_load": 80.0,
        "last_inspection_date": "2026-01-10",
        "risk_flood_zone": 0,
        "risk_high_traffic": 1,
        "risk_age_over30": 0,
        "risk_previous_scour": 0,
        "risk_previous_cracks": 0,
        "notes": "[DEMONSTRATION RECORD] Modern 8-lane cable-stayed marine expressway. Severe marine salt-fog exposure requiring cathodic corrosion surveillance.",
    },
    {
        "bridge_id": "SS-WB-004",
        "name": "NH-44 Teesta Bridge [DEMONSTRATION RECORD]",
        "location": "Siliguri",
        "state": "West Bengal",
        "bridge_type": "Beam",
        "construction_year": 1979,
        "span_length": 780.0,
        "design_load": 65.0,
        "last_inspection_date": "2023-08-12",
        "risk_flood_zone": 1,
        "risk_high_traffic": 0,
        "risk_age_over30": 1,
        "risk_previous_scour": 1,
        "risk_previous_cracks": 0,
        "notes": "[DEMONSTRATION RECORD] Mountainous terrain river bridge over flash-flood prone Teesta basin. Significant boulder impact abrasion on pier stems.",
    },
    {
        "bridge_id": "SS-AP-005",
        "name": "Godavari Arch Bridge [DEMONSTRATION RECORD]",
        "location": "Rajahmundry",
        "state": "Andhra Pradesh",
        "bridge_type": "Arch",
        "construction_year": 1974,
        "span_length": 2745.0,
        "design_load": 75.0,
        "last_inspection_date": "2025-02-18",
        "risk_flood_zone": 0,
        "risk_high_traffic": 0,
        "risk_age_over30": 1,
        "risk_previous_scour": 0,
        "risk_previous_cracks": 1,
        "notes": "[DEMONSTRATION RECORD] Prestressed concrete bowstring arch structure. Longitudinal deck expansion joint deterioration and micro-cracking at crown bearings.",
    },
    {
        "bridge_id": "SS-GA-006",
        "name": "Zuari Bridge [DEMONSTRATION RECORD]",
        "location": "Panaji",
        "state": "Goa",
        "bridge_type": "Beam",
        "construction_year": 1986,
        "span_length": 1225.0,
        "design_load": 60.0,
        "last_inspection_date": "2024-09-04",
        "risk_flood_zone": 0,
        "risk_high_traffic": 0,
        "risk_age_over30": 1,
        "risk_previous_scour": 0,
        "risk_previous_cracks": 1,
        "notes": "[DEMONSTRATION RECORD] Coastal cantilever beam bridge. High humidity coastal environment with rebar corrosion and spalling detected in southern approach span.",
    },
    {
        "bridge_id": "SS-OD-007",
        "name": "Mahanadi Bridge NH-16 [DEMONSTRATION RECORD]",
        "location": "Cuttack",
        "state": "Odisha",
        "bridge_type": "Beam",
        "construction_year": 1995,
        "span_length": 2100.0,
        "design_load": 70.0,
        "last_inspection_date": "2025-06-22",
        "risk_flood_zone": 1,
        "risk_high_traffic": 0,
        "risk_age_over30": 0,
        "risk_previous_scour": 0,
        "risk_previous_cracks": 0,
        "notes": "[DEMONSTRATION RECORD] Multi-span prestressed concrete bridge crossing Mahanadi floodplain. Flood discharge monitoring required during cyclonic storm events.",
    },
    {
        "bridge_id": "SS-MP-008",
        "name": "Betwa Bridge NH-86 [DEMONSTRATION RECORD]",
        "location": "Jhansi",
        "state": "Madhya Pradesh",
        "bridge_type": "Beam",
        "construction_year": 2001,
        "span_length": 640.0,
        "design_load": 70.0,
        "last_inspection_date": "2025-10-14",
        "risk_flood_zone": 0,
        "risk_high_traffic": 0,
        "risk_age_over30": 0,
        "risk_previous_scour": 0,
        "risk_previous_cracks": 0,
        "notes": "[DEMONSTRATION RECORD] Medium-span reinforced concrete girder bridge on NH-86. Stable subgrade and normal service performance observed.",
    },
]

SAMPLE_INSPECTIONS = [
    # SS-NH19-001 (High Risk / Escalated)
    {
        "bridge_id": "SS-NH19-001",
        "inspection_date": "2024-03-15",
        "inspector_name": "Er. R. K. Sharma",
        "inspection_type": "Detailed",
        "observations": "[DEMONSTRATION RECORD] Deep shear cracks observed on Pier Cap P4 near bearing seat. Transverse fissure width approx 2.2mm with efflorescence leaching.",
        "severity_rating": 4,
        "action_status": "Escalated",
        "ai_crack_detected": 1,
        "ai_confidence": 0.89,
        "ai_severity": "High",
        "image_path": "",
    },
    {
        "bridge_id": "SS-NH19-001",
        "inspection_date": "2023-06-10",
        "inspector_name": "Er. Priya Verma",
        "inspection_type": "Visual",
        "observations": "[DEMONSTRATION RECORD] Hairline diagonal cracks forming along western soffit. Bituminous wear course degraded.",
        "severity_rating": 3,
        "action_status": "Pending",
        "ai_crack_detected": 1,
        "ai_confidence": 0.74,
        "ai_severity": "Medium",
        "image_path": "",
    },
    {
        "bridge_id": "SS-NH19-001",
        "inspection_date": "2023-01-20",
        "inspector_name": "Er. Amit Saxena",
        "inspection_type": "Special",
        "observations": "[DEMONSTRATION RECORD] Post-monsoon flood debris cleared from upstream pier noses. Minor surface abrasion.",
        "severity_rating": 2,
        "action_status": "Completed",
        "ai_crack_detected": 0,
        "ai_confidence": 0.82,
        "ai_severity": "None",
        "image_path": "",
    },

    # SS-AS-002 (High/Critical Overdue & Scour)
    {
        "bridge_id": "SS-AS-002",
        "inspection_date": "2023-11-20",
        "inspector_name": "Er. Bipul Borah",
        "inspection_type": "Detailed",
        "observations": "[DEMONSTRATION RECORD] Severe scour cavity around Pier P7 footing (>3.4m below bed level). Steel gusset plates showing active corrosion scale.",
        "severity_rating": 5,
        "action_status": "Escalated",
        "ai_crack_detected": 1,
        "ai_confidence": 0.91,
        "ai_severity": "High",
        "image_path": "",
    },
    {
        "bridge_id": "SS-AS-002",
        "inspection_date": "2023-04-12",
        "inspector_name": "Er. D. Kalita",
        "inspection_type": "Visual",
        "observations": "[DEMONSTRATION RECORD] Expansion finger joints clogged with ballast and river silt. Joint movement restricted.",
        "severity_rating": 3,
        "action_status": "Scheduled",
        "ai_crack_detected": 0,
        "ai_confidence": 0.78,
        "ai_severity": "None",
        "image_path": "",
    },

    # SS-MH-003 (Low Risk / Routine)
    {
        "bridge_id": "SS-MH-003",
        "inspection_date": "2026-01-10",
        "inspector_name": "Er. S. Deshmukh",
        "inspection_type": "Visual",
        "observations": "[DEMONSTRATION RECORD] Regular quarterly cable damping and stay cable sheath inspection. Tension loads within tolerance, paint intact.",
        "severity_rating": 1,
        "action_status": "Completed",
        "ai_crack_detected": 0,
        "ai_confidence": 0.95,
        "ai_severity": "None",
        "image_path": "",
    },
    {
        "bridge_id": "SS-MH-003",
        "inspection_date": "2025-06-18",
        "inspector_name": "Er. Rahul Patil",
        "inspection_type": "Visual",
        "observations": "[DEMONSTRATION RECORD] Deck expansion seals intact. Minor salt deposit build-up washed away under routine maintenance.",
        "severity_rating": 1,
        "action_status": "Completed",
        "ai_crack_detected": 0,
        "ai_confidence": 0.93,
        "ai_severity": "None",
        "image_path": "",
    },

    # SS-WB-004 (Overdue / High Risk)
    {
        "bridge_id": "SS-WB-004",
        "inspection_date": "2023-08-12",
        "inspector_name": "Er. S. Ganguly",
        "inspection_type": "Special",
        "observations": "[DEMONSTRATION RECORD] Boulder impact damages on Pier 3 upstream cutoff wall. Scour depression observed around foundation apron.",
        "severity_rating": 4,
        "action_status": "Escalated",
        "ai_crack_detected": 1,
        "ai_confidence": 0.86,
        "ai_severity": "High",
        "image_path": "",
    },
    {
        "bridge_id": "SS-WB-004",
        "inspection_date": "2023-02-14",
        "inspector_name": "Er. M. Das",
        "inspection_type": "Visual",
        "observations": "[DEMONSTRATION RECORD] Abutment A1 wing wall settling with 15mm separation crack at joint.",
        "severity_rating": 3,
        "action_status": "Pending",
        "ai_crack_detected": 1,
        "ai_confidence": 0.72,
        "ai_severity": "Medium",
        "image_path": "",
    },

    # SS-AP-005 (Medium Risk)
    {
        "bridge_id": "SS-AP-005",
        "inspection_date": "2025-02-18",
        "inspector_name": "Er. K. V. Rao",
        "inspection_type": "Detailed",
        "observations": "[DEMONSTRATION RECORD] Vertical crack noticed on east spandrel column. Acoustic sounding indicates no deep hollow voiding.",
        "severity_rating": 3,
        "action_status": "Scheduled",
        "ai_crack_detected": 1,
        "ai_confidence": 0.76,
        "ai_severity": "Medium",
        "image_path": "",
    },
    {
        "bridge_id": "SS-AP-005",
        "inspection_date": "2024-05-11",
        "inspector_name": "Er. P. Reddy",
        "inspection_type": "Visual",
        "observations": "[DEMONSTRATION RECORD] Arch rib hinge bearings cleaned and regreased. Minor hairline cracking in parapet coping.",
        "severity_rating": 2,
        "action_status": "Completed",
        "ai_crack_detected": 0,
        "ai_confidence": 0.88,
        "ai_severity": "None",
        "image_path": "",
    },

    # SS-GA-006 (Medium/High Risk)
    {
        "bridge_id": "SS-GA-006",
        "inspection_date": "2024-09-04",
        "inspector_name": "Er. Francis Noronha",
        "inspection_type": "Detailed",
        "observations": "[DEMONSTRATION RECORD] Delamination and concrete cover spalling under Span 5 cantilever. Exposed rusted reinforcement visible.",
        "severity_rating": 4,
        "action_status": "Pending",
        "ai_crack_detected": 1,
        "ai_confidence": 0.87,
        "ai_severity": "High",
        "image_path": "",
    },
    {
        "bridge_id": "SS-GA-006",
        "inspection_date": "2023-12-08",
        "inspector_name": "Er. A. Kamat",
        "inspection_type": "Visual",
        "observations": "[DEMONSTRATION RECORD] Rust staining spreading along soffit slab near drainage spouts.",
        "severity_rating": 3,
        "action_status": "Scheduled",
        "ai_crack_detected": 1,
        "ai_confidence": 0.69,
        "ai_severity": "Low",
        "image_path": "",
    },

    # SS-OD-007 (Low/Medium Risk)
    {
        "bridge_id": "SS-OD-007",
        "inspection_date": "2025-06-22",
        "inspector_name": "Er. T. Mohapatra",
        "inspection_type": "Visual",
        "observations": "[DEMONSTRATION RECORD] Pre-monsoon water clearance and weep hole check. Bridge deck drainage fully operational.",
        "severity_rating": 1,
        "action_status": "Completed",
        "ai_crack_detected": 0,
        "ai_confidence": 0.94,
        "ai_severity": "None",
        "image_path": "",
    },
    {
        "bridge_id": "SS-OD-007",
        "inspection_date": "2024-10-18",
        "inspector_name": "Er. S. Nayak",
        "inspection_type": "Visual",
        "observations": "[DEMONSTRATION RECORD] Minor elastomeric bearing pad extrusion on Pier 12. Does not impede articulation.",
        "severity_rating": 2,
        "action_status": "Completed",
        "ai_crack_detected": 0,
        "ai_confidence": 0.85,
        "ai_severity": "None",
        "image_path": "",
    },

    # SS-MP-008 (Low Risk)
    {
        "bridge_id": "SS-MP-008",
        "inspection_date": "2025-10-14",
        "inspector_name": "Er. Vikram Singh",
        "inspection_type": "Visual",
        "observations": "[DEMONSTRATION RECORD] Annual routine visual survey. Girder diaphragms in good condition, crash barriers intact.",
        "severity_rating": 1,
        "action_status": "Completed",
        "ai_crack_detected": 0,
        "ai_confidence": 0.96,
        "ai_severity": "None",
        "image_path": "",
    },
    {
        "bridge_id": "SS-MP-008",
        "inspection_date": "2024-11-02",
        "inspector_name": "Er. R. Yadav",
        "inspection_type": "Visual",
        "observations": "[DEMONSTRATION RECORD] Approach road wearing course smooth. Guard rails repainted.",
        "severity_rating": 1,
        "action_status": "Completed",
        "ai_crack_detected": 0,
        "ai_confidence": 0.95,
        "ai_severity": "None",
        "image_path": "",
    },
]


def seed_database(db_path: Optional[str] = None, force: bool = False) -> Tuple[int, int]:
    """
    Seed database with the 8 sample bridges and their inspection logs.
    If force is False, only seeds if the bridges table is currently empty.
    Returns (num_bridges_inserted, num_inspections_inserted).
    """
    init_db(db_path)
    existing = get_all_bridges(db_path)

    if existing and not force:
        return 0, 0

    bridges_added = 0
    for b in SAMPLE_BRIDGES:
        try:
            add_bridge(b, db_path)
            bridges_added += 1
        except Exception as e:
            # Skip if already exists
            pass

    inspections_added = 0
    for insp in SAMPLE_INSPECTIONS:
        try:
            add_inspection(insp, db_path)
            inspections_added += 1
        except Exception as e:
            pass

    return bridges_added, inspections_added


if __name__ == "__main__":
    b_count, i_count = seed_database(force=True)
    print(f"Seeded {b_count} sample bridges and {i_count} inspection logs into SetuSentry database.")
