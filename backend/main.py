
from pathlib import Path
import io
from typing import Optional, List, Dict

import numpy as np
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from astropy.io import fits
from astropy.wcs import WCS
from astropy.coordinates import SkyCoord
import astropy.units as u

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from image_processing import (
    load_fits_image,
    align_observations,
    detect_sources,
    compare_observations,
)

from motion_detection import get_motion_results
from band_explorer import (
    get_band_explorer_summary,
    extract_spectrum_at_source,
    generate_spectral_plot,
    ALL_102_CHANNELS,
)
from catalog_overlay import (
    query_external_catalogs,
    generate_catalog_overlay_image,
)
from candidate_ranking import (
    rank_and_classify_candidates,
    extract_candidate_evidence_image,
)
from validation.engine import validate_all_targets, validate_target
from validation.observation_discovery import discover_observations
from validation.plots import plot as validation_plot, difference_plot
from validation.target_registry import get_target as get_validation_target, list_targets as list_validation_targets
import json


# ==================================================
# PROJECT CONFIGURATION
# ==================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

OBSERVATIONS = {
    "first": DATA_DIR / "wise0855_first_cutout.fits",
    "second": DATA_DIR / "wise0855_second_cutout.fits",
}

TARGET_RA = 133.79513
TARGET_DEC = -7.24515

app = FastAPI(
    title="SPHEREx WISE 0855 Explorer",
    description="Astronomical image exploration and analysis API",
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================================================
# HELPER FUNCTIONS
# ==================================================

def get_file(observation_id: str) -> Path:

    if observation_id not in OBSERVATIONS:
        raise HTTPException(
            status_code=404,
            detail="Observation not found"
        )

    file_path = OBSERVATIONS[observation_id]

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="FITS file not found"
        )

    return file_path


def image_png(
    image,
    title="SPHEREx Image",
    marker=None,
    symmetric=False
):

    image = np.asarray(image, dtype=float)
    valid = image[np.isfinite(image)]

    if valid.size == 0:
        raise HTTPException(
            status_code=422,
            detail="No valid image pixels"
        )

    fig, ax = plt.subplots(figsize=(7, 7))

    if symmetric:

        limit = float(np.nanpercentile(np.abs(valid), 99))

        if not np.isfinite(limit) or limit <= 0:
            limit = 1e-8

        vmin = -limit
        vmax = limit
        cmap = "RdBu_r"

    else:

        vmin, vmax = np.nanpercentile(valid, [1, 99])

        if vmin == vmax:
            vmax = vmin + 1e-8

        cmap = "inferno"

    ax.imshow(
        image,
        origin="lower",
        cmap=cmap,
        vmin=vmin,
        vmax=vmax,
        interpolation="nearest",
    )

    if marker is not None:

        x, y = marker

        ax.scatter(
            [x],
            [y],
            marker="+",
            s=150,
            linewidths=2,
            color="cyan",
        )

        ax.set_title(f"{title} — searched position")

    else:
        ax.set_title(title)

    ax.set_xlabel("Pixel X")
    ax.set_ylabel("Pixel Y")

    buffer = io.BytesIO()

    fig.savefig(
        buffer,
        format="png",
        bbox_inches="tight",
        dpi=120
    )

    plt.close(fig)
    buffer.seek(0)

    return buffer


def observation_metadata(observation_id, file_path):

    with fits.open(file_path) as hdul:

        image_hdu = hdul["IMAGE"]
        header = image_hdu.header
        image = image_hdu.data

        return {
            "id": observation_id,
            "filename": file_path.name,
            "date": header.get("DATE-OBS"),
            "mjd": header.get(
                "MJD-AVG",
                header.get("MJD-OBS")
            ),
            "image_shape": list(image.shape),
            "unit": header.get("BUNIT"),
            "available": True,
        }


def get_comparison_result():

    try:

        return compare_observations(
            OBSERVATIONS["first"],
            OBSERVATIONS["second"],
        )

    except Exception as exc:

        raise HTTPException(
            status_code=422,
            detail=str(exc)
        )


# ==================================================
# BASIC API
# ==================================================

@app.get("/")
def home():

    return {
        "message": "SPHEREx Explorer Backend is running",
        "target": "WISE 0855",
        "status": "online",
        "version": "3.0.0",
    }


@app.get("/api/health")
def health():

    return {
        "status": "healthy",
        "available_observations": sum(
            path.exists()
            for path in OBSERVATIONS.values()
        ),
    }


# ==================================================
# OBSERVATIONS
# ==================================================

@app.get("/api/observations")
def get_observations():

    results = []

    for observation_id, file_path in OBSERVATIONS.items():

        if file_path.exists():

            results.append(
                observation_metadata(
                    observation_id,
                    file_path
                )
            )

    results.sort(
        key=lambda item: item["mjd"] or 0
    )

    return {
        "target": "WISE 0855",
        "total_observations": len(results),
        "observations": results,
    }


@app.get("/api/observations/{observation_id}")
def get_observation(observation_id: str):

    file_path = get_file(observation_id)

    with fits.open(file_path) as hdul:

        result = observation_metadata(
            observation_id,
            file_path
        )

        result["extensions"] = [
            hdu.name for hdu in hdul
        ]

    return result


# ==================================================
# IMAGE VIEWER
# ==================================================

@app.get("/api/observations/{observation_id}/image")
def get_observation_image(observation_id: str):

    file_path = get_file(observation_id)

    image, _, _ = load_fits_image(file_path)

    return StreamingResponse(
        image_png(
            image,
            f"WISE 0855 — {observation_id}"
        ),
        media_type="image/png",
    )


# ==================================================
# COORDINATE SEARCH
# ==================================================

@app.get("/api/search")
def search_coordinates(

    ra: float = Query(..., ge=0, lt=360),
    dec: float = Query(..., ge=-90, le=90),

):

    target = SkyCoord(
        ra=ra * u.deg,
        dec=dec * u.deg
    )

    matches = []

    for observation_id, file_path in OBSERVATIONS.items():

        if not file_path.exists():
            continue

        image, wcs, _ = load_fits_image(file_path)

        x, y = wcs.world_to_pixel(target)

        height, width = image.shape

        inside = (
            np.isfinite(x)
            and np.isfinite(y)
            and 0 <= x < width
            and 0 <= y < height
        )

        metadata = observation_metadata(
            observation_id,
            file_path
        )

        matches.append({

            **metadata,

            "inside_image": bool(inside),

            "pixel_x": float(x) if np.isfinite(x) else None,

            "pixel_y": float(y) if np.isfinite(y) else None,

            "image_url": (
                f"/api/search/image/{observation_id}"
                f"?ra={ra}&dec={dec}"
                if inside else None
            ),

        })

    return {

        "searched_coordinates": {
            "ra": ra,
            "dec": dec,
        },

        "search_scope": (
            "Currently downloaded local FITS cutouts only"
        ),

        "matches": matches,

        "message": (
            "Search completed. At least one local image covers this position."
            if any(item["inside_image"] for item in matches)
            else "No downloaded image covers these coordinates."
        ),

    }


@app.get("/api/search/image/{observation_id}")
def get_searched_image(

    observation_id: str,

    ra: float = Query(..., ge=0, lt=360),

    dec: float = Query(..., ge=-90, le=90),

):

    file_path = get_file(observation_id)

    image, wcs, _ = load_fits_image(file_path)

    target = SkyCoord(
        ra=ra * u.deg,
        dec=dec * u.deg
    )

    x, y = wcs.world_to_pixel(target)

    height, width = image.shape

    inside = (
        np.isfinite(x)
        and np.isfinite(y)
        and 0 <= x < width
        and 0 <= y < height
    )

    if not inside:

        raise HTTPException(
            status_code=404,
            detail="Coordinates are outside this image",
        )

    return StreamingResponse(
        image_png(
            image,
            observation_id,
            (x, y)
        ),
        media_type="image/png",
    )


# ==================================================
# TIME-LAPSE
# ==================================================

@app.get("/api/timelapse")
def get_timelapse():

    frames = []

    for observation_id, file_path in OBSERVATIONS.items():

        if file_path.exists():

            metadata = observation_metadata(
                observation_id,
                file_path
            )

            metadata["image_url"] = (
                f"/api/observations/{observation_id}/image"
            )

            frames.append(metadata)

    frames.sort(
        key=lambda item: item["mjd"] or 0
    )

    return {

        "target": "WISE 0855",

        "frame_count": len(frames),

        "frames": frames,

        "note": (
            "Only downloaded FITS observations are included. "
            "This is not yet the complete 27-date archive sequence."
        ),

    }


# ==================================================
# SOURCE DETECTION
# ==================================================

