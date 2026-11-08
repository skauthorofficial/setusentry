# SetuSentry (सेतु संतरी)
### AI-Assisted Bridge Inspection and Risk-Prioritisation System

SetuSentry is an engineering decision-support prototype and triage tool designed to assist civil infrastructure agencies in maintaining bridge registries, logging visual inspection records, screening surface defect imagery using convolutional neural networks and OpenCV, and prioritising maintenance scheduling through an explainable multi-factor risk index.

---

> ### ⚠️ Mandatory Engineering & Safety Notice
> **"This system is an educational prototype for preliminary visual inspection and inspection prioritisation. It does not establish structural safety, predict bridge collapse or replace qualified bridge engineers and recognised structural testing procedures."**
>
> The priority indices computed herein are strictly operational scheduling triage scores. The system does not predict probability of failure or collapse.

---

## 🏛️ System Modules

### 1. Bridge Registry
- Comprehensive asset management: Bridge ID, Name, Location, State, Structural Type (Beam, Arch, Cable-Stayed, Suspension, Slab, Truss), Construction Year, Span Length, Design Load, Last Inspection Date.
- Environmental hazard tags: Active flood zone, high commercial traffic density, age >30 years, previous riverbed scour, previous crack history.
- Searchable, filterable asset inventory with full record detail inspector.

### 2. AI Visual Inspection (MobileNetV2 + OpenCV)
- Upload bridge inspection photography (JPG/PNG) or test using built-in synthetic benchmark imagery.
- Dual-stage analysis pipeline:
  - **PyTorch MobileNetV2**: Feature extraction backbone pre-trained on ImageNet.
  - **OpenCV Computer Vision**: Grayscale normalization, CLAHE contrast equalization, Gaussian smoothing, adaptive Canny edge detection, and elongated contour aspect-ratio screening.
- Visual outputs: Original photo, side-by-side edge map, and annotated defect visualization with highlighted fissure contours and bounding boxes.
- Metrics: Defect classification (Cracked / Non-Cracked), Calibrated Confidence %, Severity (Low / Medium / High), and actionable engineering recommendation.
- Direct option to log visual inspection findings directly into the bridge's permanent record.
- **Label**: `DEMONSTRATION MODE — model requires fine-tuning on crack dataset.`

### 3. Inspection History
- Log detailed multi-tier inspection logs: Inspection Date, Inspector Name, Inspection Type (Visual, Detailed, Special), Narrative Observations, Defect Severity Rating (Scale 1–5), Action Status (Pending, Scheduled, Completed, Escalated), and uploaded photo attachment.
- Interactive historical inspection timeline and filtering by bridge, date range, and status.

### 4. Explainable Risk Prioritisation
- Computes deterministic triage priority score (0–100) mapped to four operational tiers:
  - 🟢 **LOW (0–29)**: Standard routine surveillance cycle.
  - 🟡 **MEDIUM (30–54)**: Maintain regular surveillance, resolve pending items.
  - 🟠 **HIGH (55–79)**: Schedule expedited inspection within 30 days.
  - 🔴 **CRITICAL (80+)**: Prioritize for immediate on-site structural engineering review.
- **Explainable breakdown**: Clear natural-language explanation of exactly which factors elevated priority (e.g., overdue inspection days, unresolved escalated observations, structural age >50 years, flood/scour hazard flags, recent severity rating).

### 5. Executive Dashboard
- Real-time KPI summary metric cards (Total Bridges, Overdue Inspections, High/Critical Priority Assets, Total Inspection Logs).
- Interactive Plotly visualizations:
  - Priority Tier Distribution bar chart.
  - 12-Month Inspection Activity timeline.
  - Structural Type breakdown.
- Top 5 Highest Priority Triage Table with quick action jump links.

### 6. Alerts & Engineering Reporting
- Automated overdue inspection tracker (bridges with >365 days since last inspection).
- Open defect monitor listing all unresolved (Pending / Escalated) observations across the network.
- Full CSV data export for bridges and inspection history.
- Print-friendly, responsive HTML dossier generator designed for A4 print-to-PDF with formal engineering signature sign-off blocks.

---

## 🛠️ Tech Stack

- **Python**: 3.10+ (Tested on Python 3.12 / 3.14)
- **UI Framework**: Streamlit
- **Relational Database**: SQLite3 (Foreign key constraints & indexing enabled)
- **Computer Vision**: OpenCV (cv2)
- **Deep Learning**: PyTorch (`torch`), Torchvision (`mobilenet_v2`)
- **Data & Visualisation**: Pandas, Plotly Express & Graph Objects, NumPy
- **Image Handling**: Pillow (PIL)
- **Testing**: Python `unittest`

---

## 🚀 Quickstart & Setup

### 1. Install Dependencies
```bash
cd c:\Users\user\Downloads\Chem_PPT\setusentry
pip install -r requirements.txt
```

### 2. Run Automated Setup & Verification
```bash
python setup.py
```
This automated script will:
- Initialize the SQLite database (`setusentry.db`).
- Seed 8 sample Indian bridge records with realistic multi-year inspection logs (labeled `[DEMONSTRATION RECORD]`).
- Generate high-resolution synthetic cracked and sound concrete test images in `uploads/samples/`.
- Validate the PyTorch MobileNetV2 and OpenCV pipeline.
- Run all unit tests to confirm module health.

### 3. Launch Streamlit Web Application
```bash
streamlit run app.py
```

---

## 📂 Project Directory Structure

```
setusentry/
├── app.py                      # Streamlit multi-module web application
├── database.py                 # SQLite schema, connection management, CRUD queries
├── risk_engine.py              # Explainable priority scoring engine and categorization
├── model/
│   ├── crack_detector.py       # MobileNetV2 architecture with binary classification head
│   ├── train.py                # Complete SDNET2018 fine-tuning pipeline script
│   └── demo_inference.py       # Demonstration inference combining MobileNetV2 + OpenCV
├── utils/
│   ├── image_utils.py          # Validation, uploads, and synthetic test image generation
│   └── report_utils.py         # CSV exports and print-friendly HTML dossier generator
├── data/
│   └── seed_data.py            # 8 demonstration Indian bridge records and inspection history
├── tests/
│   ├── test_database.py        # Database CRUD, cascade, and query unit tests
│   ├── test_risk_engine.py     # Risk scoring, explainability, and safety phrasing tests
│   └── test_image_utils.py     # Image validation and synthetic generator tests
├── uploads/                    # Stores uploaded inspection photos
│   └── samples/                # Pre-generated cracked and sound test photos
├── requirements.txt            # Python dependency specification
├── setup.py                    # Environment initialization and test runner
└── README.md                   # Comprehensive technical documentation
```

---

## 🧠 AI Model & SDNET2018 Training

The application includes `model/train.py`, a complete PyTorch training script for fine-tuning MobileNetV2 on the **SDNET2018** concrete crack benchmark dataset:

```bash
# Example training command:
python model/train.py --data_dir data/SDNET2018 --epochs 20 --batch_size 32 --lr 1e-4
```
Features include:
- Automatic discovery of SDNET2018 subdirectories (Bridge Decks, Pavements, Walls).
- Data augmentation (RandomResizedCrop, Rotation, Flips, ColorJitter, Normalization).
- Validation tracking of Precision, Recall, and F1-score with best-model checkpoint saving.

---

## 📄 License & Attribution
Developed for educational research and infrastructure maintenance planning. Built with Streamlit, PyTorch, and OpenCV.
