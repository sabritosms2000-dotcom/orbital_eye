"""Catalog propagation and measured-vs-predicted FITS astrometry."""
import numpy as np
from astropy.coordinates import SkyCoord, CartesianRepresentation, ICRS, get_body_barycentric
from astropy.time import Time
import astropy.units as u

def predict_position(target, time):
    r=target["reference"]; base=SkyCoord(r["ra_deg"]*u.deg,r["dec_deg"]*u.deg,frame="icrs")
    pmra=r.get("pm_ra_cosdec_mas_yr"); pmdec=r.get("pm_dec_mas_yr")
    if pmra is None or pmdec is None: return base
    kw={}
    if r.get("parallax_mas"): kw["distance"]=(1000/r["parallax_mas"])*u.pc
    if r.get("radial_velocity_kms") is not None and "distance" in kw: kw["radial_velocity"]=r["radial_velocity_kms"]*u.km/u.s
    source=SkyCoord(ra=base.ra,dec=base.dec,pm_ra_cosdec=pmra*u.mas/u.yr,pm_dec=pmdec*u.mas/u.yr,
        obstime=Time(r["epoch_mjd"],format="mjd"),frame="icrs",**kw)
    moved=source.apply_space_motion(new_obstime=time)
    if "distance" not in kw: return moved
    earth=get_body_barycentric("earth",time).xyz.to(u.au)
    return SkyCoord(CartesianRepresentation(moved.cartesian.xyz.to(u.au)-earth),frame=ICRS())

def compare_epochs(a,b):
    dt=abs((b["mjd"]-a["mjd"])/365.25)
    pa,pb=a.get("predicted"),b.get("predicted")
    pred=SkyCoord(pa["ra_deg"]*u.deg,pa["dec_deg"]*u.deg).separation(SkyCoord(pb["ra_deg"]*u.deg,pb["dec_deg"]*u.deg)).arcsec if pa and pb else None
    ma,mb=a.get("measured_centroid"),b.get("measured_centroid"); measured=None; sig=None; residual=None
    if ma and mb:
        measured=SkyCoord(ma["ra_deg"]*u.deg,ma["dec_deg"]*u.deg).separation(SkyCoord(mb["ra_deg"]*u.deg,mb["dec_deg"]*u.deg)).arcsec
        errors=[ma.get("uncertainty_arcsec"),mb.get("uncertainty_arcsec")]
        if pred is not None and all(x is not None for x in errors):
            residual=measured-pred; sig=abs(residual)/np.hypot(*errors) if np.hypot(*errors)>0 else None
    return {"status":"compared" if dt else "zero_baseline","baseline_years":dt,"predicted_angular_shift_arcsec":pred,
        "measured_angular_shift_arcsec":measured,"predicted_rate_arcsec_yr":pred/dt if pred is not None and dt else None,
        "measured_rate_arcsec_yr":measured/dt if measured is not None and dt else None,
        "measured_minus_predicted_shift_arcsec":residual,"motion_residual_significance_sigma":sig,
        "uncertainty_note":"Centroid-only approximation; excludes WCS and spacecraft systematics."}