@app.get("/api/analysis/detection/{observation_id}")
def analyze_detection(observation_id: str):

    file_path = get_file(observation_id)

    image, _, _ = load_fits_image(file_path)

    try:

        result = detect_sources(image)

    except Exception as exc:

        raise HTTPException(
            status_code=422,
            detail=str(exc)
        )

    return {

        "observation_id": observation_id,

        "method": "Photutils DAOStarFinder",

        "result": result,

        "scientific_note": (
            "Detections are candidates and are not automatically "
            "confirmed astronomical identifications."
        ),

    }


# ==================================================
# IMAGE ALIGNMENT
# ==================================================

@app.get("/api/analysis/alignment")
def analyze_alignment():

    try:

        result = align_observations(
            OBSERVATIONS["first"],
            OBSERVATIONS["second"],
        )

    except Exception as exc:

        raise HTTPException(
            status_code=422,
            detail=str(exc)
        )

    return {

        "status": "alignment completed",

        "image_shape": list(result["image_shape"]),

        "valid_pixels": result["valid_pixel_count"],

        "total_pixels": result["total_pixel_count"],

        "overlap_percentage": round(
            100
            * result["valid_pixel_count"]
            / result["total_pixel_count"],
            2
        ),

        "unit": result["first_unit"],

        "note": (
            "Pixel overlap is not by itself proof of astrometric accuracy."
        ),

    }


# ==================================================
# IMAGE COMPARISON API
# ==================================================

@app.get("/api/analysis/comparison")
def get_image_comparison():

    result = get_comparison_result()

    return {

        "status": "comparison completed",

        "valid_pixels": result["valid_pixel_count"],

        "total_pixels": result["total_pixel_count"],

        "overlap_percentage": round(
            result["overlap_percentage"],
            2
        ),

        "unit": result["unit"],

        "first_observation": {

            "background": result["first_background"],

            "source_candidates": (
                result["first_sources"]["number_of_sources"]
            ),

            "noise": result["first_sources"]["noise"],

        },

        "second_observation": {

            "background": result["second_background"],

            "source_candidates": (
                result["second_sources"]["number_of_sources"]
            ),

            "noise": result["second_sources"]["noise"],

        },

        "background_offset": result["background_offset"],

        "difference_median": result["difference_median"],

        "difference_std": result["difference_std"],

        "scientific_note": (
            "Preliminary comparison. Source candidates are not "
            "confirmed identifications. PSF matching, astrometric "
            "correction and full uncertainty propagation are still needed."
        ),

    }


# ==================================================
# PRELIMINARY DIFFERENCE IMAGE DATA
# ==================================================

@app.get("/api/analysis/difference")
def get_difference():

    result = get_comparison_result()

    return {

        "status": "preliminary difference generated",

        "background_offset": result["background_offset"],

        "median_difference": result["difference_median"],

        "standard_deviation": result["difference_std"],

        "valid_pixels": result["valid_pixel_count"],

        "image_shape": list(
            result["difference_image"].shape
        ),

        "unit": result["unit"],

        "note": (
            "Preliminary difference only. PSF matching, "
            "photometric calibration and uncertainty propagation "
            "are not yet applied. Do not interpret this as confirmed variability."
        ),

    }


# ==================================================
# PRELIMINARY DIFFERENCE IMAGE PNG
# ==================================================

@app.get("/api/analysis/difference/image")
def get_difference_image():

    result = get_comparison_result()

    return StreamingResponse(
        image_png(
            result["difference_image"],
            "Preliminary Image Difference",
            symmetric=True,
        ),
        media_type="image/png",
    )


# ==================================================
# ALIGNED IMAGE PNG
# ==================================================

@app.get("/api/analysis/alignment/image")
def get_aligned_image():

    result = get_comparison_result()

    return StreamingResponse(
        image_png(
            result["aligned_first"],
            "First Observation — Reprojected"
        ),
        media_type="image/png",
    )


# ==================================================
# ROOT TARGET INFORMATION
# ==================================================

@app.get("/api/target")
def get_target():

    return {

        "name": "WISE 0855",

        "reference_ra": TARGET_RA,

        "reference_dec": TARGET_DEC,

        "coordinate_note": (
            "These are the project's current reference coordinates. "
            "They have not yet been propagated to each observation epoch."
        ),

    }


# ==================================================
# MOTION DETECTION API
# ==================================================

@app.get("/api/analysis/motion")
def analyze_motion():

    try:

        return get_motion_results()

    except Exception as exc:

        raise HTTPException(
            status_code=422,
            detail=str(exc)
        )

@app.get("/api/timeline")
def get_timeline():
    import pandas as pd

    file_path = BASE_DIR / "wise0855_timeline_summary.csv"

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Timeline CSV not found"
        )

    df = pd.read_csv(file_path)
    df = df.fillna(0)

    return {
        "status": "success",
        "total_dates": int(df["date"].nunique()),
        "total_bands": int(df["energy_bandpassname"].nunique()),
        "total_groups": len(df),
        "timeline": df.to_dict(orient="records")
    }


# ==================================================
# PHASE 4: SCIENTIFIC INTELLIGENCE ENDPOINTS
# ==================================================

# --------------------------------------------------
# A. 102-Band Explorer
# --------------------------------------------------

@app.get("/api/bands/summary")
def get_bands_summary():
    """Returns overview of SPHEREx 6 detector bands and the 102 spectroscopic channels."""
    return get_band_explorer_summary()


@app.get("/api/bands/channels")
def get_bands_channels():
    """Returns the complete list of 102 channels with center wavelengths and bandwidths."""
    return {"total_channels": len(ALL_102_CHANNELS), "channels": ALL_102_CHANNELS}


@app.get("/api/bands/extract")
def extract_spectral_point(
    observation_id: str = Query("first", description="Observation ID (first or second)"),
    pixel_x: float = Query(28.22, description="Pixel X in cutout"),
    pixel_y: float = Query(28.74, description="Pixel Y in cutout"),
    radius: float = Query(2.0, description="Aperture radius in pixels"),
):
    """
    Extracts local in-situ wavelength, bandwidth, and aperture flux density
    from the FITS WCS-WAVE calibration table and local aperture photometry.
    """
    file_path = get_file(observation_id)
    try:
        return extract_spectrum_at_source(file_path, pixel_x, pixel_y, aperture_radius=radius)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@app.get("/api/bands/spectral-plot")
def get_spectral_plot(
    channel_id: Optional[int] = Query(None, description="Highlight specific SPHEREx channel (1-102)"),
    observation_id: str = Query("first", description="Observation ID"),
    pixel_x: Optional[float] = Query(None, description="Optional Pixel X for measured point"),
    pixel_y: Optional[float] = Query(None, description="Optional Pixel Y for measured point"),
):
    """Generates publication-quality 102-band SED chart as PNG."""
    file_path = get_file(observation_id)
    extracted_data = None
    if pixel_x is not None and pixel_y is not None:
        try:
            extracted_data = extract_spectrum_at_source(file_path, pixel_x, pixel_y)
        except Exception:
            pass

    buf = generate_spectral_plot(selected_channel_id=channel_id, extracted_data=extracted_data)
    return StreamingResponse(buf, media_type="image/png")


# --------------------------------------------------
# B. External Catalog Overlay (Cone Search)
# --------------------------------------------------

@app.get("/api/catalogs/overlay")
def get_catalogs_overlay(
    ra: float = Query(TARGET_RA, description="Target Right Ascension (deg)"),
    dec: float = Query(TARGET_DEC, description="Target Declination (deg)"),
    radius_arcmin: float = Query(2.0, description="Cone search search radius in arcminutes"),
    observation_id: str = Query("first", description="Reference observation for pixel projection"),
):
    """
    Cone search querying Gaia DR3, AllWISE, and CatWISE catalogs around coordinates via IRSA.
    Projects sources into FITS cutout pixel space.
    """
    file_path = get_file(observation_id)
    try:
        return query_external_catalogs(ra, dec, radius_arcmin=radius_arcmin, reference_fits_path=file_path)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@app.get("/api/catalogs/overlay-image/{observation_id}")
def get_catalog_overlay_image(
    observation_id: str,
    ra: float = Query(TARGET_RA, description="Target RA (deg)"),
    dec: float = Query(TARGET_DEC, description="Target Dec (deg)"),
    show_gaia: bool = Query(True, description="Show Gaia DR3 stars"),
    show_wise: bool = Query(True, description="Show AllWISE sources"),
    show_catwise: bool = Query(True, description="Show CatWISE sources"),
):
    """Renders FITS image with Gaia diamonds, WISE squares, and target reticle overlay as PNG."""
    file_path = get_file(observation_id)
    try:
        cat_data = query_external_catalogs(ra, dec, radius_arcmin=2.0, reference_fits_path=file_path)
        buf = generate_catalog_overlay_image(
            file_path,
            cat_data,
            show_gaia=show_gaia,
            show_wise=show_wise,
            show_catwise=show_catwise,
            target_ra=ra,
            target_dec=dec,
        )
        return StreamingResponse(buf, media_type="image/png")
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))


# --------------------------------------------------
# C. Candidate Ranking System
# --------------------------------------------------

@app.get("/api/candidates/rank")
def get_candidate_rankings(
    target_ra: float = Query(TARGET_RA, description="Target RA (deg)"),
    target_dec: float = Query(TARGET_DEC, description="Target Dec (deg)"),
):
    """
    Ranks candidate sources with motion estimation, SNR, quality flags, catalog cross-matches,
    and rigorous scientific classification:
    - 'Likely moving source'
    - 'Possible motion'
    - 'Known matched object'
    - 'Artifact / Flagged'
    """
    f1 = get_file("first")
    f2 = get_file("second")
    try:
        return rank_and_classify_candidates(f1, f2, target_ra=target_ra, target_dec=target_dec)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@app.get("/api/candidates/{candidate_id}/evidence")
def get_candidate_evidence(
    candidate_id: str,
    target_ra: float = Query(TARGET_RA, description="Target RA (deg)"),
    target_dec: float = Query(TARGET_DEC, description="Target Dec (deg)"),
):
    """Renders a 3-panel evidence strip [Epoch 1 Zoom | Epoch 2 Zoom | Difference Zoom] as PNG."""
    f1 = get_file("first")
    f2 = get_file("second")
    ranking_data = rank_and_classify_candidates(f1, f2, target_ra=target_ra, target_dec=target_dec)
    cand = next((c for c in ranking_data["candidates"] if c["id"] == candidate_id), None)
    if not cand:
        raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} not found")

    px1 = cand["position"]["epoch_1"]["pixel_x"]
    py1 = cand["position"]["epoch_1"]["pixel_y"]
    px2 = cand["position"]["epoch_2"]["pixel_x"]
    py2 = cand["position"]["epoch_2"]["pixel_y"]

    buf = extract_candidate_evidence_image(f1, f2, px1, py1, px2, py2)
    return StreamingResponse(buf, media_type="image/png")


# Phase 5 scientific validation API
VALIDATION_DIR = DATA_DIR / "validation_cache"

def _validation_target_or_404(target_id):
    try:
        return get_validation_target(target_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

def _validation_report(target_id, compute=False):
    target = _validation_target_or_404(target_id)
    path = VALIDATION_DIR / f"{target['id']}_report.json"
    if path.exists():
        try: return json.loads(path.read_text(encoding="utf-8"))
        except Exception: pass
    if not compute: raise HTTPException(status_code=404, detail="No validation result; run POST /api/validation/run/{target_id} first.")
    report = validate_target(target["id"], live_archive_query=False, use_discovery_cache=True)
    VALIDATION_DIR.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(report,indent=2,default=str),encoding="utf-8")
    return report

@app.get("/api/validation/targets")
def validation_targets():
    targets=list_validation_targets()
    for target in targets:
        path=VALIDATION_DIR/f"{target['id']}_report.json"
        target["validation_status"]=json.loads(path.read_text()).get("validation_status","NOT_RUN") if path.exists() else "NOT_RUN"
    return {"status":"success","count":len(targets),"targets":targets}

@app.get("/api/validation/targets/{target_id}")
def validation_target_detail(target_id:str):
    target=_validation_target_or_404(target_id)
    return {"target":target,"latest_result":_validation_report(target_id) if (VALIDATION_DIR/f"{target['id']}_report.json").exists() else None}

@app.post("/api/validation/run/{target_id}")
def run_validation(target_id:str,live_archive_query:bool=Query(True),use_discovery_cache:bool=Query(True)):
    target=_validation_target_or_404(target_id)
    try:
        result=validate_target(target["id"],live_archive_query,use_discovery_cache)
        VALIDATION_DIR.mkdir(parents=True,exist_ok=True); (VALIDATION_DIR/f"{target['id']}_report.json").write_text(json.dumps(result,indent=2,default=str),encoding="utf-8")
        return result
    except Exception as exc: raise HTTPException(status_code=422,detail=f"Validation failed: {type(exc).__name__}: {exc}") from exc

@app.get("/api/validation/results/{target_id}")
def validation_results(target_id:str): return _validation_report(target_id)

