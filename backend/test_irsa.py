from astroquery.ipac.irsa import Irsa
from astropy.coordinates import SkyCoord
import astropy.units as u

targets = {
    'barnards_star': (269.4485, 4.7394),
    'epsilon_indi_b': (331.0438, -56.7827),
    'wise_0855': (133.79513, -7.24515),
    'rw_aurigae': (76.9565, 30.4014),
    'r_draconis': (248.1676, 66.7541),
}

for name, (ra, dec) in targets.items():
    coord = SkyCoord(ra=ra*u.deg, dec=dec*u.deg, frame='icrs')
    try:
        table = Irsa.query_sia(pos=(coord, 1*u.arcmin), collection='spherex_dr1')
        print(f'{name}: SUCCESS - {len(table)} records')
        if len(table) > 0:
            print(f'  Columns: {table.colnames}')
            print(f'  First row: obs_id={table[0].get("obs_id")}, band={table[0].get("energy_bandpassname")}, date={table[0].get("t_min")}, url={table[0].get("access_url")}')
    except Exception as e:
        print(f'{name}: FAILED - {type(e).__name__}: {e}')