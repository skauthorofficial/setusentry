"""
SetuSentry Reporting Utilities
Provides CSV export generators and print-friendly HTML report generation
for bridge inspection and risk prioritisation summaries.
"""

from __future__ import annotations
import io
from datetime import datetime
from typing import Any, Dict, List, Optional
import pandas as pd


def export_bridges_csv(bridges: List[Dict[str, Any]]) -> str:
    """Generate CSV string from bridge records list."""
    if not bridges:
        return ""
    df = pd.DataFrame(bridges)
    return df.to_csv(index=False)


def export_inspections_csv(inspections: List[Dict[str, Any]]) -> str:
    """Generate CSV string from inspection records list."""
    if not inspections:
        return ""
    df = pd.DataFrame(inspections)
    return df.to_csv(index=False)


def generate_print_friendly_report_html(
    bridge: Dict[str, Any],
    inspections: List[Dict[str, Any]],
    risk_info: Dict[str, Any],
) -> str:
    """
    Generate an HTML inspection and risk triage dossier formatted
    for on-screen viewing and clean print-to-PDF output.
    """
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    b_id = bridge.get("bridge_id", "N/A")
    name = bridge.get("name", "Unknown Bridge")
    loc = bridge.get("location", "N/A")
    state = bridge.get("state", "N/A")
    b_type = bridge.get("bridge_type", "N/A")
    year = bridge.get("construction_year", "N/A")
    span = bridge.get("span_length", "N/A")
    load = bridge.get("design_load", "N/A")
    last_insp = bridge.get("last_inspection_date", "None recorded")

    score = risk_info.get("score", 0)
    category = risk_info.get("category", "LOW")
    reasons = risk_info.get("reasons", ["All indicators within standard baseline tolerances."])
    rec_action = risk_info.get("recommended_action", "Routine periodic surveillance.")

    badge_colors = {
        "LOW": ("#15803d", "#dcfce7"),
        "MEDIUM": ("#b45309", "#fef3c7"),
        "HIGH": ("#c2410c", "#ffedd5"),
        "CRITICAL": ("#b91c1c", "#fee2e2"),
    }
    fg_col, bg_col = badge_colors.get(category, ("#374151", "#f3f4f6"))

    # Build risk flags list
    flags = []
    if bridge.get("risk_flood_zone"):
        flags.append("Active Flood Zone")
    if bridge.get("risk_high_traffic"):
        flags.append("High Traffic Corridor")
    if bridge.get("risk_age_over30"):
        flags.append("Age > 30 Years")
    if bridge.get("risk_previous_scour"):
        flags.append("Previous Pier/Abutment Scour")
    if bridge.get("risk_previous_cracks"):
        flags.append("Previous Crack History")
    flags_html = ", ".join(flags) if flags else "No specific hazard flags recorded"

    # Build inspections table rows
    insp_rows = []
    if inspections:
        for insp in inspections:
            ai_tag = (
                f"<span style='color:#b91c1c; font-weight:600;'>Cracked ({insp.get('ai_severity', 'N/A')})</span>"
                if insp.get("ai_crack_detected")
                else "<span style='color:#15803d;'>Sound</span>"
            )
            insp_rows.append(
                f"""
                <tr>
                    <td style="padding: 8px 12px; border-bottom: 1px solid #e5e7eb;">{insp.get('inspection_date', '')}</td>
                    <td style="padding: 8px 12px; border-bottom: 1px solid #e5e7eb;">{insp.get('inspector_name', '')}</td>
                    <td style="padding: 8px 12px; border-bottom: 1px solid #e5e7eb;">{insp.get('inspection_type', '')}</td>
                    <td style="padding: 8px 12px; border-bottom: 1px solid #e5e7eb; text-align:center;">
                        <strong>{insp.get('severity_rating', '-')}</strong>/5
                    </td>
                    <td style="padding: 8px 12px; border-bottom: 1px solid #e5e7eb;">{insp.get('action_status', '')}</td>
                    <td style="padding: 8px 12px; border-bottom: 1px solid #e5e7eb;">{ai_tag}</td>
                    <td style="padding: 8px 12px; border-bottom: 1px solid #e5e7eb;">{insp.get('observations', '')}</td>
                </tr>
                """
            )
    else:
        insp_rows.append(
            '<tr><td colspan="7" style="padding: 12px; text-align:center; color: #6b7280;">No prior inspections on record.</td></tr>'
        )
    inspections_tbody = "\n".join(insp_rows)

    reasons_list_html = "\n".join([f"<li style='margin-bottom: 4px;'>{r}</li>" for r in reasons])

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>SetuSentry Dossier - {b_id} {name}</title>
<style>
    @page {{
        size: A4 portrait;
        margin: 15mm;
    }}
    body {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        color: #1f2937;
        background: #ffffff;
        margin: 0;
        padding: 24px;
        line-height: 1.45;
        font-size: 13px;
    }}
    .header {{
        border-bottom: 2px solid #0f766e;
        padding-bottom: 12px;
        margin-bottom: 18px;
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
    }}
    .header h1 {{
        margin: 0;
        color: #0f766e;
        font-size: 22px;
        letter-spacing: -0.5px;
    }}
    .header .subtitle {{
        color: #4b5563;
        font-size: 12px;
        margin-top: 4px;
    }}
    .badge {{
        display: inline-block;
        padding: 6px 14px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 13px;
        letter-spacing: 0.5px;
        background-color: {bg_col};
        color: {fg_col};
        border: 1px solid {fg_col};
    }}
    .disclaimer-banner {{
        background: #fef2f2;
        border-left: 4px solid #ef4444;
        padding: 10px 14px;
        margin-bottom: 18px;
        color: #991b1b;
        font-size: 11px;
        font-weight: 500;
    }}
    .grid-2 {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 16px;
        margin-bottom: 18px;
    }}
    .card {{
        border: 1px solid #e5e7eb;
        border-radius: 6px;
        padding: 14px;
        background: #fafafa;
    }}
    .card h3 {{
        margin-top: 0;
        margin-bottom: 10px;
        font-size: 14px;
        color: #111827;
        border-bottom: 1px solid #e5e7eb;
        padding-bottom: 6px;
    }}
    table.data-table {{
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 8px;
    }}
    table.data-table th {{
        background: #f3f4f6;
        text-align: left;
        padding: 8px 10px;
        font-weight: 600;
        font-size: 12px;
        border-bottom: 2px solid #e5e7eb;
    }}
    .sign-block {{
        margin-top: 30px;
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 40px;
        padding-top: 20px;
        border-top: 1px dashed #d1d5db;
    }}
    .sign-line {{
        border-bottom: 1px solid #374151;
        height: 35px;
        margin-bottom: 6px;
    }}
    @media print {{
        body {{
            padding: 0;
        }}
        .no-print {{
            display: none;
        }}
    }}
