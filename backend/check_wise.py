from validation.engine import validate_target
r = validate_target('wise_0855', False, False)
for i, e in enumerate(r['epochs']):
    print(f'Epoch {i}: obs={e.get("observation")}, band={e.get("band")}, status={e.get("status")}, centroid={e.get("centroid_candidate")}, phot_snr={e.get("photometry",{}).get("snr")}')