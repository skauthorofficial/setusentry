"""
SetuSentry AI Demonstration Inference Engine
Executes MobileNetV2 feature analysis combined with OpenCV edge and contour
density metrics to detect concrete cracks and defects.

LABELED AS DEMONSTRATION MODE:
"DEMONSTRATION MODE — model requires fine-tuning on crack dataset."

PORTABILITY: torch/torchvision are optional. If not installed, falls back to
pure OpenCV-based crack analysis (still fully functional for demonstration).
"""

from __future__ import annotations
import os
import sys
from typing import Any, Dict, Union
import cv2
import numpy as np
from PIL import Image

# Add parent directory to sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

# Optional PyTorch — graceful fallback if not installed
TORCH_AVAILABLE = False
try:
    import torch
    from torchvision import transforms
    from model.crack_detector import MobileNetV2CrackDetector
    TORCH_AVAILABLE = True
except ImportError:
    pass

DISCLAIMER_AI = (
    "This system is an educational prototype for preliminary visual inspection "
    "and inspection prioritisation. It does not establish structural safety, "
    "predict bridge collapse or replace qualified bridge engineers and "
    "recognised structural testing procedures."
)

DEMO_MODE_NOTICE = "DEMONSTRATION MODE — model requires fine-tuning on crack dataset."

# Singleton model cache to avoid reloading on every Streamlit rerun
_CACHED_MODEL = None


def get_inference_model(device: str = "cpu"):
    """Retrieve or initialize the cached MobileNetV2 crack detector.
    Returns None if PyTorch is not available (falls back to pure OpenCV mode)."""
    global _CACHED_MODEL
    if not TORCH_AVAILABLE:
        return None
    if _CACHED_MODEL is None:
        _CACHED_MODEL = MobileNetV2CrackDetector(pretrained=True)
        weights_path = os.path.join(PARENT_DIR, "model", "mobilenetv2_crack_finetuned.pth")
        if os.path.exists(weights_path):
            try:
                state = torch.load(weights_path, map_location=device)
                _CACHED_MODEL.load_state_dict(state)
            except Exception:
                pass
        _CACHED_MODEL.to(device)
        _CACHED_MODEL.eval()
    return _CACHED_MODEL


