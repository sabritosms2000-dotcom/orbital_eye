"""Five-target FITS validation engine."""
from pathlib import Path
import numpy as np
from astropy.io import fits
from astropy.time import Time
from astropy.wcs import WCS
from photutils.centroids import centroid_com
from .target_registry import get_target, TARGETS
from .astrometry import predict_position, compare_epochs
from .photometry import quality, aperture
from .observation_discovery import discover_observations

ROOT=Path(__file__).resolve().parents[2]

def _local_files(t):
    return [{**x,"path":str(ROOT/x["relative_path"]),"exists":(ROOT/x["relative_path"]).exists(),"data_origin":"local_download"} for x in t.get("local_fits",[])]

def _phot_test(epochs):
    grouped={}
    for e in epochs:
        p=e.get("photometry") or {}
        if p.get("status")=="measured" and e.get("band") and e.get("unit"):
            grouped.setdefault((e["band"],e["unit"]),[]).append(e)
    group=max(grouped.values(),key=len) if grouped else []
    if len(group)<2: return {"result":"insufficient_photometry","status":"insufficient_epochs","interpretation":"Fewer than two compatible same-band, same-unit measurements."}
    a,b=group[0],group[-1]; p,q=a["photometry"],b["photometry"]
    sigma=float(np.hypot(p["flux_error_jy"],q["flux_error_jy"])); diff=float(q["flux_jy"]-p["flux_jy"]); sig=abs(diff)/sigma if sigma else None
    if not p["detected_snr_ge_3"] or not q["detected_snr_ge_3"]: result="mixed_or_low_snr"
    else: result="candidate_variability" if sig is not None and sig>=3 else "no_significant_variability"
    return {"status":"compared","result":result,"compatible_band":a["band"],"compatible_unit":a["unit"],"flux_epoch_1_jy":p["flux_jy"],"flux_error_epoch_1_jy":p["flux_error_jy"],
        "flux_epoch_2_jy":q["flux_jy"],"flux_error_epoch_2_jy":q["flux_error_jy"],"significance_sigma":sig,
        "interpretation":f"Compatible-epoch flux difference is {sig:.2f} sigma; two observations are not a complete light curve." if sig is not None else "No significant variability test."}

