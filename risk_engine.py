"""
SetuSentry Risk Prioritisation Engine
Computes transparent, explainable triage priority scores for bridges
based on inspection recency, unresolved observations, structural age,
known environmental hazards, and recent defect severity ratings.

IMPORTANT DISCLAIMER:
This is an educational prototype triage tool. It does not predict
bridge collapse or replace structural engineering assessment.
"""

from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

DISCLAIMER_TEXT = (
    "This is an educational prototype triage tool. It does not predict "
    "bridge collapse or replace structural engineering assessment."
)

CATEGORY_LOW = "LOW"
CATEGORY_MEDIUM = "MEDIUM"
CATEGORY_HIGH = "HIGH"
CATEGORY_CRITICAL = "CRITICAL"

COLOR_MAP = {
    CATEGORY_LOW: "#22c55e",       # Green
    CATEGORY_MEDIUM: "#eab308",    # Yellow/Amber
    CATEGORY_HIGH: "#f97316",      # Orange
    CATEGORY_CRITICAL: "#ef4444",  # Red
}

BG_COLOR_MAP = {
    CATEGORY_LOW: "rgba(34, 197, 94, 0.15)",
    CATEGORY_MEDIUM: "rgba(234, 179, 8, 0.15)",
    CATEGORY_HIGH: "rgba(249, 115, 22, 0.15)",
    CATEGORY_CRITICAL: "rgba(239, 68, 68, 0.15)",
}


def calculate_days_since_inspection(
    last_inspection_date: Optional[str],
    reference_date: Optional[str] = None
) -> Tuple[Optional[int], str]:
    """
    Calculate days elapsed since last recorded inspection.
    Returns (days_elapsed, human_readable_note).
    """
    if not last_inspection_date:
        return None, "No inspection recorded (overdue)"

    try:
        ref_dt = datetime.strptime(reference_date, "%Y-%m-%d") if reference_date else datetime.now()
        last_dt = datetime.strptime(last_inspection_date, "%Y-%m-%d")
        diff_days = max(0, (ref_dt - last_dt).days)
        return diff_days, f"{diff_days} days ago ({last_inspection_date})"
    except ValueError:
        return None, "Invalid date format"


