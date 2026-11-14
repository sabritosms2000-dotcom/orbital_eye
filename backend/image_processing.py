
from pathlib import Path

import numpy as np

from astropy.io import fits
from astropy.stats import sigma_clipped_stats
from astropy.wcs import WCS

from reproject import reproject_interp

from photutils.background import (
    Background2D,
    MedianBackground,
    StdBackgroundRMS,
)

from photutils.detection import DAOStarFinder


# =========================================================
# 1. LOAD FITS IMAGE
# =========================================================

def load_fits_image(file_path):

    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"FITS file not found: {file_path}"
        )

    with fits.open(file_path) as hdul:

        image_hdu = hdul["IMAGE"]

        image = np.asarray(
            image_hdu.data,
            dtype=np.float64
        )

        header = image_hdu.header.copy()

    if image.ndim != 2:
        raise ValueError(
            "Expected a 2D astronomical image."
        )

    wcs = WCS(header).celestial

    if not wcs.has_celestial:
        raise ValueError(
            "The FITS image does not contain a valid celestial WCS."
        )

    return image, wcs, header


# =========================================================
# 2. ALIGN TWO OBSERVATIONS
# =========================================================

def align_observations(first_path, second_path):

    first_image, first_wcs, first_header = (
        load_fits_image(first_path)
    )

    second_image, second_wcs, second_header = (
        load_fits_image(second_path)
    )

    first_unit = first_header.get("BUNIT")
    second_unit = second_header.get("BUNIT")

    if not first_unit or not second_unit:
        raise ValueError(
            "Missing BUNIT information."
        )

    if first_unit != second_unit:
        raise ValueError(
            f"Image units differ: {first_unit} vs {second_unit}"
        )

    # Reproject first image onto second image WCS
    aligned_first, footprint = reproject_interp(
        (first_image, first_wcs),
        second_wcs,
        shape_out=second_image.shape,
        order="bilinear",
        return_footprint=True
    )

    valid_pixels = (
        np.isfinite(aligned_first)
        & np.isfinite(second_image)
        & np.isfinite(footprint)
        & (footprint > 0)
    )

    valid_count = int(np.count_nonzero(valid_pixels))

    if valid_count == 0:
        raise ValueError(
            "No overlapping valid pixels between observations."
        )

    return {
        "aligned_first": aligned_first,
        "second_image": second_image,
        "footprint": footprint,
        "valid_mask": valid_pixels,
        "reference_wcs": second_wcs,
        "image_shape": second_image.shape,
        "valid_pixel_count": valid_count,
        "total_pixel_count": int(valid_pixels.size),
        "first_unit": first_unit,
        "second_unit": second_unit,
    }


# =========================================================
# 3. BACKGROUND MATCHING
# =========================================================

def match_background(aligned_first, second_image, valid_mask):

    valid_values = (
        valid_mask
        & np.isfinite(aligned_first)
        & np.isfinite(second_image)
    )

    first_values = aligned_first[valid_values]
    second_values = second_image[valid_values]

    if len(first_values) < 20:
        raise ValueError(
            "Not enough overlapping pixels for background matching."
        )

    # Robust background estimates
    first_background = float(
        sigma_clipped_stats(first_values)[1]
    )

    second_background = float(
        sigma_clipped_stats(second_values)[1]
    )

    # Background difference between observations
    background_offset = (
        second_background - first_background
    )

    # Match first observation to second observation background
    matched_first = (
        aligned_first + background_offset
    )

    return {
        "matched_first": matched_first,
        "first_background": first_background,
        "second_background": second_background,
        "background_offset": float(background_offset),
    }


# =========================================================
# 4. CREATE DIFFERENCE IMAGE
# =========================================================

