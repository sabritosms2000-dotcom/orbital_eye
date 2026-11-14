import io
import json
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
from astroquery.ipac.irsa import Irsa

BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_FILE = BASE_DIR / "data" / "catalog_cache.json"

# Default coordinates for WISE 0855
DEFAULT_RA = 133.79513
DEFAULT_DEC = -7.24515

def safe_float(val, ndigits: int = 2) -> Optional[float]:
    """Safely converts potential masked/None/NaN value to float."""
    if val is None or np.ma.is_masked(val):
        return None
    try:
        f = float(val)
        return round(f, ndigits) if np.isfinite(f) else None
    except Exception:
        return None

def get_reference_wcs(file_path: Path) -> WCS:
    """Loads celestial WCS from FITS image header."""
    with fits.open(file_path) as hdul:
        return WCS(hdul["IMAGE"].header).celestial

def load_cache() -> dict:
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_cache(cache_data: dict):
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(cache_data, f, indent=2)
    except Exception as e:
        print("Warning: could not write catalog cache:", e)

def query_external_catalogs(
    ra: float = DEFAULT_RA,
    dec: float = DEFAULT_DEC,
    radius_arcmin: float = 2.0,
    reference_fits_path: Optional[Path] = None,
) -> dict:
    """
    Performs an astronomical Cone Search across Gaia DR3, AllWISE, and CatWISE catalogs via IRSA.
    Projects celestial coordinates into FITS pixel space using the reference WCS.
    """
    if reference_fits_path is None or not reference_fits_path.exists():
        reference_fits_path = BASE_DIR / "data" / "wise0855_first_cutout.fits"

    ref_wcs = get_reference_wcs(reference_fits_path)
    with fits.open(reference_fits_path) as hdul:
        img_shape = hdul["IMAGE"].data.shape  # (height, width) e.g. (59, 58)

    cache_key = f"{ra:.5f}_{dec:.5f}_{radius_arcmin:.1f}"
    cache = load_cache()

    center_coord = SkyCoord(ra=ra * u.deg, dec=dec * u.deg, frame="icrs")
    results = {
        "query": {
            "center_ra": ra,
            "center_dec": dec,
            "radius_arcmin": radius_arcmin,
            "target": "WISE 0855",
        },
        "gaia_dr3": [],
        "allwise": [],
        "catwise2020": [],
        "total_sources": 0,
        "inside_cutout_count": 0,
    }

    # If cached, load from cache
    if cache_key in cache:
        cached_res = cache[cache_key]
        results["gaia_dr3"] = cached_res.get("gaia_dr3", [])
        results["allwise"] = cached_res.get("allwise", [])
        results["catwise2020"] = cached_res.get("catwise2020", [])
    else:
        # 1. Gaia DR3 Query
        try:
            tbl_gaia = Irsa.query_region(center_coord, catalog="gaia_dr3_source", radius=radius_arcmin * u.arcmin)
            for row in tbl_gaia:
                s_ra = float(row["ra"])
                s_dec = float(row["dec"])
                s_coord = SkyCoord(ra=s_ra * u.deg, dec=s_dec * u.deg, frame="icrs")
                sep_arcsec = float(center_coord.separation(s_coord).arcsec)

                # Project to pixel
                px, py = ref_wcs.world_to_pixel(s_coord)
                inside = bool(0 <= px < img_shape[1] and 0 <= py < img_shape[0])

                pmra = safe_float(row["pmra"]) if "pmra" in row.colnames else None
                pmdec = safe_float(row["pmdec"]) if "pmdec" in row.colnames else None
                total_pm = round(float(np.sqrt(pmra**2 + pmdec**2)), 2) if pmra is not None and pmdec is not None else None

                results["gaia_dr3"].append({
                    "id": str(row.get("source_id", "")),
                    "ra": round(s_ra, 6),
                    "dec": round(s_dec, 6),
                    "separation_arcsec": round(sep_arcsec, 2),
                    "pixel_x": round(float(px), 2),
                    "pixel_y": round(float(py), 2),
                    "inside_cutout": inside,
                    "g_mag": safe_float(row.get("phot_g_mean_mag")),
                    "pm_ra_mas_yr": pmra,
                    "pm_dec_mas_yr": pmdec,
                    "total_pm_mas_yr": total_pm,
                    "parallax_mas": safe_float(row.get("parallax")),
                })
        except Exception as e:
            print("Notice: Gaia cone query encountered:", e)

        # 2. AllWISE Query
        try:
            tbl_wise = Irsa.query_region(center_coord, catalog="allwise_p3as_psd", radius=radius_arcmin * u.arcmin)
            for row in tbl_wise:
                s_ra = float(row["ra"])
                s_dec = float(row["dec"])
                s_coord = SkyCoord(ra=s_ra * u.deg, dec=s_dec * u.deg, frame="icrs")
                sep_arcsec = float(center_coord.separation(s_coord).arcsec)

                px, py = ref_wcs.world_to_pixel(s_coord)
                inside = bool(0 <= px < img_shape[1] and 0 <= py < img_shape[0])

                results["allwise"].append({
                    "id": str(row.get("designation", "")),
                    "ra": round(s_ra, 6),
                    "dec": round(s_dec, 6),
                    "separation_arcsec": round(sep_arcsec, 2),
                    "pixel_x": round(float(px), 2),
                    "pixel_y": round(float(py), 2),
                    "inside_cutout": inside,
                    "w1_mag": safe_float(row.get("w1mpro")),
                    "w2_mag": safe_float(row.get("w2mpro")),
                    "w3_mag": safe_float(row.get("w3mpro")),
                    "w4_mag": safe_float(row.get("w4mpro")),
                })
        except Exception as e:
            print("Notice: AllWISE cone query encountered:", e)

        # 3. CatWISE 2020 Query
        try:
            tbl_cat = Irsa.query_region(center_coord, catalog="catwise_2020", radius=radius_arcmin * u.arcmin)
            for row in tbl_cat:
                s_ra = float(row["ra"])
                s_dec = float(row["dec"])
                s_coord = SkyCoord(ra=s_ra * u.deg, dec=s_dec * u.deg, frame="icrs")
                sep_arcsec = float(center_coord.separation(s_coord).arcsec)

                px, py = ref_wcs.world_to_pixel(s_coord)
                inside = bool(0 <= px < img_shape[1] and 0 <= py < img_shape[0])

                pmra = safe_float(row["pmra"]) if "pmra" in row.colnames else None
                pmdec = safe_float(row["pmdec"]) if "pmdec" in row.colnames else None

                results["catwise2020"].append({
                    "id": str(row.get("source_name", row.get("source_id", ""))),
                    "ra": round(s_ra, 6),
                    "dec": round(s_dec, 6),
                    "separation_arcsec": round(sep_arcsec, 2),
                    "pixel_x": round(float(px), 2),
                    "pixel_y": round(float(py), 2),
                    "inside_cutout": inside,
                    "w1_mag": safe_float(row.get("w1mpro")),
                    "w2_mag": safe_float(row.get("w2mpro")),
                    "pm_ra_mas_yr": pmra,
                    "pm_dec_mas_yr": pmdec,
                })
        except Exception as e:
            print("Notice: CatWISE query encountered:", e)

        # Update cache
        cache[cache_key] = {
            "gaia_dr3": results["gaia_dr3"],
            "allwise": results["allwise"],
            "catwise2020": results["catwise2020"],
        }
        save_cache(cache)

    # Sort each list by angular separation from query center
    for cat_key in ["gaia_dr3", "allwise", "catwise2020"]:
        results[cat_key].sort(key=lambda s: s["separation_arcsec"])

    all_sources = results["gaia_dr3"] + results["allwise"] + results["catwise2020"]
    results["total_sources"] = len(all_sources)
    results["inside_cutout_count"] = sum(1 for s in all_sources if s["inside_cutout"])

    return results