def analyze_image_opencv(image_bgr: np.ndarray) -> Dict[str, Any]:
    """
    Perform OpenCV image preprocessing and crack feature extraction:
    - Grayscale conversion
    - Contrast Limited Adaptive Histogram Equalization (CLAHE)
    - Bilateral / Gaussian smoothing
    - Canny edge detection
    - Morphological filtering
    - Contour extraction for elongated crack structures
    """
    h, w = image_bgr.shape[:2]
    total_pixels = h * w

    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)

    # Enhance contrast with CLAHE
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    # Slight blur to reduce sensor noise while preserving crack edges
    blurred = cv2.GaussianBlur(enhanced, (5, 5), 0)

    # Adaptive Canny edge detection
    med_val = np.median(blurred)
    lower = int(max(0, 0.65 * med_val))
    upper = int(min(255, 1.35 * med_val))
    edges = cv2.Canny(blurred, lower, upper)

    # Morphological closing to connect fragmented crack lines
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    dilated_edges = cv2.dilate(edges, kernel, iterations=1)

    # Find contours of edge segments
    contours, _ = cv2.findContours(dilated_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Filter contours based on structural crack characteristics (elongation, length)
    crack_contours = []
    total_crack_length = 0.0
    bounding_boxes = []

    for cnt in contours:
        area = cv2.contourArea(cnt)
        perimeter = cv2.arcLength(cnt, closed=False)
        if perimeter > 25 and area > 10:
            # Check aspect ratio or tortuosity: cracks have high perimeter relative to area
            x, y, bw, bh = cv2.boundingRect(cnt)
            aspect_ratio = max(bw, bh) / (min(bw, bh) + 1e-5)
            if aspect_ratio > 1.8 or perimeter > 50:
                crack_contours.append(cnt)
                total_crack_length += perimeter
                bounding_boxes.append((x, y, bw, bh))

    # Calculate edge density metrics
    edge_pixel_count = np.count_nonzero(edges)
    edge_density = edge_pixel_count / float(total_pixels)

    return {
        "gray": gray,
        "enhanced": enhanced,
        "edges": edges,
        "dilated_edges": dilated_edges,
        "crack_contours": crack_contours,
        "bounding_boxes": bounding_boxes,
        "edge_density": edge_density,
        "edge_pixel_count": edge_pixel_count,
        "total_crack_length": total_crack_length,
        "contour_count": len(crack_contours),
    }


def create_annotated_display(
    image_bgr: np.ndarray,
    cv_results: Dict[str, Any],
    is_cracked: bool,
    severity: str
) -> np.ndarray:
    """
    Generate an annotated visualization with highlighted crack paths,
    bounding boxes, and HUD status banner.
    """
    annotated = image_bgr.copy()
    h, w = annotated.shape[:2]

    if is_cracked and cv_results["crack_contours"]:
        # Create transparent colored mask over detected crack regions
        overlay = annotated.copy()
        # Draw neon red/coral contour lines for detected cracks
        cv2.drawContours(overlay, cv_results["crack_contours"], -1, (0, 0, 255), 2)

        # Alpha blend crack traces
        alpha = 0.7
        cv2.addWeighted(overlay, alpha, annotated, 1 - alpha, 0, annotated)

        # Draw bounding boxes with subtle severity color
        color_box = (0, 0, 230) if severity == "High" else (0, 140, 255) if severity == "Medium" else (0, 200, 200)
        for x, y, bw, bh in cv_results["bounding_boxes"]:
            # Pad bounding box slightly
            px = max(0, x - 4)
            py = max(0, y - 4)
            pw = min(w - px, bw + 8)
            ph = min(h - py, bh + 8)
            cv2.rectangle(annotated, (px, py), (px + pw, py + ph), color_box, 1)

    # Draw semi-transparent header HUD bar
    hud_height = max(40, int(h * 0.08))
    hud_overlay = annotated.copy()
    cv2.rectangle(hud_overlay, (0, 0), (w, hud_height), (20, 24, 30), -1)
    cv2.addWeighted(hud_overlay, 0.75, annotated, 0.25, 0, annotated)

    status_str = f"STATUS: {'CRACK DETECTED' if is_cracked else 'NO CRACKS DETECTED'} | SEVERITY: {severity.upper()}"
    tag_color = (60, 60, 240) if is_cracked else (60, 220, 60)
    font_scale = max(0.45, min(w / 800.0, 0.8))
    cv2.putText(
        annotated,
        status_str,
        (12, int(hud_height * 0.65)),
        cv2.FONT_HERSHEY_SIMPLEX,
        font_scale,
        tag_color,
        2,
        cv2.LINE_AA,
    )

    return annotated


def run_visual_inspection(
    image_input: Union[str, Image.Image, np.ndarray],
    device: str = "cpu"
) -> Dict[str, Any]:
    """
    Complete inspection pipeline:
    1. Loads and standardizes image
    2. Runs PyTorch MobileNetV2 forward pass & feature extraction
    3. Runs OpenCV computer vision edge density & structural crack analysis
    4. Computes calibrated confidence score & severity grade
    5. Returns annotated imagery, metrics, and actionable recommendations
    """
    # Standardize image to numpy RGB and BGR
    if isinstance(image_input, str):
        pil_img = Image.open(image_input).convert("RGB")
    elif isinstance(image_input, Image.Image):
        pil_img = image_input.convert("RGB")
    elif isinstance(image_input, np.ndarray):
        if len(image_input.shape) == 2:
            pil_img = Image.fromarray(image_input).convert("RGB")
        elif image_input.shape[2] == 4:
            pil_img = Image.fromarray(image_input).convert("RGB")
        else:
            pil_img = Image.fromarray(image_input)
    else:
        raise ValueError("Unsupported image input type.")

    img_rgb = np.array(pil_img)
    img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)

    # 1. PyTorch MobileNetV2 Inference (optional — skipped if torch not installed)
    feature_norm = 100.0  # default neutral value for pure-OpenCV mode
    if TORCH_AVAILABLE:
        model = get_inference_model(device=device)
        if model is not None:
            transform = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ])
            tensor_input = transform(pil_img).unsqueeze(0).to(device)
            with torch.no_grad():
                features = model.extract_features(tensor_input)
                feature_norm = float(torch.norm(features).item())

    # 2. OpenCV Structural Crack Analysis (always runs — works without torch)
    cv_results = analyze_image_opencv(img_bgr)
    edge_density = cv_results["edge_density"]
    contour_count = cv_results["contour_count"]
    total_length = cv_results["total_crack_length"]

    # 3. Demonstration Mode Heuristic Calibration
    # Concrete without cracks usually has edge_density < 0.015 and low elongated contours.
    # Concrete with cracks exhibits distinct elongated edges and edge_density > 0.018.
    crack_metric = (edge_density * 45.0) + (contour_count * 0.04) + (min(total_length, 1000) / 1500.0)

    # Neural feature activation modulation (neutral 1.0 when torch unavailable)
    neural_factor = min(max(feature_norm / 150.0, 0.8), 1.2)
    calibrated_score = crack_metric * neural_factor

    threshold = 0.55
    is_cracked = calibrated_score >= threshold

    if is_cracked:
        # Confidence scaled between 0.65 and 0.98
        confidence = min(0.65 + (calibrated_score - threshold) * 0.45, 0.97)
        if confidence >= 0.85 or cv_results["contour_count"] >= 8 or total_length > 400:
            severity = "High"
            recommendation = (
                "Expedited on-site structural engineering inspection recommended. "
                "Deploy crack gauge to record aperture width and monitor crack propagation under live vehicular loads."
            )
        elif confidence >= 0.72 or cv_results["contour_count"] >= 4:
            severity = "Medium"
            recommendation = (
                "Schedule detailed non-destructive testing (NDT / Ultrasonic pulse velocity). "
                "Document baseline fissure dimensions and inspect for subsurface delamination."
            )
        else:
            severity = "Low"
            recommendation = (
                "Hairline surface fissures detected. Likely superficial shrinkage or early weathering. "
                "Log in asset registry and review during next scheduled maintenance cycle."
            )
        classification = "Cracked"
    else:
        confidence = max(0.70, 1.0 - calibrated_score)
        severity = "None"
        classification = "Non-Cracked"
        recommendation = (
            "No significant structural surface fissures detected in the examined photograph. "
            "Concrete surface appears sound. Continue regular periodic surveillance."
        )

    # 4. Generate visual outputs
    annotated_bgr = create_annotated_display(img_bgr, cv_results, is_cracked, severity)
    annotated_rgb = cv2.cvtColor(annotated_bgr, cv2.COLOR_BGR2RGB)

    # Edge visualization (RGB for display)
    edge_rgb = cv2.cvtColor(cv_results["edges"], cv2.COLOR_GRAY2RGB)

    mode_label = DEMO_MODE_NOTICE
    if not TORCH_AVAILABLE:
        mode_label = "OPENCV-ONLY MODE — PyTorch not installed. Using edge-density analysis. " + DEMO_MODE_NOTICE

    return {
        "is_cracked": is_cracked,
        "classification": classification,
        "confidence": float(round(confidence, 3)),
        "confidence_pct": float(round(confidence * 100, 1)),
        "severity": severity,
        "recommendation": recommendation,
        "original_image": img_rgb,
        "annotated_image": annotated_rgb,
        "edge_image": edge_rgb,
        "metrics": {
            "edge_density": float(round(edge_density, 4)),
            "crack_contours_count": contour_count,
            "estimated_length_px": float(round(total_length, 1)),
            "feature_norm": float(round(feature_norm, 2)),
        },
        "is_demo_mode": True,
        "torch_available": TORCH_AVAILABLE,
        "demo_mode_label": mode_label,
        "disclaimer": DISCLAIMER_AI,
    }
