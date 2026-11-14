"""Small diagnostic plots for evidence APIs."""
import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def plot(report,kind):
    fig,ax=plt.subplots(figsize=(7,4)); epochs=report.get("epochs",[])
    if kind=="photometry":
        rows=[e for e in epochs if (e.get("photometry") or {}).get("status")=="measured"]
        if rows:
            x=[e.get("mjd",i) for i,e in enumerate(rows)]; y=[e["photometry"]["flux_jy"]*1e6 for e in rows]; err=[e["photometry"]["flux_error_jy"]*1e6 for e in rows]
            ax.errorbar(x,y,yerr=err,fmt="o",capsize=4); ax.set_xlabel("MJD"); ax.set_ylabel("Aperture flux (µJy)")
        else: ax.text(.5,.5,"No measured photometry",ha="center",transform=ax.transAxes)
        ax.set_title("Compatible-band photometry with 1σ errors")
    else:
        pred=[e.get("predicted") for e in epochs if e.get("predicted")]; meas=[e.get("measured_centroid") for e in epochs if e.get("measured_centroid")]
        if pred: ax.plot([p["ra_deg"] for p in pred],[p["dec_deg"] for p in pred],"o--",label="Predicted")
        if meas: ax.scatter([m["ra_deg"] for m in meas],[m["dec_deg"] for m in meas],marker="x",label="Measured")
        ax.set_xlabel("RA (deg)"); ax.set_ylabel("Dec (deg)"); ax.set_title("Prediction and measured centroid are distinct"); ax.legend()
    buf=io.BytesIO(); fig.tight_layout(); fig.savefig(buf,format="png"); plt.close(fig); buf.seek(0); return buf

def difference_plot(first_path,second_path):
    from image_processing import align_observations
    import numpy as np
    aligned=align_observations(first_path,second_path)
    diff=aligned["second_image"]-aligned["aligned_first"]
    mask=aligned["valid_mask"]; values=diff[mask]
    if not values.size: raise ValueError("No WCS-aligned overlap pixels.")
    lim=float(np.percentile(np.abs(values),95)) or 1e-8
    fig,ax=plt.subplots(figsize=(6,5)); ax.imshow(diff,origin="lower",cmap="coolwarm",vmin=-lim,vmax=lim); ax.set_title("WCS-aligned difference (exploratory)"); ax.set_axis_off()
    buf=io.BytesIO(); fig.tight_layout(); fig.savefig(buf,format="png"); plt.close(fig); buf.seek(0); return buf