def generate_catalog_overlay_image(
    file_path: Path,
    catalog_results: dict,
    show_gaia: bool = True,
    show_wise: bool = True,
    show_catwise: bool = True,
    target_ra: float = DEFAULT_RA,
    target_dec: float = DEFAULT_DEC,
) -> io.BytesIO:
    """Renders FITS image with Gaia diamonds, WISE squares, and target reticle overlay."""
    with fits.open(file_path) as hdul:
        image = np.array(hdul["IMAGE"].data, dtype=float)
        wcs = WCS(hdul["IMAGE"].header).celestial

    fig, ax = plt.subplots(figsize=(7, 7), dpi=140)
    fig.patch.set_facecolor("#07090e")
    ax.set_facecolor("#000000")

    valid = image[np.isfinite(image)]
    vmin, vmax = np.percentile(valid, [2, 98])
    im = ax.imshow(image, origin="lower", cmap="inferno", vmin=vmin, vmax=vmax)

    # 1. Overlay Gaia DR3 stars
    if show_gaia:
        gaia_sources = [s for s in catalog_results.get("gaia_dr3", []) if s["inside_cutout"]]
        for s in gaia_sources:
            px, py = s["pixel_x"], s["pixel_y"]
            ax.plot(px, py, marker="d", markersize=8, color="#38bdf8", markeredgecolor="#ffffff", markeredgewidth=1.2, fillstyle="none")
            if s.get("g_mag"):
                ax.text(px + 1.2, py + 1.2, f"G={s['g_mag']}", color="#38bdf8", fontsize=7, fontweight="bold")
            # Draw vector if proper motion is significant
            if s.get("pm_ra_mas_yr") and s.get("pm_dec_mas_yr"):
                # Scale: 10 mas/yr = 0.5 pixels
                dx = (s["pm_ra_mas_yr"] / 20.0)
                dy = (s["pm_dec_mas_yr"] / 20.0)
                ax.arrow(px, py, dx, dy, color="#38bdf8", width=0.15, head_width=0.6, alpha=0.8)

    # 2. Overlay AllWISE sources
    if show_wise:
        wise_sources = [s for s in catalog_results.get("allwise", []) if s["inside_cutout"]]
        for s in wise_sources:
            px, py = s["pixel_x"], s["pixel_y"]
            ax.plot(px, py, marker="s", markersize=9, color="#fbbf24", markeredgecolor="#ffffff", markeredgewidth=1.2, fillstyle="none")
            if s.get("w1_mag"):
                ax.text(px + 1.2, py - 2.0, f"W1={s['w1_mag']}", color="#fbbf24", fontsize=7)

    # 3. Target Position Reticle
    tgt_coord = SkyCoord(ra=target_ra * u.deg, dec=target_dec * u.deg, frame="icrs")
    tx, ty = wcs.world_to_pixel(tgt_coord)
    if 0 <= tx < image.shape[1] and 0 <= ty < image.shape[0]:
        ax.plot(tx, ty, marker="+", markersize=16, markeredgewidth=2.2, color="#f43f5e")
        circ = plt.Circle((tx, ty), radius=3.0, fill=False, color="#f43f5e", linestyle="--", linewidth=1.5)
        ax.add_patch(circ)
        ax.text(tx - 6, ty + 4.5, "WISE 0855 Target", color="#f43f5e", fontsize=8, fontweight="bold", backgroundcolor="#07090ecc")

    # Legend & styling
    custom_lines = []
    custom_labels = []
    if show_gaia:
        custom_lines.append(plt.Line2D([0], [0], marker="d", color="#38bdf8", linestyle="", markersize=7))
        custom_labels.append("Gaia DR3 (Star)")
    if show_wise:
        custom_lines.append(plt.Line2D([0], [0], marker="s", color="#fbbf24", linestyle="", markersize=7))
        custom_labels.append("AllWISE (IR Source)")
    custom_lines.append(plt.Line2D([0], [0], marker="+", color="#f43f5e", linestyle="", markersize=9, markeredgewidth=2))
    custom_labels.append("Target Reticle")

    ax.legend(custom_lines, custom_labels, loc="upper right", facecolor="#0b0f19", edgecolor="#334155", labelcolor="#f1f5f9", fontsize=8)

    ax.set_title("SPHEREx Cutout with External Catalog Overlay", color="#f8fafc", fontsize=10, pad=10)
    ax.set_xlabel("Pixel X (Dispersion Axis)", color="#94a3b8", fontsize=8)
    ax.set_ylabel("Pixel Y (Spatial Axis)", color="#94a3b8", fontsize=8)
    ax.tick_params(colors="#94a3b8", labelsize=8)
    for spine in ax.spines.values():
        spine.set_color("#334155")

    plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf
