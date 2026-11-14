"""Live IRSA SIA discovery with an explicit local metadata fallback."""
import csv, json
from datetime import datetime, timezone
from pathlib import Path
from astropy.coordinates import SkyCoord
from astropy.time import Time
import astropy.units as u
from .target_registry import get_target

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "wise0855_sia_results.csv"
CACHE = ROOT / "data" / "validation_cache"

def discover_observations(target_id, live_query=True, use_cache=True):
    target = get_target(target_id); cache = CACHE / f"{target['id']}_discovery.json"
    if use_cache and cache.exists():
        cached = json.loads(cache.read_text(encoding="utf-8"))
        if (not live_query and cached.get("query_epoch") == 2025.75) or (live_query and cached.get("query_epoch") == 2025.75 and cached.get("archive_status") in {"queried", "no_records"}):
            cached["from_cache"] = True; return cached
    ref = target["reference"]
    from .astrometry import predict_position
    coord = predict_position(target, Time(2025.75, format="jyear"))
    result = {"target_id": target["id"], "query_center": {"ra_deg": float(coord.ra.deg), "dec_deg": float(coord.dec.deg)},
        "query_epoch": 2025.75, "collection": "spherex_dr1", "queried_at": datetime.now(timezone.utc).isoformat(),
        "archive_status": "live_query_skipped" if not live_query else "unavailable", "live_query_error": None, "record_source": "none", "records": []}
    if live_query:
        try:
            from astroquery.ipac.irsa import Irsa
            table = Irsa.query_sia(pos=(SkyCoord(coord), 1*u.arcmin), collection="spherex_dr1")
            for row in table:
                mjd = row.get("t_min")
                result["records"].append({"obs_id": str(row.get("obs_id")), "date": Time(float(mjd), format="mjd").isot[:10] if mjd is not None else None,
                    "mjd": float(mjd) if mjd is not None else None, "band": row.get("energy_bandpassname"), "detector": None,
                    "access_url": row.get("access_url"), "data_origin": "irsa_sia"})
            result["archive_status"] = "queried" if result["records"] else "no_records"; result["record_source"] = "irsa_sia"
        except Exception as exc:
            result["live_query_error"] = f"{type(exc).__name__}: {exc}"
    if target["id"] == "wise_0855" and CSV_PATH.exists() and result["archive_status"] != "queried":
        try:
            with CSV_PATH.open(newline="", encoding="utf-8-sig") as f:
                for row in csv.DictReader(f):
                    band = row.get("energy_bandpassname")
                    try: mjd = float(row["t_min"])
                    except (TypeError, ValueError): mjd = None
                    result["records"].append({"obs_id": row.get("obs_id"), "date": Time(mjd, format="mjd").isot[:10] if mjd else None,
                        "mjd": mjd, "band": band, "detector": int(band.rsplit("D",1)[1]) if band and band.rsplit("D",1)[1].isdigit() else None,
                        "access_url": row.get("access_url"), "data_origin": "local_sia_csv"})
            result["archive_status"] = "local_index_only"; result["record_source"] = "local_sia_csv"
        except Exception as exc: result["local_index_error"] = f"{type(exc).__name__}: {exc}"
    records = result["records"]; result["record_count"] = len(records)
    result["distinct_dates"] = len({x.get("date") for x in records if x.get("date")})
    result["distinct_observation_ids"] = len({x.get("obs_id") for x in records if x.get("obs_id")})
    result["bands"] = sorted({x.get("band") for x in records if x.get("band")})
    result["preview_records"] = records[:20]
    result["coverage_interpretation"] = "Archive metadata are not target detections or downloaded image measurements."
    CACHE.mkdir(parents=True, exist_ok=True); cache.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    return result
