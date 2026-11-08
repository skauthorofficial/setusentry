"""
SetuSentry (सेतु संतरी) - AI-Assisted Bridge Inspection and Risk-Prioritisation System
Streamlit Main Application
"""

from __future__ import annotations
import os
import sys
from datetime import date, datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from PIL import Image

# Ensure current directory is on path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from database import (
    add_bridge,
    add_inspection,
    delete_bridge,
    get_all_bridges,
    get_all_bridges_df,
    get_all_inspections,
    get_all_inspections_df,
    get_bridge,
    get_inspections_for_bridge,
    get_overdue_bridges,
    get_unresolved_inspections,
    init_db,
    update_bridge,
    update_inspection_status,
)
from risk_engine import (
    CATEGORY_CRITICAL,
    CATEGORY_HIGH,
    CATEGORY_LOW,
    CATEGORY_MEDIUM,
    COLOR_MAP,
    DISCLAIMER_TEXT as RISK_DISCLAIMER,
    calculate_bridge_risk,
    rank_bridges_by_risk,
)
from model.demo_inference import (
    DISCLAIMER_AI,
    DEMO_MODE_NOTICE,
    run_visual_inspection,
)
from utils.image_utils import (
    generate_synthetic_concrete_image,
    save_uploaded_image,
    validate_image_upload,
)
from utils.report_utils import (
    export_bridges_csv,
    export_inspections_csv,
    generate_print_friendly_report_html,
)
from data.seed_data import seed_database