def create_difference_image(first_path, second_path):

    alignment = align_observations(
        first_path,
        second_path
    )

    aligned_first = alignment["aligned_first"]
    second_image = alignment["second_image"]
    valid_mask = alignment["valid_mask"]

    background_result = match_background(
        aligned_first,
        second_image,
        valid_mask
    )

    matched_first = background_result["matched_first"]

    # Difference: second observation minus first observation
    difference = np.full(
        second_image.shape,
        np.nan,
        dtype=float
    )

    difference[valid_mask] = (
        second_image[valid_mask]
        - matched_first[valid_mask]
    )

    difference_values = difference[valid_mask]

    difference_median = float(
        np.nanmedian(difference_values)
    )

    difference_std = float(
        np.nanstd(difference_values)
    )

    return {
        **alignment,
        **background_result,
        "difference_image": difference,
        "difference_median": difference_median,
        "difference_std": difference_std,
    }


# =========================================================
# 5. SOURCE DETECTION
# =========================================================

def detect_sources(image, valid_mask=None):

    image = np.asarray(image, dtype=float)

    if image.ndim != 2:
        raise ValueError(
            "Expected a 2D image."
        )

    mask = ~np.isfinite(image)

    if valid_mask is not None:

        valid_mask = np.asarray(
            valid_mask,
            dtype=bool
        )

        if valid_mask.shape != image.shape:
            raise ValueError(
                "Valid mask shape does not match image shape."
            )

        mask |= ~valid_mask

    if np.count_nonzero(~mask) < 20:
        raise ValueError(
            "Not enough valid pixels for source detection."
        )

    # Estimate background and noise
    background_estimator = MedianBackground()
    rms_estimator = StdBackgroundRMS()

    background = Background2D(
        image,
        box_size=(15, 15),
        filter_size=(3, 3),
        mask=mask,
        bkg_estimator=background_estimator,
        bkg_rms_estimator=rms_estimator,
        exclude_percentile=90,
    )

    background_subtracted = (
        image - background.background
    )

    noise_values = background.background_rms[~mask]

    noise = float(
        np.nanmedian(noise_values)
    )

    if not np.isfinite(noise) or noise <= 0:
        raise ValueError(
            "Could not estimate image noise."
        )

    # Detect sources
    finder = DAOStarFinder(
        fwhm=2.5,
        threshold=5.0 * noise,
    )

    sources = finder(
        background_subtracted,
        mask=mask,
    )

    if sources is None:

        return {
            "number_of_sources": 0,
            "background_level": float(
                np.nanmedian(
                    background.background[~mask]
                )
            ),
            "noise": noise,
            "sources": [],
        }

    results = []

    for source in sources:

        results.append({
            "x": float(source["x_centroid"]),
            "y": float(source["y_centroid"]),
            "flux": float(source["flux"]),
            "sharpness": float(source["sharpness"]),
            "roundness": float(source["roundness1"]),
        })

    return {
        "number_of_sources": len(results),
        "background_level": float(
            np.nanmedian(
                background.background[~mask]
            )
        ),
        "noise": noise,
        "sources": results,
    }


# =========================================================
# 6. COMPLETE IMAGE COMPARISON
# =========================================================

def compare_observations(first_path, second_path):

    result = create_difference_image(
        first_path,
        second_path
    )

    first_sources = detect_sources(
        result["aligned_first"],
        result["valid_mask"]
    )

    second_sources = detect_sources(
        result["second_image"],
        result["valid_mask"]
    )

    return {
        "valid_pixel_count": result["valid_pixel_count"],
        "total_pixel_count": result["total_pixel_count"],
        "overlap_percentage": (
            100.0
            * result["valid_pixel_count"]
            / result["total_pixel_count"]
        ),
        "unit": result["first_unit"],
        "first_background": result["first_background"],
        "second_background": result["second_background"],
        "background_offset": result["background_offset"],
        "difference_median": result["difference_median"],
        "difference_std": result["difference_std"],
        "difference_image": result["difference_image"],
        "aligned_first": result["aligned_first"],
        "second_image": result["second_image"],
        "valid_mask": result["valid_mask"],
        "first_sources": first_sources,
        "second_sources": second_sources,
    }
