# ORBITAL EYE Phase 5: Scientific Validation Report

**Report date:** 2026-11-14

## Target results

All five targets are registered in `backend/validation/target_registry.py`. Reference coordinates are ICRS with epoch, provenance, and a source URL. Unverified kinematics are `null`. Barnard's Star uses Gaia DR3. Epsilon Indi B uses a SIMBAD J2000 position and Gaia DR3 Ba kinematics, with the epoch mismatch marked approximate. RW Aur and R Dra have null proper motion/parallax because verified component appropriate values are not recorded.

| Target | Status | Evidence and limitations |
| --- | --- | --- |
| Barnard's Star | `INSUFFICIENT_DATA` | No local target FITS. Live IRSA query attempted; SIA capabilities endpoint unreachable. Gaia predictions are available, but no image position was measured. |
| Epsilon Indi Ba/Bb | `INSUFFICIENT_DATA` | No local target FITS. Live IRSA query attempted; endpoint unreachable. Published separation is about 0.732 arcsec, only 0.12 of a 6.15 arcsec SPHEREx pixel, so the pair is unresolved in these data. |
| WISE 0855 | `INCONCLUSIVE` | Two local D3 FITS epochs processed. Current aperture SNR is 6.49 and 7.04, but neither centroid is associated with the target: each is more than one detector pixel from its propagated position. No measured target motion is emitted. |
| RW Aurigae | `INSUFFICIENT_DATA` | No local target FITS. Live IRSA query attempted; endpoint unreachable. No compatible photometry or variability test is available. |
| R Draconis | `INSUFFICIENT_DATA` | No local target FITS. Live IRSA query attempted; endpoint unreachable. No complete light curve or variability result is claimed. |

## WISE 0855 evidence audit

The local IRSA SIA CSV has 258 metadata rows, 129 distinct observation IDs, 27 dates from 2025-05-05 to 2026-05-14, and bands D1–D6. These are metadata rows, not downloaded FITS images or detections. The live SIA request failed at `https://irsa.ipac.caltech.edu/SIA/capabilities`; the project falls back to this local index and preserves the error.

| Local epoch | SPHEREx observation ID | UTC date | Detector / band | SNR | Flux (Jy) | 1σ error (Jy) |
| --- | --- | --- | --- | ---: | ---: | ---: |
| first | `2025W19_1B_0116_1` | 2025-05-05 | 3 / SPHEREx-D3 | 6.49 | 4.726e-4 | 7.282e-5 |
| second | `2026W20_1A_0033_1` | 2026-05-11 | 3 / SPHEREx-D3 | 7.04 | 5.713e-4 | 8.112e-5 |

Both cutouts are 59×58 pixels with valid celestial WCS, all finite science pixels, and IMAGE, FLAGS, and VARIANCE extensions. The aperture's nonzero flag is `2097152` (`SOURCE` mask); IRSA documents this as potentially nominal, though source contamination still needs inspection. WCS reprojection gives 3,363 common pixels (98.3%). The difference image is exploratory: it has no PSF matching, calibration normalization, or propagated variance.

The same-band flux difference is about 0.91σ, not statistically significant; these two points do not constitute a complete light curve. The current aperture calculation does not reproduce the earlier approximate SNR values 1.58 and 0.31. The exact aperture, background annulus, predicted center, and flux/error calculation are in `backend/validation/photometry.py`.

The catalog model predicts an 8.26 arcsec shift over the 1.014-year baseline (8.14 arcsec/year); this is a prediction only. The local image centroid candidates are offset from the predicted target positions by about 9.87 and 14.91 arcsec, both greater than the approximately 6.15 arcsec detector pixel scale. Despite aperture SNR above 5, the pipeline rejects both centroids as target positions because their association is uncertain. Consequently `measured_angular_shift_arcsec` is null and no measured motion rate is reported. The earlier 0.74-pixel value is not an independent target displacement measurement. This target remains `INCONCLUSIVE`; the `Likely moving source` label is not returned.

The repository also contains a separate 68.4 MB FITS image, observation `2025W19_2B_0073_2` (detector 3, 2025-05-08), centered near RA 156.093°, Dec -41.647°. WISE 0855 is outside its field and its WCS projection fails to converge there, so it is excluded from WISE target epochs.

## Implementation

- Modular registry, archive discovery, FITS quality checks, motion prediction, gated centroiding, aperture photometry, compatible-band variability, plots, and image comparison.
- Motion centroids below SNR 5 are excluded from measured positions. Photometric detection uses SNR 3; variability needs compatible epochs and at least 3σ significance.
- Required target, run, result, light-curve, motion, and evidence APIs are registered. The legacy `/api/validation/run-all` route remains available.
- Validation Lab uses per-target POST requests and displays reference frame/epoch, observation IDs/dates/bands/detectors, quality flags, SNR, predicted/measured positions, uncertainty, plots, FITS images, and limitations.
- Synthetic unit tests (`backend/test_validation_synthetic.py`) are separated from local FITS integration tests (`backend/test_validation.py`). API contract tests are in `backend/test_validation_api.py`.

## Verification

- `python -m unittest test_validation test_validation_synthetic test_validation_api -v` from `backend`: **10 passed**, covering real FITS, clearly labeled synthetic astrometry, API registration, and WISE 0855 run/result/evidence/plot/image endpoints.
- `next build` from `frontend`: **passed**, including TypeScript and static generation.
- Live IRSA SIA queries were attempted for all five targets. The capabilities endpoint was unreachable. WISE used the local metadata CSV; archive coverage for the other four remains unknown.

## Sources

- [IRSA SPHEREx archive and DR1](https://irsa.ipac.caltech.edu/Missions/spherex.html)
- [SPHEREx data products and FITS flags](https://caltech-ipac.github.io/spherex-archive-documentation/spherex-data-products/)
- [IRSA flag guidance](https://irsa.ipac.caltech.edu/onlinehelp/spherex/help.pdf?id=607b86d)
- [Gaia DR3 documentation](https://gea.esac.esa.int/archive/documentation/GDR3/)
- [SIMBAD Epsilon Indi B](https://simbad.u-strasbg.fr/simbad/sim-id?Ident=%2A+eps+Ind+B)
- [Epsilon Indi Ba/Bb separation reference](https://arxiv.org/abs/astro-ph/0309256)
- [WISE 0855 astrometry reference](https://ui.adsabs.harvard.edu/abs/2016AJ....152...70L/abstract)
- [SIMBAD RW Aur](https://simbad.cds.unistra.fr/simbad/sim-id?Ident=RW+Aur) and [SIMBAD R Dra](https://simbad.u-strasbg.fr/simbad/sim-id?Ident=R+Dra)

## Remaining limitation

Retry the live archive queries when IRSA is reachable, then download and validate any additional observations. Review WISE 0855 source identification, aperture correction, and instrument/spacecraft astrometric systematics before changing its `INCONCLUSIVE` status.
