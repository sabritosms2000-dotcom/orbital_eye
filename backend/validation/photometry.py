"""Aperture photometry, pixel flags, and FITS quality checks."""
from pathlib import Path
import numpy as np
from astropy.io import fits
from astropy.wcs import WCS

FLAG_NAMES={2097152:"SOURCE"}

def quality(path):
    out={"filename":Path(path).name,"accepted":False,"rejection_reasons":[],"warnings":[]}
    try:
        with fits.open(path,memmap=True) as h:
            im=h["IMAGE"].data; flags=h["FLAGS"].data; var=h["VARIANCE"].data; hdr=h["IMAGE"].header
            out.update({"observation_id":hdr.get("OBSID"),"date":hdr.get("DATE-OBS"),"mjd":hdr.get("MJD-AVG",hdr.get("MJD-OBS")),
                "detector":hdr.get("DETECTOR"),"unit":hdr.get("BUNIT"),"l1_quality_flag":hdr.get("L1DQAFLG"),"l2_quality_flag":hdr.get("L2DQAFLG"),
                "extensions":[x.name for x in h],"image_shape":list(im.shape),"finite_pixel_fraction":float(np.isfinite(im).mean()),
                "flagged_pixel_fraction":float(np.mean(flags!=0)),"has_celestial_wcs":bool(WCS(hdr).celestial.has_celestial)})
            if hdr.get("L2DQAFLG") not in (None,"Pass","PASS","pass"): out["warnings"].append(f"FITS L2DQAFLG={hdr.get('L2DQAFLG')}")
            if hdr.get("BUNIT") and hdr.get("BUNIT").replace(" ","").lower() not in {"mjy/sr","mjy/sr"}: out["warnings"].append(f"Unrecognized BUNIT {hdr.get('BUNIT')}")
            if im.ndim!=2 or not all(x in h for x in ("FLAGS","VARIANCE")): out["rejection_reasons"].append("Required 2D IMAGE/FLAGS/VARIANCE data unavailable")
            if not out["has_celestial_wcs"]: out["rejection_reasons"].append("Missing celestial WCS")
            if not np.isfinite(im).any(): out["rejection_reasons"].append("No finite science pixels")
            if out["finite_pixel_fraction"]<.5: out["rejection_reasons"].append("Less than half of science pixels finite")
            out["accepted"]=not out["rejection_reasons"]
    except Exception as e: out["rejection_reasons"].append(f"FITS read failed: {type(e).__name__}: {e}")
    return out

def aperture(path,x,y,radius=2.0):
    """Memory-efficient aperture photometry: reads only the cutout region around (x,y)."""
    # Determine cutout bounds (expand by annulus + margin)
    ann_outer = max(int(radius) + 7, 20)
    margin = ann_outer + 10
    with fits.open(path, memmap=True) as h:
        im_shape = h["IMAGE"].data.shape
        hdr = h["IMAGE"].header
        wcs = WCS(hdr).celestial
        area = float(wcs.proj_plane_pixel_area().to_value("deg2")) * (np.pi/180)**2
        
        # Clamp cutout to image bounds
        x_int, y_int = int(round(x)), int(round(y))
        x0 = max(0, x_int - margin)
        y0 = max(0, y_int - margin)
        x1 = min(im_shape[1], x_int + margin + 1)
        y1 = min(im_shape[0], y_int + margin + 1)
        
        # Read only the cutout section
        im = np.asarray(h["IMAGE"].section[y0:y1, x0:x1], dtype=float)
        var = np.asarray(h["VARIANCE"].section[y0:y1, x0:x1], dtype=float)
        flags = np.asarray(h["FLAGS"].section[y0:y1, x0:x1])
        
        # Local coordinates within cutout
        lx = x - x0
        ly = y - y0
        
        if not (0 <= lx < im.shape[1] and 0 <= ly < im.shape[0]):
            return {"status": "rejected", "reason": "Target outside cutout"}
        
        yy, xx = np.indices(im.shape)
        d = np.hypot(xx - lx, yy - ly)
        ap = (d <= radius) & np.isfinite(im)
        ann = (d >= 4) & (d <= 7) & np.isfinite(im)
        
        if ap.sum() < 1 or ann.sum() < 5:
            return {"status": "rejected", "reason": "Aperture or background outside image or insufficient pixels"}
        
        bg = float(np.median(im[ann]))
        noise = 1.4826 * float(np.median(np.abs(im[ann] - bg)))
        net = float(np.sum(im[ap] - bg))
        vs = np.asarray(var[ap])
        err = float(np.sqrt(np.nansum(vs[vs >= 0]) + ap.sum() * noise**2))
        
        flux = net * area * 1e6
        fluxerr = err * area * 1e6
        snr = flux / fluxerr if fluxerr > 0 else 0
        unique, counts = np.unique(flags[ap], return_counts=True)
        flagged = [{"value": int(v), "name": FLAG_NAMES.get(int(v), "UNKNOWN"), "pixels": int(c)} for v, c in zip(unique, counts)]
        
        return {"status": "measured", "flux_jy": flux, "flux_error_jy": fluxerr, "snr": snr, "detected_snr_ge_3": bool(snr >= 3 and flux > 0),
            "quality_flags": flagged, "flagged_pixel_fraction": float(np.mean(flags[ap] != 0)), "background_mjy_sr": bg, "background_noise_mjy_sr": noise,
            "aperture_radius_px": radius, "contamination_warning": "Aperture/annulus does not model neighboring sources; inspect flags and image.",
            "quality_warning": "2097152 SOURCE is a potentially nominal mask; other flag meanings need release-specific review."}