def calculate_bridge_risk(
    bridge: Dict[str, Any],
    inspections: Optional[List[Dict[str, Any]]] = None,
    reference_date: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Calculate the risk priority score, category, and explainable breakdown
    for a bridge record and its associated inspections.

    Returns a structured dictionary with full explainability.
    """
    score = 0
    reasons: List[str] = []
    breakdown_points: Dict[str, int] = {}

    current_year = (
        datetime.strptime(reference_date, "%Y-%m-%d").year
        if reference_date else datetime.now().year
    )

    # -------------------------------------------------------------
    # 1. Days Since Last Inspection (Recency / Overdue)
    # -------------------------------------------------------------
    last_date = bridge.get("last_inspection_date")
    days_elapsed, recency_note = calculate_days_since_inspection(last_date, reference_date)

    if days_elapsed is None:
        recency_pts = 30
        reasons.append("No record of inspection found; inspection is significantly overdue (+30 pts)")
    elif days_elapsed > 730:
        recency_pts = 35
        reasons.append(f"Inspection overdue by {days_elapsed} days (>2 years overdue) (+35 pts)")
    elif days_elapsed > 365:
        recency_pts = 22
        reasons.append(f"Inspection overdue by {days_elapsed} days (>1 year overdue) (+22 pts)")
    elif days_elapsed > 180:
        recency_pts = 8
        reasons.append(f"Last inspected {days_elapsed} days ago (approaching annual review) (+8 pts)")
    else:
        recency_pts = 0

    score += recency_pts
    breakdown_points["recency"] = recency_pts

    # -------------------------------------------------------------
    # 2. Structure Age
    # -------------------------------------------------------------
    const_year = bridge.get("construction_year")
    age_pts = 0
    if const_year and isinstance(const_year, (int, float)):
        age = current_year - int(const_year)
        if age > 50:
            age_pts = 22
            reasons.append(f"Structure is {age} years old (exceeds 50-year design threshold) (+22 pts)")
        elif age > 30:
            age_pts = 14
            reasons.append(f"Structure is {age} years old (>30 years service age) (+14 pts)")
        elif age > 15:
            age_pts = 4
        else:
            age_pts = 0
    score += age_pts
    breakdown_points["structure_age"] = age_pts

    # -------------------------------------------------------------
    # 3. Known Environmental & Historical Risk Factors
    # -------------------------------------------------------------
    risk_pts = 0
    if bridge.get("risk_previous_scour"):
        risk_pts += 14
        reasons.append("Historical pier or abutment scour documented (+14 pts)")

    if bridge.get("risk_previous_cracks"):
        risk_pts += 12
        reasons.append("Previous crack or structural defect history recorded (+12 pts)")

    if bridge.get("risk_flood_zone"):
        risk_pts += 10
        reasons.append("Structure located in designated active flood zone (+10 pts)")

    if bridge.get("risk_high_traffic"):
        risk_pts += 8
        reasons.append("High daily heavy-vehicle traffic density corridor (+8 pts)")

    if bridge.get("risk_age_over30") and age_pts < 14:
        # If manually flagged as age > 30 but not already scored above
        risk_pts += 6
        reasons.append("Flagged for age > 30 years (+6 pts)")

    score += risk_pts
    breakdown_points["known_risk_factors"] = risk_pts

    # -------------------------------------------------------------
    # 4. Unresolved Observations (Pending / Escalated)
    # -------------------------------------------------------------
    pending_count = 0
    escalated_count = 0
    recent_severity = 0
    most_recent_inspection = None

    if inspections:
        # Sort inspections to get most recent
        sorted_inspections = sorted(
            inspections,
            key=lambda x: str(x.get("inspection_date", "")),
            reverse=True,
        )
        if sorted_inspections:
            most_recent_inspection = sorted_inspections[0]
            recent_severity = int(most_recent_inspection.get("severity_rating") or 0)

        for insp in inspections:
            st = str(insp.get("action_status", "")).strip().capitalize()
            if st == "Escalated":
                escalated_count += 1
            elif st == "Pending":
                pending_count += 1

    # Points for unresolved observations
    unresolved_pts = min(escalated_count * 15, 30) + min(pending_count * 6, 18)
    if escalated_count > 0:
        reasons.append(
            f"{escalated_count} unresolved observation(s) marked as ESCALATED (+{min(escalated_count * 15, 30)} pts)"
        )
    if pending_count > 0:
        reasons.append(
            f"{pending_count} observation(s) currently PENDING action (+{min(pending_count * 6, 18)} pts)"
        )

    score += unresolved_pts
    breakdown_points["unresolved_observations"] = unresolved_pts

    # -------------------------------------------------------------
    # 5. Most Recent Defect Severity Rating (1-5)
    # -------------------------------------------------------------
    severity_pts = 0
    if recent_severity == 5:
        severity_pts = 26
        reasons.append("Most recent inspection recorded Critical Severity Level 5 (+26 pts)")
    elif recent_severity == 4:
        severity_pts = 18
        reasons.append("Most recent inspection recorded High Severity Level 4 (+18 pts)")
    elif recent_severity == 3:
        severity_pts = 10
        reasons.append("Most recent inspection recorded Moderate Severity Level 3 (+10 pts)")
    elif recent_severity == 2:
        severity_pts = 4
    score += severity_pts
    breakdown_points["recent_severity"] = severity_pts

    # Cap raw score to 100 for clean visualization
    normalized_score = min(score, 100)

    # -------------------------------------------------------------
    # Classification & Action Tier
    # -------------------------------------------------------------
    if normalized_score >= 75:
        category = CATEGORY_CRITICAL
        recommended_action = "Prioritize for immediate on-site structural engineering review."
    elif normalized_score >= 50:
        category = CATEGORY_HIGH
        recommended_action = "Schedule expedited detailed inspection within 30 days."
    elif normalized_score >= 25:
        category = CATEGORY_MEDIUM
        recommended_action = "Maintain regular surveillance and resolve pending observations."
    else:
        category = CATEGORY_LOW
        recommended_action = "Standard routine monitoring cycle recommended."

    if not reasons:
        reasons.append("All structural, recency, and environmental parameters within baseline thresholds.")

    return {
        "bridge_id": bridge.get("bridge_id"),
        "bridge_name": bridge.get("name"),
        "raw_score": score,
        "score": normalized_score,
        "category": category,
        "color": COLOR_MAP[category],
        "bg_color": BG_COLOR_MAP[category],
        "reasons": reasons,
        "breakdown": breakdown_points,
        "recommended_action": recommended_action,
        "pending_count": pending_count,
        "escalated_count": escalated_count,
        "days_since_inspection": days_elapsed,
        "recency_note": recency_note,
        "recent_severity": recent_severity,
        "disclaimer": DISCLAIMER_TEXT,
    }


def rank_bridges_by_risk(
    bridges: List[Dict[str, Any]],
    inspections_by_bridge: Dict[str, List[Dict[str, Any]]],
    reference_date: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Compute risk assessment for all bridges and return sorted list
    from highest priority (Critical) to lowest (Low).
    """
    ranked = []
    for b in bridges:
        b_id = b.get("bridge_id")
        b_inspections = inspections_by_bridge.get(b_id, [])
        risk_res = calculate_bridge_risk(b, b_inspections, reference_date)
        # Combine original bridge attributes with risk evaluation
        combined = {**b, **risk_res}
        ranked.append(combined)

    # Sort descending by score, then unresolved escalated count
    ranked.sort(key=lambda x: (x["score"], x.get("escalated_count", 0)), reverse=True)
    return ranked
