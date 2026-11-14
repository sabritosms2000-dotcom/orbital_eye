"""Five target reference records. Values are catalog references, not detections."""

from copy import deepcopy

J2000_MJD = 51544.5
J2016_MJD = 57388.0

TARGETS = {
    "barnards_star": {
        "id": "barnards_star", "name": "Barnard's Star", "object_type": "M4V high-proper-motion red dwarf",
        "science_case": "astrometry", "aliases": ["Barnard", "GJ 699"],
        "science_goal": "Measure apparent movement between epochs using proper motion and parallax.",
        "reference": {"catalog": "Gaia DR3", "catalog_id": "4472832130942575872", "frame": "ICRS", "ra_deg": 269.448502525, "dec_deg": 4.739420404,
            "epoch_label": "J2016.0", "epoch_mjd": J2016_MJD, "pm_ra_cosdec_mas_yr": -801.551, "pm_dec_mas_yr": 10362.394,
            "parallax_mas": 546.9759, "radial_velocity_kms": -110.51, "coordinate_uncertainty_mas": None, "pm_uncertainty_mas_yr": None, "parallax_uncertainty_mas": None, "radial_velocity_uncertainty_kms": None, "provenance": "Gaia DR3 source 4472832130942575872; ICRS position and astrometry at J2016.0.",
            "reference_url": "https://gea.esac.esa.int/archive/documentation/GDR3/"},
        "local_fits": [
            {"observation_id": "barnards_star_1", "relative_path": "data/barnards_star_2025W33_2C_0321_1_SPHEREx-D3.fits"},
            {"observation_id": "barnards_star_2", "relative_path": "data/barnards_star_2025W33_2C_0321_1_SPHEREx-D6.fits"},
            {"observation_id": "barnards_star_3", "relative_path": "data/barnards_star_2025W33_2C_0321_2_SPHEREx-D3.fits"},
            {"observation_id": "barnards_star_4", "relative_path": "data/barnards_star_2025W33_2C_0321_2_SPHEREx-D6.fits"},
            {"observation_id": "barnards_star_5", "relative_path": "data/barnards_star_2025W34_2B_0090_4_SPHEREx-D2.fits"},
            {"observation_id": "barnards_star_6", "relative_path": "data/barnards_star_2025W34_2B_0090_4_SPHEREx-D5.fits"},
            {"observation_id": "barnards_star_7", "relative_path": "data/barnards_star_2025W34_2B_0557_1_SPHEREx-D2.fits"},
            {"observation_id": "barnards_star_8", "relative_path": "data/barnards_star_2025W34_2B_0557_1_SPHEREx-D5.fits"},
            {"observation_id": "barnards_star_9", "relative_path": "data/barnards_star_2025W35_1A_0432_4_SPHEREx-D1.fits"},
            {"observation_id": "barnards_star_10", "relative_path": "data/barnards_star_2025W35_1A_0432_4_SPHEREx-D4.fits"},
            {"observation_id": "barnards_star_11", "relative_path": "data/barnards_star_2025W35_1A_0658_1_SPHEREx-D1.fits"},
            {"observation_id": "barnards_star_12", "relative_path": "data/barnards_star_2025W35_1A_0658_1_SPHEREx-D4.fits"},
        ]},
    "epsilon_indi_b": {
        "id": "epsilon_indi_b", "name": "Epsilon Indi Ba/Bb", "object_type": "Binary brown dwarf system (Ba T1 + Bb T6)",
        "science_case": "astrometry", "aliases": ["Epsilon Indi B", "eps Ind Ba/Bb"],
        "science_goal": "Test detectability and motion; treat Ba/Bb separately only if the images resolve them.",
        "reference": {"catalog": "SIMBAD position + Gaia DR3 Ba astrometry", "catalog_id": "Gaia DR3 6412596012146801152", "frame": "ICRS", "ra_deg": 331.043839, "dec_deg": -56.782688,
            "epoch_label": "J2000.0 position; Gaia DR3 motion epoch J2016.0", "epoch_mjd": J2000_MJD, "pm_ra_cosdec_mas_yr": 3981.977, "pm_dec_mas_yr": -2466.832,
            "parallax_mas": 270.658, "radial_velocity_kms": None, "coordinate_uncertainty_mas": None, "pm_uncertainty_mas_yr": None, "parallax_uncertainty_mas": None, "radial_velocity_uncertainty_kms": None, "provenance": "SIMBAD ICRS J2000 system coordinate; proper motion and parallax are Gaia DR3 Ba values. Epoch mismatch is approximate. Published Ba/Bb separation 0.732 arcsec; SPHEREx pixel scale is about 6.15 arcsec.",
            "reference_url": "https://simbad.u-strasbg.fr/simbad/sim-id?Ident=%2A+eps+Ind+B"},
        "local_fits": [
            {"observation_id": "epsilon_indi_b_1", "relative_path": "data/epsilon_indi_b_2025W17_4B_0017_1_SPHEREx-D2.fits"},
            {"observation_id": "epsilon_indi_b_2", "relative_path": "data/epsilon_indi_b_2025W17_4B_0017_1_SPHEREx-D5.fits"},
            {"observation_id": "epsilon_indi_b_3", "relative_path": "data/epsilon_indi_b_2025W17_4B_0017_2_SPHEREx-D2.fits"},
            {"observation_id": "epsilon_indi_b_4", "relative_path": "data/epsilon_indi_b_2025W17_4B_0017_2_SPHEREx-D5.fits"},
            {"observation_id": "epsilon_indi_b_5", "relative_path": "data/epsilon_indi_b_2025W17_4B_0077_2_SPHEREx-D4.fits"},
            {"observation_id": "epsilon_indi_b_6", "relative_path": "data/epsilon_indi_b_2025W17_4B_0077_3_SPHEREx-D1.fits"},
            {"observation_id": "epsilon_indi_b_7", "relative_path": "data/epsilon_indi_b_2025W17_4B_0077_3_SPHEREx-D4.fits"},
            {"observation_id": "epsilon_indi_b_8", "relative_path": "data/epsilon_indi_b_2025W17_4B_0468_1_SPHEREx-D1.fits"},
            {"observation_id": "epsilon_indi_b_9", "relative_path": "data/epsilon_indi_b_2025W18_1B_0081_2_SPHEREx-D3.fits"},
            {"observation_id": "epsilon_indi_b_10", "relative_path": "data/epsilon_indi_b_2025W18_1B_0081_2_SPHEREx-D6.fits"},
            {"observation_id": "epsilon_indi_b_11", "relative_path": "data/epsilon_indi_b_2025W18_1B_0081_3_SPHEREx-D3.fits"},
            {"observation_id": "epsilon_indi_b_12", "relative_path": "data/epsilon_indi_b_2025W18_1B_0081_3_SPHEREx-D6.fits"},
        ]},
    "wise_0855": {
        "id": "wise_0855", "name": "WISE 0855 (WISE J085510.83−071442.5)", "object_type": "Extremely cold Y-dwarf brown dwarf",
        "science_case": "astrometry", "aliases": ["WISE 0855", "WISE J085510.83-071442.5"],
        "science_goal": "Assess detectability and measured movement; low-SNR centroids cannot confirm motion.",
        "reference": {"catalog": "Luhman & Esplin 2016", "catalog_id": "WISE J085510.83-071442.5", "frame": "ICRS", "ra_deg": 133.79513, "dec_deg": -7.24515,
            "epoch_label": "MJD 55320.4", "epoch_mjd": 55320.4, "pm_ra_cosdec_mas_yr": -8118.0, "pm_dec_mas_yr": 680.0,
            "parallax_mas": 449.0, "radial_velocity_kms": None, "coordinate_uncertainty_mas": None, "pm_uncertainty_mas_yr": None, "parallax_uncertainty_mas": None, "radial_velocity_uncertainty_kms": None, "provenance": "Project astrometry from Luhman & Esplin (2016); RV unknown. Parallax propagation is geocentric, without spacecraft ephemeris.",
            "reference_url": "https://ui.adsabs.harvard.edu/abs/2016AJ....152...70L/abstract"},
        "local_fits": [
            {"observation_id": "first", "relative_path": "data/wise0855_first_cutout.fits"},
            {"observation_id": "second", "relative_path": "data/wise0855_second_cutout.fits"},
            {"observation_id": "wise_0855_3", "relative_path": "data/wise_0855_2025W19_1B_0116_1_SPHEREx-D3.fits"},
        ]},
    "rw_aurigae": {
        "id": "rw_aurigae", "name": "RW Aurigae", "object_type": "Young variable T Tauri binary system",
        "science_case": "photometry", "aliases": ["RW Aur", "HD 240764"],
        "science_goal": "Compare calibrated compatible-band fluxes across epochs with contamination checks.",
        "reference": {"catalog": "SIMBAD", "catalog_id": "RW Aur", "frame": "ICRS", "ra_deg": 76.9565267, "dec_deg": 30.4014381,
            "epoch_label": "J2000.0", "epoch_mjd": J2000_MJD, "pm_ra_cosdec_mas_yr": None, "pm_dec_mas_yr": None, "parallax_mas": None,
            "radial_velocity_kms": None, "coordinate_uncertainty_mas": None, "pm_uncertainty_mas_yr": None, "parallax_uncertainty_mas": None, "radial_velocity_uncertainty_kms": None, "provenance": "SIMBAD ICRS J2000 position. Component-specific astrometry is unverified here; binary blending is possible.",
            "reference_url": "https://simbad.cds.unistra.fr/simbad/sim-id?Ident=RW+Aur"},
        "local_fits": [
            {"observation_id": "rw_aurigae_1", "relative_path": "data/rw_aurigae_2025W36_1A_0095_1_SPHEREx-D1.fits"},
            {"observation_id": "rw_aurigae_2", "relative_path": "data/rw_aurigae_2025W36_1A_0095_1_SPHEREx-D4.fits"},
        ]},
    "r_draconis": {
        "id": "r_draconis", "name": "R Draconis", "object_type": "Mira-type long-period variable",
        "science_case": "photometry", "aliases": ["R Dra", "HD 149787"],
        "science_goal": "Measure brightness changes only from comparable epochs; do not imply a full light curve.",
        "reference": {"catalog": "SIMBAD", "catalog_id": "R Dra", "frame": "ICRS", "ra_deg": 248.167636, "dec_deg": 66.754149,
            "epoch_label": "J2000.0", "epoch_mjd": J2000_MJD, "pm_ra_cosdec_mas_yr": None, "pm_dec_mas_yr": None, "parallax_mas": None,
            "radial_velocity_kms": None, "coordinate_uncertainty_mas": None, "pm_uncertainty_mas_yr": None, "parallax_uncertainty_mas": None, "radial_velocity_uncertainty_kms": None, "provenance": "SIMBAD ICRS J2000 position; astrometric parameters remain unknown in this registry.",
            "reference_url": "https://simbad.u-strasbg.fr/simbad/sim-id?Ident=R+Dra"},
        "local_fits": [
            {"observation_id": "r_draconis_1", "relative_path": "data/r_draconis_2025W20_2D_0243_1_SPHEREx-D3.fits"},
            {"observation_id": "r_draconis_2", "relative_path": "data/r_draconis_2025W20_2D_0243_2_SPHEREx-D6.fits"},
        ]},
}

def list_targets():
    return deepcopy(list(TARGETS.values()))

def get_target(target_id):
    key = (target_id or "").lower().strip()
    aliases = {a.lower(): t["id"] for t in TARGETS.values() for a in t["aliases"]}
    target = TARGETS.get(key) or TARGETS.get(aliases.get(key, ""))
    if target is None:
        raise KeyError(f"Unknown validation target: {target_id}")
    return deepcopy(target)