@app.get("/api/validation/lightcurve/{target_id}")
def validation_lightcurve(target_id:str,format:str=Query("json")):
    report=_validation_report(target_id,compute=True)
    if format=="png": return StreamingResponse(validation_plot(report,"photometry"),media_type="image/png")
    points=[]
    for e in report["epochs"]:
        p=e.get("photometry") or {}
        if p.get("status")=="measured": points.append({"observation_id":e.get("observation_id"),"date":e.get("date"),"mjd":e.get("mjd"),"band":e.get("band"),"snr":p.get("snr"),"flux_jy":p.get("flux_jy"),"uncertainty_jy":p.get("flux_error_jy"),"quality_flags":p.get("quality_flags")})
    return {"target_id":report["target"]["id"],"validation_status":report["validation_status"],"points":points,"variability_test":report["photometric_test"],"plot_url":f"/api/validation/lightcurve/{target_id}?format=png"}

@app.get("/api/validation/motion/{target_id}")
def validation_motion(target_id:str):
    r=_validation_report(target_id,compute=True)
    return {"target_id":r["target"]["id"],"validation_status":r["validation_status"],"reference_astrometry":r["target"]["reference"],"epochs":r["epochs"],"comparison":r["epoch_comparison"],"note":"Predictions and measured centroids are separate fields; only centroids passing SNR 5 are measured positions."}

@app.get("/api/validation/evidence/{target_id}")
def validation_evidence(target_id:str):
    r=_validation_report(target_id,compute=True)
    return {"target_id":r["target"]["id"],"validation_status":r["validation_status"],"local_fits":r["local_fits"],"data_quality":r["data_quality"],"epochs":r["epochs"],"image_comparison":r["image_comparison"],"archive_discovery":r["archive_discovery"],"astrometry_plot_url":f"/api/validation/astrometry/{target_id}/plot","photometry_plot_url":f"/api/validation/photometry/{target_id}/plot","difference_image_url":f"/api/validation/difference/{target_id}","limitations":r["limitations"]}

@app.get("/api/validation/image/{target_id}/{observation_id}")
def validation_image(target_id:str,observation_id:str):
    r=_validation_report(target_id,compute=True)
    local=next((x for x in r["local_fits"] if x["observation_id"]==observation_id and x["exists"]),None)
    if not local: raise HTTPException(status_code=404,detail="No local FITS image for this target epoch.")
    image,_,_=load_fits_image(Path(local["path"]))
    epoch=next((x for x in r["epochs"] if x.get("observation")==observation_id),{})
    pred=epoch.get("predicted") or {}; marker=(pred.get("pixel_x"),pred.get("pixel_y")) if pred.get("inside_image") else None
    return StreamingResponse(image_png(image,f"{r['target']['name']} {epoch.get('date','')} (prediction marker)",marker),media_type="image/png")

@app.get("/api/validation/astrometry/{target_id}/plot")
def validation_astrometry_plot(target_id:str): return StreamingResponse(validation_plot(_validation_report(target_id,True),"astrometry"),media_type="image/png")

@app.get("/api/validation/photometry/{target_id}/plot")
def validation_photometry_plot(target_id:str): return StreamingResponse(validation_plot(_validation_report(target_id,True),"photometry"),media_type="image/png")

@app.get("/api/validation/difference/{target_id}")
def validation_difference(target_id:str):
    r=_validation_report(target_id,compute=True)
    if r["image_comparison"].get("status")!="wcs_aligned": raise HTTPException(status_code=404,detail="No compatible WCS-aligned difference image is available.")
    files=[x for x in r["local_fits"] if x.get("exists")]
    if len(files)<2: raise HTTPException(status_code=404,detail="Two local FITS epochs are required.")
    try: return StreamingResponse(difference_plot(files[0]["path"],files[-1]["path"]),media_type="image/png")
    except Exception as exc: raise HTTPException(status_code=422,detail=f"Difference image failed: {exc}") from exc

@app.get("/api/validation/discover/{target_id}")
def validation_discover(target_id:str,live_query:bool=Query(True),use_cache:bool=Query(True)):
    target=_validation_target_or_404(target_id); return discover_observations(target["id"],live_query=live_query,use_cache=use_cache)

@app.get("/api/validation/run-all")
def validation_run_all(live_query:bool=Query(False),use_cache:bool=Query(True)):
    results=validate_all_targets(live_query,use_cache)
    for r in results["results"]:
        VALIDATION_DIR.mkdir(parents=True,exist_ok=True); (VALIDATION_DIR/f"{r['target']['id']}_report.json").write_text(json.dumps(r,indent=2,default=str),encoding="utf-8")
    return results