def validate_target(target_id,live_archive_query=True,use_discovery_cache=True):
    t=get_target(target_id); discovery=discover_observations(t["id"],live_query=live_archive_query,use_cache=use_discovery_cache)
    local=_local_files(t); epochs=[]; qcs=[]
    for item in local:
        if not item["exists"]:
            epochs.append({"observation":item["observation_id"],"status":"missing_file","data_class":"unavailable"}); continue
        qc=quality(item["path"]); qc["observation"] = item["observation_id"]; qcs.append(qc)
        if not qc["accepted"]:
            epochs.append({"observation":item["observation_id"],"status":"rejected","rejection_reasons":qc["rejection_reasons"]}); continue
        with fits.open(item["path"],memmap=True) as h:
            hd=h["IMAGE"].header; mjd=float(hd.get("MJD-AVG",hd.get("MJD-OBS"))); time=Time(mjd,format="mjd")
            coord=predict_position(t,time); wcs=WCS(hd).celestial; x,y=wcs.world_to_pixel(coord); inside=bool(np.isfinite(x) and np.isfinite(y) and 0<=x<hd.get("NAXIS1",2040) and 0<=y<hd.get("NAXIS2",2040))
            row=next((r for r in discovery["records"] if r.get("obs_id")==hd.get("OBSID") and (r.get("detector") is None or r.get("detector")==int(hd.get("DETECTOR",-1)))),None)
            band=(row or {}).get("band") or hd.get("ENERGY_BANDPASSNAME") or hd.get("BAND"); unit=hd.get("BUNIT")
            phot=aperture(item["path"],float(x),float(y)) if inside else None
            centroid=None; candidate=None
            if inside:
                # Read small cutout for centroiding (memory efficient)
                radius=4; x0=max(0,int(x)-radius); x1=min(hd.get("NAXIS1",2040),int(x)+radius+1); y0=max(0,int(y)-radius); y1=min(hd.get("NAXIS2",2040),int(y)+radius+1)
                stamp = np.asarray(h["IMAGE"].section[y0:y1, x0:x1], dtype=float)
                bg = float(np.nanmedian(stamp))
                net = np.where(np.isfinite(stamp), np.maximum(stamp - bg, 0), 0)
                if net.sum() > 0:
                    cx, cy = centroid_com(net)
                    mc = wcs.pixel_to_world(x0 + cx, y0 + cy)
                    scale = float(np.sqrt(wcs.proj_plane_pixel_area().to_value("deg2")) * 3600)
                    candidate = {"ra_deg": float(mc.ra.deg), "dec_deg": float(mc.dec.deg), "pixel_x": float(x0 + cx), "pixel_y": float(y0 + cy), "offset_arcsec": float(np.hypot(x0 + cx - x, y0 + cy - y) * scale)}
                    if phot and phot.get("snr", 0) >= 5 and candidate["offset_arcsec"] <= scale:
                        candidate["uncertainty_arcsec"] = float(2.5 / (2.355 * phot["snr"]) * scale); centroid = candidate
            if phot: phot["quality_flags"] = phot.get("quality_flags",[])
            epochs.append({"observation":item["observation_id"],"observation_id":hd.get("OBSID"),"status":"success","date":time.isot,"mjd":mjd,
                "band":band,"detector":int(hd["DETECTOR"]) if hd.get("DETECTOR") is not None else None,"unit":unit,
                "predicted":{"data_class":"prediction","ra_deg":float(coord.ra.deg),"dec_deg":float(coord.dec.deg),"pixel_x":float(x) if np.isfinite(x) else None,"pixel_y":float(y) if np.isfinite(y) else None,"inside_image":inside},
                "measured_centroid":centroid,"centroid_candidate":candidate if centroid is None else None,"photometry":phot,
                "source_detection_confidence":{"snr":phot.get("snr") if phot else None,"threshold_sigma":5,"centroid_accepted":centroid is not None,"warning":"Centroid is not accepted as the target unless SNR >= 5 and its offset from the propagated position is <= one detector pixel." if centroid is None else "Centroid uncertainty excludes WCS systematics."},
                "quality_flags":(phot or {}).get("quality_flags",[]),"wcs_checked":True,"wcs_frame":wcs.wcs.radesys})
    successful=[e for e in epochs if e.get("status")=="success"]
    motion=compare_epochs(successful[0],successful[-1]) if len(successful)>1 else {"status":"insufficient_epochs","measured_angular_shift_arcsec":None}
    photo=_phot_test(successful)
    image_comparison={"status":"insufficient_epochs","difference_image_available":False,"reason":"Need two accepted compatible local FITS epochs."}
    if len(successful)>1:
        a,b=successful[0],successful[-1]
        if a.get("band") and a.get("band")==b.get("band") and a.get("unit")==b.get("unit"):
            try:
                from image_processing import align_observations
                aligned=align_observations(local[0]["path"],local[-1]["path"]); mask=aligned["valid_mask"]; d=aligned["second_image"][mask]-aligned["aligned_first"][mask]
                image_comparison={"status":"wcs_aligned","first_observation":a["observation_id"],"second_observation":b["observation_id"],"band":a["band"],"valid_pixels":int(mask.sum()),"total_pixels":int(mask.size),"overlap_fraction":float(mask.mean()),"difference_median":float(np.median(d)),"difference_std":float(np.std(d)),"difference_image_available":True,"note":"Exploratory: no PSF matching or propagated variance."}
            except Exception as e: image_comparison={"status":"failed","reason":str(e),"difference_image_available":False}
        else: image_comparison={"status":"incompatible_epochs","reason":"Band or units differ/unknown.","difference_image_available":False}
    science=t["science_case"]
    if not successful: status="INSUFFICIENT_DATA"
    elif science=="astrometry":
        if sum(e.get("measured_centroid") is not None for e in epochs)<2: status="INCONCLUSIVE" if successful else "INSUFFICIENT_DATA"
        elif motion.get("motion_residual_significance_sigma") and motion["motion_residual_significance_sigma"]>2.5: status="INCONCLUSIVE"
        else: status="PARTIALLY_VALIDATED"
    else: status="PARTIALLY_VALIDATED" if photo.get("result") in {"candidate_variability","no_significant_variability"} else "INCONCLUSIVE"
    if not local and not successful: status="INSUFFICIENT_DATA"
    return {"target":{k:t[k] for k in ("id","name","object_type","science_case","science_goal","reference")},"validation_status":status,
        "archive_discovery":discovery,"local_fits":local,"data_quality":qcs,"epochs":epochs,"epoch_comparison":motion,
        "photometric_test":photo,"image_comparison":image_comparison,"is_confirmed_detection":False,
        "limitations":["Predictions are not measurements.","WCS/spacecraft systematic uncertainties are not included.","Archive rows are metadata, not target detections."]}

def validate_all_targets(live_archive_query=True,use_discovery_cache=True):
    reports=[validate_target(tid,live_archive_query,use_discovery_cache) for tid in ("barnards_star","epsilon_indi_b","wise_0855","rw_aurigae","r_draconis")]
    return {"status":"completed","count":len(reports),"results":reports}
