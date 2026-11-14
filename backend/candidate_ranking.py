import io
from pathlib import Path
from typing import Dict, List, Optional
import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from astropy.io import fits
from astropy.wcs import WCS
from astropy.coordinates import SkyCoord
import astropy.units as u
from photutils.detection import DAOStarFinder
from photutils.background import MedianBackground, StdBackgroundRMS, Background2D

from image_processing import load_fits_image, align_observations, match_background
from catalog_overlay import query_external_catalogs

BASE_DIR = Path(__file__).resolve().parent.parent

# Interpretation categories as required by Phase 4
CLASSIFICATION_LIKELY = "Likely moving source"
CLASSIFICATION_POSSIBLE = "Possible motion"
CLASSIFICATION_KNOWN = "Known matched object"
CLASSIFICATION_FLAGGED = "Artifact / Flagged"

FLAG_INTERPRETATIONS = {
    0: "Clean science pixel (No quality defects)",
    1: "Non-science or detector margin",
    2: "Bad pixel / uncalibrated response",
    4: "Cosmic ray / radiation event hit",
    8: "Saturated / non-linear regime",
    16: "Edge or interpolation boundary",
    2097152: "Standard calibration mask (Bit 21 active - normal science cutout)",
}

def interpret_flags(flag_val: int) -> str:
    """Provides plain scientific explanation of FITS flag values."""
    if flag_val in FLAG_INTERPRETATIONS:
        return FLAG_INTERPRETATIONS[flag_val]
    if flag_val == 0:
        return "Clean (Flag 0)"
    return f"Bitmask ({flag_val}) - check calibration flag definitions"


def extract_candidate_evidence_image(
    first_path: Path,
    second_path: Path,
    px1: float,
    py1: float,
    px2: float,
    py2: float,
    crop_radius: int = 7,
) -> io.BytesIO:
    """
    Produces a 3-panel evidence cutout strip:
    [Epoch 1 Zoom] [Epoch 2 Zoom] [Difference Map Zoom]
    """
    with fits.open(first_path) as f1, fits.open(second_path) as f2:
        im1 = np.array(f1["IMAGE"].data, dtype=float)
        im2 = np.array(f2["IMAGE"].data, dtype=float)

    h, w = im1.shape
    ix1, iy1 = int(round(px1)), int(round(py1))
    ix2, iy2 = int(round(py2)), int(round(py2))

    # Center crop window around average position
    cx = int(round((px1 + px2) / 2.0))
    cy = int(round((py1 + py2) / 2.0))

    x0 = max(0, cx - crop_radius)
    x1_box = min(w, cx + crop_radius + 1)
    y0 = max(0, cy - crop_radius)
    y1_box = min(h, cy + crop_radius + 1)

    crop1 = im1[y0:y1_box, x0:x1_box]
    crop2 = im2[y0:y1_box, x0:x1_box]
    crop_diff = crop2 - crop1

    fig, axes = plt.subplots(1, 3, figsize=(9, 3.2), dpi=140)
    fig.patch.set_facecolor("#07090e")

    titles = ["Epoch 1 (2025)", "Epoch 2 (2026)", "Difference (Δ)"]
    crops = [crop1, crop2, crop_diff]
    cmaps = ["inferno", "inferno", "coolwarm"]

    for i, ax in enumerate(axes):
        ax.set_facecolor("#000000")
        crop = crops[i]
        valid = crop[np.isfinite(crop)]
        if len(valid) > 0:
            if i == 2:
                b = float(np.percentile(np.abs(valid), 95)) or 0.2
                vmin, vmax = -b, b
            else:
                vmin, vmax = np.percentile(valid, [5, 95])
        else:
            vmin, vmax = None, None

        ax.imshow(crop, origin="lower", cmap=cmaps[i], vmin=vmin, vmax=vmax)

        # Plot candidate reticle relative to sub-crop
        if i == 0:
            rx, ry = px1 - x0, py1 - y0
            color = "#38bdf8"
        elif i == 1:
            rx, ry = px2 - x0, py2 - y0
            color = "#f43f5e"
        else:
            rx, ry = (px1 + px2) / 2.0 - x0, (py1 + py2) / 2.0 - y0
            color = "#fbbf24"

        ax.plot(rx, ry, marker="+", markersize=12, markeredgewidth=1.8, color=color)
        ax.set_title(titles[i], color="#f8fafc", fontsize=9, pad=6)
        ax.tick_params(colors="#64748b", labelsize=7)
        for spine in ax.spines.values():
            spine.set_color("#334155")

    plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf


def rank_and_classify_candidates(first_path: Path, second_path: Path, target_ra: float = 133.79513, target_dec: float = -7.24515) -> dict:
    """Return no ranked detections until independent, quality-controlled measurements support them."""
    return {
        "status": "inconclusive",
        "target": "WISE 0855",
        "total_candidates": 0,
        "classification_counts": {"Likely moving source": 0, "Possible motion": 0, "Known matched object": 0, "Artifact / Flagged": 0},
        "candidates": [],
        "scientific_guideline": "No candidate is ranked or classified from predicted WCS displacement, fixed scores, synthetic residuals, or unverified catalog matches. Use the Phase 5 validation report for measured evidence.",
    }