</style>
</head>
<body>

<div class="header">
    <div>
        <h1>SetuSentry Bridge Inspection & Risk Dossier</h1>
        <div class="subtitle">AI-Assisted Infrastructure Inspection & Risk Prioritisation System</div>
    </div>
    <div style="text-align: right;">
        <span class="badge">PRIORITY: {category} ({score}/100)</span>
        <div class="subtitle" style="margin-top: 6px;">Report Generated: {now_str}</div>
    </div>
</div>

<div class="disclaimer-banner">
    <strong>OFFICIAL PROTOTYPE NOTICE:</strong> This is an educational prototype triage tool. It does not predict
    bridge collapse or replace qualified structural engineering assessment, non-destructive testing, or load rating computations.
</div>

<div class="grid-2">
    <div class="card">
        <h3>Bridge Asset Information</h3>
        <p><strong>Bridge ID:</strong> {b_id}</p>
        <p><strong>Bridge Name:</strong> {name}</p>
        <p><strong>Location:</strong> {loc}, {state}</p>
        <p><strong>Bridge Type:</strong> {b_type}</p>
        <p><strong>Construction Year:</strong> {year}</p>
        <p><strong>Span Length:</strong> {span} m &nbsp;|&nbsp; <strong>Design Load:</strong> {load} tons</p>
        <p><strong>Last Recorded Inspection:</strong> {last_insp}</p>
        <p><strong>Hazard Risk Factors:</strong> {flags_html}</p>
    </div>

    <div class="card">
        <h3>Risk Triage Analysis</h3>
        <p><strong>Triage Priority Score:</strong> <strong style="font-size: 16px; color: {fg_col};">{score} / 100 ({category})</strong></p>
        <p><strong>Recommended Protocol:</strong> {rec_action}</p>
        <p><strong>Elevating Factors Breakdown:</strong></p>
        <ul style="padding-left: 18px; margin: 4px 0;">
            {reasons_list_html}
        </ul>
        <p><strong>Asset Notes:</strong> {bridge.get('notes', 'None recorded')}</p>
    </div>
</div>

<div class="card" style="margin-bottom: 18px;">
    <h3>Inspection History & Visual Observations</h3>
    <table class="data-table">
        <thead>
            <tr>
                <th>Date</th>
                <th>Inspector</th>
                <th>Type</th>
                <th>Severity</th>
                <th>Status</th>
                <th>AI Defect</th>
                <th>Observations</th>
            </tr>
        </thead>
        <tbody>
            {inspections_tbody}
        </tbody>
    </table>
</div>

<div class="sign-block">
    <div>
        <div class="sign-line"></div>
        <div><strong>Inspecting Engineer / Evaluator</strong></div>
        <div style="font-size: 11px; color: #6b7280;">Date: ________________________</div>
    </div>
    <div>
        <div class="sign-line"></div>
        <div><strong>Division Executive Engineer Verification</strong></div>
        <div style="font-size: 11px; color: #6b7280;">Date: ________________________</div>
    </div>
</div>

</body>
</html>
"""
    return html
