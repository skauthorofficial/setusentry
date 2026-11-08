"""
SetuSentry — Bridge Failure Simulator
Interactive 2-D physics simulation showing how each failure factor
(overloading, corrosion, scour, flood, construction quality, maintenance
neglect, design error, bearing wear, fatigue, seismic) degrades a bridge
over time and eventually causes collapse.

DISCLAIMER: All physics are simplified educational models.
Not suitable for any form of engineering assessment.
"""

import os
import streamlit as st

st.set_page_config(
    page_title="Bridge Failure Simulator | SetuSentry",
    page_icon="🏗️",
    layout="wide",
)

st.markdown("""
<style>
/* Hide Streamlit chrome so the sim fills the frame cleanly */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 !important; }
</style>
""", unsafe_allow_html=True)

# Load the simulation HTML
SIM_PATH = os.path.join(os.path.dirname(__file__), "..", "bridge_sim.html")

try:
    with open(SIM_PATH, "r", encoding="utf-8") as fh:
        sim_html = fh.read()
    # Render full-page inside an iframe-equivalent component
    st.components.v1.html(sim_html, height=820, scrolling=False)
except FileNotFoundError:
    st.error(
        "Simulation file `bridge_sim.html` not found. "
        "Make sure it exists in the `setusentry/` root directory."
    )