# -------------------------------------------------------------
# STREAMLIT PAGE CONFIGURATION
# -------------------------------------------------------------
st.set_page_config(
    page_title="SetuSentry | Bridge Inspection & Risk Triage",
    page_icon="🌉",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize database and seed data if needed
init_db()
seed_database(force=False)

# Directory paths
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
SAMPLES_DIR = os.path.join(UPLOADS_DIR, "samples")
os.makedirs(SAMPLES_DIR, exist_ok=True)


# -------------------------------------------------------------
# CUSTOM CSS STYLING
# -------------------------------------------------------------
st.markdown(
    """
    <style>
    /* Global styles */
    .main-header {
        background: linear-gradient(135deg, #0f766e 0%, #1e293b 100%);
        padding: 20px 24px;
        border-radius: 10px;
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .main-header h1 {
        color: #f8fafc;
        margin: 0;
        font-size: 26px;
        font-weight: 700;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .main-header p {
        color: #99f6e4;
        margin: 6px 0 0 0;
        font-size: 14px;
    }
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        text-align: center;
    }
    .metric-card .title {
        font-size: 13px;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-card .value {
        font-size: 28px;
        font-weight: 700;
        color: #0f172a;
        margin-top: 4px;
    }
    .badge-critical {
        background-color: #fee2e2;
        color: #b91c1c;
        border: 1px solid #ef4444;
        padding: 3px 10px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 12px;
        display: inline-block;
    }
    .badge-high {
        background-color: #ffedd5;
        color: #c2410c;
        border: 1px solid #f97316;
        padding: 3px 10px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 12px;
        display: inline-block;
    }
    .badge-medium {
        background-color: #fef3c7;
        color: #b45309;
        border: 1px solid #eab308;
        padding: 3px 10px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 12px;
        display: inline-block;
    }
    .badge-low {
        background-color: #dcfce7;
        color: #15803d;
        border: 1px solid #22c55e;
        padding: 3px 10px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 12px;
        display: inline-block;
    }
    .disclaimer-box {
        background-color: #fffbeb;
        border-left: 4px solid #f59e0b;
        padding: 12px 16px;
        border-radius: 4px;
        color: #92400e;
        font-size: 13px;
        margin: 12px 0 20px 0;
        line-height: 1.45;
    }
    .disclaimer-ai-box {
        background-color: #fef2f2;
        border-left: 4px solid #ef4444;
        padding: 12px 16px;
        border-radius: 4px;
        color: #991b1b;
        font-size: 13px;
        margin: 12px 0 20px 0;
        line-height: 1.45;
    }
    .demo-tag {
        background-color: #3b82f6;
        color: white;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# -------------------------------------------------------------
# SIDEBAR NAVIGATION
# -------------------------------------------------------------
st.sidebar.markdown(
    """
    <div style="padding: 10px 0; text-align: center;">
        <h2 style="color: #0f766e; margin: 0; font-size: 24px;">🌉 SetuSentry</h2>
        <span style="font-size: 12px; color: #64748b; font-weight: 500;">सेतु संतरी | Infrastructure AI</span>
    </div>
    """,
    unsafe_allow_html=True,
)

nav_selection = st.sidebar.radio(
    "Navigation Modules",
    [
        "📊 Executive Dashboard",
        "🌉 Bridge Registry",
        "🔍 AI Visual Inspection",
        "📋 Inspection History",
        "⚡ Risk Prioritisation",
        "⚠️ Alerts & Reporting",
    ],
    index=0,
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    <div style="font-size: 11px; color: #64748b; line-height: 1.4;">
        <strong>Prototype Build:</strong> v1.0.4-demo<br>
        <strong>Engine:</strong> PyTorch MobileNetV2 + OpenCV<br>
        <strong>Safety Note:</strong> Educational triage tool. Does not replace structural testing.
    </div>
    """,
    unsafe_allow_html=True,
)


# -------------------------------------------------------------
# HELPER: RENDER HEADER
# -------------------------------------------------------------
def render_page_header(title: str, subtitle: str):
    st.markdown(
        f"""
        <div class="main-header">
            <h1>🌉 {title}</h1>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =============================================================
# MODULE 5: EXECUTIVE DASHBOARD
# =============================================================
if nav_selection == "📊 Executive Dashboard":
    render_page_header(
        "Executive Dashboard",
        "Real-time surveillance overview, inspection recency, and risk priority distribution.",
    )

    bridges = get_all_bridges()
    inspections = get_all_inspections()
    overdue_bridges = get_overdue_bridges(days_threshold=365)
    unresolved_list = get_unresolved_inspections()

    # Pre-calculate risk rankings for all bridges
    insp_map = {}
    for insp in inspections:
        bid = insp["bridge_id"]
        insp_map.setdefault(bid, []).append(insp)

    ranked_bridges = rank_bridges_by_risk(bridges, insp_map)

    crit_count = sum(1 for b in ranked_bridges if b["category"] == CATEGORY_CRITICAL)
    high_count = sum(1 for b in ranked_bridges if b["category"] == CATEGORY_HIGH)
    med_count = sum(1 for b in ranked_bridges if b["category"] == CATEGORY_MEDIUM)
    low_count = sum(1 for b in ranked_bridges if b["category"] == CATEGORY_LOW)

    # 4 Metric Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="title">Total Bridge Assets</div>
                <div class="value">{len(bridges)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="title">Overdue Inspections (>365d)</div>
                <div class="value" style="color: {'#b91c1c' if len(overdue_bridges) > 0 else '#15803d'};">{len(overdue_bridges)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="title">High / Critical Priority</div>
                <div class="value" style="color: {'#ef4444' if (crit_count + high_count) > 0 else '#0f172a'};">{crit_count + high_count}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="title">Unresolved Observations</div>
                <div class="value" style="color: {'#f97316' if len(unresolved_list) > 0 else '#0f172a'};">{len(unresolved_list)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Charts Row
    ch1, ch2 = st.columns(2)

    with ch1:
        st.subheader("Triage Priority Distribution")
        cat_df = pd.DataFrame({
            "Priority Tier": ["Low", "Medium", "High", "Critical"],
            "Asset Count": [low_count, med_count, high_count, crit_count],
            "Color": ["#22c55e", "#eab308", "#f97316", "#ef4444"],
        })
        fig_bar = px.bar(
            cat_df,
            x="Priority Tier",
            y="Asset Count",
            color="Priority Tier",
            color_discrete_map={
                "Low": "#22c55e",
                "Medium": "#eab308",
                "High": "#f97316",
                "Critical": "#ef4444",
            },
            text="Asset Count",
        )
        fig_bar.update_layout(showlegend=False, height=320, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_bar, use_container_width=True)

    with ch2:
        st.subheader("12-Month Inspection Timeline")
        if inspections:
            insp_df = pd.DataFrame(inspections)
            insp_df["inspection_date"] = pd.to_datetime(insp_df["inspection_date"], errors="coerce")
            insp_df = insp_df.dropna(subset=["inspection_date"])
            insp_df["month_year"] = insp_df["inspection_date"].dt.to_period("M").astype(str)
            monthly_counts = insp_df.groupby(["month_year", "inspection_type"]).size().reset_index(name="count")

            fig_line = px.bar(
                monthly_counts,
                x="month_year",
                y="count",
                color="inspection_type",
                barmode="stack",
                labels={"month_year": "Month", "count": "Inspections Conducted", "inspection_type": "Type"},
                color_discrete_sequence=px.colors.qualitative.Prism,
            )
            fig_line.update_layout(height=320, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("No inspection timeline records available.")

    # Top 5 Triage Table
    st.subheader("Top Priority Bridges Requiring Attention")
    top_5 = ranked_bridges[:5]
    if top_5:
        top_data = []
        for b in top_5:
            top_data.append({
                "Bridge ID": b["bridge_id"],
                "Bridge Name": b["name"],
                "State": b["state"],
                "Type": b["bridge_type"],
                "Priority Tier": b["category"],
                "Triage Score": f"{b['score']} / 100",
                "Last Inspected": b.get("last_inspection_date", "Never"),
                "Recommended Action": b["recommended_action"],
            })
        top_df = pd.DataFrame(top_data)
        st.dataframe(top_df, use_container_width=True, hide_index=True)
    else:
        st.write("No bridges registered.")


# =============================================================
# MODULE 1: BRIDGE REGISTRY
# =============================================================
elif nav_selection == "🌉 Bridge Registry":
    render_page_header(
        "Bridge Asset Registry",
        "Register civil bridge assets, configure structural parameters, and review infrastructure records.",
    )

    tab_view, tab_add = st.tabs(["📋 View & Search Registry", "➕ Register New Bridge"])

    # TAB 1: VIEW & SEARCH
    with tab_view:
        bridges_df = get_all_bridges_df()
        if not bridges_df.empty:
            # Filter bar
            f1, f2, f3 = st.columns([2, 1, 1])
            with f1:
                search_query = st.text_input("🔍 Search by ID, Name, or Location", "")
            with f2:
                state_filter = st.selectbox(
                    "Filter by State",
                    ["All States"] + sorted(list(bridges_df["state"].unique()))
                )
            with f3:
                type_filter = st.selectbox(
                    "Filter by Bridge Type",
                    ["All Types"] + sorted(list(bridges_df["bridge_type"].unique()))
                )

            filtered_df = bridges_df.copy()
            if search_query:
                q = search_query.lower()
                filtered_df = filtered_df[
                    filtered_df["bridge_id"].str.lower().str.contains(q)
                    | filtered_df["name"].str.lower().str.contains(q)
                    | filtered_df["location"].str.lower().str.contains(q)
                ]
            if state_filter != "All States":
                filtered_df = filtered_df[filtered_df["state"] == state_filter]
            if type_filter != "All Types":
                filtered_df = filtered_df[filtered_df["bridge_type"] == type_filter]

            # Display table
            display_cols = [
                "bridge_id", "name", "location", "state", "bridge_type",
                "construction_year", "span_length", "design_load", "last_inspection_date"
            ]
            st.dataframe(
                filtered_df[display_cols],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "bridge_id": "Bridge ID",
                    "name": "Name",
                    "location": "Location",
                    "state": "State",
                    "bridge_type": "Type",
                    "construction_year": "Year",
                    "span_length": "Span (m)",
                    "design_load": "Load (t)",
                    "last_inspection_date": "Last Inspection",
                },
            )

            st.markdown("---")
            st.subheader("Bridge Detail Inspector")
            selected_b_id = st.selectbox(
                "Select a bridge to view full dossier & inspection records:",
                options=bridges_df["bridge_id"].tolist(),
                format_func=lambda x: f"{x} - {bridges_df.loc[bridges_df['bridge_id'] == x, 'name'].values[0]}"
            )

            if selected_b_id:
                b_record = get_bridge(selected_b_id)
                b_inspections = get_inspections_for_bridge(selected_b_id)
                risk_summary = calculate_bridge_risk(b_record, b_inspections)

                col_det1, col_det2 = st.columns([1, 1])
                with col_det1:
                    st.markdown(f"### {b_record['name']}")
                    st.write(f"**Bridge ID:** `{b_record['bridge_id']}`")
                    st.write(f"**Location:** {b_record['location']}, {b_record['state']}")
                    st.write(f"**Structural Form:** {b_record['bridge_type']}")
                    st.write(f"**Construction Year:** {b_record['construction_year']}")
                    st.write(f"**Span Length:** {b_record['span_length']} meters")
                    st.write(f"**Design Load:** {b_record['design_load']} metric tons")
                    st.write(f"**Last Inspection:** {b_record['last_inspection_date'] or 'Never'}")
                    st.write(f"**Notes:** {b_record.get('notes', 'None')}")

                with col_det2:
                    st.markdown("### Risk Triage Status")
                    badge_class = f"badge-{risk_summary['category'].lower()}"
                    st.markdown(
                        f"""
                        <div style="margin-bottom: 12px;">
                            <span class="{badge_class}" style="font-size: 15px; padding: 6px 14px;">
                                PRIORITY TIER: {risk_summary['category']} ({risk_summary['score']}/100)
                            </span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    st.write(f"**Recommended Action:** {risk_summary['recommended_action']}")
                    st.write("**Identified Risk Factors:**")
                    reasons = risk_summary.get("reasons", [])
                    for r in reasons:
                        st.markdown(f"- {r}")

                # Delete bridge option with confirmation
                with st.expander("⚠️ Danger Zone: Delete Bridge Asset"):
                    st.warning("Deleting this bridge will permanently remove it and all of its associated inspection logs.")
                    if st.button(f"Confirm Deletion of {selected_b_id}", type="primary"):
                        delete_bridge(selected_b_id)
                        st.success(f"Bridge {selected_b_id} deleted successfully.")
                        st.rerun()
        else:
            st.info("No bridges currently registered in the database.")

    # TAB 2: REGISTER NEW BRIDGE
    with tab_add:
        st.subheader("Register a New Bridge Asset")
        with st.form("add_bridge_form"):
            c1, c2 = st.columns(2)
            with c1:
                b_id_input = st.text_input("Bridge ID *", placeholder="e.g. SS-DL-009")
                b_name_input = st.text_input("Bridge Name *", placeholder="e.g. Yamuna Signature Bridge [DEMONSTRATION RECORD]")
                b_loc_input = st.text_input("Location (City / River) *", placeholder="e.g. Wazirabad, New Delhi")
                b_state_input = st.selectbox(
                    "State *",
                    [
                        "Andhra Pradesh", "Assam", "Bihar", "Delhi", "Goa", "Gujarat",
                        "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala",
                        "Madhya Pradesh", "Maharashtra", "Odisha", "Punjab", "Rajasthan",
                        "Tamil Nadu", "Telangana", "Uttar Pradesh", "Uttarakhand", "West Bengal"
                    ],
                )
                b_type_input = st.selectbox(
                    "Bridge Type *",
                    ["Beam", "Arch", "Suspension", "Cable-stayed", "Slab", "Truss"]
                )

            with c2:
                b_year_input = st.number_input("Construction Year", min_value=1850, max_value=2026, value=1995)
                b_span_input = st.number_input("Span Length (meters)", min_value=1.0, max_value=20000.0, value=650.0)
                b_load_input = st.number_input("Design Load (metric tons)", min_value=1.0, max_value=500.0, value=70.0)
                b_last_insp = st.date_input("Last Inspection Date", value=date.today())
                b_notes_input = st.text_area("Engineering Notes", placeholder="Include [DEMONSTRATION RECORD] tag for demo assets.")

            st.markdown("**Known Risk Factors & Hazards:**")
            rf1, rf2, rf3, rf4, rf5 = st.columns(5)
            with rf1:
                r_flood = st.checkbox("Flood Zone")
            with rf2:
                r_traffic = st.checkbox("High Traffic")
            with rf3:
                r_age = st.checkbox("Age > 30 Years")
            with rf4:
                r_scour = st.checkbox("Previous Scour")
            with rf5:
                r_cracks = st.checkbox("Previous Cracks")

            submitted = st.form_submit_button("Register Bridge", type="primary")
            if submitted:
                if not b_id_input.strip() or not b_name_input.strip():
                    st.error("Bridge ID and Name are mandatory fields.")
                else:
                    existing = get_bridge(b_id_input.strip())
                    if existing:
                        st.error(f"Bridge ID '{b_id_input}' already exists in registry.")
                    else:
                        new_data = {
                            "bridge_id": b_id_input.strip(),
                            "name": b_name_input.strip(),
                            "location": b_loc_input.strip(),
                            "state": b_state_input,
                            "bridge_type": b_type_input,
                            "construction_year": int(b_year_input),
                            "span_length": float(b_span_input),
                            "design_load": float(b_load_input),
                            "last_inspection_date": b_last_insp.strftime("%Y-%m-%d"),
                            "risk_flood_zone": 1 if r_flood else 0,
                            "risk_high_traffic": 1 if r_traffic else 0,
                            "risk_age_over30": 1 if r_age else 0,
                            "risk_previous_scour": 1 if r_scour else 0,
                            "risk_previous_cracks": 1 if r_cracks else 0,
                            "notes": b_notes_input.strip(),
                        }
                        add_bridge(new_data)
                        st.success(f"Bridge '{b_id_input}' registered successfully!")
                        st.rerun()


# =============================================================
# MODULE 2: AI VISUAL INSPECTION
# =============================================================
elif nav_selection == "🔍 AI Visual Inspection":
    render_page_header(
        "AI Visual Inspection & Defect Screening",
        "Convolutional neural network inference and OpenCV edge analysis for concrete crack detection.",
    )

    # Mandatory AI Prototype Notice
    st.markdown(
        f"""
        <div class="disclaimer-ai-box">
            <strong>MANDATORY ENGINEERING NOTICE:</strong> {DISCLAIMER_AI}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div style="margin-bottom: 16px;">
            <span class="demo-tag">{DEMO_MODE_NOTICE}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Input method selection
    col_opt1, col_opt2 = st.columns([1, 1])
    with col_opt1:
        input_source = st.radio(
            "Select Inspection Image Source:",
            ["Choose Synthetic Benchmark Sample", "Upload Inspection Photograph (JPG/PNG)"],
            horizontal=True,
        )

    target_image = None
    target_filename = ""

    if input_source == "Choose Synthetic Benchmark Sample":
        sample_choice = st.selectbox(
            "Select Benchmark Concrete Sample:",
            [
                "Sample 1: Cracked Concrete Pier [Surface Fissure]",
                "Sample 2: Sound Concrete Deck Slab [No Defect]",
            ],
        )
        if "Cracked" in sample_choice:
            sample_path = os.path.join(SAMPLES_DIR, "sample_cracked_pier.jpg")
            if not os.path.exists(sample_path):
                img = generate_synthetic_concrete_image(is_cracked=True, width=640, height=480)
                img.save(sample_path, quality=95)
            target_image = Image.open(sample_path)
            target_filename = "sample_cracked_pier.jpg"
        else:
            sample_path = os.path.join(SAMPLES_DIR, "sample_sound_deck.jpg")
            if not os.path.exists(sample_path):
                img = generate_synthetic_concrete_image(is_cracked=False, width=640, height=480)
                img.save(sample_path, quality=95)
            target_image = Image.open(sample_path)
            target_filename = "sample_sound_deck.jpg"

    else:
        uploaded_file = st.file_uploader("Upload Bridge Inspection Photo", type=["jpg", "jpeg", "png"])
        if uploaded_file is not None:
            bytes_data = uploaded_file.getvalue()
            is_valid, err_msg = validate_image_upload(bytes_data, uploaded_file.name)
            if not is_valid:
                st.error(f"Upload Error: {err_msg}")
            else:
                target_image = Image.open(uploaded_file)
                target_filename = uploaded_file.name
                saved_upload_path = save_uploaded_image(bytes_data, uploaded_file.name, UPLOADS_DIR)

    # Run Analysis if image is present
    if target_image is not None:
        with st.spinner("Executing MobileNetV2 forward pass & OpenCV edge extraction..."):
            res = run_visual_inspection(target_image)

        st.markdown("---")
        st.subheader("Visual Inspection Analysis Results")

        # 3 Imagery Columns: Original, OpenCV Edges, Annotated Overlay
        img_col1, img_col2, img_col3 = st.columns(3)
        with img_col1:
            st.markdown("**Original Photograph**")
            st.image(res["original_image"], use_column_width=True)
        with img_col2:
            st.markdown("**OpenCV Canny Edge Preprocessing**")
            st.image(res["edge_image"], use_column_width=True)
        with img_col3:
            st.markdown("**Annotated Defect Visualization**")
            st.image(res["annotated_image"], use_column_width=True)

        # Classification & Confidence Badges
        st.markdown("<br>", unsafe_allow_html=True)
        res_c1, res_c2, res_c3, res_c4 = st.columns(4)

        with res_c1:
            status_color = "#ef4444" if res["is_cracked"] else "#22c55e"
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="title">Classification Result</div>
                    <div class="value" style="color: {status_color}; font-size: 22px;">{res['classification']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with res_c2:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="title">Confidence Score</div>
                    <div class="value" style="font-size: 22px;">{res['confidence_pct']}%</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with res_c3:
            sev_color = "#ef4444" if res["severity"] == "High" else "#f97316" if res["severity"] == "Medium" else "#22c55e"
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="title">Defect Severity</div>
                    <div class="value" style="color: {sev_color}; font-size: 22px;">{res['severity']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with res_c4:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="title">Edge Density</div>
                    <div class="value" style="font-size: 22px;">{res['metrics']['edge_density']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Engineering Recommendation
        st.info(f"**Engineering Action Recommendation:** {res['recommendation']}")

        # Option to Attach Inspection Finding to a Bridge
        st.markdown("---")
        with st.expander("📝 Attach AI Inspection Finding Directly to a Bridge Record"):
            bridges = get_all_bridges()
            bridge_options = [b["bridge_id"] for b in bridges]

            with st.form("attach_inspection_form"):
                af1, af2 = st.columns(2)
                with af1:
                    sel_b = st.selectbox(
                        "Target Bridge:",
                        options=bridge_options,
                        format_func=lambda x: f"{x} - {next((b['name'] for b in bridges if b['bridge_id'] == x), '')}"
                    )
                    insp_date = st.date_input("Inspection Date", value=date.today())
                    insp_name = st.text_input("Inspector Name", value="Er. AI Vision Operator")
                    insp_type = st.selectbox("Inspection Type", ["Visual", "Detailed", "Special"], index=0)

                with af2:
                    severity_map = {"None": 1, "Low": 2, "Medium": 3, "High": 5}
                    suggested_sev = severity_map.get(res["severity"], 1)
                    sev_rating = st.slider("Severity Rating (1 to 5)", min_value=1, max_value=5, value=suggested_sev)
                    status_option = st.selectbox(
                        "Action Status",
                        ["Pending", "Scheduled", "Escalated", "Completed"],
                        index=2 if res["severity"] == "High" else 0
                    )
                    obs_text = st.text_area(
                        "Observations & Notes",
                        value=f"AI Visual Screening: {res['classification']} detected with {res['confidence_pct']}% confidence. {res['recommendation']}"
                    )

                save_insp = st.form_submit_button("Save Inspection to Bridge Dossier", type="primary")
                if save_insp:
                    insp_entry = {
                        "bridge_id": sel_b,
                        "inspection_date": insp_date.strftime("%Y-%m-%d"),
                        "inspector_name": insp_name.strip(),
                        "inspection_type": insp_type,
                        "observations": obs_text.strip(),
                        "severity_rating": int(sev_rating),
                        "action_status": status_option,
                        "ai_crack_detected": 1 if res["is_cracked"] else 0,
                        "ai_confidence": res["confidence"],
                        "ai_severity": res["severity"],
                        "image_path": target_filename,
                    }
                    add_inspection(insp_entry)
                    st.success(f"Inspection successfully logged for Bridge {sel_b}!")


# =============================================================
# MODULE 3: INSPECTION HISTORY
# =============================================================
elif nav_selection == "📋 Inspection History":
    render_page_header(
        "Bridge Inspection Logs",
        "Record visual and non-destructive inspection logs, filter by bridge, date, and status.",
    )

    tab_history, tab_record = st.tabs(["📜 Inspection Records Explorer", "✍️ Record New Inspection"])

    # TAB 1: HISTORY EXPLORER
    with tab_history:
        inspections_df = get_all_inspections_df()
        bridges = get_all_bridges()

        if not inspections_df.empty:
            # Filters
            f1, f2, f3 = st.columns(3)
            with f1:
                bridge_opts = ["All Bridges"] + [b["bridge_id"] for b in bridges]
                sel_b_filter = st.selectbox("Filter by Bridge ID", bridge_opts)
            with f2:
                status_opts = ["All Statuses", "Pending", "Scheduled", "Escalated", "Completed"]
                sel_status_filter = st.selectbox("Filter by Action Status", status_opts)
            with f3:
                type_opts = ["All Types", "Visual", "Detailed", "Special"]
                sel_type_filter = st.selectbox("Filter by Inspection Type", type_opts)

            filtered_insp = inspections_df.copy()
            if sel_b_filter != "All Bridges":
                filtered_insp = filtered_insp[filtered_insp["bridge_id"] == sel_b_filter]
            if sel_status_filter != "All Statuses":
                filtered_insp = filtered_insp[filtered_insp["action_status"] == sel_status_filter]
            if sel_type_filter != "All Types":
                filtered_insp = filtered_insp[filtered_insp["inspection_type"] == sel_type_filter]

            st.write(f"Showing **{len(filtered_insp)}** inspection record(s):")

            # Table display
            disp_cols = [
                "id", "bridge_id", "bridge_name", "inspection_date", "inspector_name",
                "inspection_type", "severity_rating", "action_status", "ai_crack_detected"
            ]
            st.dataframe(
                filtered_insp[disp_cols],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "id": "Log ID",
                    "bridge_id": "Bridge ID",
                    "bridge_name": "Bridge Name",
                    "inspection_date": "Date",
                    "inspector_name": "Inspector",
                    "inspection_type": "Type",
                    "severity_rating": "Severity (1-5)",
                    "action_status": "Status",
                    "ai_crack_detected": "AI Detected",
                },
            )

            # Detail expander for inspection observations
            st.markdown("---")
            st.subheader("Inspection Observation Viewer")
            insp_id_select = st.selectbox(
                "Select Log ID to view full observations:",
                options=filtered_insp["id"].tolist(),
                format_func=lambda x: f"Log #{x} - {filtered_insp.loc[filtered_insp['id'] == x, 'bridge_id'].values[0]} ({filtered_insp.loc[filtered_insp['id'] == x, 'inspection_date'].values[0]})"
            )

            if insp_id_select:
                row = filtered_insp[filtered_insp["id"] == insp_id_select].iloc[0]
                ic1, ic2 = st.columns([2, 1])
                with ic1:
                    st.write(f"**Bridge:** {row['bridge_id']} — {row['bridge_name']}")
                    st.write(f"**Inspection Date:** {row['inspection_date']} &nbsp;|&nbsp; **Inspector:** {row['inspector_name']}")
                    st.write(f"**Inspection Type:** {row['inspection_type']}")
                    st.write(f"**Defect Severity Rating:** {row['severity_rating']} / 5")
                    st.write(f"**Action Status:** `{row['action_status']}`")
                    st.markdown("**Observations:**")
                    st.info(row["observations"])

                with ic2:
                    st.write("**Quick Status Update:**")
                    new_st = st.selectbox(
                        "Change Status To:",
                        ["Pending", "Scheduled", "Escalated", "Completed"],
                        key=f"status_change_{insp_id_select}"
                    )
                    if st.button("Update Status"):
                        update_inspection_status(int(insp_id_select), new_st)
                        st.success(f"Log #{insp_id_select} status updated to {new_st}!")
                        st.rerun()

        else:
            st.info("No inspection records found.")

    # TAB 2: RECORD NEW INSPECTION
    with tab_record:
        st.subheader("Record a New Inspection Entry")
        bridges = get_all_bridges()
        if not bridges:
            st.warning("Please register at least one bridge in the Bridge Registry before logging inspections.")
        else:
            with st.form("manual_inspection_form"):
                rc1, rc2 = st.columns(2)
                with rc1:
                    b_target = st.selectbox(
                        "Bridge *",
                        options=[b["bridge_id"] for b in bridges],
                        format_func=lambda x: f"{x} - {next(b['name'] for b in bridges if b['bridge_id'] == x)}"
                    )
                    i_date = st.date_input("Inspection Date *", value=date.today())
                    i_inspector = st.text_input("Inspector Name *", placeholder="e.g. Er. Sunil Verma")
                    i_type = st.selectbox("Inspection Type *", ["Visual", "Detailed", "Special"])

                with rc2:
                    i_severity = st.slider("Severity Rating (1 = Minor Surface Wear, 5 = Critical Defect) *", 1, 5, 2)
                    i_status = st.selectbox("Action Status *", ["Pending", "Scheduled", "Escalated", "Completed"])
                    i_obs = st.text_area("Narrative Observations *", placeholder="Describe observed spalling, cracking, scour, or bearing issues...")

                manual_submit = st.form_submit_button("Record Inspection Entry", type="primary")
                if manual_submit:
                    if not i_inspector.strip() or not i_obs.strip():
                        st.error("Inspector name and observations are required.")
                    else:
                        new_insp = {
                            "bridge_id": b_target,
                            "inspection_date": i_date.strftime("%Y-%m-%d"),
                            "inspector_name": i_inspector.strip(),
                            "inspection_type": i_type,
                            "observations": i_obs.strip(),
                            "severity_rating": int(i_severity),
                            "action_status": i_status,
                            "ai_crack_detected": 0,
                            "ai_confidence": 0.0,
                            "ai_severity": "None",
                            "image_path": "",
                        }
                        add_inspection(new_insp)
                        st.success(f"Inspection entry logged successfully for bridge {b_target}!")
                        st.rerun()


# =============================================================
# MODULE 4: RISK PRIORITISATION
# =============================================================
elif nav_selection == "⚡ Risk Prioritisation":
    render_page_header(
        "Risk Prioritisation & Triage Engine",
        "Explainable multi-factor scoring for asset inspection prioritization.",
    )

    # Mandatory Triage Tool Disclaimer
    st.markdown(
        f"""
        <div class="disclaimer-box">
            <strong>OFFICIAL OPERATIONAL NOTICE:</strong> {RISK_DISCLAIMER}
        </div>
        """,
        unsafe_allow_html=True,
    )

    bridges = get_all_bridges()
    inspections = get_all_inspections()

    insp_map = {}
    for insp in inspections:
        bid = insp["bridge_id"]
        insp_map.setdefault(bid, []).append(insp)

    ranked_bridges = rank_bridges_by_risk(bridges, insp_map)

    # Filter by priority category
    cat_filter = st.selectbox(
        "Filter by Priority Tier:",
        ["All Priority Tiers", CATEGORY_CRITICAL, CATEGORY_HIGH, CATEGORY_MEDIUM, CATEGORY_LOW]
    )

    if cat_filter != "All Priority Tiers":
        ranked_bridges = [b for b in ranked_bridges if b["category"] == cat_filter]

    st.write(f"Showing **{len(ranked_bridges)}** prioritised bridge asset(s):")

    for idx, b in enumerate(ranked_bridges, 1):
        tier = b["category"]
        badge_class = f"badge-{tier.lower()}"
        score = b["score"]
        color = COLOR_MAP.get(tier, "#64748b")

        with st.container():
            st.markdown(
                f"""
                <div style="border: 1px solid #e2e8f0; border-left: 6px solid {color}; border-radius: 8px; padding: 16px; margin-bottom: 16px; background-color: #ffffff;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <div>
                            <span style="font-size: 18px; font-weight: 700; color: #0f172a;">#{idx}. {b['name']}</span>
                            <span style="color: #64748b; font-size: 13px; margin-left: 8px;">({b['bridge_id']})</span>
                        </div>
                        <div>
                            <span class="{badge_class}" style="font-size: 13px;">{tier} PRIORITY &nbsp;|&nbsp; SCORE: {score}/100</span>
                        </div>
                    </div>
                    <div style="font-size: 13px; color: #334155; margin-bottom: 8px;">
                        <strong>Location:</strong> {b['location']}, {b['state']} &nbsp;|&nbsp;
                        <strong>Type:</strong> {b['bridge_type']} &nbsp;|&nbsp;
                        <strong>Age:</strong> {datetime.now().year - (b.get('construction_year') or datetime.now().year)} yrs &nbsp;|&nbsp;
                        <strong>Last Inspected:</strong> {b.get('recency_note', 'Unknown')}
                    </div>
                    <div style="font-size: 13px; color: #0f766e; font-weight: 600; margin-bottom: 10px;">
                        Recommended Action: {b['recommended_action']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            with st.expander(f"🔍 Explainable Breakdown: Why is {b['bridge_id']} priority elevated?"):
                st.markdown("**Priority elevated because:**")
                for reason in b.get("reasons", []):
                    st.markdown(f"- {reason}")

                st.markdown("**Scoring Component Contributions:**")
                breakdown = b.get("breakdown", {})
                b_df = pd.DataFrame([
                    {"Factor": "Inspection Overdue / Recency", "Points": breakdown.get("recency", 0)},
                    {"Factor": "Structure Age (>30 / >50 yrs)", "Points": breakdown.get("structure_age", 0)},
                    {"Factor": "Known Hazard Factors (Flood/Scour/Cracks)", "Points": breakdown.get("known_risk_factors", 0)},
                    {"Factor": "Unresolved Pending/Escalated Defect Logs", "Points": breakdown.get("unresolved_observations", 0)},
                    {"Factor": "Most Recent Defect Severity Rating", "Points": breakdown.get("recent_severity", 0)},
                ])
                st.dataframe(b_df, use_container_width=True, hide_index=True)


# =============================================================
# MODULE 6: ALERTS & REPORTING
# =============================================================
elif nav_selection == "⚠️ Alerts & Reporting":
    render_page_header(
        "Alerts & Engineering Reporting",
        "Track overdue inspections, monitor unresolved defect logs, export CSV data, and generate printable dossiers.",
    )

    tab_alerts, tab_export, tab_print = st.tabs(["⚠️ Active Alerts", "📥 Export CSV Data", "🖨️ Print-Friendly Bridge Dossier"])

    # TAB 1: ACTIVE ALERTS
    with tab_alerts:
        overdue_list = get_overdue_bridges(days_threshold=365)
        st.subheader("1. Inspection Overdue Alerts (> 365 Days)")
        if overdue_list:
            st.error(f"⚠️ {len(overdue_list)} bridge(s) currently exceed the 365-day annual inspection threshold!")
            od_df = pd.DataFrame(overdue_list)[[
                "bridge_id", "name", "location", "state", "last_inspection_date", "days_overdue"
            ]]
            st.dataframe(
                od_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "bridge_id": "Bridge ID",
                    "name": "Name",
                    "location": "Location",
                    "state": "State",
                    "last_inspection_date": "Last Inspected",
                    "days_overdue": "Days Overdue",
                },
            )
        else:
            st.success("All registered bridges have been inspected within the last 365 days.")

        st.markdown("---")
        st.subheader("2. Unresolved Observation Tracker (Pending & Escalated)")
        unresolved = get_unresolved_inspections()
        if unresolved:
            st.warning(f"⚠️ Found {len(unresolved)} unresolved observation(s) across the infrastructure network.")
            unres_df = pd.DataFrame(unresolved)[[
                "id", "bridge_id", "bridge_name", "inspection_date", "inspector_name",
                "severity_rating", "action_status", "observations"
            ]]
            st.dataframe(
                unres_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "id": "Log ID",
                    "bridge_id": "Bridge ID",
                    "bridge_name": "Bridge Name",
                    "inspection_date": "Date",
                    "inspector_name": "Inspector",
                    "severity_rating": "Severity",
                    "action_status": "Status",
                    "observations": "Observations",
                },
            )
        else:
            st.success("No unresolved observations pending action.")

    # TAB 2: EXPORT CSV
    with tab_export:
        st.subheader("Export System Data (CSV)")
        st.write("Download complete tabular snapshots of asset registers and inspection records.")

        ec1, ec2 = st.columns(2)
        with ec1:
            st.markdown("### Bridge Assets Registry")
            all_b = get_all_bridges()
            b_csv = export_bridges_csv(all_b)
            st.download_button(
                label="📥 Download Bridges CSV",
                data=b_csv,
                file_name=f"setusentry_bridges_{date.today().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                type="primary",
            )
            st.write(f"Total bridge records: {len(all_b)}")

        with ec2:
            st.markdown("### Historical Inspection Logs")
            all_i = get_all_inspections()
            i_csv = export_inspections_csv(all_i)
            st.download_button(
                label="📥 Download Inspections CSV",
                data=i_csv,
                file_name=f"setusentry_inspections_{date.today().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                type="primary",
            )
            st.write(f"Total inspection entries: {len(all_i)}")

    # TAB 3: PRINT-FRIENDLY DOSSIER
    with tab_print:
        st.subheader("Print-Friendly Bridge Inspection Dossier")
        bridges = get_all_bridges()

        if bridges:
            b_sel_print = st.selectbox(
                "Select Bridge for Dossier Generation:",
                options=[b["bridge_id"] for b in bridges],
                format_func=lambda x: f"{x} - {next(b['name'] for b in bridges if b['bridge_id'] == x)}"
            )

            b_record = get_bridge(b_sel_print)
            b_inspections = get_inspections_for_bridge(b_sel_print)
            risk_summary = calculate_bridge_risk(b_record, b_inspections)

            html_report = generate_print_friendly_report_html(b_record, b_inspections, risk_summary)

            st.download_button(
                label="📄 Download Print-Ready HTML Dossier",
                data=html_report,
                file_name=f"setusentry_report_{b_sel_print}_{date.today().strftime('%Y%m%d')}.html",
                mime="text/html",
                type="primary",
            )

            st.markdown("#### Report Preview:")
            st.components.v1.html(html_report, height=650, scrolling=True)
        else:
            st.info("No bridges available to report.")
